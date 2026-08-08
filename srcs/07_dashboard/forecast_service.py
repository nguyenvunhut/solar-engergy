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
import pickle
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

GOC_REPO = Path(__file__).resolve().parents[2]
PIPELINE = GOC_REPO / "srcs/05_machine_learning/pipeline"
MLMART = GOC_REPO / "data/mlmart_base/v3_final_cleaned.parquet"
QUY_MO = GOC_REPO / "data/model/v3/03_2_features_spatial/quy_mo_tram.json"
MODEL_DIR = GOC_REPO / "data/model/v3/06_train"

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
}


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

    def __init__(self, loss: str = "huber", horizon: int = 1):
        self.loss, self.horizon = loss, horizon
        thu_muc = MODEL_DIR / loss / f"h{horizon}"
        self.cfg_model = json.loads((thu_muc / "model_config.json").read_text(encoding="utf-8"))
        with open(thu_muc / "model.pkl", "rb") as fh:
            self.model = pickle.load(fh)
        self.features: list[str] = list(self.cfg_model["features"])
        self.medians = pd.Series(self.cfg_model.get("feature_medians", {}), dtype="float64")
        self.quy_mo = json.loads(QUY_MO.read_text(encoding="utf-8"))

        from core.config import load_config  # noqa: PLC0415 — can sys.path o tren

        self.cfg = load_config()
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
            d = pd.read_parquet(MLMART, columns=cot)
            self._sieu_du_lieu = d.groupby("site_id").first().reset_index()
        return self._sieu_du_lieu

    def danh_sach_tram(self) -> list[int]:
        return sorted(int(s) for s in self.sieu_du_lieu()["site_id"].unique())

    def lich_su_gan_nhat(self, site_id: int, so_buoc: int = LICH_SU_CAN) -> pd.DataFrame:
        """Doan cuoi cung cua chuoi san luong that — dung lam moi cho de quy.

        mlmart_base chua co cot energy_source (cot do duoc pipeline tao o stage s01),
        nen chi doc 3 cot chac chan ton tai.
        """
        d = pd.read_parquet(MLMART, columns=["site_id", "timestamp", "energy_generated_kwh"])
        d = d[d["site_id"] == site_id].sort_values("timestamp")
        d = d.dropna(subset=["energy_generated_kwh"])
        if len(d) < so_buoc:
            raise ValueError(
                f"Tram {site_id} chi co {len(d)} dong lich su, can it nhat {so_buoc} "
                f"de dung lag_96/rolling_96."
            )
        return d.tail(so_buoc).reset_index(drop=True)

    # ── Thoi tiet ────────────────────────────────────────────────────────────
    def lay_thoi_tiet(self, lat: float, lon: float, so_ngay: int) -> pd.DataFrame:
        """Keo du bao thoi tiet theo gio tu Open-Meteo."""
        import requests  # noqa: PLC0415 — chi can khi thuc su goi mang

        r = requests.get(OPEN_METEO, params={
            "latitude": lat, "longitude": lon,
            "hourly": ",".join(DOI_TEN_THOI_TIET),
            "forecast_days": min(int(so_ngay), 16),
            "timezone": "auto",
        }, timeout=30)
        r.raise_for_status()
        h = r.json()["hourly"]
        d = pd.DataFrame(h).rename(columns={"time": "timestamp", **DOI_TEN_THOI_TIET})
        d["timestamp"] = pd.to_datetime(d["timestamp"])
        return d

    # ── Dung khung dac trung ─────────────────────────────────────────────────
    def khung_dac_trung(self, site_id: int, thoi_tiet: pd.DataFrame) -> pd.DataFrame:
        """Dung khung 15 phut day du dac trung BIET TRUOC (chua co lag/rolling).

        Thoi tiet Open-Meteo la theo GIO -> ffill xuong 15 phut. Chi ffill, tuyet doi
        khong bfill: bfill se keo gia tri tuong lai ve qua khu, dung sai lech nhan qua.
        """
        md = self.sieu_du_lieu()
        md = md[md["site_id"] == site_id].iloc[0]

        luoi = pd.date_range(thoi_tiet["timestamp"].min(),
                             thoi_tiet["timestamp"].max() + pd.Timedelta(minutes=45),
                             freq=f"{BUOC_PHUT}min")
        d = pd.DataFrame({"timestamp": luoi})
        d = d.merge(thoi_tiet, on="timestamp", how="left").ffill()
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
        d["cs_factor"] = float(self.quy_mo["cs_factor"].get(str(site_id), 1.0))

        # Ma hoa phan loai — mo hinh nhan so nguyen, khong nhan chuoi.
        d["site_id_enc"] = int(site_id)
        for c in ("weather_description_enc", "weather_condition_enc"):
            if c not in d.columns:
                d[c] = 0

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
        chuan_hoa = bool(self.cfg_model.get("chuan_hoa"))

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
                y_bao = np.clip(tho, 0, 1.5) * quy_mo * max(sin_e, eps)
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
        chuan_hoa = bool(self.cfg_model.get("chuan_hoa"))

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
            y_bao = np.clip(tho, 0, 1.5) * quy_mo * np.maximum(sin_e, eps)
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


def lay_dich_vu(loss: str = "huber", horizon: int = 1) -> DichVuDuBao:
    """Dung chung 1 the hien — nap model.pkl moi lan goi la lang phi."""
    khoa = (loss, horizon)
    if khoa not in _DICH_VU:
        _DICH_VU[khoa] = DichVuDuBao(loss, horizon)
    return _DICH_VU[khoa]
