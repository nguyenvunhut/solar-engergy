#!/usr/bin/env python3
"""ACTION (khong nam trong pipeline chuan): toi uu sieu tham so bang Optuna.

    python srcs/05_machine_learning/pipeline/actions/tune_optuna.py --loss huber --horizon 1 --trials 15

VI SAO TACH RA KHOI PIPELINE:
  Ban cu nhet Optuna thang vao giua ham train, nen MOI lan chay lai pipeline la phai
  ngoi cho tuning ~1 tieng, ke ca khi chi muon train lai bang bo tham so da tim duoc.
  Gio Optuna la 1 hanh dong RIENG, chay khi nao can; ket qua ghi ra best_params.json,
  pipeline chuan chi doc file do (xem core/config.py::sieu_tham_so).

Toi uu theo POOLED WAPE tren 5 fold TimeSeriesSplit - gop tu so/mau so cua ca 5 fold
chu khong lay trung binh cac WAPE (dung dinh nghia WAPE). Tuyet doi khong dung tap
test o day: tap test chi duoc cham DUY NHAT 1 LAN o stage s09.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

THU_MUC_PIPELINE = Path(__file__).resolve().parents[1]
if str(THU_MUC_PIPELINE) not in sys.path:
    sys.path.insert(0, str(THU_MUC_PIPELINE))

from core.config import load_config  # noqa: E402
from core.context import Ctx  # noqa: E402
from core.io import read_json, write_json  # noqa: E402
from core.lgbm import dat_env_opencl, dat_env_threads, fit_an_toan, kiem_tra_gpu, them_tham_so_gpu  # noqa: E402
from core.paths import Paths  # noqa: E402


def khong_gian_tim_kiem(trial, loss_name: str) -> dict:
    """Khoang tim kiem cho tung sieu tham so - copy nguyen si tu tham_so_co_ban(trial)."""
    p = {
        "n_estimators": trial.suggest_int("n_estimators", 400, 1200),
        "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.12, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 63, 255),
        "min_child_samples": trial.suggest_int("min_child_samples", 20, 120),
        "subsample": trial.suggest_float("subsample", 0.7, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.7, 1.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 10.0),
        "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 10.0),
    }
    # alpha la delta cua Huber (cang lon cang gan MSE, cang nhay voi sai so lon nen bat
    # dinh tot hon). Chi co y nghia khi objective = 'huber'.
    if loss_name == "huber":
        p["alpha"] = trial.suggest_float("alpha", 0.5, 20.0, log=True)
    return p


def tune(loss_name: str, horizon: int, n_trials: int) -> dict:
    import optuna
    from optuna.samplers import TPESampler

    from stages import s08a_prepare, s08b_train_folds

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    cfg = load_config()
    ctx = Ctx(cfg=cfg, paths=Paths(cfg), loss_name=loss_name, horizon_steps=horizon)

    s08a_prepare.chuan_bi(ctx)
    s08b_train_folds.nap_cac_fold(ctx)
    gpu, _ = kiem_tra_gpu(cfg)
    co_ban, _ = cfg.sieu_tham_so(loss_name, horizon)
    t0 = time.time()

    def objective(trial):
        params = them_tham_so_gpu({**co_ban, **khong_gian_tim_kiem(trial, loss_name)}, cfg, gpu)
        models = []
        for f in ctx.cac_fold:
            m, _ = fit_an_toan(params, f["Xtr"], f["ytr"], sample_weight=f["wtr"], cfg=cfg)
            models.append(m)
        gop, theo_fold = s08b_train_folds.pooled_wape(models, ctx)
        trial.set_user_attr("wape_theo_fold", theo_fold)
        return gop

    def log_trial(study, trial):
        xong = trial.number + 1
        phut = (time.time() - t0) / 60
        gt = f"{trial.value:.4f}%" if trial.value is not None else "pruned"
        con = phut / xong * (n_trials - xong)
        fold = trial.user_attrs.get("wape_theo_fold", {})
        chi_tiet = " | ".join(f"f{k}={v:.1f}%" for k, v in sorted(fold.items()))
        print(f"   [Trial {xong:>2}/{n_trials}] pooled WAPE {gt:>10} "
              f"| tot nhat {study.best_value:.4f}% | {phut:.1f}p, con ~{con:.1f}p")
        if chi_tiet:
            print(f"        tung fold: {chi_tiet}")

    study = optuna.create_study(direction="minimize",
                                sampler=TPESampler(seed=cfg.runtime["lightgbm"]["seed"]))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False, callbacks=[log_trial])

    print(f"\nPooled WAPE tot nhat tren {len(ctx.cac_fold)} fold = {study.best_value:.4f}%")
    # tien to '_' = so lieu kem theo, sieu_tham_so() se bo qua khi ghep tham so cho
    # LightGBM (neu khong LightGBM se nhan mot tham so la ten 'pooled_wape_cv')
    return {**study.best_params, "_pooled_wape_cv": float(study.best_value)}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--loss", default="huber", help="mae | huber | mse")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--trials", type=int, default=15)
    args = p.parse_args()

    cfg = load_config()
    dat_env_threads(cfg)
    dat_env_opencl(cfg)

    best = tune(args.loss, args.horizon, args.trials)

    # Gop vao file cu thay vi ghi de - de tune tung (loss, horizon) rieng ma khong mat
    # ket qua truoc. Long theo horizon: h1 va h4 la hai phien tune doc lap, bo tham so
    # khac han nhau (huber h1 alpha = 1,0407 con h4 alpha = 13,5687).
    duong_dan = Paths(cfg).action("best_params")
    hien_co = read_json(duong_dan) if duong_dan.exists() else {}
    hien_co.setdefault(args.loss, {})[f"h{args.horizon}"] = best
    write_json(hien_co, duong_dan)
    print(f"\nDa ghi sieu tham so vao: {duong_dan}")
    print("Pipeline chuan se tu doc file nay o lan train sau (khong chay lai Optuna).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
