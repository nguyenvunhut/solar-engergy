"""Stage 09a: chon mo hinh vo dich cho tung horizon.

Tach tu phan dau run_final_test() cua 05_1_final_test.py.

QUY TAC BAT BUOC - day la diem tung xay ra loi ro ri nghiem trong:
  Chi duoc doc metrics_val.json (so lieu tren tap VALIDATION). TUYET DOI khong duoc
  doc metrics_test.json de chon mo hinh - lam vay thi tap test khong con "niem phong",
  vi no da tham gia vao 1 quyet dinh mo hinh.

  Loi that (2026-08-06): metrics_val.json truoc day bi ghi tu so lieu TEST, khien viec
  chon MAE/Huber/MSE that ra da nhin truoc tap test. Sau khi sua, mo hinh vo dich doi
  tu MAE sang HUBER. Ham _doc_metrics_val() duoi day tu chan file test de loi khong
  tai dien du ai do vo tinh doi ten file.
"""

from __future__ import annotations

import pandas as pd
from core.config import Cfg
from core.io import read_json
from core.metrics import PHAM_VI_CHINH_THUC
from core.paths import Paths


# Nhan mo ta bo dac trung - copy nguyen van tu notebook 07 (bien FEATURE_SET_LABEL).
# Doi chu nao o day la best_loss.json lech byte so voi notebook.
NHAN_BO_DAC_TRUNG = "chuan (lag_96, khong lag_1/lag_4)"

# Thu tu duyet loss - copy tu notebook 07 (loss_list). KHONG sap theo chu cai: thu tu nay
# quyet dinh thu tu phan tu trong mang 'comparison' cua best_loss.json.
THU_TU_LOSS = ("mse", "mae", "huber")

# Khoa chi dung noi bo pipeline, phai loai truoc khi ghi best_loss.json vi notebook
# khong co khoa nay - de lai la file lech byte.
KHOA_NOI_BO = ("thu_muc_model",)


def _doc_metrics_val(thu_muc, h_label: str) -> dict | None:
    """Doc metrics_val.json cua 1 model. Tra ve None neu chua train."""
    duong_dan = thu_muc / "metrics_val.json"
    if not duong_dan.exists():
        return None
    d = read_json(duong_dan)
    if h_label in d:  # tuong thich dinh dang cu (long theo horizon)
        d = d[h_label]
    return d


def bang_so_sanh(cfg: Cfg, paths: Paths, horizon: int) -> pd.DataFrame:
    """Bang doi chieu moi loss tren tap validation, cho 1 horizon.

    TEN COT va THU TU LOSS bam theo notebook 07 (bien loss_list = ['mse','mae','huber'])
    de mang 'comparison' trong best_loss.json khop tung byte. Khong sap xep loss theo
    thu tu chu cai: notebook duyet theo dung thu tu tren, doi la file lech.
    """
    h_label = f"h{horizon}"
    dong = []
    for loss in THU_TU_LOSS:
        if loss not in cfg.train["losses"]:
            continue
        for thu_muc in (
            paths.model_dir(loss, horizon),
            paths.stage_goc("s08_train") / loss / h_label,
        ):
            d = _doc_metrics_val(thu_muc, h_label)
            if d is not None:
                break
        if d is None:
            continue
        chinh = d.get(
            PHAM_VI_CHINH_THUC, d.get("scope_c_measured_daylight_official", {})
        )
        dong.append(
            {
                "horizon": h_label,
                "loss_name": loss.upper(),
                "feature_set": NHAN_BO_DAC_TRUNG,
                "raw_f_set": "",
                "folder": loss,
                # Notebook khong tinh pooled WAPE tren CV o buoc nay nen luon de trong
                "pooled_wape_cv_%": d.get("pooled_wape_cv"),
                "val_measured_daylight_wape_%": chinh.get("wape"),
                "val_measured_daylight_rmse": chinh.get("rmse"),
                "val_measured_daylight_mae": chinh.get("mae"),
                "val_measured_daylight_r2": chinh.get("r2"),
                # cot noi bo cua pipeline, bi loai truoc khi ghi JSON
                "_thu_muc": str(thu_muc),
            }
        )
    return pd.DataFrame(dong)


def chon_vo_dich(cfg: Cfg, paths: Paths) -> dict:
    """Chon loss co WAPE validation nho nhat cho tung horizon.

    Tra ve dict {h1: {...}, h4: {...}} - dinh dang giong best_loss.json cu de
    stage s10/s11 doc duoc ma khong phai sua.
    """
    ket_qua = {}
    for h in cfg.train["horizon_steps"]:
        h_label = f"h{h}"
        bang = bang_so_sanh(cfg, paths, h)
        if bang.empty or bang["val_measured_daylight_wape_%"].isna().all():
            print(f"[BO QUA] {h_label}: chua co metrics_val.json cua model nao.")
            continue

        print(f"--- SO SANH TREN TAP VALIDATION ({h_label}) ---")
        print(bang[["loss_name", "val_measured_daylight_wape_%",
                    "val_measured_daylight_rmse", "val_measured_daylight_r2"]]
              .to_string(index=False))

        tot = bang.loc[bang["val_measured_daylight_wape_%"].idxmin()]
        # THU TU VA TEN KHOA bam theo notebook 07 de best_loss.json khop tung byte.
        # 'thu_muc_model' KHONG duoc ghi vao JSON (notebook khong co khoa nay) - no chi
        # duoc truyen trong bo nho cho s09b/s10 biet nap model o dau, xem s09_final_test.
        ket_qua[h_label] = {
            "winning_loss": tot["folder"],
            "feature_set_name": "",
            "feature_set_label": NHAN_BO_DAC_TRUNG,
            "folder_name": tot["folder"],
            "rationale": (
                f"Horizon {h_label.upper()}: Mô hình VÔ ĐỊCH là '{tot['loss_name']}' "
                f"({NHAN_BO_DAC_TRUNG}) với Validation Measured & Daylight WAPE = "
                f"{tot['val_measured_daylight_wape_%']:.2f}%."
            ),
            "val_wape": float(tot["val_measured_daylight_wape_%"]),
            "comparison": bang.drop(columns=["_thu_muc"]).to_dict("records"),
            "thu_muc_model": tot["_thu_muc"],
        }
        print(
            f"=> VO DICH {h_label.upper()}: {tot['loss_name']} "
            f"(WAPE_val = {tot['val_measured_daylight_wape_%']:.2f}%)\n"
        )
    return ket_qua
