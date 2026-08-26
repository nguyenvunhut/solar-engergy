"""Middleware do thoi gian moi request va ghi vao nhat ky.

Gan header X-Thoi-Gian-Ms de client biet request ton bao lau ma khong phai doan.
"""
from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware

from ..core.logging import lay_logger

_log = lay_logger("bimart.http")


class DoThoiGianMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        t0 = time.perf_counter()
        res = await call_next(request)
        ms = (time.perf_counter() - t0) * 1000.0
        res.headers["X-Thoi-Gian-Ms"] = f"{ms:.1f}"
        _log.info("%s %s -> %s | %.1f ms",
                  request.method, request.url.path, res.status_code, ms)
        return res
