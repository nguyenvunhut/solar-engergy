"""Stage 01: dung luoi 15 phut lien tuc + dien target + gan nhan outlier (dieu phoi).

    python srcs/05_machine_learning/pipeline/run.py --stage s01

Dau vao : data/mlmart_base/v3_final_cleaned.parquet
Dau ra  : data/model/v3/01_reindex<suffix>/v3_continuous_grid.parquet

SAU BUOC, khong duoc dao thu tu:
  0. gan energy_source           (s01_provenance) - doi chieu CSV raw, PHAI truoc
     moi thu vi cascade o buoc 4 chi thu thap gia tri co energy_source == 'measured'
  1. reindex luoi 15 phut        (s01a) - phai truoc, cac buoc sau gia dinh luoi deu
  2. gan provenance mac dinh     (s01a) - danh dau dong nao la moi chen
  3. ffill thoi tiet CAUSAL      (s01a) - phai truoc buoc 4 vi cascade dung is_daylight
                                          suy tu weather_is_day da ffill
  4. dien target bang cascade    (s01b)
  5. phan loai outlier + QA/QC   (s01c)
"""
from __future__ import annotations

from core.config import Cfg, load_config
from core.io import read_parquet, write_parquet
from core.paths import Paths
from stages import (
    s01_provenance,
    s01a_build_grid,
    s01b_fill_energy,
    s01c_outlier_group,
    s01d_weather_causal,
)


def run_s01(cfg: Cfg | None = None):
    cfg = cfg or load_config()
    paths = Paths(cfg)

    duong_vao = paths.mlmart_base
    if not duong_vao.exists():
        raise FileNotFoundError(
            f"Khong tim thay du lieu goc {duong_vao}. Kiem lai paths.yaml: mlmart_base"
        )
    df = read_parquet(duong_vao)
    print(f"Doc {duong_vao.name}: {len(df):,} dong x {len(df.columns)} cot, "
          f"{df['site_id'].nunique()} site\n")

    print("[1/7] Gan energy_source (doi chieu CSV raw) + khoi tao provenance")
    df = s01_provenance.chuan_bi_dau_vao(df, cfg, paths)
    print()

    print("[2/7] Join lai thoi tiet causal (notebook 01 cell 6)")
    df, tk_tt = s01d_weather_causal.join_causal(df)
    print(f"      bang tra: {tk_tt['so_ban_ghi_thoi_tiet']:,} ban ghi (site x nhan gio)")
    print(f"      dong join duoc thoi tiet: {tk_tt['so_dong_join_duoc']:,}/{len(df):,}")
    print(f"      dong dung thoi tiet TUONG LAI: {tk_tt['ro_ri_truoc']:,} -> "
          f"{tk_tt['ro_ri_sau']:,} (phai = 0)")
    print(f"      so cot thuc su doi gia tri: {len(tk_tt['cot_doi_gia_tri'])}")
    print()

    print("[3/7] Reindex luoi thoi gian")
    df = s01a_build_grid.reindex_luoi(df, cfg)
    df = s01a_build_grid.them_cot_lich(df)
    n_chen = int(df["timestamp_was_inserted"].sum())
    print(f"      {len(df):,} dong sau reindex "
          f"(goc {len(df) - n_chen:,} | moi chen {n_chen:,})\n")

    print("[4/7] Gan provenance mac dinh cho dong moi chen")
    df = s01a_build_grid.gan_provenance_mac_dinh(df)
    print(f"      weather_is_observed: {int(df['weather_is_observed'].sum()):,}/{len(df):,}\n")

    print("[5/7] Forward-fill thoi tiet (CAUSAL, per-site, khong bfill)")
    df, tk = s01a_build_grid.ffill_thoi_tiet(df, cfg)
    print(f"      {tk['so_cot']} cot | NaN {tk['nan_truoc']:,} -> {tk['nan_sau']:,} "
          f"(lap {tk['da_lap']:,})\n")

    print("[6/7] Dien target bang cascade causal")
    df = s01b_fill_energy.dien_target(df, cfg)
    print(f"      da dien {n_chen:,} slot moi chen\n")

    print("[7/7] Phan loai outlier va kiem chung")
    df = s01c_outlier_group.phan_loai_outlier(df)
    ket = s01c_outlier_group.qa_qc(df, cfg)
    s01c_outlier_group.in_qa_qc(ket)
    if not ket["dat"]:
        raise ValueError(
            "QA/QC khong dat - KHONG ghi file de tranh dua du lieu hong xuong stage sau. "
            "Xem cac dong [LOI] o tren."
        )

    df, tk_bo = s01d_weather_causal.bo_cot_khong_dung(df)
    print(f"\nBo {tk_bo['da_bo']} cot khong dung lam dac trung: "
          f"{tk_bo['so_cot_truoc']} -> {tk_bo['so_cot_sau']} cot")

    duong_ra = paths.stage("s01_reindex")
    write_parquet(df, duong_ra)
    print(f"\nDa ghi: {duong_ra} ({len(df):,} dong x {len(df.columns)} cot)")
    return df
