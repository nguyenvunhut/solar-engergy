"""Cau hinh nhat ky cho service BI Mart."""
from __future__ import annotations

import logging
import sys

_DA_DAT = False


def lay_logger(ten: str = "bimart") -> logging.Logger:
    global _DA_DAT
    if not _DA_DAT:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                                         datefmt="%H:%M:%S"))
        root = logging.getLogger("bimart")
        root.handlers.clear()
        root.addHandler(h)
        root.setLevel(logging.INFO)
        _DA_DAT = True
    return logging.getLogger(ten)
