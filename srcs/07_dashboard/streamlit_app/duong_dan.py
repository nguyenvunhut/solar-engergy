"""Dat sys.path cho ung dung. Import module nay truoc cac import noi bo khac."""
from __future__ import annotations

from pathlib import Path
import sys

GOC = Path(__file__).resolve().parent
DASHBOARD = GOC.parent

for _p in (GOC, DASHBOARD):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
