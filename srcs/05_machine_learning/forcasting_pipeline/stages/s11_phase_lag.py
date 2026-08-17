"""Stage 11: kiem chung TRE PHA bang phep do lech dinh local.

    python srcs/05_machine_learning/pipeline/run.py --stage s11

NGUON: notebook 09_kiem_chung_tre_pha.ipynb. Ghi ra dung 5 file CSV nhu notebook, de doi
chieu tung byte duoc.

DAY LA TIEU CHI NGHIEM THU QUAN TRONG HON CA WAPE: du bao cao hay thap hon thuc te con
chap nhan duoc, nhung neu du bao den SAU thuc te thi no khong con la du bao nua. Vi vay
phai do rieng tung (site, ngay) - con so gop co the dep trong khi mot site le tre 45 phut.

KHONG MO LAI TAP TEST: doc snapshot prediction_audit.parquet do stage s09 xuat ra, va nhan
outlier tu 05_selected (khong chua nhan nao cua qua trinh cham diem).
"""
from __future__ import annotations

import pandas as pd

from core.columns import SITE_COL, TIMESTAMP_COL
from core.config import Cfg, load_config
from core.io import write_csv
from core.paths import Paths
from stages import s11a_lech_dinh as ld


def _doc_du_bao(paths: Paths, horizon: int) -> pd.DataFrame:
    """Doc file du bao tong hop cua s09, doi ten cot cho de doc."""
    duong = paths.stage("s09_final_test") / "prediction_audit.parquet"
    if not duong.exists():
        raise FileNotFoundError(
            f"Chua co {duong}. Chay stage s09 truoc:\n"
            f"    python srcs/05_machine_learning/pipeline/run.py --stage s09"
        )
    cot_that, cot_du_bao = f"y_true_h{horizon}", f"y_pred_h{horizon}"
    au = pd.read_parquet(duong)
    thieu = [c for c in (cot_that, cot_du_bao) if c not in au.columns]
    if thieu:
        raise KeyError(f"{duong.name} thieu cot {thieu} - s09 chua cham horizon h{horizon}?")

    df = au[[SITE_COL, TIMESTAMP_COL, "energy_source", "is_daylight",
             cot_that, cot_du_bao]].copy()
    df = df.dropna(subset=[cot_that, cot_du_bao])
    df = df.sort_values([SITE_COL, TIMESTAMP_COL]).reset_index(drop=True)
    return df.rename(columns={cot_that: "thuc_te", cot_du_bao: "du_bao"})


def _them_nhan_outlier(df: pd.DataFrame, paths: Paths) -> pd.DataFrame:
    """Gan nhan outlier tu 05_selected de do rieng sai so tai diem outlier."""
    duong = paths.selected("test_selected")
    # Doc thang bang pandas (giong notebook 09): chi lay 4 cot metadata nen core.io.
    # read_parquet se bao thieu cot bat buoc - o day khong can chung.
    ol = pd.read_parquet(
        duong, columns=[SITE_COL, TIMESTAMP_COL, "outlier_group", "exclude_from_training"]
    )
    out = df.merge(ol, on=[SITE_COL, TIMESTAMP_COL], how="left")
    out["la_outlier"] = out["outlier_group"].notna() & (out["outlier_group"] != "normal")
    return out


def kiem_1_horizon(cfg: Cfg, paths: Paths, horizon: int) -> dict:
    """Chay du 5 phep do cho 1 horizon va ghi ra CSV."""
    h_label = f"h{horizon}"
    df = _them_nhan_outlier(_doc_du_bao(paths, horizon), paths)
    thu_muc = paths.stage("s11_phase_lag")
    thu_muc.mkdir(parents=True, exist_ok=True)

    print(f"--- KIEM TRE PHA {h_label.upper()} ---")
    print(f"So dong: {len(df):,} | so site: {df[SITE_COL].nunique()} | "
          f"ban ngay {df['is_daylight'].mean() * 100:.2f}%")
    print(f"Dong bi gan outlier: {int(df['la_outlier'].sum()):,} "
          f"({df['la_outlier'].mean() * 100:.2f}%)")

    df_lech = ld.lech_dinh_moi_ngay(df)
    if df_lech.empty:
        print("   [BO QUA] khong du du lieu ban ngay de do lech dinh.")
        return {"so_ngay": 0}
    write_csv(df_lech, thu_muc / f"lech_dinh_moi_ngay_{h_label}.csv")
    write_csv(ld.theo_vi_tri_trong_gio(df_lech),
              thu_muc / f"lech_theo_vi_tri_trong_gio_{h_label}.csv")
    bang_site = ld.theo_site(df_lech)
    write_csv(bang_site, thu_muc / f"lech_dinh_theo_site_{h_label}.csv")
    write_csv(ld.theo_gio_dinh(df_lech), thu_muc / f"lech_dinh_theo_gio_{h_label}.csv")
    bang_ol = ld.outlier_theo_site(df)
    if not bang_ol.empty:
        write_csv(bang_ol, thu_muc / f"outlier_theo_site_{h_label}.csv")

    phai = int((df_lech["lech_phut"] > 0).sum())
    dung = int((df_lech["lech_phut"] == 0).sum())
    trai = int((df_lech["lech_phut"] < 0).sum())
    n = len(df_lech)
    print(f"Lech dinh tren {df_lech['site_id'].nunique()} site x {n:,} ngay "
          f"(duong = du bao den SAU thuc te):")
    print(f"   trung vi {df_lech['lech_phut'].median():+.1f} phut | "
          f"trung binh {df_lech['lech_phut'].mean():+.2f} phut")
    print(f"   dich PHAI (tre) {phai:,} ({phai / n * 100:.1f}%) | "
          f"dung khop {dung:,} ({dung / n * 100:.1f}%) | "
          f"dich TRAI (som) {trai:,} ({trai / n * 100:.1f}%)")
    te = int((bang_site["lech_trung_vi"] > 0).sum())
    print(f"   so site thien ve TRE: {te}/{len(bang_site)}\n")
    return {
        "so_ngay": n,
        "so_site": int(df_lech["site_id"].nunique()),
        "lech_trung_vi_phut": float(df_lech["lech_phut"].median()),
        "ty_le_dich_phai_%": round(phai / n * 100, 2),
        "so_site_thien_tre": te,
    }


def run_s11(cfg: Cfg | None = None) -> dict:
    cfg = cfg or load_config()
    paths = Paths(cfg)
    ket = {f"h{h}": kiem_1_horizon(cfg, paths, h) for h in cfg.train["horizon_steps"]}
    print(f"Da ghi ket qua kiem tre pha vao: {paths.stage('s11_phase_lag')}")
    return ket
