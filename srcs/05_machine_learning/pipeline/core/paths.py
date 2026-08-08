"""Resolve duong dan tu paths.yaml thanh duong dan tuyet doi.

Truoc day moi file .py tu viet '../../../data/model/v3/...' - chay tu thu muc khac
la sai duong dan. Gio moi duong dan deu tinh tu goc repo, chay tu dau cung dung.

An toan: co the dat paths.output_suffix = "_new" trong YAML de pipeline moi ghi ra
thu muc rieng, KHONG de len ket qua chinh thuc cua notebook.
"""
from __future__ import annotations

from pathlib import Path

from .config import REPO_ROOT, Cfg


class Paths:
    """Sinh duong dan cho tung stage. Luon tra ve Path tuyet doi."""

    def __init__(self, cfg: Cfg):
        self._cfg = cfg
        self._p = cfg.paths
        self.root = REPO_ROOT / self._p["root"]
        self.version = self._p["version"]
        self.suffix = self._p.get("output_suffix", "") or ""

    # ── Dau vao goc ──
    @property
    def mlmart_base(self) -> Path:
        return REPO_ROOT / self._p["mlmart_base"]

    @property
    def raw_solar(self) -> Path:
        """CSV raw goc - dung de xac dinh dong nao do that (energy_source)."""
        return REPO_ROOT / self._p["raw_solar"]

    @property
    def raw_cot(self) -> dict:
        """Ten cot trong CSV raw (khac ten trong mart nen phai doi ten khi merge)."""
        return dict(self._p["raw_cot"])

    # ── Thu muc cua tung stage ──
    def stage(self, ten_stage: str) -> Path:
        """Vd stage('s08_train') -> <repo>/data/model/v3/06_train<suffix>"""
        cac_stage = self._p["stages"]
        if ten_stage not in cac_stage:
            raise KeyError(
                f"Stage '{ten_stage}' khong co trong paths.yaml. "
                f"Cac stage: {sorted(cac_stage)}"
            )
        tuong_doi = cac_stage[ten_stage]
        # Stage s01 tro thang toi 1 file .parquet, khong phai thu muc
        if tuong_doi.endswith(".parquet"):
            duong_dan = Path(tuong_doi)
            return self.root / f"{duong_dan.parent}{self.suffix}" / duong_dan.name
        return self.root / f"{tuong_doi}{self.suffix}"

    def stage_goc(self, ten_stage: str) -> Path:
        """Duong dan KHONG co suffix - dung de doi chieu voi ket qua notebook."""
        tuong_doi = self._p["stages"][ten_stage]
        return self.root / tuong_doi

    def stage_doc(self, ten_stage: str) -> Path:
        """Duong dan de DOC dau vao. Khac stage() la duong dan de GHI.

        Uu tien ban co suffix (do stage truoc cua chinh pipeline nay sinh ra); chua co
        thi doc ban goc cua notebook. Nho vay chay rieng 1 stage giua chung van co dau
        vao, ma van KHONG BAO GIO ghi de len ket qua goc (ghi luon di qua stage()).
        """
        moi = self.stage(ten_stage)
        return moi if moi.exists() else self.stage_goc(ten_stage)

    # ── File trong thu muc ──
    def file(self, ten_file: str, **kwargs) -> str:
        """Vd file('x_test', h=4) -> 'X_test_h4.parquet'"""
        mau = self._p["files"][ten_file]
        return mau.format(version=self.version, **kwargs)

    def selected(self, ten_file: str, **kwargs) -> Path:
        """File trong 05_selected - luon la DAU VAO cua s08 nen dung stage_doc()."""
        return self.stage_doc("s07_selected") / self.file(ten_file, **kwargs)

    def fold(self, n: int, vai_tro: str) -> Path:
        """vai_tro: 'train' hoac 'val'. Cung la dau vao -> stage_doc()."""
        if vai_tro not in ("train", "val"):
            raise ValueError(f"vai_tro phai la 'train' hoac 'val', nhan duoc '{vai_tro}'")
        return self.stage_doc("s07_selected") / self.file(f"fold_{vai_tro}", n=n)

    def model_dir(self, ten_loss: str, horizon: int) -> Path:
        """Vd model_dir('huber', 4) -> <repo>/data/model/v3/06_train/huber/h4"""
        return self.stage("s08_train") / ten_loss / f"h{horizon}"

    def horizon_dir(self, ten_stage: str, horizon: int) -> Path:
        return self.stage(ten_stage) / f"h{horizon}"

    # ── Action (khong thuoc pipeline chuan) ──
    def action(self, ten: str) -> Path:
        tuong_doi = self._p["actions"][ten]
        # best_params nam trong config/, khong nam trong data/model
        if tuong_doi.startswith("config/"):
            return REPO_ROOT / tuong_doi
        return self.root / tuong_doi

    def tao_thu_muc(self, *duong_dan: Path) -> None:
        """Tao thu muc neu chua co. Goi truoc khi ghi file."""
        for d in duong_dan:
            d.mkdir(parents=True, exist_ok=True)
