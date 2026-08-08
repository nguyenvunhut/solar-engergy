"""Stage 09b: cham diem mo hinh vo dich tren TAP TEST NIEM PHONG - duy nhat 1 lan.

Tach tu phan sau run_final_test() cua 05_1_final_test.py.

TAP TEST NIEM PHONG NGHIA LA GI:
  Tap test khong tham gia BAT KY quyet dinh mo hinh nao - khong train, khong tune,
  khong chon loss. No duoc cham DUNG 1 LAN o day, thuan tuy de bao cao kha nang
  tong quat hoa. Mo hinh dem cham la mo hinh da duoc chon xong o stage s09a bang
  so lieu validation.

DAY LA NOI DUY NHAT TRONG CA PIPELINE MO TAP TEST.
  Stage s01-s07 co ghi file test (phai bien doi dac trung cho no) nhung KHONG dung test
  de suy ra bat ky tham so nao: site_scale/cs_factor lay tu train, bang ma categorical
  fit tren train, danh sach dac trung chon tren train. Stage s08 KHONG mo test.
  Kiem lai bang: python srcs/05_machine_learning/pipeline/checks/audit_test_sealed.py

SUA LOI CUA BAN CU:
  Ban cu doc X_test_h{n}.parquet do buoc train ghi ra - tuc la tap test da bi mo tu
  luc train. Neu thieu file do thi co nhanh du phong doc lai file test tho, nhung nhanh
  do KHONG tai tao 14 cot hau to _mt nen chi con 40/54 dac trung -> LightGBM bao
  "number of features in data (40) is not the same as it was in training data (54)".
  Ban moi tu dung ma tran test o day bang dung ham them_muc_tieu() ma luc train da dung,
  nen luon du 54 cot va khong phu thuoc file do stage khac ghi ra.
"""

from __future__ import annotations

import pickle

import pandas as pd
from core.columns import (
    DAYLIGHT_COL,
    PRED_COL,
    SITE_COL,
    SOURCE_COL,
    TARGET_SHIFTED,
    TIMESTAMP_COL,
)
from core.config import Cfg
from core.io import read_json, write_csv, write_json, write_parquet
from core.lgbm import chuan_bi_X
from core.metrics import PHAM_VI_CHINH_THUC, metrics_3_pham_vi, metrics_theo_site
from core.paths import Paths
from core.target import du_bao_ve_kwh, them_muc_tieu


def _nap_model(thu_muc, horizon: int):
    """Nap model.pkl + model_config.json, kiem horizon co khop khong."""
    cfg_model = read_json(thu_muc / "model_config.json")
    khai_bao = int(cfg_model.get("horizon_steps", -1))
    if khai_bao != horizon:
        raise ValueError(
            f"Model o {thu_muc} khai bao horizon_steps={khai_bao} nhung dang cham diem "
            f"h{horizon}. Doc nham model giua cac horizon la loi nghiem trong."
        )
    with open(thu_muc / "model.pkl", "rb") as f:
        return pickle.load(f), cfg_model


def _dung_ma_tran_test(cfg: Cfg, paths: Paths, horizon: int, features: list[str]) -> pd.DataFrame:
    """MO TAP TEST (lan duy nhat trong pipeline) va dung ma tran cham diem.

    Dung DUNG cac phep bien doi ma luc train da dung tren tap development:
      1. loc 4 dieu kien (exclude_from_training, has_complete_history_features,
         target khong NaN, bo exclude_sites)
      2. them_muc_tieu() - sinh y_true = shift(-h) VA 14 cot tat dinh hau to _mt
    Nho dung chung 1 ham voi luc train nen khong the lech logic.
    """
    from stages.s08a_prepare import _doc_tap

    duong_test = paths.selected("test_selected")
    print(f"   MO TAP TEST NIEM PHONG: {duong_test}")
    test = _doc_tap(duong_test, features, cfg, "test")
    # Tra ve CA khung goc (truoc them_muc_tieu) de lam nen cho file audit - notebook 07
    # dung khung nay, no du 486.160 dong thay vi 486.120 sau khi shift(-h) + dropna.
    nen = test[[c for c in (SITE_COL, TIMESTAMP_COL, SOURCE_COL, DAYLIGHT_COL)
                if c in test.columns]].copy()
    return them_muc_tieu(test, horizon, cfg), nen


