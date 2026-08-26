"""Kieu du lieu vao/ra cua kich ban what-if - hop dong giua HTTP va service."""
from __future__ import annotations

from pydantic import BaseModel, Field


class HangMucKetQua(BaseModel):
    ma: str = Field(description="ma hang muc: bess | ventilation | cbm")
    ten: str
    delta_kwh: float = Field(description="san luong thu hoi them, kWh tren toan pham vi")
    delta_revenue_aud: float = Field(description="doanh thu tang them, AUD")
    ty_le_tang_pt: float = Field(alias="ty_le_tang_%", description="% so voi san luong co so")
    tinh_tu_du_lieu_kwh: float = Field(description="chay cong thuc tren du lieu that, chi de doi chieu")

    model_config = {"populate_by_name": True}


class PhamVi(BaseModel):
    nam: int | None = None
    so_dong: int
    so_tram: int
    so_nam_du_lieu: int
    bieu_gia: dict


class KetQuaWhatIf(BaseModel):
    pham_vi: PhamVi
    co_so_kwh: float
    co_so_theo: str
    cong_suat_dc_kwp: int
    co_so_revenue_aud: float
    hang_muc: list[HangMucKetQua]
    tong_delta_kwh: float
    tong_delta_revenue_aud: float
    ty_le_tang_tong_pt: float = Field(alias="ty_le_tang_tong_%")

    model_config = {"populate_by_name": True}
