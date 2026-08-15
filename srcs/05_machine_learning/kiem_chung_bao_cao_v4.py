"""Kiem chung cac phat bieu dinh luong trong bao cao hoc may v4.

Moi phep kiem o day tuong ung voi mot cau khang dinh trong `BaoCao_ML_v4.tex`. Muc dich la
de nguoi doc bao cao chay lai duoc va thay dung con so, thay vi phai tin.

Chay:
    python srcs/05_machine_learning/kiem_chung_bao_cao_v4.py

Ket qua in ra man hinh va ghi vao:
    data/model/v4/kiem_chung/kiem_chung_bao_cao_v4.json

Tat ca cac phep kiem chi DOC tep Parquet/JSON co san tren o dia cuc bo. Khong ket noi
database, khong sua tep nao.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
V4 = ROOT / "data" / "model" / "v4"
CHON = V4 / "05_selected"
FOLDS = CHON / "time_series_folds"
MLMART = ROOT / "data" / "mlmart_base" / "v4_final_cleaned.parquet"
RA = V4 / "kiem_chung"

SITE_COL = "site_id"
TS_COL = "timestamp"
TARGET_COL = "energy_generated_kwh"
EPS_ELEV = 0.05
EXCLUDE_SITES = [19, 24]

ket_qua: dict = {}


def tieu_de(so: str, ten: str) -> None:
    print()
    print("=" * 78)
    print(f"{so}. {ten}")
    print("=" * 78)


def doc_du_lieu(duong_dan: Path, cot: list[str] | None = None) -> pd.DataFrame:
    """Doc parquet roi loc DUNG BON dieu kien ma notebook 06 dung."""
    co_san = set(pq.ParquetFile(duong_dan).schema_arrow.names)
    if cot is not None:
        cot = [c for c in cot if c in co_san]
    d = pd.read_parquet(duong_dan, columns=cot)
    if "exclude_from_training" in d.columns:
        d = d[d["exclude_from_training"] == False]  # noqa: E712
    if "has_complete_history_features" in d.columns:
        d = d[d["has_complete_history_features"] == True]  # noqa: E712
    d = d.dropna(subset=[TARGET_COL])
    d = d[~d[SITE_COL].isin(EXCLUDE_SITES)]
    return d.sort_values([SITE_COL, TS_COL]).reset_index(drop=True)


def tinh_k(df: pd.DataFrame, h: int) -> pd.Series:
    """k = y(T+h) / (site_scale * max(sin_elev, eps)), theo dung cong thuc notebook 06.

    Loc `site_scale > 0` va `sin_elevation > eps` truoc khi tinh, giong cell chuan bi
    ma tran huan luyen.
    """
    d = df.copy()
    d["y_true"] = d.groupby(SITE_COL)[TARGET_COL].shift(-h)
    d = d.dropna(subset=["y_true"])
    d = d[(d["site_scale"] > 0) & (d["sin_elevation"] > EPS_ELEV)]
    mau = d["site_scale"] * d["sin_elevation"].clip(lower=EPS_ELEV)
    k = pd.Series(d["y_true"].to_numpy() / mau.to_numpy())
    return k.replace([np.inf, -np.inf], np.nan).dropna()


# ─────────────────────────────────────────────────────────────────────────────
def kiem_1_nguong_cat_theo_tam() -> None:
    """Bao cao noi CLIP_K = 1,3764 la phan vi 99 va cat khoang 1%.

    Kiem xem dieu do dung cho tam nao, va neu dung nguong cua H1 cho H4 thi cat bao nhieu.
    """
    tieu_de("1", "NGUONG CAT k THEO TUNG TAM DU BAO")

    cot = [SITE_COL, TS_COL, TARGET_COL, "site_scale", "sin_elevation",
           "exclude_from_training", "has_complete_history_features"]
    train = doc_du_lieu(CHON / "v4_train_selected.parquet", cot)

    cau_hinh_h1 = json.loads((V4 / "06_train/mae/h1/model_config.json").read_text())
    cau_hinh_h4 = json.loads((V4 / "06_train/mae/h4/model_config.json").read_text())
    clip_h1 = float(cau_hinh_h1["clip_k"])
    clip_h4 = float(cau_hinh_h4["clip_k"])

    ra = {
        "clip_k_ghi_trong_config_h1": clip_h1,
        "clip_k_ghi_trong_config_h4": clip_h4,
        "hai_config_dung_chung_mot_nguong": bool(abs(clip_h1 - clip_h4) < 1e-9),
    }

    for h in (1, 4):
        k = tinh_k(train, h)
        p99 = float(k.quantile(0.99))
        bi_cat_bang_nguong_h1 = int((k > clip_h1).sum())
        ra[f"h{h}"] = {
            "so_gia_tri_k": int(len(k)),
            "p99_neu_tinh_rieng_cho_tam_nay": round(p99, 7),
            "so_dong_bi_cat_boi_nguong_h1": bi_cat_bang_nguong_h1,
            "ty_le_bi_cat_boi_nguong_h1_pct": round(bi_cat_bang_nguong_h1 / len(k) * 100, 4),
        }
        print(f"h{h}: {len(k):,} gia tri k | p99 rieng = {p99:.7f} | "
              f"dung nguong H1 ({clip_h1:.7f}) thi cat {bi_cat_bang_nguong_h1:,} dong "
              f"({bi_cat_bang_nguong_h1 / len(k) * 100:.4f}%)")

    # Bang quet phan vi ghi p99 = 1,401453; kiem xem con so do sinh tu pham vi nao.
    quet = pd.read_csv(CHON / "quet_muc_phan_vi_nguong_cat.csv")
    p99_trong_bang_quet = float(quet.loc[quet["muc_phan_vi"] == 0.99, "nguong_cat"].iloc[0])
    ra["p99_ghi_trong_bang_quet"] = p99_trong_bang_quet
    ra["bang_quet_khop_config_h1"] = bool(abs(p99_trong_bang_quet - clip_h1) < 1e-4)
    print(f"\nBang quet phan vi ghi p99 = {p99_trong_bang_quet:.6f}; "
          f"config H1 ghi {clip_h1:.6f} -> "
          f"{'khop' if ra['bang_quet_khop_config_h1'] else 'KHONG khop'}")

    # Neu tinh rieng tren tung tap train cua tung fold thi nguong bao nhieu.
    theo_fold = {}
    for i in (1, 2, 3):
        d = doc_du_lieu(FOLDS / f"fold_{i}_train_selected.parquet", cot)
        k = tinh_k(d, 1)
        theo_fold[f"fold_{i}"] = round(float(k.quantile(0.99)), 7)
    ra["p99_h1_tinh_rieng_tung_fold"] = theo_fold
    ra["nguong_toan_cuc_dang_dung"] = clip_h1
    print(f"p99 (h1) neu tinh rieng tung fold: {theo_fold}")
    print(f"   nhung ca ba fold deu dung mot nguong toan cuc {clip_h1:.7f}")

    ket_qua["1_nguong_cat_theo_tam"] = ra


# ─────────────────────────────────────────────────────────────────────────────
def kiem_2_ngu_nghia_thoi_gian_khi_tuong() -> None:
    """Bao cao noi khi tuong duoc ghep theo moc QUA KHU. Do khoang cach thuc te."""
    tieu_de("2", "NGU NGHIA THOI GIAN CUA PHEP GHEP KHI TUONG")

    d = pd.read_parquet(MLMART, columns=[TS_COL, "weather_timestamp"])
    delta = ((pd.to_datetime(d["weather_timestamp"]) - pd.to_datetime(d[TS_COL]))
             .dt.total_seconds() / 60)
    phan_bo = delta.value_counts().sort_index()
    n = len(d)

    ra = {
        "tong_so_dong": int(n),
        "phan_bo_phut": {str(int(k)): int(v) for k, v in phan_bo.items()},
        "so_dong_khi_tuong_tuong_lai_delta_duong": int((delta > 0).sum()),
        "so_dong_khi_tuong_cung_moc_delta_bang_0": int((delta == 0).sum()),
        "so_dong_khi_tuong_qua_khu_delta_am": int((delta < 0).sum()),
    }
    ra["ty_le_cung_moc_pct"] = round(ra["so_dong_khi_tuong_cung_moc_delta_bang_0"] / n * 100, 4)
    ra["ty_le_tuong_lai_pct"] = round(ra["so_dong_khi_tuong_tuong_lai_delta_duong"] / n * 100, 4)

    print("Phan bo (weather_timestamp - timestamp), don vi phut:")
    print(phan_bo.to_string())
    print(f"\ndelta > 0  (khi tuong cua gio CHUA xay ra): "
          f"{ra['so_dong_khi_tuong_tuong_lai_delta_duong']:,} ({ra['ty_le_tuong_lai_pct']}%)")
    print(f"delta = 0  (cung moc gio, dong phut :00)  : "
          f"{ra['so_dong_khi_tuong_cung_moc_delta_bang_0']:,} ({ra['ty_le_cung_moc_pct']}%)")
    print(f"delta < 0  (khi tuong cua gio da ket thuc): "
          f"{ra['so_dong_khi_tuong_qua_khu_delta_am']:,}")

    ket_qua["2_ngu_nghia_thoi_gian_khi_tuong"] = ra


# ─────────────────────────────────────────────────────────────────────────────
def kiem_3_ghi_cs_co_phai_tran() -> None:
    """Bao cao tung noi buc xa do duoc "khong nen vuot" GHI_cs. Dem so lan vuot that."""
    tieu_de("3", "GHI_cs LA TRAN TUYET DOI HAY DUONG BAO THAM CHIEU")

    duong_dan = V4 / "03_2_features_spatial/v4_train_spatial.parquet"
    co_san = set(pq.ParquetFile(duong_dan).schema_arrow.names)
    cot = [c for c in ("shortwave_radiation", "ghi_cs", "cs_factor", "is_daylight")
           if c in co_san]
    d = pd.read_parquet(duong_dan, columns=cot)
    d = d[d["is_daylight"].fillna(False).astype(bool)]

    vuot = d["shortwave_radiation"] > d["ghi_cs"]
    manh = d[d["ghi_cs"] > 100]
    vuot_manh = manh["shortwave_radiation"] > manh["ghi_cs"]

    ra = {
        "so_dong_ban_ngay": int(len(d)),
        "so_dong_vuot_ghi_cs": int(vuot.sum()),
        "ty_le_vuot_pct": round(float(vuot.mean()) * 100, 4),
        "so_dong_ban_ngay_ghi_cs_tren_100": int(len(manh)),
        "so_dong_vuot_khi_ghi_cs_tren_100": int(vuot_manh.sum()),
        "ty_le_vuot_khi_ghi_cs_tren_100_pct": round(float(vuot_manh.mean()) * 100, 4),
        "ty_so_vuot_lon_nhat": round(float((d["shortwave_radiation"] / d["ghi_cs"]).max()), 4),
    }
    if "cs_factor" in d.columns:
        hieu_chinh = d["ghi_cs"] * d["cs_factor"]
        vuot_hc = d["shortwave_radiation"] > hieu_chinh
        ra["so_dong_vuot_sau_khi_nhan_cs_factor"] = int(vuot_hc.sum())
        ra["ty_le_vuot_sau_cs_factor_pct"] = round(float(vuot_hc.mean()) * 100, 4)

    for k, v in ra.items():
        print(f"  {k}: {v:,}" if isinstance(v, int) else f"  {k}: {v}")

    ket_qua["3_ghi_cs_khong_phai_tran"] = ra


# ─────────────────────────────────────────────────────────────────────────────
def kiem_4_dang_thuc_ty_le_buc_xa() -> None:
    """Bao cao noi dni_ratio + diffuse_ratio = 1. Kiem dang thuc va y nghia vat ly."""
    tieu_de("4", "DANG THUC dni_ratio + diffuse_ratio = 1 VA Y NGHIA VAT LY")

    duong_dan = V4 / "03_3_features_aggregate/v4_train_features.parquet"
    co_san = set(pq.ParquetFile(duong_dan).schema_arrow.names)
    can = ["dni_ratio", "diffuse_ratio", "shortwave_radiation",
           "diffuse_solar_radiation", "direct_normal_irradiance", "sin_elevation"]
    cot = [c for c in can if c in co_san]
    d = pd.read_parquet(duong_dan, columns=cot).dropna()
    d = d[d["shortwave_radiation"] > 0]

    tong = d["dni_ratio"] + d["diffuse_ratio"]
    # Neu cot direct_normal_irradiance thuc su la DNI (phap tuyen) thi phai co
    #   GHI = diffuse + DNI * sin(goc cao).
    # Neu no dang chua thanh phan truc tiep TREN MAT PHANG NGANG thi
    #   GHI = diffuse + direct.
    sai_so_ngang = float((d["diffuse_solar_radiation"]
                          + d["direct_normal_irradiance"]
                          - d["shortwave_radiation"]).abs().mean())
    sai_so_phap_tuyen = float((d["diffuse_solar_radiation"]
                               + d["direct_normal_irradiance"] * d["sin_elevation"]
                               - d["shortwave_radiation"]).abs().mean())

    ra = {
        "so_cap_kiem": int(len(d)),
        "sai_lech_lon_nhat_so_voi_1": float((tong - 1).abs().max()),
        "mae_neu_coi_la_thanh_phan_NGANG": round(sai_so_ngang, 6),
        "mae_neu_coi_la_DNI_phap_tuyen": round(sai_so_phap_tuyen, 6),
    }
    ra["cot_dang_chua"] = ("thanh phan truc tiep tren mat phang NGANG"
                           if sai_so_ngang < sai_so_phap_tuyen
                           else "DNI phap tuyen")
    print(f"  So cap kiem                         : {ra['so_cap_kiem']:,}")
    print(f"  |dni_ratio + diffuse_ratio - 1| max : {ra['sai_lech_lon_nhat_so_voi_1']:.3e}")
    print(f"  MAE neu coi la thanh phan NGANG     : {ra['mae_neu_coi_la_thanh_phan_NGANG']}")
    print(f"  MAE neu coi la DNI phap tuyen       : {ra['mae_neu_coi_la_DNI_phap_tuyen']}")
    print(f"  => cot dang chua: {ra['cot_dang_chua']}")

    ket_qua["4_dang_thuc_ty_le_buc_xa"] = ra


# ─────────────────────────────────────────────────────────────────────────────
def kiem_5_nhan_o_ranh_gioi_fold() -> None:
    """Bao cao tung noi co nhan "roi sang" validation o ranh gioi fold.

    Duong huan luyen that doc rieng tung tep fold roi moi shift(-h), nen h dong cuoi cung
    cua tap train nhan NaN va bi loai. Kiem lai dieu do bang chinh cac tep fold.
    """
    tieu_de("5", "NHAN O RANH GIOI FOLD CO LAY TU TAP KIEM DINH KHONG")

    cot = [SITE_COL, TS_COL, TARGET_COL, "exclude_from_training",
           "has_complete_history_features"]
    ra = {}
    for i in (1, 2, 3):
        tr = doc_du_lieu(FOLDS / f"fold_{i}_train_selected.parquet", cot)
        va = doc_du_lieu(FOLDS / f"fold_{i}_val_selected.parquet", cot)
        muc = {}
        for h in (1, 4):
            y = tr.groupby(SITE_COL)[TARGET_COL].shift(-h)
            muc[f"h{h}_dong_cuoi_moi_site_nhan_NaN_va_bi_loai"] = int(y.isna().sum())
        muc["moc_cuoi_tap_train"] = str(tr[TS_COL].max())
        muc["moc_dau_tap_val"] = str(va[TS_COL].min())
        muc["so_site"] = int(tr[SITE_COL].nunique())
        muc["nhan_lay_tu_tap_val"] = 0  # doc rieng hai tep nen khong the lay cheo
        ra[f"fold_{i}"] = muc
        print(f"fold {i}: train het {muc['moc_cuoi_tap_train']} | "
              f"val bat dau {muc['moc_dau_tap_val']} | "
              f"h1 loai {muc['h1_dong_cuoi_moi_site_nhan_NaN_va_bi_loai']:,} dong, "
              f"h4 loai {muc['h4_dong_cuoi_moi_site_nhan_NaN_va_bi_loai']:,} dong")

    print("\nVi tap train va tap val duoc doc tu HAI tep rieng, phep shift(-h) chi chay ben")
    print("trong tep train, nen khong co nhan nao lay duoc tu tap kiem dinh.")
    ket_qua["5_nhan_o_ranh_gioi_fold"] = ra


# ─────────────────────────────────────────────────────────────────────────────
def kiem_6_nhan_dung_tam_du_bao() -> None:
    """Sau khi loc, luoi khong lien tuc; kiem moc nhan co dung T+h khong."""
    tieu_de("6", "NHAN CO NAM DUNG TAI T+h TRONG TAP TEST KHONG")

    duong_dan = V4 / "07_final_test/prediction_audit.parquet"
    d = pd.read_parquet(duong_dan)
    ra = {}
    for h in (1, 4):
        cot_nguon = f"source_timestamp_h{h}"
        cot_nhan = f"label_timestamp_h{h}"
        if cot_nguon not in d.columns or cot_nhan not in d.columns:
            continue
        sub = d[[cot_nguon, cot_nhan]].dropna()
        lech = (pd.to_datetime(sub[cot_nhan]) - pd.to_datetime(sub[cot_nguon])
                ).dt.total_seconds() / 60
        sai = int((lech != 15 * h).sum())
        ra[f"h{h}"] = {
            "so_dong_cham_diem": int(len(sub)),
            "so_dong_nhan_khong_dung_tam": sai,
            "ty_le_sai_pct": round(sai / max(len(sub), 1) * 100, 6),
        }
        print(f"h{h}: {len(sub):,} dong | nhan lech tam: {sai:,} "
              f"({sai / max(len(sub), 1) * 100:.6f}%)")

    ket_qua["6_nhan_dung_tam_du_bao"] = ra


# ─────────────────────────────────────────────────────────────────────────────
def kiem_7_pham_vi_cham_diem() -> None:
    """Doi chieu con so headline trong bao cao voi artifact."""
    tieu_de("7", "CON SO HEADLINE DOI CHIEU VOI ARTIFACT")

    ra = {}
    for h in ("h1", "h4"):
        m = json.loads((V4 / f"07_final_test/{h}/metrics_overall.json").read_text())
        md = m["measured_daylight"]
        ra[h] = {
            "ham_mat_mat": m["winning_loss"],
            "so_dong_cham_diem": m["measured_daylight_test_rows"],
            "wape_pct": md["wape"],
            "rmse": md["rmse"],
            "mae": md["mae"],
            "r2": md["r2"],
        }
        print(f"{h}: loss={m['winning_loss']} | n={m['measured_daylight_test_rows']:,} | "
              f"WAPE={md['wape']:.7f}% | RMSE={md['rmse']:.4f} | R2={md['r2']:.4f}")

    best = json.loads((V4 / "07_final_test/best_loss.json").read_text())
    ra["ham_mat_mat_duoc_chon"] = {k: v["winning_loss"] for k, v in best.items()}
    ra["wape_kiem_dinh_cua_ham_duoc_chon"] = {k: v["val_wape"] for k, v in best.items()}
    print(f"Ham mat mat duoc chon: {ra['ham_mat_mat_duoc_chon']}")

    ket_qua["7_con_so_headline"] = ra


# ─────────────────────────────────────────────────────────────────────────────
def kiem_8_shap_tren_bao_nhieu_dong() -> None:
    """Bao cao noi SHAP tinh tren toan bo tap test. Dem so dong that su."""
    tieu_de("8", "SHAP DUOC TINH TREN BAO NHIEU DONG")

    sv = V4 / "08_explain/shap_values.parquet"
    imp = V4 / "08_explain/shap_importance.csv"
    if not sv.exists():
        print("Chua co artifact SHAP, bo qua.")
        return
    meta = pq.ParquetFile(sv).metadata
    x_test = V4 / "07_final_test/h1/X_test_h1.parquet"
    ra = {
        "so_dong_trong_shap_values_parquet": int(meta.num_rows),
        "so_cot": int(meta.num_columns),
        "so_dong_ma_tran_test_h1": int(pq.ParquetFile(x_test).metadata.num_rows),
    }
    ra["shap_phu_toan_bo_tap_test"] = (
        ra["so_dong_trong_shap_values_parquet"] == ra["so_dong_ma_tran_test_h1"]
    )
    if imp.exists():
        b = pd.read_csv(imp)
        ra["top_5_dac_trung"] = b.head(5).to_dict("records")
    for k, v in ra.items():
        if k != "top_5_dac_trung":
            print(f"  {k}: {v:,}" if isinstance(v, int) else f"  {k}: {v}")

    ket_qua["8_pham_vi_shap"] = ra


# ─────────────────────────────────────────────────────────────────────────────
def kiem_9_dieu_kien_doi_chung_prophet() -> None:
    """Prophet va LightGBM co hoc tren cung cua so du lieu khong."""
    tieu_de("9", "DIEU KIEN DOI CHUNG PROPHET")

    p = V4 / "08_baseline_prophet_test/prophet_test_summary.json"
    if not p.exists():
        print("Chua co artifact Prophet, bo qua.")
        return
    s = json.loads(p.read_text())
    cau_hinh = json.loads((V4 / "06_train/mae/h1/model_config.json").read_text())

    ra = {
        "prophet_hoc_tren": s.get("nguon_hoc"),
        "lightgbm_hoc_tren": "v4_train_selected",
        "cung_cua_so_huan_luyen": s.get("nguon_hoc", "").startswith("v4_train_selected"),
        "clip_k_lightgbm": cau_hinh.get("clip_k"),
    }
    for k in ("skill_score_h1_pct", "skill_score_h4_pct", "wape_prophet_h1_pct",
              "wape_prophet_h4_pct"):
        if k in s:
            ra[k] = s[k]
    for k, v in ra.items():
        print(f"  {k}: {v}")
    print("\nProphet hoc ca train+val, LightGBM chi hoc train -> doi chung duoc cap NHIEU")
    print("du lieu hon mo hinh duoc danh gia, tuc uu the nghieng ve phia doi chung.")

    ket_qua["9_dieu_kien_doi_chung_prophet"] = ra


def kiem_10_dac_trung_tat_dinh_tai_T_hay_T_cong_h() -> None:
    """Bang so sanh dung dac trung tat dinh tai T voi tai T+h, tach theo khung gio.

    Do bang MAE cua duong bao site_scale * max(sin h, eps) so voi san luong that tai
    T+15 phut. Bang trong bao cao truoc day chep tu khoi ghi chu trong ma nguon; muc
    nay tinh lai tu du lieu de con so dung lai duoc.
    """
    tieu_de("10", "DAC TRUNG TAT DINH: DUNG TAI T HAY TAI T+h")

    cot = [SITE_COL, TS_COL, TARGET_COL, "site_scale", "sin_elevation",
           "exclude_from_training", "has_complete_history_features"]
    d = doc_du_lieu(CHON / "v4_development_selected.parquet", cot)
    h = 1
    g = d.groupby(SITE_COL)
    d = d.assign(y=g[TARGET_COL].shift(-h), sin_mt=g["sin_elevation"].shift(-h))
    d = d.dropna(subset=["y", "sin_mt"])
    d = d[(d["site_scale"] > 0) & (d["sin_elevation"] > EPS_ELEV)]

    bao_tai_T = d["site_scale"] * d["sin_elevation"].clip(lower=EPS_ELEV)
    bao_tai_Th = d["site_scale"] * d["sin_mt"].clip(lower=EPS_ELEV)
    gio = pd.to_datetime(d[TS_COL]).dt.hour

    ra = {}
    khung = {
        "toan_bo_ban_ngay": pd.Series(True, index=d.index),
        "sang_06_09h": gio.between(6, 9),
        "chieu_16_18h": gio.between(16, 18),
    }
    for ten, m in khung.items():
        a = float((d["y"][m] - bao_tai_T[m]).abs().mean())
        b = float((d["y"][m] - bao_tai_Th[m]).abs().mean())
        ra[ten] = {
            "so_dong": int(m.sum()),
            "mae_dung_tai_T": round(a, 4),
            "mae_dung_tai_T_cong_h": round(b, 4),
            "chenh_pct": round((b - a) / a * 100, 1),
        }
        print(f"  {ten:18s} n={int(m.sum()):>8,} | tai T {a:.4f} | tai T+h {b:.4f} "
              f"| chenh {(b - a) / a * 100:+.1f}%")

    ket_qua["10_dac_trung_tat_dinh_tai_T_hay_T_cong_h"] = ra


# ─────────────────────────────────────────────────────────────────────────────
def kiem_11_hai_ngay_trong_hinh_eda() -> None:
    """So do cua hai ngay tuong phan dung trong hinh mau hinh phat dien o Muc 2.2.2."""
    tieu_de("11", "SO DO CUA HAI NGAY TRONG HINH MAU HINH PHAT DIEN")

    duong_dan = V4 / "02_split/train/v4_train.parquet"
    d = pd.read_parquet(duong_dan, columns=[SITE_COL, TS_COL, TARGET_COL])
    d = d[d[SITE_COL] == 27].copy()
    d[TS_COL] = pd.to_datetime(d[TS_COL])
    d["ngay"] = d[TS_COL].dt.normalize()

    ra = {}
    for ngay, ten in (("2020-10-02", "ngay_troi_quang"), ("2020-12-23", "ngay_nhieu_may")):
        z = d[d["ngay"] == pd.Timestamp(ngay)].sort_values(TS_COL)
        y = z[TARGET_COL].to_numpy(float)
        dinh = float(y.max())
        i = int(y.argmax())
        hieu = np.diff(y)
        j = int(hieu.argmin())
        do_gap = float(np.abs(np.diff(y, n=2)).mean() / max(dinh, 1e-9))
        ra[ten] = {
            "ngay": ngay,
            "so_buoc_trong_ngay": int(len(y)),
            "dinh_kwh": round(dinh, 2),
            "gio_dat_dinh": z[TS_COL].iloc[i].strftime("%H:%M"),
            "tong_san_luong_kwh": round(float(y.sum()), 1),
            "so_buoc_tren_80pct_dinh": int((y >= 0.8 * dinh).sum()),
            "muc_sut_lon_nhat_kwh": round(float(abs(hieu[j])), 2),
            "so_lan_doi_qua_10kwh": int((np.abs(hieu) > 10).sum()),
            "do_gap": round(do_gap, 4),
        }
        r = ra[ten]
        print(f"  {ten:16s} dinh {r['dinh_kwh']:>6} kWh luc {r['gio_dat_dinh']} | "
              f"tong {r['tong_san_luong_kwh']:>8} kWh | tren 80% dinh "
              f"{r['so_buoc_tren_80pct_dinh']:>2} buoc | sut manh nhat "
              f"{r['muc_sut_lon_nhat_kwh']:>6} kWh | {r['so_lan_doi_qua_10kwh']:>2} lan doi "
              f">10 kWh | do gap {r['do_gap']}")

    ket_qua["11_hai_ngay_trong_hinh_eda"] = ra


def main() -> None:
    print("KIEM CHUNG CAC PHAT BIEU DINH LUONG - BAO CAO HOC MAY v4")
    print("Chi doc tep cuc bo, khong ket noi database, khong sua tep nao.")

    kiem_1_nguong_cat_theo_tam()
    kiem_2_ngu_nghia_thoi_gian_khi_tuong()
    kiem_3_ghi_cs_co_phai_tran()
    kiem_4_dang_thuc_ty_le_buc_xa()
    kiem_5_nhan_o_ranh_gioi_fold()
    kiem_6_nhan_dung_tam_du_bao()
    kiem_7_pham_vi_cham_diem()
    kiem_8_shap_tren_bao_nhieu_dong()
    kiem_9_dieu_kien_doi_chung_prophet()
    kiem_10_dac_trung_tat_dinh_tai_T_hay_T_cong_h()
    kiem_11_hai_ngay_trong_hinh_eda()

    RA.mkdir(parents=True, exist_ok=True)
    duong_dan = RA / "kiem_chung_bao_cao_v4.json"
    with duong_dan.open("w", encoding="utf-8") as f:
        json.dump(ket_qua, f, ensure_ascii=False, indent=2)
    print(f"\nDa ghi toan bo ket qua kiem chung: {duong_dan}")


if __name__ == "__main__":
    main()