def _mask_hep_nhat(scored: pd.DataFrame) -> pd.Series:
    """Pham vi hep nhat con du lieu: measured & ban ngay -> measured -> tat ca.

    Copy quy tac cua notebook 07 (bien use_mask): bang metric theo tram phai tinh tren
    du lieu DO THAT ban ngay, vi tram nao cung co hang loat dong dem bang 0 - gop chung
    vao se lam moi tram deu dep nhu nhau.
    """
    do_that = ((scored[SOURCE_COL] == "measured") if SOURCE_COL in scored.columns
               else pd.Series(True, index=scored.index))
    if DAYLIGHT_COL in scored.columns:
        ban_ngay = do_that & scored[DAYLIGHT_COL].fillna(False).astype(bool)
        if ban_ngay.sum():
            return ban_ngay
    return do_that if do_that.sum() else pd.Series(True, index=scored.index)


def cham_diem_1_horizon(cfg: Cfg, paths: Paths, horizon: int, win: dict) -> dict:
    """Cham diem 1 horizon, ghi metrics_overall.json + metrics_by_site.csv."""
    from pathlib import Path

    h_label = f"h{horizon}"
    thu_muc_model = Path(win["thu_muc_model"])
    model, cfg_model = _nap_model(thu_muc_model, horizon)
    features = cfg_model["features"]
    scored, nen_audit = _dung_ma_tran_test(cfg, paths, horizon, features)

    medians = pd.Series(cfg_model["feature_medians"], dtype=float)
    thieu = [c for c in features if c not in scored.columns]
    if thieu:
        raise KeyError(
            f"Ma tran test thieu {len(thieu)} dac trung: {thieu[:5]}... "
            f"Kiem lai stage s07 co chon dung bo dac trung nay khong."
        )

    # float64 - dung y notebook 07 (.astype(float)). Khac notebook 06 (float32) la co
    # chu dich, xem runtime.yaml: dtype_cham_diem.
    X = chuan_bi_X(scored, features, medians, dtype=cfg.runtime["dtype_cham_diem"])
    scored[PRED_COL] = du_bao_ve_kwh(model.predict(X), scored, cfg)
    scored["residual"] = scored[TARGET_SHIFTED] - scored[PRED_COL]

    m = metrics_3_pham_vi(scored)
    chinh = m[PHAM_VI_CHINH_THUC]
    print(
        f"--- TAP TEST NIEM PHONG {h_label.upper()} "
        f"(mo hinh {win['winning_loss'].upper()}) ---"
    )
    print(pd.DataFrame(m).T[["n", "wape", "rmse", "mae", "r2"]].round(4).to_string())
    print(f"CON SO CHINH THUC: WAPE = {chinh['wape']:.4f}% tren {chinh['n']:,} dong")

    thu_muc_ra = paths.horizon_dir("s09_final_test", horizon)
    thu_muc_ra.mkdir(parents=True, exist_ok=True)

    # DINH DANG FILE bam theo notebook 07 de doi chieu tung byte duoc:
    #  - so dong cua tung pham vi nam o cap NGOAI (measured_test_rows, ...) chu khong
    #    phai khoa 'n' ben trong tung pham vi
    #  - moi pham vi co them baseline_persistence_wape / improvement_vs_baseline_pct.
    #    Hai khoa nay la NaN vi baseline dai dang (persistence) can cot lag_1, ma lag_1
    #    da bi loai khoi bo dac trung do gay tre pha (audit 31/07). Notebook cung ghi NaN.
    def _pham_vi(ten: str) -> dict:
        d = dict(m.get(ten, {}))
        d.pop("n", None)
        d["baseline_persistence_wape"] = float("nan")
        d["improvement_vs_baseline_pct"] = float("nan")
        return d

    write_json(
        {
            "horizon_steps": horizon,
            "winning_loss": win["winning_loss"],
            "feature_set_name": "",
            "total_test_rows": len(scored),
            "measured_test_rows": int(m.get("measured", {}).get("n", 0)),
            "measured_daylight_test_rows": int(m.get(PHAM_VI_CHINH_THUC, {}).get("n", 0)),
            "all": _pham_vi("all"),
            "measured": _pham_vi("measured"),
            PHAM_VI_CHINH_THUC: _pham_vi(PHAM_VI_CHINH_THUC),
        },
        thu_muc_ra / "metrics_overall.json",
    )

    # Notebook 07 tinh metric theo tram tren pham vi HEP NHAT con du lieu (uu tien
    # measured_daylight), khong phai tren toan bo tap test - va khong ghi cot 'n'.
    mask = _mask_hep_nhat(scored)
    theo_site = metrics_theo_site(scored[mask]).drop(columns=["n"], errors="ignore")
    write_csv(theo_site, thu_muc_ra / "metrics_by_site.csv")

    # Snapshot ma tran test de stage s10 (SHAP) dung lai, khong phai mo test lan nua
    cot_luu = list(dict.fromkeys(features + [
        c for c in ("site_id", "timestamp", "plot_timestamp", "energy_generated_kwh",
                    TARGET_SHIFTED, "energy_source", "is_daylight",
                    "site_scale", "sin_elevation", "tran_cong_suat")
        if c in scored.columns
    ]))
    write_parquet(scored[cot_luu], thu_muc_ra / paths.file("x_test", h=horizon))

    return {"scored": scored, "metrics": m, "nen_audit": nen_audit}


