"""Stage 10: giai thich mo hinh bang SHAP (TreeExplainer).

Tach tu 05_2_explainable_ai.py.

DUNG MO HINH NAO: mo hinh VO DICH do stage s09a chon (doc best_loss.json), khong
hardcode 'huber' nhu ban cu. Ban cu hardcode LOSS_NAME = 'huber' o dau file, nen neu
mo hinh vo dich doi thi bang SHAP van giai thich mo hinh cu - sai lech giua bao cao
va thuc te.

LUU Y VE GIA TRI SHAP: file shap_values.parquet CHI chua gia tri SHAP (bien do nho,
+-0.01..0.09), KHONG chua gia tri dac trung goc. Muon ve PDP/scatter phai join voi
X_test_h{n}.parquet qua (site_id, timestamp) de lay gia tri that.
"""

from __future__ import annotations

import gc
import pickle
import time
from pathlib import Path

import numpy as np
import pandas as pd
from core.columns import SITE_COL, TIMESTAMP_COL
from core.config import Cfg, load_config
from core.io import read_json, write_csv, write_parquet
from core.lgbm import chuan_bi_X
from core.paths import Paths

# Kich thuoc lo khi tinh SHAP. Ma tran dong gop la (so_dong x so_dac_trung+1) so
# float32, tren 475k dong x 55 la ~100 MB - chia lo de dinh bo nho, khong doi ket qua.
LO_SHAP = 100_000


def _thu_muc_model(cfg: Cfg, paths: Paths, horizon: int) -> tuple[Path, str]:
    """Lay thu muc model VO DICH tu best_loss.json do stage s09a ghi."""
    h_label = f"h{horizon}"
    for goc in (paths.stage("s09_final_test"), paths.stage_goc("s09_final_test")):
        f = goc / "best_loss.json"
        if f.exists():
            d = read_json(f).get(h_label)
            if d:
                if "thu_muc_model" in d:
                    return Path(d["thu_muc_model"]), d["winning_loss"]
                loss = d.get("winning_loss") or d.get("folder_name")
                return paths.stage_goc("s08_train") / loss / h_label, loss
    raise FileNotFoundError(
        "Khong tim thay best_loss.json. Chay stage s09 truoc:\n"
        "    python srcs/05_machine_learning/pipeline/run.py --stage s09"
    )


