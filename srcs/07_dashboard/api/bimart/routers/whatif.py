"""Tang CONTROLLER - chi lo HTTP. Moi tinh toan nam o services/."""
from __future__ import annotations

from fastapi import APIRouter, Query

from ..repositories import bimart_repo as repo
from ..services.whatif import HANG_MUC, chay_kich_ban

router = APIRouter()


@router.get("/hang-muc", summary="Danh sach hang muc cai tien co cong thuc")
def danh_sach_hang_muc():
    return [{"ma": m, "ten": t} for m, (t, _) in HANG_MUC.items()]


@router.get("/pham-vi", summary="Pham vi bo du lieu nen")
def pham_vi():
    return repo.tom_tat_pham_vi()


@router.get("/kich-ban", summary="Chay kich ban what-if")
def kich_ban(
    bat: list[str] | None = Query(None, description="ma hang muc duoc tich; bo trong = tat ca"),
    nam: int | None = Query(None, ge=2020, le=2022, description="dung bieu gia nam nay"),
):
    return chay_kich_ban(bat=bat, nam=nam)
