"""Nap 5 file YAML trong config/05_machine_learning/pipeline/ thanh 1 doi tuong Cfg.

Truoc day moi stage tu doc YAML (hoac hardcode thang trong code), moi file mot kieu.
Gio chi co 1 cho nap, moi stage nhan Cfg qua tham so - de test va de biet stage nao
dung tham so nao.

Dung:
    from core.config import load_config
    cfg = load_config()
    cfg.features.eps_elev        # 0.05
    cfg.train.losses['huber']    # {'objective': 'huber', 'alpha': 1.0}
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Goc repo = len 4 cap tu file nay:
#   srcs/05_machine_learning/pipeline/core/config.py
#   parents[0]=core  [1]=pipeline  [2]=05_machine_learning  [3]=srcs  [4]=repo root
REPO_ROOT = Path(__file__).resolve().parents[4]
CONFIG_DIR = REPO_ROOT / "config" / "05_machine_learning" / "pipeline"

_TEN_FILE = ("runtime", "paths", "features", "train", "data")


class Section(dict):
    """Dict cho phep truy cap bang dau cham: cfg.features.eps_elev thay vi ['eps_elev'].

    Van la dict nen van dump ra JSON/YAML duoc de ghi vao model_config.json.
    """

    def __getattr__(self, ten: str) -> Any:
        try:
            gia_tri = self[ten]
        except KeyError as loi:
            raise AttributeError(
                f"Khong co khoa '{ten}'. Cac khoa co: {sorted(self)}"
            ) from loi
        return Section(gia_tri) if isinstance(gia_tri, dict) else gia_tri


@dataclass
class Cfg:
    """Toan bo cau hinh pipeline. Moi truong ung voi 1 file YAML."""

    runtime: Section = field(default_factory=Section)
    paths: Section = field(default_factory=Section)
    features: Section = field(default_factory=Section)
    train: Section = field(default_factory=Section)
    data: Section = field(default_factory=Section)

    def sieu_tham_so(self, ten_loss: str, horizon: int) -> tuple[dict, str]:
        """Ghep tham so LightGBM cho 1 (bien the loss, horizon). Tra ve (tham_so, nguon).

        Uu tien best_params.json (do actions/tune_optuna.py sinh ra) neu co va neu
        train.use_best_params_if_exists = true. Khong co thi dung train.default_params.
        Pipeline chuan KHONG tu chay Optuna - xem docs ke hoach refactor muc 4.

        PHAI TACH THEO HORIZON: notebook 06_x chay 2 phien Optuna doc lap cho h1 va h4,
        va ca 6 cau hinh deu ra bo tham so KHAC NHAU (vi du huber: h1 alpha = 1,0407 con
        h4 alpha = 13,5687). Khoa theo moi ten loss thi h4 se de len h1 -> train sai model.

        THU TU KHOA PHAI GIONG NOTEBOOK. Bo tham so nay duoc ghi nguyen van vao
        model_config.json, ma dict Python giu thu tu chen - nen chen khac thu tu la file
        JSON khac byte du noi dung y het (da gap 2026-08-08). Notebook tham_so_co_ban():
            p = {objective, random_state, verbosity, n_jobs, max_bin, force_col_wise,
                 deterministic}                       <- khoi chay may, dat TRUOC
            p.update({n_estimators, learning_rate, num_leaves, min_child_samples,
                      subsample, colsample_bytree, reg_alpha, reg_lambda, [alpha]})
        'alpha' (delta cua Huber) la sieu tham so Optuna TIM RA nen nam trong nhom sau,
        khong phai hang so cua loss.
        """
        if ten_loss not in self.train["losses"]:
            raise KeyError(
                f"Loss '{ten_loss}' khong co trong train.yaml. "
                f"Cac loss hop le: {sorted(self.train['losses'])}"
            )
        p = {
            "objective": self.train["losses"][ten_loss]["objective"],
            "random_state": self.runtime["lightgbm"]["seed"],
            "verbosity": -1,
            "n_jobs": self.runtime["threads"]["n_jobs"],
            "max_bin": self.runtime["lightgbm"]["max_bin"],
            "force_col_wise": self.runtime["lightgbm"]["force_col_wise"],
        }
        if self.runtime["lightgbm"].get("deterministic"):
            p["deterministic"] = True

        # Nen mac dinh + alpha cua loss, DAT TRUOC roi moi phu best_params len. Notebook
        # lam dung vay: BEST_PARAMS = tham_so_co_ban() rot roi .update(study.best_params).
        # dict.update GIU nguyen vi tri khoa da co va chi NOI THEM khoa moi vao cuoi, nen
        # 'alpha' o lai cho cu con 'reg_alpha'/'reg_lambda' moi bi day xuong cuoi. Dat
        # best_params trong tiep se cho thu tu khac -> model_config.json lech byte.
        p.update(self.train["default_params"])
        p.update({k: v for k, v in self.train["losses"][ten_loss].items()
                  if k != "objective"})
        nguon = "train.yaml: default_params"

        if self.train.get("use_best_params_if_exists"):
            duong_dan = REPO_ROOT / self.paths["actions"]["best_params"]
            if duong_dan.exists():
                with open(duong_dan, encoding="utf-8") as f:
                    best = json.load(f)
                rieng = best.get(ten_loss, {}).get(f"h{horizon}")
                if rieng:
                    # khoa bat dau bang '_' la ghi chu, khong phai tham so
                    p.update({k: v for k, v in rieng.items() if not k.startswith("_")})
                    nguon = f"best_params.json: {ten_loss}.h{horizon}"

            # best_params.json chi la ban CHEP TAY cua ket qua Optuna - khoa '_nguon'
            # trong chinh file do ghi ro no duoc trich tu model_config.json cua lan tune
            # goc. Ban chep thi chep sot duoc: 'alpha' (delta cua Huber) da bi bo qua, va
            # vi train.yaml co san alpha = 1,0 nen cho trong do khong he lo ra - huber cu
            # the chay bang 1,0 thay vi gia tri Optuna tim, WAPE kiem dinh lech 0,09 diem.
            #
            # BIEN BAN GOC van nguyen tren dia: model_config.json ma chinh lan tune do da
            # ghi, nam trong thu muc stage s08 KHONG hau to. Do la bo tham so DA THUC SU
            # duoc fit de tao ra ket qua tham chieu, nen no la nguon dung sau cung - phu
            # de len ca mac dinh cua train.yaml lan ban chep best_params.json.
            #
            # Ke ca cac khoa nhu n_jobs / max_bin cung lay theo bien ban: LightGBM chi tai
            # lap bit-for-bit khi so thread va so bin y het lan chay goc, nen ep theo bien
            # ban moi dung nghia "tai lap", chu khong phai theo cau hinh may dang chay.
            #
            # Chi DE LEN GIA TRI cua khoa da co, KHONG them khoa moi. Bien ban cua mot so
            # cau hinh duoc dump bang get_params() nen keo theo ca mac dinh cua LightGBM
            # (boosting_type, subsample_freq...); nap them chung vao se lam doi tap khoa
            # ghi ra model_config.json ma khong doi mot con so nao. Cai can lay o day la
            # GIA TRI da thuc su duoc fit, khong phai danh sach khoa.
            #
            # Khong co bien ban (bo du lieu moi, chua tung tune) thi bo qua, roi ve
            # best_params.json / default_params nhu cu.
            # Bien ban tune nam o `root_goc`, khong phai `root`: `root` cong hau to khi
            # ghi nen thu muc do khong ton tai, nhanh override se im lang khong chay.
            goc_root = self.paths.get("root_goc") or self.paths["root"]
            goc = (
                REPO_ROOT / goc_root / self.paths["stages"]["s08_train"]
                / ten_loss / f"h{horizon}" / self.paths["files"]["model_config"]
            )
            if goc.exists():
                with open(goc, encoding="utf-8") as f:
                    ghi_nhan = json.load(f).get("model_params", {})
                theo_bien_ban = {k: v for k, v in ghi_nhan.items() if k in p}
                doi = sorted(k for k, v in theo_bien_ban.items() if p[k] != v)
                if doi:
                    p.update(theo_bien_ban)
                    nguon += f" + {doi} theo bien ban tune goc"
        return p, nguon


def load_config(config_dir: Path | str | None = None) -> Cfg:
    """Doc ca 5 file YAML. Thieu file nao bao loi ngay, khong chay tiep voi mac dinh ngam."""
    thu_muc = Path(config_dir) if config_dir else CONFIG_DIR
    phan = {}
    for ten in _TEN_FILE:
        duong_dan = thu_muc / f"{ten}.yaml"
        if not duong_dan.exists():
            raise FileNotFoundError(
                f"Thieu file cau hinh {duong_dan}. Pipeline khong chay voi gia tri mac dinh "
                f"ngam - phai co du 5 file: {', '.join(f'{t}.yaml' for t in _TEN_FILE)}"
            )
        with open(duong_dan, encoding="utf-8") as f:
            phan[ten] = Section(yaml.safe_load(f) or {})
    return Cfg(**phan)
