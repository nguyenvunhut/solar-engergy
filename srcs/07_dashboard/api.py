"""FastAPI phuc vu dashboard va cac he thong ngoai.

    uvicorn api:app --port 8000 --app-dir srcs/07_dashboard
    # tai lieu tu sinh: http://127.0.0.1:8000/docs

HAI NHOM ENDPOINT
-----------------
1. DOC ARTIFACT (/metrics, /predictions, /baseline, /shap): tra lai ket qua pipeline
   da tinh san. Nhanh, khong tinh toan gi.
2. DU BAO TRUC TIEP (/forecast): keo thoi tiet Open-Meteo roi chay mo hinh de quy cho
   chan troi dai. Cham hon (vai giay den vai chuc giay) vi phai goi mang va chay
   1.344 buoc cho 14 ngay.

Toan bo logic du bao nam o forecast_service.py — API chi lo tang HTTP. Nho vay
Streamlit va API dung chung mot duong tinh, khong the lech ket qua.
"""
from __future__ import annotations

import ctypes
import glob
import json
from pathlib import Path

# Nap truoc runtime C++ cho LightGBM tren Linux/NixOS. Tren Windows/macOS glob rong
# nen doan nay khong lam gi.
for _p in (
    glob.glob("/nix/store/*gcc*/lib/libstdc++.so.6")
    + glob.glob("/usr/lib*/libstdc++.so.6")
    + glob.glob("/run/current-system/sw/lib/libstdc++.so.6")
):
    try:
        ctypes.CDLL(_p, mode=ctypes.RTLD_GLOBAL)
        break
    except Exception:
        pass

import pandas as pd
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(
    title="Energy Forecasting API — The Outliers",
    description="Dự báo sản lượng điện mặt trời 15 phút cho 42 trạm quang điện.",
    version="3.0.0",
)

GOC_REPO = Path(__file__).resolve().parents[2]
DATA_DIR = GOC_REPO / "data" / "model" / "v3"
FINAL_DIR = DATA_DIR / "07_final_test"
PROPHET_DIR = DATA_DIR / "08_baseline_prophet_test"

KHO: dict = {}


def _ban_ghi(df: pd.DataFrame) -> list[dict]:
    """DataFrame -> list[dict] an toan cho JSON.

    NaN/NaT khong hop le trong JSON chuan (gay 'Out of range float values are not
    JSON compliant'), phai doi thanh None truoc khi tra ve.
    """
    return df.astype(object).where(pd.notnull(df), None).to_dict(orient="records")


@app.on_event("startup")
def khoi_dong() -> None:
    """Nap san artifact vao bo nho. Model du bao nap tre — chi khi co request /forecast."""
    for h in ("h1", "h4"):
        p = FINAL_DIR / h / "metrics_overall.json"
        if p.exists():
            KHO[f"metrics_overall_{h}"] = json.loads(p.read_text(encoding="utf-8"))
        p = FINAL_DIR / h / "metrics_by_site.csv"
        if p.exists():
            KHO[f"metrics_by_site_{h}"] = pd.read_csv(p)

    p = FINAL_DIR / "best_loss.json"
    if p.exists():
        KHO["best_loss"] = json.loads(p.read_text(encoding="utf-8"))

    p = FINAL_DIR / "prediction_audit.parquet"
    if p.exists():
        d = pd.read_parquet(p)
        d["timestamp"] = pd.to_datetime(d["timestamp"])
        KHO["predictions"] = d
        KHO["sites"] = sorted(d["site_id"].astype(int).unique().tolist())

    # Doi chung Prophet — do tren DUNG tap dong cua mo hinh (xem 08_baseline_prophet_test).
    p = PROPHET_DIR / "prophet_test_summary.json"
    if p.exists():
        KHO["prophet_summary"] = json.loads(p.read_text(encoding="utf-8"))
    p = PROPHET_DIR / "prophet_test_by_site.csv"
    if p.exists():
        KHO["prophet_by_site"] = pd.read_csv(p)

    for ten, p in (("shap_importance", DATA_DIR / "08_explain" / "shap_importance.csv"),
                   ("shap_values", DATA_DIR / "08_explain" / "shap_values.parquet")):
        if p.exists():
            KHO[ten] = pd.read_csv(p) if p.suffix == ".csv" else pd.read_parquet(p)


