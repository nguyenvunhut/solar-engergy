"""Stage 06: chan doan da cong tuyen (VIF, tuong quan, cot hang so) - dieu phoi.

    python srcs/05_machine_learning/pipeline/run.py --stage s06

Dau vao : data/model/v3/03_3_features_aggregate<suffix>/v3_train_features.parquet
Dau ra  : data/model/v3/04_diagnostics<suffix>/feature_diagnostics.csv

CHI CHAN DOAN TREN TAP TRAIN. Khong dung development/val/test - bang chan doan nay se
duoc stage s07 dung de loai dac trung, nen neu tinh tren tap khac la ro ri.

LUU Y KHI DOC: lag/rolling tuong quan cao voi nhau la BINH THUONG (deu la lich su cua
cung 1 chuoi). Khong tu dong loai chung chi vi VIF cao - stage s07 co danh sach BAO VE.

╔══════════════════════════════════════════════════════════════════════════════╗
║ VE KHA NANG TAI LAP CUA COT 'vif' (do thuc te 2026-08-07)                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
Chay CUNG code, CUNG du lieu, CUNG seed 3 lan cho 3 ket qua KHAC NHAU:
    day_of_year:  4524,60  ->  4482,29  ->  4517,29
Nguyen nhan: VIF tinh bang hoi quy tuyen tinh tren ma tran GAN SUY BIEN (R2 ~ 0,99978).
LAPACK chia viec cho nhieu thread nen thu tu cong doi theo tung lan chay, sai so bi
khuech dai manh o muc dieu kien so nay.

=> Con so trong file goc (04_diagnostics/feature_diagnostics.csv) CUNG KHONG tai lap
   duoc bang chinh notebook 04 - no la artifact cua mot lan chay cu the.

DA XU LY: ep BLAS ve 1 thread trong tinh_vif() (xem s06a_vif_compute.py). Da kiem: 3
process rieng biet cho DUNG mot ket qua. Tu gio pipeline tai lap duoc, du khong bang
dung con so cu.

DIEU QUAN TRONG: cot 'flag' - thu ma stage s07 THAT SU dung de loai dac trung - VAN
KHOP TUNG BIT voi ban goc. Ly do: cac VIF nay o muc hang tram den hang nghin, cach
nguong 10 rat xa, nen lech vai don vi khong doi duoc nhan nao. Danh sach dac trung
s07 chon ra khong doi, va moi ket qua phia sau (WAPE 17,57% / 21,31%) van khop tuyet doi.
'vif' chi la con so hien thi de tham khao muc do da cong tuyen.
"""
from __future__ import annotations

import gc

from core.columns import TARGET_COL, VERSION
from core.config import Cfg, load_config
from core.io import write_csv
from core.paths import Paths
from stages import s06a_vif_compute as vif

# THU TU COT CUA feature_diagnostics.csv - phai giu DUNG thu tu nay.
# Notebook 04 khong khai bao thu tu, no la HE QUA cua thu tu gan cot:
#   df_basic_stats(feature, dtype, nan_pct, nunique, variance, flag_basic)
#   -> ['duplicate_of'] -> ['vif'] -> ['flag'] + drop flag_basic -> ['pls_vip']
# Ban dau file nay gan 'pls_vip' TRUOC 'flag' nen ra thu tu khac notebook (phat hien
# 2026-08-08). Khai bao tuong minh o day de thu tu khong con phu thuoc vao thu tu gan
# cot nua - them cot moi thi phai them vao danh sach nay, khong thi KeyError ngay.
COT_RA = ["feature", "dtype", "nan_pct", "nunique", "variance",
          "duplicate_of", "vif", "flag", "pls_vip"]


