"""Tang dich vu du bao — thuan logic, khong Streamlit, khong FastAPI.

Ca dashboard lan API deu goi cung module nay, nen mot du bao chay tu Streamlit va
mot du bao chay tu `/forecast` cho ra ket qua giong het nhau. Truoc day logic nhan
nguoc chuan hoa nam trong pages/1_TimeSeries.py — dat trong tang giao dien thi khong
tai su dung duoc va de lech voi pipeline.

CACH DU BAO XA (14 ngay = 1.344 buoc 15 phut)
---------------------------------------------
Mo hinh chi du bao 1 buoc (T+15 phut). De di xa hon phai DE QUY: gia tri vua du bao
duoc dua nguoc vao lich su, tro thanh dau vao lag/rolling cho buoc ke tiep. Dung nhu
yeu cau "du bao 1 tuan roi lay tuan do lam dau vao cho tuan sau".

Tach lam 2 nhom dac trung, va day la diem mau chot:
  - Nhom BIET TRUOC (hinh hoc mat troi, nhan thoi gian, thoi tiet du bao Open-Meteo):
    tinh mot lan cho toan bo chan troi ngay tu dau. Khong phu thuoc vao san luong.
  - Nhom PHU THUOC SAN LUONG (lag_4, lag_96, rolling_*): chi nhom nay moi phai tinh
    lai sau moi buoc, tu lich su da co cong voi cac gia tri vua du bao.

Sai so tich luy: moi buoc de quy dua sai so cua buoc truoc vao dau vao buoc sau. Du
bao cang xa cang kem tin cay — do la ban chat cua de quy, khong phai loi cai dat. Chi
so tren tap test (WAPE ~17,6% tai h1) do NANG LUC 1 BUOC, khong phai do do chinh xac
cua chan troi 14 ngay.
"""
from __future__ import annotations

import importlib.util
import json
import os
import pickle
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

GOC_REPO = Path(__file__).resolve().parents[2]

# Doi phien ban bang bien moi truong DASHBOARD_VERSION, mac dinh v4.
VERSION = os.environ.get("DASHBOARD_VERSION", "v4")
MODEL_ROOT = GOC_REPO / "data" / "model" / VERSION

PIPELINE = GOC_REPO / "srcs/05_machine_learning/forcasting_pipeline"
MLMART = GOC_REPO / "data/mlmart_base" / f"{VERSION}_final_cleaned.parquet"
QUY_MO = MODEL_ROOT / "03_2_features_spatial/quy_mo_tram.json"
CATEGORY_MAPS = MODEL_ROOT / "03_3_features_aggregate" / f"{VERSION}_category_maps.json"
BEST_LOSS = MODEL_ROOT / "07_final_test/best_loss.json"
MODEL_DIR = MODEL_ROOT / "06_train"

BUOC_PHUT = 15
BUOC_MOI_NGAY = 24 * 60 // BUOC_PHUT      # 96
LICH_SU_CAN = 96 + 8                      # du cho lag_96 va rolling_96
OPEN_METEO = "https://api.open-meteo.com/v1/forecast"

# Bien thoi tiet lay tu Open-Meteo — dung ten ma pipeline dang dung.
DOI_TEN_THOI_TIET = {
    "shortwave_radiation": "shortwave_radiation",
    "direct_normal_irradiance": "direct_normal_irradiance",
    "diffuse_radiation": "diffuse_solar_radiation",
    "temperature_2m": "temperature_c",
    # Pipeline dung ten 'cloud_cover_total' (khong phai 'cloud_cover' cua Open-Meteo);
    # dat sai ten thi cloud_x_shortwave khong duoc tao ra.
    "cloud_cover": "cloud_cover_total",
    "cloud_cover_low": "cloud_cover_low",
    "relative_humidity_2m": "relative_humidity",
    "wind_speed_10m": "wind_speed",
    "is_day": "weather_is_day",
    "weather_code": "weather_code",
}


class ForecastDomainError(RuntimeError):
    """Input/artifact contract error safe to show in the dashboard."""


