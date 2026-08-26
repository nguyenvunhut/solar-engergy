"""Diem chay DUY NHAT cua toan bo API dashboard.

    uvicorn api.main:app --port 8000 --app-dir srcs/07_dashboard
    Tai lieu tu sinh: http://127.0.0.1:8000/docs

Hai nhom endpoint:
    /ml/...      du bao san luong 15 phut, doc artifact mo hinh
    /bimart/...  mo phong What-If tren du lieu do hat gio cua bi_mart

Nghiep vu nam trong api/ml/ va api/bimart/services — tep nay chi lo tang HTTP.
"""
from __future__ import annotations

import ctypes
import glob

# Nap truoc runtime C++ TRUOC KHI import bat cu thu gi keo theo numpy/pandas.
# Tren Windows/macOS cac glob duoi day rong nen doan nay khong lam gi.
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

from .bimart.core.logging import lay_logger  # noqa: E402
from .bimart.middleware.timing import DoThoiGianMiddleware  # noqa: E402
from .bimart.repositories import bimart_repo  # noqa: E402
from .bimart.routers.whatif import router as router_bimart  # noqa: E402

_log = lay_logger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    h = bimart_repo.doc_hourly()
    d = bimart_repo.doc_daily()
    _log.info("BI Mart: hourly %s dong · daily %s dong · %s tram",
              f"{len(h):,}", f"{len(d):,}", h["site_id"].nunique())
    yield
    bimart_repo.doc_hourly.cache_clear()
    bimart_repo.doc_daily.cache_clear()


app = FastAPI(
    title="Solar Analytics API — The Outliers",
    description="Du bao san luong dien mat troi va mo phong What-If toi uu hoa "
                "cho 42 tram ap mai Dai hoc La Trobe.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(DoThoiGianMiddleware)
app.include_router(router_bimart, prefix="/bimart", tags=["BI Mart — What-If"])


@app.get("/", tags=["Thong tin"])
def goc():
    return {"ten": "Solar Analytics API", "tai_lieu": "/docs",
            "nhom_endpoint": ["/bimart", "/ml"]}
