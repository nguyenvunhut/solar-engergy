"""Stage 01d: join lai thoi tiet theo quy tac CAUSAL + bo cot khong dung.

NGUON: notebook 01_reindex_mask_outlier.ipynb cell 6 va cell 21 (ban dang chay 2026-08-08),
tuc thuat toan cua srcs/00_utils/04_realign_mlmart_weather.py.

QUY TAC CAUSAL: dong tai thoi diem T chi duoc dung thoi tiet cua khoi gio DA KET THUC,
tuc floor(T) ve dau gio. Vi du 10:45 dung thoi tiet nhan 10:00 (do trong khoang
(09:00, 10:00]). Dung nhan 11:00 la lay du lieu CHUA XAY RA -> ro ri.

LUU Y VE THU TU COT: buoc nay gan de len TUNG COT chu khong drop roi merge, nen cot thoi
tiet GIU NGUYEN vi tri cu. Khong duoc doi sang drop+merge cho "gon": lam vay se day cot
thoi tiet xuong cuoi khung, ma thu tu cot anh huong diem Mutual Information o stage s07
(sklearn sinh nhieu ngau nhien tuan tu theo tung cot) -> lech ket qua so voi notebook.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.columns import SITE_COL, TIMESTAMP_COL

# Copy nguyen si tu notebook 01 cell 6 - GIU DUNG THU TU nay
COT_THOI_TIET = [
    "shortwave_radiation", "direct_normal_irradiance", "diffuse_solar_radiation",
    "temperature_c", "cloud_cover_total", "cloud_cover_low", "cloud_cover_mid",
    "cloud_cover_high", "wind_speed", "precipitation_mm", "sunshine_duration",
    "weather_code", "weather_is_day", "weather_type_is_day",
    "weather_condition", "weather_description", "weather_id", "weather_type_id",
]
NHAN_DA_SUA = "hour_causal_floor"
NHAN_THIEU = "missing_weather"

# Nhan do srcs/00_utils/04_realign_mlmart_weather.py dat khi no hotfix THANG vao file
# mlmart_base. Do lai 2026-08-08 tren data/mlmart_base/v3_final_cleaned.parquet:
#   2.730.100 dong mang nhan nay, va 0/2.731.946 dong dung thoi tiet tuong lai
#   (delta weather_timestamp - timestamp chi nhan -45/-30/-15/0 phut)
# => dau vao DA causal san. Buoc join o day chay tren nen do nhu mot luoi an toan
# (idempotent), va doi nhan sang 'hour_causal_floor' cho dong bo voi bo du lieu tham chieu.
#
# VI SAO PHAI DOI TEN CHU KHONG DE NGUYEN: notebook 06_x co rao chan tu choi chay neu
# con dong mang nhan nay ("con N dong mang nhan join CU"). Rao chan do doc dung - no
# duoc viet khi nhan nay dong nghia voi "chua sua". Sau khi 04_realign chay that thi
# nhan cu khong con nghia do nua, nhung PHAI xac minh bang so lieu roi moi doi ten,
# tuyet doi khong doi vo dieu kien chi de di qua rao chan.
NHAN_HOTFIX_NGUON = "raw_hour_causal_manual"

# Cot khong dung lam dac trung o bat ky stage nao (notebook cell 21)
COT_BO = [
    "capacity_kw_is_imputed", "cloud_cover_low_is_imputed", "cloud_cover_total_is_imputed",
    "number_of_panels_is_imputed", "temperature_c_is_imputed", "wind_speed_is_imputed",
    "cloud_cover_high_is_imputed", "cloud_cover_mid_is_imputed", "precipitation_mm_is_imputed",
    # GIU LAI cloud_cover_low/mid/high: may tang THAP moi che nang manh, may tang CAO
    # (cirrus) gan nhu khong can - gop chung vao cloud_cover_total se mat tin hieu nay.
    "precipitation_mm",
    "weather_code", "weather_type_is_day", "weather_is_day",
    "weather_id", "weather_type_id", "weather_timestamp",
    "gen_id", "date_id", "time_id", "geo_id", "is_dst_repeat", "full_date",
    "location_name", "site_metric", "gmm_if_outlier_reason",
]
COT_BAT_BUOC_GIU = [
    "energy_generated_kwh", "site_id", "timestamp", "energy_source", "outlier_group",
    "latitude", "longitude", "capacity_kw", "number_of_panels",
    "shortwave_radiation", "direct_normal_irradiance", "diffuse_solar_radiation",
    "temperature_c", "cloud_cover_total",
    "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high",
]


def join_causal(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Gan lai thoi tiet theo dung notebook 01 cell 6 (ban dang chay)."""
    cot = [c for c in COT_THOI_TIET if c in df.columns]
    out = df.copy()
    out[TIMESTAMP_COL] = pd.to_datetime(out[TIMESTAMP_COL])
    out["weather_timestamp"] = pd.to_datetime(out["weather_timestamp"])

    delta_truoc = (out["weather_timestamp"] - out[TIMESTAMP_COL]).dt.total_seconds() / 60
    ro_ri_truoc = int((delta_truoc > 0).sum())

    # Dau vao da qua 04_realign chua? Chi de bao cao - viec doi nhan van phai cho den khi
    # do xong ro_ri_sau o duoi, khong duoc tin nhan ma bo qua kiem chung (xem NHAN_HOTFIX_NGUON).
    nhan_hotfix = 0
    if "weather_join_method" in out.columns:
        nhan_hotfix = int(out["weather_join_method"].astype(str).eq(NHAN_HOTFIX_NGUON).sum())

    # Bang tra: moi (site, nhan gio) mot ban ghi, lay tu cac dong co PHUT = 00.
    #
    # DAY LA THUAT TOAN CUA srcs/00_utils/04_realign_mlmart_weather.py, dung y notebook 01
    # cell 6 ban dang chay. Tung co ban khac (dung o commit b7561fe) dung bang tra theo
    # weather_timestamp roi drop + merge. Hai ban KHONG cho ket qua giong nhau, da do
    # 2026-08-08 tren 2.784.438 dong:
    #   - khac THU TU COT: ban kia drop roi merge nen day cot thoi tiet xuong cuoi
    #   - khac GIA TRI o 13 cot, tu 120 den 664 o (0,004% - 0,024% so dong). Ly do: ban kia
    #     tim thay thoi tiet ca khi gio do THIEU dong phut 00, ban nay thi ra rong.
    # Giu ban NAY vi no khop voi notebook - thu ma hoi dong se doc.
    khoi = out[out[TIMESTAMP_COL].dt.minute.eq(0)].copy()
    khoi["_nhan_gio"] = khoi[TIMESTAMP_COL]
    bang = (
        khoi[[SITE_COL, "_nhan_gio"] + cot]
        .sort_values([SITE_COL, "_nhan_gio", "weather_id"], kind="stable")
        .drop_duplicates([SITE_COL, "_nhan_gio"], keep="first")
        .set_index([SITE_COL, "_nhan_gio"])
    )

    # Nhan gio HOP LE = floor ve dau gio (thoi tiet do da co san tai thoi diem do)
    nhan_gio = out[TIMESTAMP_COL].dt.floor("h")
    truoc = out[cot].copy()
    # Gan DE LEN TUNG COT (khong drop roi merge) de GIU NGUYEN vi tri cot nhu notebook
    khoa = pd.MultiIndex.from_arrays([out[SITE_COL].to_numpy(), nhan_gio.to_numpy()],
                                     names=[SITE_COL, "_nhan_gio"])
    khop_bang = bang.reindex(khoa).reset_index(drop=True)
    for c in cot:
        out[c] = khop_bang[c].to_numpy()

    out["_nhan_gio"] = nhan_gio
    khop = out[cot].notna().all(axis=1)
    delta_sau = (out["_nhan_gio"] - out[TIMESTAMP_COL]).dt.total_seconds() / 60
    ro_ri_sau = int((delta_sau > 0).sum())

    doi = []
    for c in cot:
        if pd.api.types.is_numeric_dtype(truoc[c]):
            kh = ~np.isclose(truoc[c].to_numpy(dtype="float64"),
                             out[c].to_numpy(dtype="float64"), equal_nan=True)
        else:
            kh = truoc[c].astype(str).to_numpy() != out[c].astype(str).to_numpy()
        if int(kh.sum()):
            doi.append({"cot": c, "so_dong_doi": int(kh.sum()),
                        "ty_le_%": round(float(kh.mean()) * 100, 1)})

    out["weather_timestamp"] = out["_nhan_gio"]
    out = out.drop(columns=["_nhan_gio"])

    # KIEM TRUOC, DOI NHAN SAU. Chi khi da chac chan khong con dong nao dung thoi tiet
    # tuong lai thi moi duoc dat nhan 'hour_causal_floor' - vi day dung la nhan ma rao chan
    # o notebook 06_x tin tuong de cho chay tiep. Dao thu tu hai buoc nay la bien mot cong
    # kiem tra thanh mot phep doi ten vo nghia.
    if ro_ri_sau != 0:
        raise ValueError(
            f"Van con {ro_ri_sau:,} dong dung thoi tiet TUONG LAI - KHONG dat nhan "
            f"'{NHAN_DA_SUA}'. Dat nhan luc nay se lam rao chan o notebook 06_x cho qua "
            f"du lieu con ro ri."
        )
    # CHI DOI DUNG MOT NHAN, y het notebook 01 cell 21:
    #     df.loc[df['weather_join_method'] == 'raw_hour_causal_manual',
    #            'weather_join_method'] = 'hour_causal_floor'
    # KHONG duoc ghi de ca cot. Ban cu gan lai toan bo theo mat na 'khop' nen tren bo v4
    # (nhan nguon la 'raw_hour_causal_join') no bien 2.730.100 dong thanh
    # 'hour_causal_floor' va 1.846 dong thanh 'missing_weather', trong khi notebook giu
    # nguyen 2.731.728 dong 'raw_hour_causal_join' va 218 dong 'missing_weather'.
    # Gia tri thoi tiet hai ben van giong het - chi rieng cot nhan nay bi .py viet lai.
    if "weather_join_method" in out.columns:
        can_doi = out["weather_join_method"].astype(str).eq(NHAN_HOTFIX_NGUON)
        out.loc[can_doi, "weather_join_method"] = NHAN_DA_SUA

    return out, {
        "so_ban_ghi_thoi_tiet": len(bang),
        "so_cot_join": len(cot),
        "ro_ri_truoc": ro_ri_truoc,
        "nhan_hotfix_o_dau_vao": nhan_hotfix,
        "ro_ri_sau": ro_ri_sau,
        "so_dong_join_duoc": int(khop.sum()),
        "cot_doi_gia_tri": doi,
    }


def bo_cot_khong_dung(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Bo cot khong dung lam dac trung, roi kiem lai cot bat buoc con nguyen."""
    co = [c for c in COT_BO if c in df.columns]
    out = df.drop(columns=co)
    mat = [c for c in COT_BAT_BUOC_GIU if c not in out.columns]
    if mat:
        raise KeyError(
            f"Da bo mat cot BAT BUOC: {mat}. Cac stage sau se khong chay duoc. "
            f"Kiem lai danh sach COT_BO trong s01d_weather_causal.py"
        )
    return out, {"da_bo": len(co), "so_cot_truoc": df.shape[1], "so_cot_sau": out.shape[1]}