def _doc_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise ForecastDomainError(f"Thiếu {label}: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ForecastDomainError(f"Không đọc được {label}: {path}") from exc
    if not isinstance(value, dict):
        raise ForecastDomainError(f"{label} không hợp lệ: {path}")
    return value


def _loss_tu_validation(horizon: int) -> str:
    best = _doc_json(BEST_LOSS, "best_loss.json")
    entry = best.get(f"h{horizon}")
    if not isinstance(entry, dict) or not isinstance(entry.get("winning_loss"), str):
        raise ForecastDomainError(f"best_loss.json thiếu winning_loss cho h{horizon}")
    return entry["winning_loss"]


def _weather_label(code: object, is_day: object) -> tuple[str, str]:
    try:
        code = int(code)
        is_day = bool(int(is_day))
    except (TypeError, ValueError) as exc:
        raise ForecastDomainError("Open-Meteo trả weather_code/is_day không hợp lệ") from exc

    if code == 0 and is_day:
        return (
            "Sunny / Clear Sky",
            "Troi quang dang, khong co may che phu. Hieu suat toi da; nhiet do cao co the lam giam nhe voltage.",
        )
    if code in (0, 1, 2, 3) and not is_day:
        return "Clear / Cloudy Night", "Dem quang may hoac co may rai rac. Buc xa bang 0, khong phat dien."
    if code in (1, 2) and is_day:
        return "Partly Cloudy", "Troi co may rai rac. Hieu suat cao, co dao dong nhe khi may di chuyen qua tam pin."
    if code == 3 and is_day:
        return "Overcast", "Troi am u, may che phu hoan toan. San luong sut giam manh, chu yeu thu duoc buc xa tan xa."
    if code in (51, 53, 61, 80):
        return "Light Rain / Drizzle", "Mua phun hoac mua rao nhe. Giam san luong, co the rua troi bui ban tren tam pin."
    if code in (55, 63, 65, 81, 82):
        return "Moderate to Heavy Rain", "Mua vua den mua to hoac mua rao xoi xa. San luong tiem can 0, may thuong che phu cao."
    if code in (71, 73, 75, 77, 85, 86):
        return "Snowfall", "Tuyet roi. Nguy hiem cho van hanh, mang pin co the bi che phu boi tuyet."
    raise ForecastDomainError(f"Open-Meteo weather_code={code} chưa có category pipeline")


def _nap(ten: str, duong: Path):
    """Nap module pipeline bang duong dan — ten file bat dau bang so nen khong import thuong duoc."""
    spec = importlib.util.spec_from_file_location(ten, duong)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[ten] = mod
    spec.loader.exec_module(mod)
    return mod


if str(PIPELINE) not in sys.path:
    sys.path.insert(0, str(PIPELINE))


class DichVuDuBao:
    """Nap mo hinh + sieu du lieu tram mot lan, phuc vu nhieu lan goi du bao."""

    def __init__(self, loss: str | None = None, horizon: int = 1):
        if horizon not in (1, 4):
            raise ForecastDomainError(f"Horizon không được hỗ trợ: {horizon}")
        if loss is None:
            loss = _loss_tu_validation(horizon)
        if loss not in ("mae", "huber", "mse"):
            raise ForecastDomainError(f"Loss không được hỗ trợ: {loss}")
        self.loss, self.horizon = loss, horizon
        thu_muc = MODEL_DIR / loss / f"h{horizon}"
        self.cfg_model = _doc_json(thu_muc / "model_config.json", "model_config.json")
        model_path = thu_muc / "model.pkl"
        if not model_path.is_file():
            raise ForecastDomainError(f"Thiếu model.pkl: {model_path}")
        try:
            with open(model_path, "rb") as fh:
                bundle = pickle.load(fh)
        except Exception as exc:
            raise ForecastDomainError(f"Không nạp được model.pkl: {model_path}") from exc
        self.model = bundle.get("model", bundle) if isinstance(bundle, dict) else bundle
        if not hasattr(self.model, "predict"):
            raise ForecastDomainError(f"Artifact không có model.predict: {model_path}")
        if self.cfg_model.get("loss_name") != loss or self.cfg_model.get("horizon_steps") != horizon:
            raise ForecastDomainError(f"Metadata không khớp model path: {thu_muc}")
        try:
            self.features = list(self.cfg_model["features"])
            medians = self.cfg_model["feature_medians"]
            if not self.features or set(medians) != set(self.features):
                raise ValueError
            self.medians = pd.Series(medians, index=self.features, dtype="float64")
            if not np.isfinite(self.medians.to_numpy()).all():
                raise ValueError
            self.chuan_hoa = self.cfg_model["chuan_hoa"]
            self.eps = float(self.cfg_model["eps_elev"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ForecastDomainError(f"Metadata feature/scale không đầy đủ: {thu_muc}") from exc
        self.quy_mo = _doc_json(QUY_MO, "quy_mo_tram.json")
        category = _doc_json(CATEGORY_MAPS, CATEGORY_MAPS.name).get("development_to_test")
        if not isinstance(category, dict):
            raise ForecastDomainError(f"{CATEGORY_MAPS.name} thiếu development_to_test")
        self.category_maps = category
        for name in ("site_id", "weather_condition", "weather_description"):
            if not isinstance(category.get(name), dict):
                raise ForecastDomainError(f"{CATEGORY_MAPS.name} thiếu map {name}")

        from core.config import load_config  # noqa: PLC0415 — can sys.path o tren

        self.cfg = load_config()
        try:
            self.excluded_sites = {int(s) for s in self.cfg.data["exclude_sites"]}
            self.k_target_min = float(self.cfg.train["k_target_min"])
            self.k_target_max = float(self.cfg.train["k_target_max"])
            self.tran_he_so = float(self.cfg.train["tran_cong_suat_he_so"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ForecastDomainError("Config inference thiếu scale/cap hoặc exclude_sites") from exc
        self._s03a = _nap("s03a", PIPELINE / "stages/s03a_time_cyclical.py")
        self._s03b = _nap("s03b", PIPELINE / "stages/s03b_lag_rolling.py")
        self._s04a = _nap("s04a", PIPELINE / "stages/s04a_solar_geometry.py")
        self._s04b = _nap("s04b", PIPELINE / "stages/s04b_downscale_radiation.py")
        self._s04c = _nap("s04c", PIPELINE / "stages/s04c_site_scale.py")
        self._s05a = _nap("s05a", PIPELINE / "stages/s05a_weather_interaction.py")
        self._sieu_du_lieu: pd.DataFrame | None = None

    # ── Sieu du lieu tram ────────────────────────────────────────────────────
    def sieu_du_lieu(self) -> pd.DataFrame:
        if self._sieu_du_lieu is None:
            cot = ["site_id", "latitude", "longitude", "capacity_kw", "number_of_panels"]
            if not MLMART.is_file():
                raise ForecastDomainError(f"Thiếu metadata trạm: {MLMART}")
            try:
                d = pd.read_parquet(MLMART, columns=cot)
            except Exception as exc:
                raise ForecastDomainError(f"Không đọc được metadata trạm: {MLMART}") from exc
            if d.empty or d[cot].isna().any().any():
                raise ForecastDomainError("Metadata trạm có cột thiếu/NaN")
            self._sieu_du_lieu = d.groupby("site_id").first().reset_index()
        return self._sieu_du_lieu

    def danh_sach_tram(self) -> list[int]:
        map_sites = {int(s) for s in self.category_maps["site_id"] if s != "__MISSING__"}
        return sorted(map_sites - self.excluded_sites)

    def _metadata_tram(self, site_id: int) -> pd.Series:
        if site_id in self.excluded_sites:
            raise ForecastDomainError(f"Trạm {site_id} bị loại khỏi training")
        d = self.sieu_du_lieu()
        rows = d[d["site_id"] == site_id]
        if rows.empty:
            raise ForecastDomainError(f"Không có metadata cho trạm {site_id}")
        return rows.iloc[0]

    def _quy_mo_tram(self, site_id: int) -> tuple[float, float, float]:
        values = []
        for name in ("site_scale", "tran_cong_suat", "cs_factor"):
            table = self.quy_mo.get(name)
            if not isinstance(table, dict) or str(site_id) not in table:
                raise ForecastDomainError(f"quy_mo_tram.json thiếu {name} cho trạm {site_id}")
            try:
                value = float(table[str(site_id)])
            except (TypeError, ValueError) as exc:
                raise ForecastDomainError(f"{name} không hợp lệ cho trạm {site_id}") from exc
            if not np.isfinite(value) or value <= 0:
                raise ForecastDomainError(f"{name} không dương cho trạm {site_id}")
            values.append(value)
        return tuple(values)

    def lich_su_gan_nhat(self, site_id: int, so_buoc: int = LICH_SU_CAN) -> pd.DataFrame:
        """Doan cuoi cung cua chuoi san luong that — dung lam moi cho de quy.

        mlmart_base chua co cot energy_source (cot do duoc pipeline tao o stage s01),
        nen chi doc 3 cot chac chan ton tai.
        """
        self._metadata_tram(site_id)
        try:
            d = pd.read_parquet(MLMART, columns=["site_id", "timestamp", "energy_generated_kwh"])
        except Exception as exc:
            raise ForecastDomainError(f"Không đọc được lịch sử sản lượng: {MLMART}") from exc
        d = d[d["site_id"] == site_id].sort_values("timestamp").tail(so_buoc).reset_index(drop=True)
        if len(d) < so_buoc or d[["timestamp", "energy_generated_kwh"]].isna().any().any():
            raise ForecastDomainError(f"Trạm {site_id} thiếu {so_buoc} dòng lịch sử đầy đủ")
        d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce")
        if d["timestamp"].isna().any() or d["timestamp"].diff().iloc[1:].ne(pd.Timedelta(minutes=15)).any():
            raise ForecastDomainError(f"Lịch sử trạm {site_id} không liên tục 15 phút")
        return d

    # ── Thoi tiet ────────────────────────────────────────────────────────────
    def lay_thoi_tiet(self, lat: float, lon: float, so_ngay: int) -> pd.DataFrame:
        """Keo du bao thoi tiet theo gio tu Open-Meteo."""
        import requests  # noqa: PLC0415 — chi can khi thuc su goi mang

        if not 1 <= int(so_ngay) <= 16:
            raise ForecastDomainError(f"Số ngày thời tiết không hợp lệ: {so_ngay}")
        try:
            r = requests.get(OPEN_METEO, params={
                "latitude": lat, "longitude": lon,
                "hourly": ",".join(DOI_TEN_THOI_TIET),
                "forecast_days": int(so_ngay),
                "timezone": "auto",
            }, timeout=30)
            r.raise_for_status()
            h = r.json()["hourly"]
            d = pd.DataFrame(h).rename(columns={"time": "timestamp", **DOI_TEN_THOI_TIET})
        except Exception as exc:
            raise ForecastDomainError(f"Không lấy được weather forecast Open-Meteo: {exc}") from exc
        required = ["timestamp", *DOI_TEN_THOI_TIET.values()]
        if d.empty or any(c not in d.columns for c in required):
            raise ForecastDomainError("Open-Meteo thiếu cột weather bắt buộc")
        d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce")
        if d[required].isna().any().any() or d["timestamp"].duplicated().any():
            raise ForecastDomainError("Open-Meteo trả weather thiếu/NaN/duplicate timestamp")
        labels = [_weather_label(code, day) for code, day in zip(d["weather_code"], d["weather_is_day"])]
        d["weather_condition"], d["weather_description"] = zip(*labels)
        return d

    # ── Dung khung dac trung ─────────────────────────────────────────────────
    def khung_dac_trung(self, site_id: int, thoi_tiet: pd.DataFrame) -> pd.DataFrame:
        """Dung khung 15 phut day du dac trung BIET TRUOC (chua co lag/rolling).

        Thoi tiet Open-Meteo la theo GIO -> ffill xuong 15 phut. Chi ffill, tuyet doi
        khong bfill: bfill se keo gia tri tuong lai ve qua khu, dung sai lech nhan qua.
        """
        md = self._metadata_tram(site_id)
        required = ["timestamp", *DOI_TEN_THOI_TIET.values(), "weather_condition", "weather_description"]
        if thoi_tiet.empty or any(c not in thoi_tiet.columns for c in required):
            raise ForecastDomainError("Weather snapshot thiếu cột bắt buộc")
        if thoi_tiet[required].isna().any().any():
            raise ForecastDomainError("Weather snapshot chứa giá trị thiếu")

        luoi = pd.date_range(thoi_tiet["timestamp"].min(),
                             thoi_tiet["timestamp"].max() + pd.Timedelta(minutes=45),
                             freq=f"{BUOC_PHUT}min")
        d = pd.DataFrame({"timestamp": luoi})
        d = d.merge(thoi_tiet, on="timestamp", how="left").ffill()
        if d[required].isna().any().any():
            raise ForecastDomainError("Weather snapshot không phủ kín lưới 15 phút")
        d["site_id"] = site_id
        for c in ("latitude", "longitude", "capacity_kw", "number_of_panels"):
            d[c] = md[c]

        # s03a tao hour_sin/hour_cos/doy_* nhung khong tao 'hour' va 'interval_hour' tho —
        # hai cot nay nam trong tap dac trung nen phai dung tay o day.
        d["hour"] = d["timestamp"].dt.hour
        d["interval_hour"] = d["timestamp"].dt.hour
        d = self._s03a.add_time_features(d)
        d = self._s04a.add_metadata_features(d)
        d = self._s04a.add_solar_geometry_features(d, self.cfg)
        d = self._s04b.add_downscaled_radiation(d, self.cfg)
        d = self._s04c.add_site_scale_features(d, self.quy_mo)
        d = self._s05a.add_weather_domain_features(d)

        # cs_factor la hang so hieu chinh troi quang cua tung tram, uoc luong tu tap
        # train va luu trong quy_mo_tram.json — khong tinh lai luc du bao.
        _, _, d["cs_factor"] = self._quy_mo_tram(site_id)

        # Ma hoa phan loai — mo hinh nhan so nguyen, khong nhan chuoi.
        site_code = self.category_maps["site_id"].get(str(site_id))
        if site_code is None:
            raise ForecastDomainError(f"Category map thiếu site_id={site_id}")
        d["site_id_enc"] = int(site_code)
        for raw in ("weather_description", "weather_condition"):
            encoded = d[raw].astype("string").map(self.category_maps[raw])
            if encoded.isna().any():
                bad = d.loc[encoded.isna(), raw].iloc[0]
                raise ForecastDomainError(f"Category map thiếu weather {raw}={bad}")
            d[f"{raw}_enc"] = encoded.astype("int32")

        # Dac trung TAT DINH tai moc muc tieu T+h: dich len h buoc. Khong phai leakage —
        # vi tri mat troi va nhan thoi gian tai T+h la lich thien van, dung o T da biet.
        for c in [f for f in self.features if f.endswith("_mt")]:
            goc = c[:-3]
            if goc in d.columns:
                d[c] = d[goc].shift(-self.horizon)
        return d

    # ── De quy ───────────────────────────────────────────────────────────────
    def du_bao(self, site_id: int, so_ngay: int = 14,
               dieu_chinh: dict[str, float] | None = None) -> pd.DataFrame:
        """Du bao san lượng cho `so_ngay` ngay toi.

        `dieu_chinh`: he so nhan ap len dac trung thoi tiet truoc khi du bao, phuc vu
        phan What-if (vi du {"shortwave_radiation": 1.1} = buc xa tang 10%).
        """
        md = self.sieu_du_lieu()
        md = md[md["site_id"] == site_id].iloc[0]
        tt = self.lay_thoi_tiet(float(md["latitude"]), float(md["longitude"]), so_ngay)

        if dieu_chinh:
            for cot, he_so in dieu_chinh.items():
                if cot in tt.columns:
                    tt[cot] = tt[cot] * float(he_so)

        khung = self.khung_dac_trung(site_id, tt)
        lich_su = self.lich_su_gan_nhat(site_id)

        # Chuoi san luong lam viec: lich su that noi tiep cac gia tri se du bao.
        y = list(lich_su["energy_generated_kwh"].astype(float).to_numpy())
        n_lich_su = len(y)

        quy_mo = float(self.quy_mo["site_scale"].get(str(site_id), np.nan))
        tran = float(self.quy_mo["tran_cong_suat"].get(str(site_id), np.nan))
        eps = float(self.cfg_model.get("eps_elev", 0.05))
        # Nguong cat lay TU ARTIFACT. Tu 2026-08-13 no duoc suy tu phan vi 99 cua k tren
        # tap TRAIN nen moi mo hinh mot khac; viet cung 1.5 se cho tran du bao lech han
        # so voi luc train. Thieu thi dung ngay thay vi doan.
        # Phai doc chuan_hoa TRUOC khi dung no o dieu kien ben duoi.
        chuan_hoa = bool(self.cfg_model.get("chuan_hoa"))
        if chuan_hoa and "clip_k" not in self.cfg_model:
            raise ForecastDomainError(
                "model_config.json thieu clip_k - hay chay lai notebook 06 de sinh artifact moi"
            )
        clip_k = float(self.cfg_model.get("clip_k", 1.5))

        ket_qua = []
        for i in range(len(khung) - self.horizon):
            hang = khung.iloc[[i]].copy()
            lich = np.array(y[-LICH_SU_CAN:], dtype=float)

            # Chi nhom dac trung PHU THUOC SAN LUONG moi phai tinh lai moi buoc.
            hang["lag_4"] = lich[-4] if len(lich) >= 4 else np.nan
            hang["lag_96"] = lich[-96] if len(lich) >= 96 else np.nan
            for cua_so in (4, 96):
                if len(lich) >= cua_so:
                    w = lich[-cua_so:]
                    hang[f"rolling_mean_{cua_so}"] = w.mean()
                    hang[f"rolling_std_{cua_so}"] = w.std(ddof=0)
                    hang[f"rolling_min_{cua_so}"] = w.min()
                    hang[f"rolling_max_{cua_so}"] = w.max()

            X = hang.reindex(columns=self.features).fillna(self.medians).astype(np.float32)
            tho = float(self.model.predict(X)[0])

            if chuan_hoa:
                sin_e = float(hang["sin_elevation"].iloc[0])
                y_bao = np.clip(tho, 0, clip_k) * quy_mo * max(sin_e, eps)
                y_bao = min(y_bao, tran * 1.02)
                if sin_e <= eps:
                    y_bao = 0.0
            else:
                y_bao = max(tho, 0.0)

            y.append(y_bao)
            ket_qua.append({
                "site_id": site_id,
                "timestamp": hang["timestamp"].iloc[0],
                "plot_timestamp": hang["timestamp"].iloc[0] + pd.Timedelta(minutes=BUOC_PHUT * self.horizon),
                "y_pred_kwh": y_bao,
                "sin_elevation": float(hang["sin_elevation"].iloc[0]),
                "shortwave_radiation": float(hang.get("shortwave_radiation", pd.Series([np.nan])).iloc[0]),
                "so_buoc_de_quy": i + 1,
            })

        ra = pd.DataFrame(ket_qua)
        ra["ngay_thu"] = (ra["so_buoc_de_quy"] - 1) // BUOC_MOI_NGAY + 1
        assert len(y) == n_lich_su + len(ra), "So gia tri lich su khong khop so buoc du bao"
        return ra

    def du_bao_mot_buoc(self, site_id: int, so_ngay: int = 7,
                        dieu_chinh: dict[str, float] | None = None) -> pd.DataFrame:
        """Du bao MOT BUOC tai moi moc, giu nguyen lich su that — KHONG de quy.

        VI SAO CAN HAM NAY BEN CANH du_bao()
        ------------------------------------
        Bon trong muoi dac trung quan trong nhat cua mo hinh la lag_4 va rolling_*_4,
        tuc san luong gan day. Trong che do de quy, cac dac trung do lay tu chinh dau
        ra cua mo hinh, tao ra mot vong tu neo: du bao buoc sau bam theo du bao buoc
        truoc thay vi bam theo thoi tiet.

        Do thuc te tren tram 1, tang buc xa 20%:
            mot buoc (ham nay)  : +7,33%   <- do nhay that cua mo hinh voi thoi tiet
            de quy 7 ngay       : +0,47%   <- bi vong tu neo lam tat, co ngay con doi dau

        Vi vay moi phan tich What-if phai chay tren ham nay. Dung so de quy cho What-if
        se ra bieu do gan nhu phang, va nguoi doc se ket luan sai rang mo hinh khong
        quan tam den thoi tiet — trong khi su that nguoc lai.

        Danh doi: giu lich su co dinh nghia la ket qua khong phai mot du bao thuc te cho
        14 ngay toi, ma la mot phep DO DO NHAY: "neu thoi tiet the nay, mo hinh noi gi
        khi no biet chinh xac san luong gan nhat".
        """
        md = self.sieu_du_lieu()
        md = md[md["site_id"] == site_id].iloc[0]
        tt = self.lay_thoi_tiet(float(md["latitude"]), float(md["longitude"]), so_ngay)
        if dieu_chinh:
            for cot, he_so in dieu_chinh.items():
                if cot in tt.columns:
                    tt[cot] = tt[cot] * float(he_so)

        khung = self.khung_dac_trung(site_id, tt)
        lich = self.lich_su_gan_nhat(site_id)["energy_generated_kwh"].astype(float).to_numpy()

        quy_mo = float(self.quy_mo["site_scale"].get(str(site_id), np.nan))
        tran = float(self.quy_mo["tran_cong_suat"].get(str(site_id), np.nan))
        eps = float(self.cfg_model.get("eps_elev", 0.05))
        # Nguong cat lay TU ARTIFACT. Tu 2026-08-13 no duoc suy tu phan vi 99 cua k tren
        # tap TRAIN nen moi mo hinh mot khac; viet cung 1.5 se cho tran du bao lech han
        # so voi luc train. Thieu thi dung ngay thay vi doan.
        # Phai doc chuan_hoa TRUOC khi dung no o dieu kien ben duoi.
        chuan_hoa = bool(self.cfg_model.get("chuan_hoa"))
        if chuan_hoa and "clip_k" not in self.cfg_model:
            raise ForecastDomainError(
                "model_config.json thieu clip_k - hay chay lai notebook 06 de sinh artifact moi"
            )
        clip_k = float(self.cfg_model.get("clip_k", 1.5))

        d = khung.iloc[: len(khung) - self.horizon].copy()
        # Lich su CO DINH cho moi hang — day chinh la diem khac du_bao().
        d["lag_4"], d["lag_96"] = lich[-4], lich[-96]
        for cua_so in (4, 96):
            w = lich[-cua_so:]
            d[f"rolling_mean_{cua_so}"] = w.mean()
            d[f"rolling_std_{cua_so}"] = w.std(ddof=0)
            d[f"rolling_min_{cua_so}"] = w.min()
            d[f"rolling_max_{cua_so}"] = w.max()

        X = d.reindex(columns=self.features).fillna(self.medians).astype(np.float32)
        tho = self.model.predict(X)

        sin_e = d["sin_elevation"].to_numpy(float)
        if chuan_hoa:
            y_bao = np.clip(tho, 0, clip_k) * quy_mo * np.maximum(sin_e, eps)
            y_bao = np.minimum(y_bao, tran * 1.02)
            y_bao = np.where(sin_e <= eps, 0.0, y_bao)
        else:
            y_bao = np.maximum(tho, 0.0)

        ra = pd.DataFrame({
            "site_id": site_id,
            "timestamp": d["timestamp"].to_numpy(),
            "plot_timestamp": d["timestamp"].to_numpy()
            + pd.Timedelta(minutes=BUOC_PHUT * self.horizon),
            "y_pred_kwh": y_bao,
            "sin_elevation": sin_e,
            "shortwave_radiation": d.get("shortwave_radiation", pd.Series(np.nan, index=d.index)).to_numpy(),
        })
        ra["ngay_thu"] = (np.arange(len(ra)) // BUOC_MOI_NGAY) + 1
        return ra


_DICH_VU: dict[tuple[str, int], DichVuDuBao] = {}


def lay_dich_vu(loss: str | None = None, horizon: int = 1) -> DichVuDuBao:
    """Dung chung 1 the hien — nap model.pkl moi lan goi la lang phi."""
    if loss is None:
        best_path = BEST_LOSS
        if best_path.exists():
            loss = json.loads(best_path.read_text(encoding="utf-8")).get(
                f"h{horizon}", {}
            ).get("winning_loss", "mae")
        else:
            loss = "mae"
    khoa = (loss, horizon)
    if khoa not in _DICH_VU:
        _DICH_VU[khoa] = DichVuDuBao(loss, horizon)
    return _DICH_VU[khoa]