def tinh_shap(cfg: Cfg, paths: Paths, horizon: int) -> pd.DataFrame:
    """Tinh SHAP cho mo hinh vo dich cua 1 horizon, ghi ra 08_explain/."""
    thu_muc, loss = _thu_muc_model(cfg, paths, horizon)
    h_label = f"h{horizon}"
    print(f"Mo hinh vo dich {h_label}: {loss.upper()} tai {thu_muc}")

    cfg_model = read_json(thu_muc / "model_config.json")
    with open(thu_muc / "model.pkl", "rb") as f:
        model = pickle.load(f)

    # Doc snapshot ma tran test do stage s09 ghi ra - KHONG tu mo lai tap test.
    # Tap test chi duoc mo dung 1 lan o s09; s10 dung lai snapshot do.
    duong_test = paths.horizon_dir("s09_final_test", horizon) / paths.file("x_test", h=horizon)
    if not duong_test.exists():
        raise FileNotFoundError(
            f"Khong tim thay {duong_test}. File nay do stage s09 xuat ra. "
            f"Chay truoc: python srcs/05_machine_learning/pipeline/run.py --stage s09"
        )
    test_df = pd.read_parquet(duong_test).reset_index(drop=True)

    features = [c for c in cfg_model["features"] if c in test_df.columns]
    thieu = [c for c in cfg_model["features"] if c not in features]
    if thieu:
        raise KeyError(f"Ma tran test thieu {len(thieu)} dac trung: {thieu[:8]}")

    medians = pd.Series(cfg_model["feature_medians"], dtype=float)
    X = chuan_bi_X(test_df, features, medians, dtype="float64")
    print(f"Da nap {len(X):,} dong x {len(features)} dac trung")

    # SHAP tren TOAN BO ma tran test, KHONG lay mau. Ban cu lay ngau nhien 2.000 dong
    # cho nhanh nen bang xep hang tam quan trong chi la uoc luong tren mau - da du de
    # doi thu hang hai dac trung dan dau (direct_normal_irradiance vs ky_vong).
    #
    # Dung booster_.predict(pred_contrib=True) thay cho shap.TreeExplainer: LightGBM cai
    # dat san chinh thuat toan TreeSHAP cua Lundberg trong loi C++, ra CUNG bo gia tri
    # nhung nhanh hon nhieu bac - do la thu duy nhat khien viec bo lay mau kha thi.
    # Cot CUOI CUNG cua pred_contrib la gia tri co so, phai cat bo truoc khi gop.
    n = len(X)
    n_lo = (n + LO_SHAP - 1) // LO_SHAP
    print(f"Tinh SHAP tren TOAN BO {n:,} dong x {len(features)} dac trung "
          f"({n_lo} lo, moi lo {LO_SHAP:,} dong)...")

    booster = model.booster_ if hasattr(model, "booster_") else model
    t0 = time.time()
    phan = []
    co_so = None
    for i in range(n_lo):
        a, b = i * LO_SHAP, min((i + 1) * LO_SHAP, n)
        ct = np.asarray(
            booster.predict(X.iloc[a:b], pred_contrib=True), dtype=np.float32
        )
        if co_so is None:
            co_so = float(ct[0, -1])
        phan.append(ct[:, :-1])
        print(f"   lo {i + 1}/{n_lo}: dong {a:,}-{b:,} | {time.time() - t0:,.0f}s")

    gia_tri = np.concatenate(phan, axis=0)
    del phan
    gc.collect()
    print(f"Xong trong {time.time() - t0:,.0f}s. Ma tran SHAP: {gia_tri.shape} "
          f"| gia tri co so {co_so:.6f}")

    # Kiem TINH CONG cua TreeSHAP: tong dong gop + gia tri co so phai bang du bao goc.
    # Sai o day nghia la da cat nham cot co so hoac gop lo sai thu tu.
    thu = model.predict(X.iloc[:2000])
    sai_so = float(np.abs(gia_tri[:2000].sum(axis=1) + co_so - thu).max())
    print(f"Kiem tinh cong (2.000 dong dau): sai lech lon nhat {sai_so:.3e}")

    tam_quan_trong = pd.DataFrame(
        {
            "feature": features,
            "mean_abs_shap": np.abs(gia_tri).mean(axis=0),
        }
    ).sort_values("mean_abs_shap", ascending=False)
    tam_quan_trong["so_dong_tinh"] = n

    print(f"TOP 10 DAC TRUNG QUAN TRONG NHAT ({h_label}):")
    print(tam_quan_trong.head(10).to_string(index=False))

    thu_muc_ra = paths.stage("s10_explain")
    thu_muc_ra.mkdir(parents=True, exist_ok=True)
    write_csv(tam_quan_trong, thu_muc_ra / f"shap_importance_{h_label}.csv")
    # Notebook 08 chi lam h1 nen ghi ten KHONG hau to. Ghi them ban do de doi chieu duoc
    # va de bao cao/dashboard tro san vao ten cu ma khong phai sua duong dan.
    if horizon == 1:
        write_csv(tam_quan_trong, thu_muc_ra / "shap_importance.csv")

    cot_meta = [c for c in (SITE_COL, TIMESTAMP_COL) if c in test_df.columns]
    khung = pd.concat(
        [
            test_df[cot_meta].copy(),
            pd.DataFrame(gia_tri, columns=features, index=X.index),
        ],
        axis=1,
    )
    write_parquet(khung, thu_muc_ra / f"shap_values_{h_label}.parquet")
    if horizon == 1:
        write_parquet(khung, thu_muc_ra / "shap_values.parquet")
    print(f"Da ghi SHAP vao: {thu_muc_ra}\n")
    return tam_quan_trong


def run_s10(cfg: Cfg | None = None) -> dict:
    cfg = cfg or load_config()
    paths = Paths(cfg)
    return {f"h{h}": tinh_shap(cfg, paths, h) for h in cfg.train["horizon_steps"]}