def _sach_json(x):
    """Doi NaN/Inf thanh None de tra ve duoc JSON hop le.

    metrics_overall.json do pipeline ghi co chua NaN (vi du baseline_persistence_wape
    khi khong tinh baseline). NaN/Infinity KHONG hop le trong JSON chuan — tra thang
    ra thi client bao 'Expecting value: line 1 column 1'.
    """
    import math

    if isinstance(x, dict):
        return {k: _sach_json(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_sach_json(v) for v in x]
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x


def _lay(khoa: str, goi_y: str):
    if khoa not in KHO:
        raise HTTPException(404, f"Chưa có dữ liệu '{khoa}'. {goi_y}")
    return KHO[khoa]


# ══════════════════════════════════════════════════════════════════════════════
#  Thong tin chung
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/", tags=["Thông tin"])
def goc():
    return {
        "trang_thai": "online",
        "mo_ta": "Energy Forecasting API — nhóm The Outliers",
        "tai_lieu": "/docs",
        "doc_artifact": ["/sites", "/metrics/overall", "/metrics/by_site",
                         "/predictions", "/baseline/prophet", "/shap/importance"],
        "du_bao_truc_tiep": ["/forecast", "/forecast/what-if"],
    }


@app.get("/sites", tags=["Thông tin"])
def danh_sach_tram():
    return {"sites": _lay("sites", "Chạy stage s09 trước.")}


@app.get("/model/info", tags=["Thông tin"])
def thong_tin_mo_hinh():
    """Mô hình nào đang phục vụ, và nó được chọn trên tập nào."""
    bl = _lay("best_loss", "Chạy stage s09 trước.")
    return {
        h: {
            "hàm_mất_mát": v.get("winning_loss"),
            "wape_validation_%": v.get("val_wape"),
            "ghi_chú": "Mô hình được chọn trên tập VALIDATION; tập test không tham "
                       "gia vào quyết định này.",
        }
        for h, v in bl.items()
    }


# ══════════════════════════════════════════════════════════════════════════════
#  Doc artifact
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/metrics/overall", tags=["Chỉ số"])
def chi_so_tong(horizon: str = Query("h1", pattern="^h[14]$")):
    return _sach_json(_lay(f"metrics_overall_{horizon}", "Chạy stage s09 trước."))


@app.get("/metrics/by_site", tags=["Chỉ số"])
def chi_so_theo_tram(horizon: str = Query("h1", pattern="^h[14]$")):
    return _ban_ghi(_lay(f"metrics_by_site_{horizon}", "Chạy stage s09 trước."))


@app.get("/baseline/prophet", tags=["Chỉ số"])
def doi_chung_prophet():
    """Skill Score so với Prophet — hai mô hình chấm trên cùng một tập dòng."""
    return _lay("prophet_summary",
                "Chạy actions/baseline_prophet_test_set.py trước.")


@app.get("/predictions", tags=["Dự báo"])
def du_bao_da_luu(
    site_id: int | None = None,
    start: str | None = None,
    end: str | None = None,
    limit: int = Query(2000, le=500_000),
):
    """Kết quả mô hình trên tập test niêm phong (đã tính sẵn, không chạy lại)."""
    d = _lay("predictions", "Chạy stage s09 trước.")
    if site_id is not None:
        d = d[d["site_id"].astype(int) == site_id]
    if start:
        d = d[d["timestamp"] >= pd.to_datetime(start)]
    if end:
        d = d[d["timestamp"] <= pd.to_datetime(end)]
    ra = d.head(limit).copy()
    for c in ra.columns:
        if pd.api.types.is_datetime64_any_dtype(ra[c]):
            ra[c] = ra[c].dt.strftime("%Y-%m-%d %H:%M:%S")
    return _ban_ghi(ra)


@app.get("/shap/importance", tags=["Giải thích"])
def shap_quan_trong():
    return _ban_ghi(_lay("shap_importance", "Chạy stage s10 trước."))


# ══════════════════════════════════════════════════════════════════════════════
#  Du bao truc tiep
# ══════════════════════════════════════════════════════════════════════════════
def _dich_vu():
    from forecast_service import lay_dich_vu  # noqa: PLC0415 — nap tre, tranh cham khoi dong

    return lay_dich_vu()


@app.get("/forecast", tags=["Dự báo"])
def du_bao_toi(
    site_id: int = Query(..., description="Mã trạm 1–42"),
    so_ngay: int = Query(14, ge=1, le=16, description="Số ngày dự báo tới"),
    gop_theo_ngay: bool = Query(False, description="Trả về tổng theo ngày thay vì từng bước 15 phút"),
):
    """Dự báo sản lượng cho `so_ngay` ngày tới, dùng thời tiết Open-Meteo.

    Mô hình chỉ dự báo 1 bước (15 phút), nên chân trời dài được thực hiện bằng **đệ quy**:
    giá trị vừa dự báo trở thành đầu vào lag/rolling cho bước kế tiếp. Sai số vì thế
    tích lũy dần — dự báo càng xa càng kém tin cậy. Chỉ số WAPE công bố đo năng lực
    **một bước**, không phải độ chính xác của chân trời 14 ngày.
    """
    try:
        d = _dich_vu().du_bao(site_id=site_id, so_ngay=so_ngay)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(502, f"Không dự báo được: {type(e).__name__}: {e}") from e

    if gop_theo_ngay:
        g = (d.assign(ngay=d["plot_timestamp"].dt.date)
             .groupby("ngay")
             .agg(tong_kwh=("y_pred_kwh", "sum"),
                  dinh_kwh=("y_pred_kwh", "max"),
                  so_buoc=("y_pred_kwh", "size"))
             .reset_index())
        g["ngay"] = g["ngay"].astype(str)
        return {"site_id": site_id, "so_ngay": so_ngay, "theo_ngay": _ban_ghi(g)}

    ra = d.copy()
    for c in ("timestamp", "plot_timestamp"):
        ra[c] = ra[c].dt.strftime("%Y-%m-%d %H:%M:%S")
    return {"site_id": site_id, "so_ngay": so_ngay, "so_buoc": len(ra),
            "du_bao": _ban_ghi(ra)}


@app.get("/forecast/what-if", tags=["Dự báo"])
def du_bao_what_if(
    site_id: int = Query(..., description="Mã trạm 1–42"),
    so_ngay: int = Query(7, ge=1, le=16),
    buc_xa: float = Query(1.0, ge=0.0, le=3.0, description="Hệ số nhân bức xạ sóng ngắn"),
    nhiet_do: float = Query(1.0, ge=0.0, le=3.0, description="Hệ số nhân nhiệt độ"),
    may: float = Query(1.0, ge=0.0, le=3.0, description="Hệ số nhân độ mây"),
):
    # KHONG co tham so 'gio': wind_speed khong nam trong 54 dac trung cua mo hinh, nen
    # moi he so nhan len no deu tra ve dung 0,00% thay doi (da do). Bay mot thanh truot
    # khong lam gi la danh lua nguoi dung — bo han thay vi de do roi ghi chu.
    """So sánh kịch bản thời tiết thay đổi với kịch bản gốc.

    Mỗi hệ số nhân được áp lên biến thời tiết tương ứng **trước khi** dựng đặc trưng,
    nên các đặc trưng dẫn xuất (`temp_x_shortwave`, `cloud_x_shortwave`, chỉ số trời
    quang...) cũng thay đổi theo — đúng cách một thay đổi thời tiết thật lan trong mô hình.

    **Chạy ở chế độ một bước, không đệ quy.** Bốn trong mười đặc trưng quan trọng nhất là
    `lag_4` và `rolling_*_4` — sản lượng gần đây. Trong chế độ đệ quy chúng lấy từ chính
    đầu ra của mô hình, tạo vòng tự neo làm tắt tín hiệu thời tiết: đo thực tế trên trạm 1,
    bức xạ +20% cho **+7,33%** ở chế độ một bước nhưng chỉ **+0,47%** khi đệ quy 7 ngày,
    có ngày còn đổi dấu. Dùng số đệ quy cho What-if sẽ ra biểu đồ gần như phẳng và người
    đọc kết luận sai rằng mô hình không quan tâm thời tiết.

    **Giới hạn:** đây là phân tích độ nhạy của mô hình, không phải dự báo thời tiết.
    Nhân bức xạ lên 1,5 lần không có nghĩa trời sẽ nắng gấp rưỡi; nó trả lời câu hỏi
    "nếu bức xạ cao hơn 50% thì mô hình dự báo ra sao".
    """
    dv = _dich_vu()
    dieu_chinh = {
        "shortwave_radiation": buc_xa,
        "direct_normal_irradiance": buc_xa,
        "diffuse_solar_radiation": buc_xa,
        "temperature_c": nhiet_do,
        "cloud_cover_total": may,
        "cloud_cover_low": may,
    }
    try:
        goc = dv.du_bao_mot_buoc(site_id=site_id, so_ngay=so_ngay)
        kich_ban = dv.du_bao_mot_buoc(site_id=site_id, so_ngay=so_ngay, dieu_chinh=dieu_chinh)
    except Exception as e:
        raise HTTPException(502, f"Không dự báo được: {type(e).__name__}: {e}") from e

    t_goc = float(goc["y_pred_kwh"].sum())
    t_kb = float(kich_ban["y_pred_kwh"].sum())
    return {
        "site_id": site_id,
        "so_ngay": so_ngay,
        "che_do": "một bước (không đệ quy) — đo độ nhạy thật của mô hình với thời tiết",
        "he_so_ap_dung": {k: v for k, v in
                          {"bức_xạ": buc_xa, "nhiệt_độ": nhiet_do,
                           "mây": may}.items() if v != 1.0},
        "tong_kwh_goc": round(t_goc, 3),
        "tong_kwh_kich_ban": round(t_kb, 3),
        "thay_doi_kwh": round(t_kb - t_goc, 3),
        "thay_doi_%": round((t_kb - t_goc) / t_goc * 100, 3) if t_goc else None,
    }
