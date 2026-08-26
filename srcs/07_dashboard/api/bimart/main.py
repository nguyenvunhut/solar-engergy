"""FastAPI cho nhanh BI Mart - trang mo phong what-if.

    uvicorn bimart.api.main:app --port 8100 --app-dir srcs/07_dashboard
    tai lieu tu sinh: http://127.0.0.1:8100/docs

DUNG `lifespan`, KHONG dung @app.on_event("startup") - FastAPI da bo tu 0.93.
Du lieu nap MOT LAN luc khoi dong, moi request sau do tinh tren RAM.
"""
from __future__ import annotations

import ctypes
import glob

# Nap truoc runtime C++ TRUOC KHI import bat cu thu gi keo theo numpy/pandas.
# Tren NixOS khong co /usr/lib nen numpy bao "libstdc++.so.6: cannot open shared
# object file" ngay o buoc import. Chep dung cach api.py da lam - tren Windows/macOS
# cac glob duoi day RONG nen doan nay khong lam gi, khong anh huong may cua nhom.
for _p in (
    glob.glob("/nix/store/*gcc*/lib/libstdc++.so.6")
    + glob.glob("/usr/lib*/libstdc++.so.6")
    + glob.glob("/run/current-system/sw/lib/libstdc++.so.6")
):
    try:
        ctypes.CDLL(_p, mode=ctypes.RTLD_GLOBAL)
        break
    except OSError:
        pass

from contextlib import asynccontextmanager  # noqa: E402

from fastapi import FastAPI  # noqa: E402

from .core.logging import lay_logger  # noqa: E402
from .middleware.timing import DoThoiGianMiddleware  # noqa: E402
from .repositories import bimart_repo as repo  # noqa: E402
from .routers.whatif import router as router_whatif  # noqa: E402

_log = lay_logger("bimart.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    h, d = repo.doc_hourly(), repo.doc_daily()
    _log.info("Nap xong: hourly %s dong · daily %s dong · %s tram",
              f"{len(h):,}", f"{len(d):,}", h["site_id"].nunique())
    yield
    repo.doc_hourly.cache_clear()
    repo.doc_daily.cache_clear()
    _log.info("Da giai phong bo nho.")


app = FastAPI(
    title="BI Mart — What-If Optimization API",
    description="Mo phong 3 hang muc cai tien tren du lieu do hat GIO cua bi_mart.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(DoThoiGianMiddleware)
app.include_router(router_whatif, prefix="/bimart", tags=["BI Mart What-If"])


@app.get("/", tags=["Thong tin"])
def goc():
    return {"ten": "BI Mart What-If API", "tai_lieu": "/docs", "tien_to": "/bimart"}