def run_cham_diem(cfg: Cfg, paths: Paths, vo_dich: dict) -> pd.DataFrame:
    """Cham diem moi horizon co mo hinh vo dich, gop thanh 1 file audit chung.

    KHUNG AUDIT lay tu TOAN BO tap test da loc (truoc buoc them_muc_tieu), roi left-merge
    du bao cua tung horizon vao - dung y notebook 07. Neu lay khung tu ket qua cham diem
    thi se thieu dong CUOI CUNG cua moi site (shift(-h) khong co nhan nen bi dropna),
    tuc mat 40 dong voi h1. Giu lai de nhin duoc vung nao khong co du bao.
    """
    gop = None
    for h in cfg.train["horizon_steps"]:
        h_label = f"h{h}"
        if h_label not in vo_dich:
            print(f"[BO QUA] {h_label}: chua co mo hinh vo dich.")
            continue
        kq = cham_diem_1_horizon(cfg, paths, h, vo_dich[h_label])
        s = kq["scored"]

        if gop is None:
            gop = kq["nen_audit"]

        phan = s[[SITE_COL, TIMESTAMP_COL, TARGET_SHIFTED, PRED_COL, "residual"]].rename(
            columns={
                TARGET_SHIFTED: f"y_true_{h_label}",
                PRED_COL: f"y_pred_{h_label}",
                "residual": f"residual_{h_label}",
            }
        )
        # Bon cot dau thoi gian - dung ten va dung thu tu nhu notebook 07 ghi ra.
        # source = thoi diem lay dac trung (T); ba cot con lai deu la thoi diem duoc du
        # bao (T+h). Notebook giu ca ba ten khac nhau cho cac muc dich doc khac nhau
        # (nhan, ve bieu do, doi chieu) du gia tri nhu nhau - giu nguyen de khop file.
        freq = int(cfg.data["freq_minutes"])
        goc_ts = pd.to_datetime(phan[TIMESTAMP_COL])
        muc_tieu = goc_ts + pd.Timedelta(minutes=freq * h)
        phan[f"source_timestamp_{h_label}"] = goc_ts
        phan[f"target_timestamp_{h_label}"] = muc_tieu
        phan[f"label_timestamp_{h_label}"] = muc_tieu
        phan[f"plot_timestamp_{h_label}"] = muc_tieu
        # left-merge: giu nguyen so dong cua khung nen, dong nao khong co du bao thi NaN
        gop = gop.merge(phan, on=[SITE_COL, TIMESTAMP_COL], how="left")
        print()

    if gop is not None:
        duong_dan = paths.stage("s09_final_test") / paths.file("prediction_audit")
        write_parquet(gop, duong_dan)
        print(f"Da ghi file du bao tong hop: {duong_dan} ({len(gop):,} dong)")
    return gop
