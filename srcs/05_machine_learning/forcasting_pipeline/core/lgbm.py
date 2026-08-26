"""Thiet lap GPU/OpenCL va huan luyen LightGBM an toan.

Gop 3 ban gan giong nhau: _fit_thu() (buoc 10) va fit_an_toan() (buoc 11) trong
04_x_train_*.py, cung khoi thiet lap OCL_ICD_VENDORS lap lai o 04_1/04_2/04_3/05_1.

NGUYEN TAC BAT BUOC: GPU loi thi lui ve CPU, TUYET DOI khong lui sang sklearn.
Lui sang sklearn = doi mo hinh khac ma van bao cao la LightGBM.
"""
from __future__ import annotations

import os
import platform

import numpy as np

from .config import Cfg

_KHOA_GPU = ("device", "gpu_platform_id", "gpu_device_id", "gpu_use_dp")


def dat_env_threads(cfg: Cfg) -> None:
    """Gioi han so thread cua BLAS/OpenMP.

    PHAI goi TRUOC khi import numpy/lightgbm moi co tac dung - dat sau la vo hieu.
    Dung het 12 thread tren CPU hybrid (4 P-core + 4 E-core) lam cac thread tranh
    nhau va CHAM HON dung 6.
    """
    n = str(cfg.runtime["threads"]["n_jobs"])
    for bien in cfg.runtime["threads"]["env_vars"]:
        os.environ.setdefault(bien, n)


def dat_env_opencl(cfg: Cfg) -> str | None:
    """Tu tim thu muc ICD OpenCL tren Linux/NixOS. Windows/macOS bo qua.

    Tra ve duong dan da dat, hoac None neu khong tim thay / khong phai Linux.
    """
    if not (os.name == "posix" and platform.system() == "Linux"):
        return None
    if "OCL_ICD_VENDORS" in os.environ:
        return os.environ["OCL_ICD_VENDORS"]
    for p in cfg.runtime["gpu"]["opencl_icd_candidates"]:
        if os.path.isdir(p) and any(f.endswith(".icd") for f in os.listdir(p)):
            os.environ["OCL_ICD_VENDORS"] = p
            return p
    return None


def kiem_tra_gpu(cfg: Cfg, cho_phep_thu_nghiem: bool = False) -> tuple[bool, str]:
    """Train 1 model ti hon tren GPU de biet co dung duoc khong.

    Thu that thay vi doan - driver co the co ma van loi luc chay.

    cho_phep_thu_nghiem: chi checks/do_tinh_tai_lap_s08.py dat True, de do duoc ca to hop
    GPU + deterministic (to hop ma pipeline chuan cam). Khong dung o duong chay that.
    """
    if not cfg.runtime["gpu"]["use_gpu"]:
        return False, "use_gpu = false trong runtime.yaml"

    # Bat ca hai la mot cai bay AM THAM: LightGBM khong bao loi, chi lang le bo qua
    # deterministic (tai lieu: "Used only with cpu device type") va ket qua het tai lap
    # duoc - dung thu ma khong ai phat hien ra cho den luc chay lai thay so khac.
    if cfg.runtime["lightgbm"].get("deterministic") and not cho_phep_thu_nghiem:
        raise ValueError(
            "runtime.yaml dang bat CA HAI: gpu.use_gpu = true va lightgbm.deterministic "
            "= true. LightGBM chi ho tro deterministic tren CPU, nen cau hinh nay khong "
            "tai lap duoc du da bat deterministic. Chon MOT:\n"
            "  - can tai lap tung bit  -> gpu.use_gpu = false  (cham hon ~7 giay/model)\n"
            "  - can nhanh, chap nhan lech -> lightgbm.deterministic = false\n"
            "Xem so lieu do o ghi chu trong runtime.yaml, muc lightgbm.deterministic."
        )

    import lightgbm as lgb

    try:
        X = np.random.rand(200, 4)
        y = np.random.rand(200)
        lgb.train(
            {
                "objective": "regression",
                "device": "gpu",
                "gpu_platform_id": cfg.runtime["gpu"]["platform_id"],
                "gpu_device_id": cfg.runtime["gpu"]["device_id"],
                "verbose": -1,
            },
            lgb.Dataset(X, y),
            num_boost_round=1,
        )
        return True, ""
    except Exception as e:  # noqa: BLE001 - can bat moi loi driver
        return False, str(e)[:200]


