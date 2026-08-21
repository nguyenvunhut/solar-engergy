#!/usr/bin/env python3
"""ACTION: baseline Prophet do tren DUNG TAP TEST NIEM PHONG.

    python -u srcs/05_machine_learning/pipeline/actions/baseline_prophet_test_set.py

VI SAO PHAI CO FILE NAY (khac gi baseline_prophet.py cu):
  baseline_prophet.py va notebook 06_0b deu dat TY_LE_TRAIN = 0.8 roi TU CAT 80/20
  ben trong file audit. Nghia la Prophet duoc cham diem tren 20% cuoi chuoi cua rieng
  no, con LightGBM duoc cham tren tap test niem phong - HAI TAP DONG KHAC NHAU.
  Ghep 2 con so do lai thanh Skill Score la sai phep so sanh, du ket qua co dep den may.

  File nay sua dung 1 diem do:
    - Prophet HOC tren tap development (train + val), dung phan du lieu ma LightGBM
      cung duoc hoc, khong hon khong kem.
    - Prophet DU BAO tai dung cac moc thoi gian muc tieu T+h cua tap test.
    - Cham diem tren DUNG tap dong ma metrics headline cua du an da cham LightGBM,
      lay thang tu prediction_audit.parquet -> cung tu so, cung mau so.

DIEU KIEN DOI CHUNG CONG BANG (giu nguyen tu ban cu):
  Prophet CHI hoc tu lich su san luong + seasonality ngay/tuan cua chinh no, KHONG
  duoc dua bat ky dac trung thoi tiet nao vao. Do la ban chat cua 1 baseline chuoi
  thoi gian thuan tuy - doi lap co chu dich voi LightGBM co day du dac trung thoi tiet.

KHONG GHI DE KET QUA CU: ghi vao thu muc rieng 08_baseline_prophet_test/.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

THU_MUC_PIPELINE = Path(__file__).resolve().parents[1]
if str(THU_MUC_PIPELINE) not in sys.path:
    sys.path.insert(0, str(THU_MUC_PIPELINE))

GOC_REPO = Path(__file__).resolve().parents[4]

DEV = GOC_REPO / "data/model/v3/05_selected/v3_development_selected.parquet"
AUDIT = GOC_REPO / "data/model/v3/07_final_test/prediction_audit.parquet"
TEST = GOC_REPO / "data/model/v3/05_selected/v3_test_selected.parquet"
RA = GOC_REPO / "data/model/v3/08_baseline_prophet_test"

BUOC_PHUT = 15  # luoi 15 phut

# Tham so chuan hoa — DOC TU model_config.json cua LightGBM, khong viet lai bang tay.
# Hai mo hinh phai dung DUNG cung mot cong thuc thi so sanh moi co nghia.
CAU_HINH_MODEL = GOC_REPO / "data/model/v3/06_train/huber/h1/model_config.json"
# SUA 2026-08-22: nguong cat KHONG ghim cung 1.5 nua. Quy uoc cua du an: 06_4 cham
# validation bang k_target_max, con 07/07b cham TEST bang clip_k cua chinh mo hinh.
# File nay so tren tap TEST nen phai theo clip_k - doc tu model_config trong
# tham_so_chuan_hoa(). Ghim 1.5 lam Prophet duoc tran rong hon LightGBM.
TRAN_HE_SO = 1.02         # train.yaml: tran_cong_suat_he_so


def tham_so_chuan_hoa() -> dict:
    """Lay dung bo tham so chuan hoa ma LightGBM dang dung."""
    c = json.loads(CAU_HINH_MODEL.read_text(encoding="utf-8"))
    return {
        "quy_mo": c["cot_quy_mo"],          # site_scale
        # model_config ghi 'sin_elevation_mt' (mau so lay tai T+h). File nay TU tra
        # sang T+h bang hau to _mt_h{h} o duoi, con tep 05_selected chi co cot GOC -
        # nen phai lui ve TEN GOC, neu khong vua doc thieu cot vua dich hai lan.
        "sin_elev": (c["cot_sin_elev"][:-3]
                     if c["cot_sin_elev"].endswith("_mt") else c["cot_sin_elev"]),
        "tran": c["cot_tran"],              # tran_cong_suat
        "eps": float(c.get("eps_elev", 0.05)),
        "clip_k": float(c["clip_k"]),
    }


def giai_chuan_hoa(k, quy_mo, sin_elev, tran, eps, clip_k) -> np.ndarray:
    """Nhan nguoc k -> kWh, DUNG y cong thuc LightGBM dung o s09b.

        y = clip(k, 0, clip_k) * site_scale * max(sin_elev, eps)
        y = min(y, tran_cong_suat * 1.02)
        y = 0  khi sin_elev <= eps        <- ban dem tu ve 0, khong phai chan tay
    """
    y = np.clip(k, 0.0, clip_k) * quy_mo * np.maximum(sin_elev, eps)
    y = np.minimum(y, tran * TRAN_HE_SO)
    return np.where(sin_elev <= eps, 0.0, y)


def wape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """WAPE = tong |sai so| / tong |thuc te|, don vi %."""
    mau = np.abs(y_true).sum()
    return float(np.abs(y_true - y_pred).sum() / mau * 100.0) if mau > 0 else float("nan")


def nap_du_lieu(horizons: list[int]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Doc tap hoc (dev, chi dong measured) va tap cham diem (audit + nhan tai T+h).

    Mask cham diem dung DUNG dieu kien headline cua du an, cong them dieu kien
    'nhan tai T+h cung phai la so do that' - vi cham mot du bao bang mot nhan do ETL
    bia ra thi con so khong con do nang luc du bao nua.
    """
    ts = tham_so_chuan_hoa()
    dev = pd.read_parquet(
        DEV,
        columns=["site_id", "timestamp", "energy_generated_kwh", "energy_source",
                 "is_daylight", ts["quy_mo"], ts["sin_elev"]],
    )
    # ── PROPHET HOC TREN MUC TIEU CHUAN HOA, DUNG NHU LIGHTGBM ──────────────────
    #
    # VI SAO PHAI LAM THE. LightGBM khong du bao kWh tho — no du bao ty le
    #     k = energy / (site_scale * sin_elevation)
    # roi moi nhan nguoc ra kWh. Nho vay phan HINH HOC MAT TROI duoc xu ly bang vat
    # ly, mo hinh chi phai hoc phan bien dong con lai, va ban dem tu ve 0 vi
    # sin_elevation ~ 0.
    #
    # Ban truoc bat Prophet du bao THANG kWh tho. No phai tu hoc ca nhip moc/lan
    # bang chuoi Fourier tron — thu ve nguyen tac khong dung duoc canh sac. Ket qua
    # do tren tap test: trang thai 18:30 tram tat han (thuc te 0.000, LightGBM
    # 0.000) nhung Prophet van bao 3.980 va con "ro" toi 20:45.
    #
    # Do la HAI BAI TOAN KHAC DO KHO, khong phai hai mo hinh cung dieu kien. Cho mot
    # ben cong cu vat ly roi bat ben kia lam tay khong thi so sanh khong con nghia.
    #
    # Cach lam nay cung la chuan cua nganh: du bao mat troi lam tren chi so chuan hoa
    # chu khong tren cong suat tho — xem Lauret et al. (2022), "Solar Forecasts Based
    # on the Clear Sky Index or the Clearness Index", DOI 10.3390/solar2040026, chinh
    # la bai bao cao da trich dan.
    #
    # Chi giu dong BAN NGAY co so do that: dung tap ma LightGBM duoc hoc. Ban dem
    # khong can hoc nua vi phep nhan nguoc da ep ve 0.
    se = dev[ts["sin_elev"]].to_numpy(float)
    giu = (
        (dev["energy_source"] == "measured")
        & dev["is_daylight"].fillna(False).astype(bool)
        & (se > ts["eps"])
        & (dev[ts["quy_mo"]] > 0)
    )
    dev = dev[giu].copy()
    dev["k"] = (dev["energy_generated_kwh"]
                / (dev[ts["quy_mo"]] * np.maximum(dev[ts["sin_elev"]], ts["eps"])))
    dev["k"] = dev["k"].clip(0.0, ts["clip_k"])
    dev = dev.rename(columns={"timestamp": "ds", "k": "y"})

    au = pd.read_parquet(AUDIT)
    goc = pd.read_parquet(
        TEST,
        columns=["site_id", "timestamp", "energy_source",
                 ts["quy_mo"], ts["sin_elev"], ts["tran"]],
    )
    au = au.merge(goc.rename(columns={"energy_source": "src_goc"}),
                  on=["site_id", "timestamp"], how="left")
    au = au.sort_values(["site_id", "timestamp"]).reset_index(drop=True)
    for h in horizons:
        # SUA 2026-08-21: TRA THEO MOC THOI GIAN, khong con shift(-h) theo DONG.
        # shift dem theo VI TRI DONG nen thung luoi mot moc la vo phai dong ke tiep CON
        # SONG chu khong phai moc T+h that. Dai luong de nhan nguoc phai lay tai MOC MUC
        # TIEU T+h: sin_elevation la dai luong thien van tinh truoc duoc nen dung o T da
        # biet chinh xac gia tri tai T+h - khong phai leakage.
        _cot = [c for c in (ts["sin_elev"], ts["quy_mo"], ts["tran"]) if c in au.columns]
        _m = au[["site_id", "timestamp"]].copy()
        _m["timestamp"] = _m["timestamp"] + pd.Timedelta(minutes=15 * h)
        _m["_i"] = au.index
        _t = au[["site_id", "timestamp", "src_goc"] + _cot].rename(
            columns={"src_goc": f"src_nhan_h{h}",
                     **{c: f"{c}_mt_h{h}" for c in _cot}})
        _kq = _m.merge(_t, on=["site_id", "timestamp"], how="left").set_index("_i")
        au[f"src_nhan_h{h}"] = _kq[f"src_nhan_h{h}"].reindex(au.index)
        for c in _cot:
            au[f"{c}_mt_h{h}"] = _kq[f"{c}_mt_h{h}"].reindex(au.index)
    return dev[["site_id", "ds", "y"]], au


