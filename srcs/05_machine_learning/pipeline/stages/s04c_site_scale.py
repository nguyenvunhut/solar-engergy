"""Stage 04c: quy mo tram, tran cong suat, he so hieu chinh troi quang.

Tach tu buoc 4.3 cua run_features_spatial() trong 02_2_features_spatial.py.

VI SAO PHAI TINH LAI TU DU LIEU: capacity_kw trong metadata SAI o 11/42 tram. So san
luong that voi tran vat ly capacity_kw x 0,25h: tram 11 vuot 7,25 lan, tram 19 vuot
4,89 lan. Gia tri 51,15 lap lai o ~20 tram - la gia tri dien bu.

DIEM CHONG RO RI BAT BUOC: thong ke nay CHI tinh tren tap TRAIN roi luu ra JSON de
dung lai cho val/test. Val va test TUYET DOI khong duoc gop vao thong ke - neu khong
thi site_scale da mang thong tin cua tap test, va moi metric deu bi thoi phong.
"""
from __future__ import annotations

import gc

import numpy as np
import pandas as pd

from core.columns import SITE_COL, TARGET_COL, TIMESTAMP_COL
from core.config import Cfg
from core.io import cot_co_san, write_json
from stages.s04a_solar_geometry import add_solar_geometry_features

TEN_FILE_QUY_MO = "quy_mo_tram.json"

# Nguong loc khi tinh cs_factor: sin(10 do). LOC THEO GOC CAO MAT TROI, khong theo
# ghi_cs W/m2 truc tiep.
# BUG DA SUA (2026-07-31): nguong cu chi 'ghi_cs > 50' qua long, lot ca vung gan moc/lan
# mat troi. O do ghi_cs (Haurwitz, lien tuc) roi ve 0 RAT NHANH nhung shortwave_radiation
# goc (theo gio, lap 4 lan/15p) chua kip giam theo -> chia cho so gan 0 lam ty le NO TUNG
# (do that: p98 ty le luc 19h la 3,2 trong khi giua trua chi ~1,0-1,1). Hau qua: cs_factor
# bi day len tran clip(2.0) o CA 42/42 tram, thanh cot hang so vo dung.
# Nguon nguong 10 do: Kwarikunda & Chiguvare (2021) DOI 10.1155/2021/4369959;
# Mabasa et al. (2021) MDPI Energies 14(9) 2583.
NGUONG_SIN_ELEVATION = 0.1736


def tinh_quy_mo_tu_train(duong_train, cfg: Cfg, thu_muc_ra) -> dict:
    """Tinh site_scale / tran_cong_suat / cs_factor. CHI tren tap train."""
    q_scale = float(cfg.features.get("quantile_scale", 0.99))
    q_tran = float(cfg.features.get("quantile_tran", 0.999))
    q_cs = float(cfg.features.get("quantile_cs_factor", 0.98))

    co_san = cot_co_san(duong_train)
    cot = [c for c in (SITE_COL, TIMESTAMP_COL, TARGET_COL, "is_daylight",
                       "shortwave_radiation", "latitude", "longitude") if c in co_san]
    d = pd.read_parquet(duong_train, columns=cot)

    ban_ngay = (d["is_daylight"].fillna(False).astype(bool)
                if "is_daylight" in d.columns else d[TARGET_COL] > 0)
    dn = d[ban_ngay].reset_index(drop=True)

    g = dn.groupby(SITE_COL)[TARGET_COL]
    thong_ke = {
        # phan vi 99 san luong ban ngay - dung chuan hoa muc tieu khi train
        "site_scale": {str(k): float(v) for k, v in g.quantile(q_scale).items()},
        # phan vi 99,9 - giup model hoc doan inverter cat dinh
        "tran_cong_suat": {str(k): float(v) for k, v in g.quantile(q_tran).items()},
        "nguon": str(duong_train.name),
        "quantile_scale": q_scale,
        "quantile_tran": q_tran,
    }

    # cs_factor: mo hinh Haurwitz uoc luong THIEU (buc xa do vuot ghi_cs o 27% so buoc),
    # khien chi so troi quang k bi day len tren 1 roi bi CLIP cat mat. Nhan ghi_cs voi
    # cs_factor de dua k ve quanh 1. KHONG lam sai lech buc xa sau downscale vi cong thuc
    # chia roi nhan lai cung mot so.
    if {"shortwave_radiation", "latitude", "longitude"}.issubset(d.columns):
        tmp = add_solar_geometry_features(dn.reset_index(drop=True), cfg)
        m = (tmp["sin_elevation"] > NGUONG_SIN_ELEVATION) & (tmp["shortwave_radiation"] > 50)
        ty_le = tmp.loc[m, "shortwave_radiation"] / tmp.loc[m, "ghi_cs"]
        he_so = ty_le.groupby(tmp.loc[m, SITE_COL]).quantile(q_cs).clip(0.8, 2.0)
        thong_ke["cs_factor"] = {str(k): float(v) for k, v in he_so.items()}
        thong_ke["quantile_cs_factor"] = q_cs
        print(f"      cs_factor: trung vi {float(he_so.median()):.3f} | "
              f"min {float(he_so.min()):.3f} | max {float(he_so.max()):.3f}")
        del tmp
        gc.collect()
    else:
        thong_ke["cs_factor"] = {}
        print("      [CANH BAO] Thieu cot de tinh cs_factor, dung 1.0 cho moi tram.")

    thu_muc_ra.mkdir(parents=True, exist_ok=True)
    write_json(thong_ke, thu_muc_ra / TEN_FILE_QUY_MO)
    return thong_ke


def add_site_scale_features(df: pd.DataFrame, thong_ke: dict) -> pd.DataFrame:
    """Gan quy mo, tran cong suat va cac dac trung bao hoa."""
    out = df.copy()
    scale = {int(k): v for k, v in thong_ke["site_scale"].items()}
    tran = {int(k): v for k, v in thong_ke["tran_cong_suat"].items()}
    out["site_scale"] = out[SITE_COL].map(scale).astype("float32")
    out["tran_cong_suat"] = out[SITE_COL].map(tran).astype("float32")

    # san luong ky vong neu troi hoan toan quang
    out["ky_vong"] = (
        out["site_scale"] * out["sin_elevation"].clip(lower=0)
    ).astype("float32")
    # gan 1 nghia la sap cham tran inverter
    out["ty_le_bao_hoa"] = (
        out["ky_vong"] / out["tran_cong_suat"].replace(0, np.nan)
    ).clip(0, 3).astype("float32")
    out["con_cach_tran"] = (out["tran_cong_suat"] - out["ky_vong"]).astype("float32")
    return out
