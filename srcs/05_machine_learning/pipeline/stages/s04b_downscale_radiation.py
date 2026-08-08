"""Stage 04b: dua buc xa tu do phan giai 1 gio ve 15 phut.

Tach tu buoc 4.2 cua run_features_spatial() trong 02_2_features_spatial.py.
Day la THUAT TOAN RIENG cua nhom (cung nguyen ly chung voi Grantham et al. 2017:
nhan ty le chi so troi-quang voi GHI clear-sky o do phan giai cao hon).

VAN DE: Open-Meteo tra ve buc xa theo GIO, luoi san luong la 15 PHUT -> gia tri buc xa
bi lap 4 lan trong moi khoi gio (chi 15,4% so buoc co gia tri doi). Model mat nguon tin
hieu 15 phut duy nhat, phai bam vao lag_1 -> tre pha.

CACH LAM: NHAN QUA, khong noi suy.
    k = buc_xa_do(dau khoi) / ghi_cs(dau khoi)       <- chi so troi quang cua ca khoi
    buc_xa_15p(t) = clip(k, 0, CLIP_CSI) * ghi_cs(t)  <- nhan lai theo ghi_cs tung buoc
ghi_cs la ham thien van xac dinh nen phep nay khong dua them thong tin do vao -> causal.

BA DIEM TU PHAT TRIEN (khac paper, da kiem chung bang tay tren du lieu that):
  1. Ranh gioi khoi gio xac dinh TU DU LIEU (moi khi buc xa doi gia tri la khoi moi),
     KHONG gia dinh co dinh o phut :00 hay :15 - reindex o s01 co the lam lech pha vai
     khoi (da gap khoi chi 3 diem thay vi 4).
  2. Chi downscale khoi co ty le bien thien ghi_cs max/min <= 1.5 lan. Khoi khong dat
     giu nguyen bac thang goc thay vi ep downscale sai.
  3. Dung TY LE max/min (doi xung ca 2 chieu tang va giam), KHONG dung nguong tuyet doi
     sin_elevation. Ly do o docstring ham ben duoi.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.columns import SITE_COL
from core.config import Cfg

COT_BUC_XA = ("shortwave_radiation", "direct_normal_irradiance", "diffuse_solar_radiation")

# Bien thien ghi_cs trong 1 khoi khong duoc vuot qua 1,5 lan thi moi cho downscale.
# VI SAO KHONG DUNG NGUONG TUYET DOI: da kiem chung bang tay - ghi_cs van tang toi 5,66 lan
# trong 1 khoi ngay tai sin_elevation = 0,15.
# VI SAO KHONG DUNG TY LE max/dau_khoi: chieu toi ghi_cs giam dan nen dau khoi luon = max,
# ty le do luon bang 1 du giam bao nhieu -> bo sot het truong hop luc mat troi lan.
TY_LE_GHI_CS_TOI_DA = 1.5


def ap_he_so_troi_quang(df: pd.DataFrame, thong_ke: dict) -> pd.DataFrame:
    """Nhan ghi_cs voi he so hieu chinh rieng tung tram (tinh tu tap TRAIN).

    He so nay bu cho do nghieng/huong tam pin cua tung tram ma mo hinh Haurwitz
    (chi cho mat phang ngang) khong biet.
    """
    out = df.copy()
    he_so = {int(k): v for k, v in (thong_ke.get("cs_factor") or {}).items()}
    out["cs_factor"] = out[SITE_COL].map(he_so).fillna(1.0).astype("float32")
    out["ghi_cs"] = (out["ghi_cs"] * out["cs_factor"]).astype("float32")
    out["clearsky_proxy"] = (out["sin_elevation"] ** 1.2).astype("float32")
    return out


def add_downscaled_radiation(df: pd.DataFrame, cfg: Cfg) -> pd.DataFrame:
    """Downscale buc xa 1h -> 15 phut + tinh chi so troi quang."""
    if "ghi_cs" not in df.columns:
        raise KeyError(
            "Phai goi add_solar_geometry_features() truoc add_downscaled_radiation()"
        )
    clip_csi = float(cfg.features["clip_csi"])
    out = df.copy()

    for cot in COT_BUC_XA:
        if cot not in out.columns:
            continue
        # Ranh gioi khoi = cho gia tri buc xa doi (trong cung 1 tram)
        doi = out.groupby(SITE_COL)[cot].diff().abs() > 1e-9
        ma_khoi = doi.groupby(out[SITE_COL]).cumsum()
        nhom = [out[SITE_COL], ma_khoi]

        ghi_dau = out.groupby(nhom)["ghi_cs"].transform("first")
        ghi_max = out.groupby(nhom)["ghi_cs"].transform("max")
        ghi_min = out.groupby(nhom)["ghi_cs"].transform("min")
        ty_le = ghi_max / ghi_min.replace(0, np.nan)
        duoc_downscale = (ghi_dau > 1) & (ty_le <= TY_LE_GHI_CS_TOI_DA)

        k = pd.Series(
            np.where(ghi_dau > 1, out[cot] / ghi_dau, np.nan), index=out.index
        )
        k = k.groupby(nhom).transform("first")      # 1 gia tri cho ca khoi
        k = k.groupby(out[SITE_COL]).ffill()        # giu k cua khoi gan nhat da biet
        cu = out[cot].copy()
        moi = np.clip(k, 0, clip_csi) * out["ghi_cs"]
        out[cot] = np.where(duoc_downscale, moi.fillna(cu), cu).astype("float32")

    out["rad_x_sinelev"] = (
        out["shortwave_radiation"] * out["sin_elevation"]
    ).astype("float32")

    # Chi so troi quang = buc xa DO DUOC / buc xa LY THUYET troi quang.
    # Gan 1 = troi quang hoan toan; gan 0 = co gi dang CHE PHU (may, bong cay, bui phu
    # tam pin) tai dung thoi diem do. Tinh SAU downscale de khop buc xa 15 phut cuoi cung.
    out["chi_so_troi_quang"] = (
        (out["shortwave_radiation"] / out["ghi_cs"].replace(0, np.nan))
        .clip(0, clip_csi)
        .fillna(0.0)
        .astype("float32")
    )
    return out


def bao_cao_downscale(truoc: pd.Series, sau: pd.Series) -> dict:
    """Do ty le buoc 15 phut co gia tri buc xa BIEN DOI - truoc va sau downscale.

    Day la con so chung minh thuat toan co tac dung: tu ~15% (lap 4 lan moi khoi gio)
    len ~97% (moi buoc mot gia tri rieng).
    """
    def ty_le_doi(s: pd.Series) -> float:
        return float((s.diff().abs() > 1e-9).mean() * 100)

    return {
        "ty_le_bien_doi_truoc_%": round(ty_le_doi(truoc), 2),
        "ty_le_bien_doi_sau_%": round(ty_le_doi(sau), 2),
    }
