"""Doi tuong mang trang thai giua cac stage - THAY THE cho globals().update(locals()).

Ban cu (srcs/05_machine_learning/forcasting_ml/04_x_train_*.py) truyen bien giua 6 stage
bang cach nhet locals() vao globals() o cuoi moi ham:

    def preprocessing():
        ...
        globals().update(locals())     # <-- FEATURES, dev_h, test_h... roi vao globals

    def train_fold():
        ...                            # doc FEATURES tu globals, khong ai biet tu dau ra

Hau qua: 6 stage dinh chat vao nhau, bat buoc goi dung thu tu, khong tach file duoc,
khong test rieng tung stage duoc, va doc code khong biet bien den tu dau.

Gio moi stage nhan Ctx vao va tra Ctx ra - nhin chu ky ham la biet stage can gi.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from .config import Cfg
from .paths import Paths


@dataclass
class Ctx:
    """Trang thai chay cua 1 lan train (1 loss x 1 horizon)."""

    cfg: Cfg
    paths: Paths
    loss_name: str
    horizon_steps: int

    # ── Du lieu (stage s08a dien vao) ──
    dev_h: pd.DataFrame | None = None       # development da them muc tieu
    test_h: pd.DataFrame | None = None      # test da them muc tieu
    features: list[str] = field(default_factory=list)
    medians: pd.Series | None = None
    X_dev: pd.DataFrame | None = None
    y_dev: pd.Series | None = None
    w_dev: pd.Series | None = None

    # ── Fold CV (stage s08b dien vao, chi khi can tune) ──
    cac_fold: list[dict] = field(default_factory=list)

    # ── Ket qua train (stage s08c dien vao) ──
    model: Any = None
    best_params: dict = field(default_factory=dict)
    gpu_san_sang: bool = False
    da_lui_ve_cpu: bool = False

    # ── Ket qua danh gia (stage s08c dien vao, s08d ghi ra file) ──
    metrics_test: dict = field(default_factory=dict)
    metrics_val: dict = field(default_factory=dict)
    quet_tre: dict = field(default_factory=dict)
    df_tre_theo_site: pd.DataFrame | None = None
    bo_di: list[str] = field(default_factory=list)

    @property
    def h_label(self) -> str:
        return f"h{self.horizon_steps}"

    @property
    def thu_muc_ra(self):
        """Thu muc ghi artifact: <root>/06_train<suffix>/<loss>/h<n>"""
        return self.paths.model_dir(self.loss_name, self.horizon_steps)

    def bat_buoc_co(self, *ten_truong: str) -> None:
        """Bao loi ro rang neu stage truoc chua chay.

        Thay cho loi NameError/KeyError mo ho cua ban cu khi goi sai thu tu stage.
        """
        thieu = [t for t in ten_truong if getattr(self, t) is None]
        if thieu:
            raise RuntimeError(
                f"Ctx thieu {thieu} - stage truoc chua chay xong. "
                f"Thu tu bat buoc: s08a_prepare -> s08b_train_folds -> "
                f"s08c_train_final -> s08d_export"
            )
