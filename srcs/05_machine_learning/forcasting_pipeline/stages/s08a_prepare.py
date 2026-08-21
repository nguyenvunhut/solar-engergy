"""Stage 08a: nap tap huan luyen, dung bien muc tieu va ma tran huan luyen.

Tach tu preprocessing() + phan dau train_fold() cua 04_x_train_*.py.

TAP HOC LA `train`, KHONG PHAI `development` (sua 2026-08-09):
  Ban cu doc `dev_selected` (= train + val) de fit mo hinh cuoi, roi lai cham diem tren
  cac fold validation - ma fold validation nam TRONG development. Ket qua: cham diem tren
  chinh du lieu da hoc. Da do bang phep giao khoa (site_id, timestamp): 100,00% trong
  2.141.447 dong fold validation nam trong tap development da dung de fit.

  Hau qua thuc te: WAPE validation 14,67% khong phai uoc luong ngoai mau, va viec chon
  Huber lam mo hinh vo dich dua tren con so do. Khi cham lai dang hoang (hoc tren train,
  cham tren val) thi thu hang DAO: MAE 20,89% < Huber 21,42% < MSE 21,44%.

  Ban moi doc `train_selected` de hoc va giu `val_selected` rieng de cham. Dong bo voi
  notebook 06_1/06_2/06_3 sau ban va cung ngay.

  Huan luyen lai tren toan bo development SAU KHI da chot cau hinh van la thong le hop le
  (mo hinh trien khai manh hon vi co them du lieu); cai khong hop le la lay con so thu
  duoc tu do lam bang chung khai quat hoa.

KHAC BAN CU - TAP TEST BI KHOA O DAY:
  Ban cu (04_x_train_*.py) nap CA tap test ngay trong buoc train, roi cham diem va ghi
  metrics_test.json. Do chinh la cho phat sinh loi ro ri 2026-08-06: so lieu test bi ghi
  nham vao metrics_val.json, khien viec chon MAE/Huber/MSE "nhin truoc" tap test.

  Ban moi: stage s08 TUYET DOI khong doc tap test. Tap test chi duoc mo DUY NHAT o
  stage s09, sau khi mo hinh vo dich da duoc chon xong bang so lieu validation.
  Muon kiem lai dieu nay, chay: python srcs/05_machine_learning/pipeline/checks/audit_test_sealed.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.columns import (
    SITE_COL,
    TARGET_COL,
    TARGET_SHIFTED,
    TIMESTAMP_COL,
    ten_cot_muc_tieu,
)
from core.config import Cfg
from core.context import Ctx
from core.io import cot_co_san, read_parquet
from core.paths import Paths
from core.target import them_muc_tieu
from core.weights import build_sample_weight


def _doc_tap(duong_dan, features: list[str], cfg: Cfg, ten: str = "") -> pd.DataFrame:
    """Doc parquet, chi lay cot can. CHI duoc loc theo TRAM o day.

    SUA 2026-08-22: ba dieu kien loc THEO DONG (exclude_from_training,
    has_complete_history_features, target NaN) da duoc chuyen xuong SAU
    them_muc_tieu() trong core/target.py. Loc chung o day duc lo hong tren luoi 15
    phut, khien phep tra nhan T+h khong tim thay moc va mat nhan oan - do duoc 31 dong
    o tam H1, keo phan vi 99 cua k lech 3e-06 va WAPE kiem dinh lech 0,015 diem so voi
    notebook. Loc theo TRAM thi an toan: moi phep tra deu nam trong groupby(site_id)
    nen bo ca mot tram khong lam thung luoi cua tram khac.
    """
    co_san = cot_co_san(duong_dan)
    muon = list(dict.fromkeys(
        features + cfg.features["cot_phu"] + cfg.features["cot_bat_buoc"]
    ))
    df = read_parquet(duong_dan, columns=[c for c in muon if c in co_san])
    n0 = len(df)

    loai = cfg.data["exclude_sites"]
    if loai and SITE_COL in df.columns:
        df = df[~df[SITE_COL].isin(loai)]

    print(f"Loc {ten or duong_dan.name}: {n0:,} -> {len(df):,} dong ({len(df.columns)} cot)")
    return df.sort_values([SITE_COL, TIMESTAMP_COL]).reset_index(drop=True)


def _loc_ban_ngay(df: pd.DataFrame, eps_elev: float) -> pd.DataFrame:
    """Bo dong khong the chuan hoa: site_scale <= 0 hoac mat troi duoi nguong."""
    return df[(df["site_scale"] > 0) & (df["sin_elevation_mt"] > eps_elev)].copy()


def chuan_bi(ctx: Ctx) -> Ctx:
    """Dien dev_h / test_h / features / medians / X_dev / y_dev / w_dev vao ctx."""
    cfg, paths = ctx.cfg, ctx.paths
    eps = float(cfg.features["eps_elev"])
    dtype = cfg.runtime["dtype"]
    h = ctx.horizon_steps

    # TAP HOC = train, KHONG phai development. Xem docstring dau file.
    # Neu chua co file train_selected (bo du lieu cu chi co development) thi lui ve
    # development va CANH BAO to, de khong am tham cham diem tren du lieu da hoc.
    duong_train = paths.selected("train_selected")
    duong_val = paths.selected("val_selected")
    if not duong_train.exists():
        duong_train = paths.selected("dev_selected")
        print("[CANH BAO] Khong tim thay train_selected -> lui ve development (= train+val). "
              "Moi chi so validation sinh ra se la IN-SAMPLE, khong dung de chon mo hinh.")

    # Danh sach dac trung lay tu selected_features.json (do stage s07 sinh ra) - KHONG
    # quet cot parquet, vi parquet con chua cot phu tro (site_scale, tran_cong_suat...)
    # dung de chuan hoa chu khong phai dac trung dau vao model.
    from core.columns import tach_dac_trung_ngan
    from core.io import read_json

    duong_sel = paths.stage_doc("s07_selected") / "selected_features.json"
    raw = read_json(duong_sel)
    selected = raw["selected_features"] if isinstance(raw, dict) else raw
    features, ctx.bo_di = tach_dac_trung_ngan(selected, cfg)
    print(f"selected_features.json: {len(selected)} cot -> giu {len(features)}, "
          f"bo {len(ctx.bo_di)} ({ctx.bo_di})")

    dev = _doc_tap(duong_train, features, cfg, duong_train.stem)
    # Chi giu dac trung co THAT trong du lieu (phong khi s07 liet ke cot da bi bo o s05)
    features = [c for c in features if c in dev.columns]

    dev_h = _loc_ban_ngay(them_muc_tieu(dev, h, cfg), eps)

    # Tap VALIDATION rieng - chua tung tham gia fit. s08c/s08e cham diem tren day.
    ctx.val_h = None
    if duong_val.exists():
        val = _doc_tap(duong_val, features, cfg, duong_val.stem)
        ctx.val_h = _loc_ban_ngay(them_muc_tieu(val, h, cfg), eps)
        del val

    # Bo sung cac cot tat dinh tai T+h vao tap dac trung. Phai lam SAU them_muc_tieu()
    # vi cot _mt duoc sinh trong do. Stage s09 dung dung cong thuc nay tren tap test.
    cot_mt = [
        ten_cot_muc_tieu(c)
        for c in cfg.features["cot_tat_dinh"]
        if ten_cot_muc_tieu(c) in dev_h.columns
    ]
    features = features + [c for c in cot_mt if c not in features]
    print(f"Them {len(cot_mt)} dac trung tat dinh tai T+{h * cfg.data['freq_minutes']} phut")
    print(f"Tong so dac trung: {len(features)}")

    medians = dev_h[features].median(numeric_only=True).fillna(0.0)

    from core.target import dat_nguong_cat, k_target, nguong_cat, tinh_nguong_cat

    # Suy nguong cat tu chinh tap train, GIONG notebook 06 (CLIP_K = None ->
    # tinh_clip_tu_train). Notebook tinh mot lan o H1 roi dung lai cho H4, nen o day
    # cung chi tinh khi chua co - de hai ben ra dung cung mot con so.
    if not cfg.train.get("clip_k"):
        dat_nguong_cat(cfg, tinh_nguong_cat(dev_h, cfg))
        print(f"Nguong cat suy tu tap train: phan vi {cfg.train['clip_phan_vi']} "
              f"cua k = {nguong_cat(cfg):.4f}")

    dev_h["k_target"] = k_target(dev_h, cfg)
    dev_h["w"] = build_sample_weight(dev_h, cfg)

    # Chi train tren dong co weight > 0 (giong srcs: mask = label_mask & weight_all.gt(0)).
    # Dong weight = 0 VAN GIU trong dev_h de bao cao, chi khong vao ham muc tieu.
    mask = dev_h["w"].gt(0)
    ctx.X_dev = dev_h.loc[mask, features].fillna(medians).astype(dtype)
    ctx.y_dev = dev_h.loc[mask, "k_target"].astype(dtype)
    ctx.w_dev = dev_h.loc[mask, "w"].astype(dtype)

    # Tap validation: dung DUNG bo dac trung va DUNG medians cua tap train. Medians phai
    # lay tu train - tinh lai tren val la ro ri thong ke tu tap dang duoc cham diem.
    if ctx.val_h is not None:
        ctx.val_h["k_target"] = k_target(ctx.val_h, cfg)
        ctx.val_h["w"] = build_sample_weight(ctx.val_h, cfg)
        print(f"Tap validation rieng: {len(ctx.val_h):,} dong "
              f"(chua tung tham gia fit, dung de chon mo hinh)")

    ctx.dev_h = dev_h
    ctx.features, ctx.medians = features, medians

    bi_loai = int((~mask).sum())
    print(f"Ma tran train: {ctx.X_dev.shape[0]:,} dong x {ctx.X_dev.shape[1]} dac trung")
    print(f"Bi loai khoi ham muc tieu: {bi_loai:,}/{len(dev_h):,} "
          f"({bi_loai / len(dev_h) * 100:.2f}%)")
    print(f"Khoang thoi gian train: {dev_h[TIMESTAMP_COL].min()} -> {dev_h[TIMESTAMP_COL].max()}")
    print("Tap test: KHONG mo o stage nay (chi mo o s09 sau khi da chon xong mo hinh)")
    return ctx


def bang_chinh_sach_outlier(ctx: Ctx) -> pd.DataFrame:
    """Bang doi chieu: moi to hop (nguon, nhom outlier) co bao nhieu dong duoc train.

    Bang nay la bang chung truoc hoi dong rang model KHONG hoc theo dong vuot tran
    vat ly - physical_over_capacity phai co ty_le_duoc_train = 0%.
    """
    ctx.bat_buoc_co("dev_h")
    bang = (
        ctx.dev_h.groupby(["nhan_energy_source", "nhan_outlier_group"], observed=True)
        .agg(so_dong=("w", "size"), so_dong_duoc_train=("w", lambda x: int((x > 0).sum())))
        .reset_index()
    )
    bang["ty_le_duoc_train_%"] = (
        bang["so_dong_duoc_train"] / bang["so_dong"] * 100
    ).round(1)
    return bang.sort_values("so_dong", ascending=False)


def chan_doan_clip(ctx: Ctx) -> dict:
    """Bao nhieu dong bi nguong k <= 1.5 cat mat - de biet clip co lam mat bien do dinh khong."""
    ctx.bat_buoc_co("dev_h")
    from core.target import mau_chuan_hoa

    eps = float(ctx.cfg.features["eps_elev"])
    k_raw = ctx.dev_h[TARGET_SHIFTED].to_numpy() / mau_chuan_hoa(ctx.dev_h, eps)
    tran = float(ctx.cfg.train["k_target_max"])
    bi_cat = int((k_raw > tran).sum())
    return {
        "so_dong_bi_clip": bi_cat,
        "tong_dong": len(ctx.dev_h),
        "ty_le_%": round(bi_cat / len(ctx.dev_h) * 100, 4),
        "k_raw_lon_nhat": float(np.nanmax(k_raw)),
    }