def them_tham_so_gpu(params: dict, cfg: Cfg, gpu_san_sang: bool) -> dict:
    """Them device=gpu vao params neu GPU dung duoc.

    gpu_use_dp ep GPU cong don bang 64-bit thay vi 32-bit mac dinh - la dieu kien de
    train tren GPU tai lap duoc (xem ghi chu day du trong runtime.yaml: gpu.gpu_use_dp).
    """
    if not gpu_san_sang:
        return dict(params)
    p = dict(params)
    p.update({
        "device": "gpu",
        "gpu_platform_id": cfg.runtime["gpu"]["platform_id"],
        "gpu_device_id": cfg.runtime["gpu"]["device_id"],
        "gpu_use_dp": bool(cfg.runtime["gpu"]["gpu_use_dp"]),
    })
    return p


def fit_an_toan(params: dict, X, y, sample_weight=None, cfg: Cfg | None = None,
                eval_set=None, dung_som: int = 0):
    """Fit LightGBM; GPU loi thi tu dong lui ve CPU (KHONG doi sang sklearn).

    Tra ve (model, da_lui_ve_cpu) de stage biet ma ghi vao log/model_config.json -
    can biet model duoc train tren GPU hay CPU khi doi chieu ket qua.

    eval_set/dung_som: bat DUNG SOM giong notebook. Notebook fit mo hinh cuoi voi
    early_stopping(EARLY_STOPPING_ROUNDS), nen so cay THUC co the it hon n_estimators
    yeu cau - vi du huber h1 xin 433 cay nhung dung o 386. Khong bat dung som thi .py
    train du 433 cay va ra mo hinh khac han. De trong hai tham so nay thi fit thang
    nhu cu.
    """
    from lightgbm import LGBMRegressor, early_stopping, log_evaluation

    # SUA 2026-08-22: khai bao cot *_enc la CATEGORICAL, giong notebook
    # (cot_categorical(X) o cell 13 cua 06_1/2/3, truyen vao moi loi goi fit).
    # Thieu khai bao nay thi LightGBM coi site_id_enc / inverter_enc /
    # weather_condition_enc / weather_description_enc la SO va tach nhanh theo nguong -
    # trong khi ma tram 7 va 8 khong he co quan he lon-be. Cay sinh ra khac han
    # notebook: do duoc WAPE kiem dinh lech 0,029 diem du moi dau vao da trung khit.
    cot_cat = [c for c in X.columns if c.endswith("_enc")] if hasattr(X, "columns") else []

    def _fit(model):
        kw = {"sample_weight": sample_weight}
        if cot_cat:
            kw["categorical_feature"] = cot_cat
        if eval_set and dung_som:
            # eval_metric='l1' + eval_names: dong bo notebook 06_x fit_an_toan.
            # Khong truyen eval_metric thi LightGBM cham bang metric CUA OBJECTIVE
            # (huber / l2), con first_metric_only=True lai chi xet metric dau -> dung som
            # theo thuoc khac han notebook, ra so cay khac.
            model.fit(X, y, eval_set=eval_set,
                      eval_names=["train", "val"], eval_metric="l1",
                      callbacks=[early_stopping(dung_som, first_metric_only=True,
                                                verbose=False),
                                 log_evaluation(0)], **kw)
        else:
            model.fit(X, y, **kw)
        return model

    try:
        return _fit(LGBMRegressor(**params)), False
    except Exception as e:  # noqa: BLE001
        if params.get("device") != "gpu":
            raise
        p2 = {k: v for k, v in params.items() if k not in _KHOA_GPU}
        if cfg is not None:
            p2["n_jobs"] = cfg.runtime["threads"]["n_jobs"]
        print(f"   [CANH BAO] GPU loi (lightgbm_cpu_after_gpu_retry): {str(e)[:90]}")
        return _fit(LGBMRegressor(**p2)), True


def chuan_bi_X(df, features: list[str], medians, dtype: str = "float32"):
    """Dien median cho o thieu roi ep kieu - dung y het luc train va luc du bao.

    Lech 1 trong 3 buoc nay (thu tu cot, gia tri median, kieu du lieu) la ket qua
    du bao sai ngam ma khong bao loi.
    """
    return df[features].fillna(medians).astype(dtype)