def run_s06(cfg: Cfg | None = None):
    cfg = cfg or load_config()
    paths = Paths(cfg)
    duong_vao = paths.stage_doc("s05_aggregate") / f"{VERSION}_train_features.parquet"
    if not duong_vao.exists():
        raise FileNotFoundError(
            f"Khong tim thay {duong_vao}. Chay stage s05 truoc:\n"
            f"    python srcs/05_machine_learning/pipeline/run.py --stage s05"
        )

    print("[1/4] Doc cot so tu tap TRAIN (ep float32 ngay trong Arrow de tiet kiem RAM)")
    cot_so, bo_qua = vif.cot_so_can_chan_doan(duong_vao)
    print(f"      {len(cot_so)} cot so dua vao chan doan | bo qua {len(bo_qua)} cot")
    df = vif.doc_float32(duong_vao, cot_so)
    print(f"      {len(df):,} dong x {df.shape[1]} cot | "
          f"RAM {df.memory_usage(deep=True).sum() / 1024**2:.0f} MB\n")

    print("[2/4] Thong ke co ban - phat hien cot hang so / thieu nhieu")
    bang = vif.thong_ke_co_ban(df, cot_so)
    print(bang["flag_basic"].value_counts().to_string())
    hang_so = bang.loc[bang["flag_basic"] == "HANG_SO", "feature"].tolist()
    if hang_so:
        print(f"      cot HANG SO (vo dung): {hang_so}")
    print()

    print(f"[3/4] Ma tran tuong quan (mau {vif.CO_MAU_TUONG_QUAN:,} dong)")
    ma_tran, cap_cao = vif.cap_tuong_quan_cao(df, cot_so)
    print(f"      {len(cap_cao)} cap co |r| >= {vif.NGUONG_TUONG_QUAN_CAO}")
    giu, nhom_trung = vif.gom_nhom_trung_lap(ma_tran, cot_so)
    print(f"      {len(nhom_trung)} nhom cong tuyen HOAN HAO (|r| >= {vif.NGUONG_TRUNG_LAP})")
    for dai_dien, ds in list(nhom_trung.items())[:5]:
        print(f"         {dai_dien} <- {ds}")
    print(f"      con {len(giu)} dac trung sau khi gom nhom\n")

    print(f"[4/4] VIF + PLS-VIP (mau {vif.CO_MAU_VIF:,} dong, tren {len(giu)} dac trung)")
    bang_vif, mau, hop_le = vif.tinh_vif(df, giu, n_thread=cfg.runtime['threads']['n_jobs'])
    n_cao = int((bang_vif["vif"].notna() & (bang_vif["vif"] > vif.NGUONG_VIF_CAO)).sum())
    print(f"      {n_cao} dac trung co VIF > {vif.NGUONG_VIF_CAO}")

    import pandas as pd
    y = pd.read_parquet(duong_vao, columns=[TARGET_COL]).loc[mau.index, TARGET_COL].values
    vip = vif.tinh_pls_vip(mau, hop_le, y)
    del df, mau
    gc.collect()

    # Ghep cac bang + danh dau cot nao la ban trung lap cua cot nao.
    # Thu tu uu tien nhan: DUPLICATE > CONSTANT/HIGH_MISSING > HIGH_VIF > OK
    trung_lap_cua = {x: dai_dien for dai_dien, ds in nhom_trung.items() for x in ds}
    bang = bang.merge(bang_vif, on="feature", how="left")
    bang["duplicate_of"] = bang["feature"].map(trung_lap_cua)
    bang["pls_vip"] = bang["feature"].map(vip)

    def _nhan(r):
        if isinstance(r["duplicate_of"], str):
            return "DUPLICATE"
        if r["flag_basic"] != "OK":
            return r["flag_basic"]
        if pd.notna(r["vif"]) and r["vif"] > vif.NGUONG_VIF_CAO:
            return "HIGH_VIF"
        return "OK"

    bang["flag"] = bang.apply(_nhan, axis=1)
    bang = bang.drop(columns=["flag_basic"])
    bang = bang[COT_RA]

    ra = paths.stage("s06_diagnostics")
    ra.mkdir(parents=True, exist_ok=True)
    write_csv(bang, ra / "feature_diagnostics.csv")
    if not cap_cao.empty:
        write_csv(cap_cao, ra / "high_correlation_pairs.csv")

    print(f"\nDa ghi: {ra / 'feature_diagnostics.csv'} ({len(bang)} dac trung)")
    print("Phan bo nhan chan doan:")
    print(bang["flag"].value_counts().to_string())
    return bang