def mask_cham_diem(au: pd.DataFrame, h: int) -> pd.Series:
    """Dong duoc dua vao con so cong bo, cho horizon h."""
    return (
        (au["energy_source"] == "measured")
        & (au[f"src_nhan_h{h}"] == "measured")
        & au["is_daylight"].fillna(False).astype(bool)
        & au[f"y_true_h{h}"].notna()
        & au[f"y_pred_h{h}"].notna()
    )


def du_bao_1_site(dev_site: pd.DataFrame, moc_can: pd.DatetimeIndex) -> pd.Series | None:
    """Fit Prophet tren lich su 1 site roi du bao tai cac moc thoi gian can.

    Tra ve Series index = moc thoi gian, value = du bao (da chan duoi 0 vi san luong
    khong the am).
    """
    from prophet import Prophet

    if len(dev_site) < 200 or len(moc_can) == 0:
        return None
    m = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False)
    m.fit(dev_site[["ds", "y"]].sort_values("ds"))
    kq = m.predict(pd.DataFrame({"ds": moc_can}))
    return pd.Series(kq["yhat"].clip(lower=0).to_numpy(), index=moc_can)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--horizons", type=int, nargs="+", default=[1, 4])
    p.add_argument("--gioi-han-site", type=int, default=0,
                   help="Chi chay N site dau (de thu nhanh); 0 = chay het.")
    args = p.parse_args()

    # Chay thu (--gioi-han-site) GHI RA THU MUC KHAC. Da tung mat ket qua 40 tram vi
    # mot lan chay thu 3 tram ghi de len dung ten file — ket qua that bien mat lang le,
    # summary chi con so_site=3 ma khong bao loi gi.
    global RA
    if args.gioi_han_site:
        RA = RA.with_name(f"{RA.name}_thu_{args.gioi_han_site}site")
        print(f"[CHAY THU {args.gioi_han_site} tram] ghi rieng vao {RA.name}, "
              f"khong dung ket qua that.\n")

    RA.mkdir(parents=True, exist_ok=True)
    print(f"Doc du lieu... (dev={DEV.name}, audit={AUDIT.name})")
    ts = tham_so_chuan_hoa()
    dev, au = nap_du_lieu(args.horizons)
    sites = sorted(au["site_id"].unique())
    if args.gioi_han_site:
        sites = sites[: args.gioi_han_site]
    print(f"So site: {len(sites)} | dev measured: {len(dev):,} dong | audit: {len(au):,} dong\n")

    # Moc thoi gian can du bao = moc muc tieu T+h cua moi dong duoc cham diem.
    can = {}
    for h in args.horizons:
        m = mask_cham_diem(au, h)
        au.loc[m, f"ds_muc_tieu_h{h}"] = (
            au.loc[m, "timestamp"] + pd.Timedelta(minutes=BUOC_PHUT * h)
        )
        can[h] = m
        print(f"  h{h}: {int(m.sum()):,} dong duoc cham diem")

    t0 = time.time()
    dong_site, loi = [], []
    for i, s in enumerate(sites, 1):
        dv = dev[dev["site_id"] == s]
        au_s = au[au["site_id"] == s]
        # Du bao tai MOI moc muc tieu cua tram, KHONG chi cac dong duoc cham diem.
        #
        # Ban dau chi lay moc trong mask cham diem, khien cot prophet_h* bi rong o moi
        # dong ngoai pham vi cham — ve len dashboard thi duong Prophet DUT QUANG tung
        # doan, trong khong ra gi cho mot mo hinh doi chung.
        # Cham diem va ve la hai viec khac nhau: cham thi phai loc chat, ve thi phai
        # lien mach. Mask van duoc ap nguyen ven o buoc tinh chi so ben duoi.
        moc = pd.DatetimeIndex(sorted({
            t for h in args.horizons
            for t in (au_s["timestamp"] + pd.Timedelta(minutes=BUOC_PHUT * h)).dropna()
        }))
        try:
            du_bao = du_bao_1_site(dv, moc)
        except Exception as e:  # noqa: BLE001 - Prophet co the loi tren site du lieu xau
            loi.append({"site_id": s, "loi": str(e)[:150]})
            print(f"   [{i:>2}/{len(sites)}] site {s}: LOI - {str(e)[:70]}")
            continue
        if du_bao is None:
            continue
        ghi = {"site_id": s, "n_train": len(dv)}
        for h in args.horizons:
            # Ghi du bao cho MOI dong cua tram -> duong ve lien mach tren dashboard.
            moc_h = au_s["timestamp"] + pd.Timedelta(minutes=BUOC_PHUT * h)
            # Prophet tra ve k (ty le chuan hoa). Nhan nguoc ra kWh bang DUNG cong
            # thuc LightGBM dung, voi dai luong lay tai moc muc tieu T+h.
            k = du_bao.reindex(moc_h).to_numpy(float)
            gia_tri = giai_chuan_hoa(
                k,
                au_s[f'{ts["quy_mo"]}_mt_h{h}'].to_numpy(float),
                au_s[f'{ts["sin_elev"]}_mt_h{h}'].to_numpy(float),
                au_s[f'{ts["tran"]}_mt_h{h}'].to_numpy(float),
                ts["eps"],
                ts["clip_k"],
            )
            au.loc[au_s.index, f"prophet_h{h}"] = gia_tri

            # Chi so thi CHI tinh tren cac dong trong pham vi cham diem.
            idx = au_s.index[can[h][au_s.index]]
            if len(idx) == 0:
                continue
            yt = au.loc[idx, f"y_true_h{h}"].to_numpy(float)
            yp = au.loc[idx, f"prophet_h{h}"].to_numpy(float)
            ok = ~np.isnan(yp)
            ghi[f"n_test_h{h}"] = int(ok.sum())
            ghi[f"wape_prophet_h{h}"] = round(wape(yt[ok], yp[ok]), 4)
            ghi[f"wape_model_h{h}"] = round(
                wape(yt[ok], au.loc[idx, f"y_pred_h{h}"].to_numpy(float)[ok]), 4)
        dong_site.append(ghi)
        mo_ta = "  ".join(f"h{h}: Prophet {ghi.get(f'wape_prophet_h{h}', float('nan')):.2f}%"
                          f" / model {ghi.get(f'wape_model_h{h}', float('nan')):.2f}%"
                          for h in args.horizons)
        print(f"   [{i:>2}/{len(sites)}] site {s}: {mo_ta}   ({(time.time()-t0)/60:.1f} phut)")

    bang = pd.DataFrame(dong_site)
    bang.to_csv(RA / "prophet_test_by_site.csv", index=False)

    # Pooled: gop toan bo sai so tuyet doi roi chia tong san luong that - dung cach
    # metrics headline gop, KHONG lay trung binh WAPE theo site (trung binh cua ty so
    # khong bang ty so cua tong, se lech).
    tom_tat = {"nguon_hoc": "v3_development_selected (train+val), chi dong measured",
               "nguon_cham_diem": "07_final_test/prediction_audit.parquet",
               "so_site": int(len(bang)), "so_site_loi": len(loi)}
    for h in args.horizons:
        c = f"prophet_h{h}"
        if c not in au.columns:
            continue
        m = can[h] & au[c].notna()
        yt = au.loc[m, f"y_true_h{h}"].to_numpy(float)
        wp = wape(yt, au.loc[m, c].to_numpy(float))
        wm = wape(yt, au.loc[m, f"y_pred_h{h}"].to_numpy(float))
        tom_tat[f"h{h}"] = {
            "n_dong": int(m.sum()),
            "wape_prophet_%": round(wp, 4),
            "wape_lightgbm_%": round(wm, 4),
            "skill_score_%": round((1 - wm / wp) * 100.0, 4),
        }
        print(f"\n=== h{h} ({int(m.sum()):,} dong, cung tap dong cho ca hai) ===")
        print(f"   Prophet  WAPE = {wp:7.4f}%")
        print(f"   LightGBM WAPE = {wm:7.4f}%")
        print(f"   Skill Score   = {(1 - wm / wp) * 100:+7.2f}%")

    if loi:
        tom_tat["site_loi"] = loi
        print(f"\n[CANH BAO] {len(loi)} site loi: {[x['site_id'] for x in loi]}")

    import json
    (RA / "prophet_test_summary.json").write_text(
        json.dumps(tom_tat, ensure_ascii=False, indent=2), encoding="utf-8")
    au_ra = [c for c in au.columns if c.startswith("prophet_h")]
    if au_ra:
        au[["site_id", "timestamp", *au_ra]].to_parquet(
            RA / "prophet_test_predictions.parquet", index=False)
    print(f"\nDa ghi vao: {RA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
