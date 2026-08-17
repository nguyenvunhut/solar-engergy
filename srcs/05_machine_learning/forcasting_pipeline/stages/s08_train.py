"""Stage 08: dieu phoi 4 buoc con cua qua trinh huan luyen.

DAY LA CHO CAT LON NHAT CUA REFACTOR:
  Ban cu: 3 file 04_1_train_mae.py / 04_2_train_huber.py / 04_3_train_mse.py,
          tong 4.165 dong, nhung khi bo comment/print ra diff thi huber va mse
          chi khac DUNG 3 dong (LOSS_NAME, LGB_OBJECTIVE, OUTPUT_DIR).
  Ban moi: 1 bo code dung chung cho ca 3 loss, ten loss la tham so.

Dung:
    python srcs/05_machine_learning/pipeline/run.py --stage s08 --loss huber --horizon 1
    python srcs/05_machine_learning/pipeline/run.py --stage s08                  # ca 3 loss x ca 2 horizon
"""
from __future__ import annotations

from core.config import Cfg, load_config
from core.context import Ctx
from core.paths import Paths
from stages import s08a_prepare, s08c_train_final, s08d_export


def train_mot_cau_hinh(loss_name: str, horizon: int, cfg: Cfg | None = None) -> Ctx:
    """Chay tron 1 cau hinh (1 loss x 1 horizon) tu du lieu den artifact."""
    cfg = cfg or load_config()
    ctx = Ctx(cfg=cfg, paths=Paths(cfg), loss_name=loss_name, horizon_steps=horizon)

    print("=" * 74)
    print(f"TRAIN loss={loss_name}  horizon=h{horizon}  -> {ctx.thu_muc_ra}")
    print("TAP TEST BI KHOA o stage nay - chi mo o s09 sau khi chon xong mo hinh.")
    print("=" * 74)

    s08a_prepare.chuan_bi(ctx)
    print()
    print("--- CHINH SACH OUTLIER (experiment = "
          f"{cfg.train['experiment']}) ---")
    print("Dong co weight = 0 khong vao ham muc tieu nhung VAN GIU de bao cao.")
    print(s08a_prepare.bang_chinh_sach_outlier(ctx).to_string(index=False))
    print(f"Clip muc tieu: {s08a_prepare.chan_doan_clip(ctx)}")
    print()

    s08c_train_final.train(ctx)
    print()
    print("--- 12 DAC TRUNG QUAN TRONG NHAT ---")
    print(s08c_train_final.dac_trung_quan_trong(ctx).to_string())
    print()

    # Moi danh gia deu tren tap VALIDATION. Tap test chua he duoc mo o stage nay.
    val_h = s08c_train_final.tinh_metrics_val(ctx)
    print()

    s08c_train_final.kiem_tre_pha(ctx, val_h)
    print()
    print("--- METRIC THEO 8 PHAM VI (tren VALIDATION) ---")
    print("physical_over_capacity_rows PHAI co sai so rat lon -> model khong hoc outlier.")
    print(s08c_train_final.bang_8_pham_vi(ctx, val_h).to_string(index=False))
    print()

    s08d_export.export_tat_ca(ctx, val_h)
    return ctx


def run_s08(
    losses: list[str] | None = None,
    horizons: list[int] | None = None,
    cfg: Cfg | None = None,
) -> dict[tuple[str, int], Ctx]:
    """Chay nhieu cau hinh. Mac dinh: moi loss trong train.yaml x moi horizon."""
    cfg = cfg or load_config()
    losses = losses or sorted(cfg.train["losses"])
    horizons = horizons or list(cfg.train["horizon_steps"])

    ket_qua = {}
    for loss in losses:
        for h in horizons:
            ket_qua[(loss, h)] = train_mot_cau_hinh(loss, h, cfg)
            print()

    print("=" * 74)
    print("TONG KET (WAPE tren VALIDATION - con so dung de CHON mo hinh vo dich)")
    print("=" * 74)
    for (loss, h), ctx in sorted(ket_qua.items()):
        m = ctx.metrics_val.get("measured_daylight", {})
        print(f"  {loss:6s} h{h}: WAPE_val = {m.get('wape', float('nan')):.4f}%")
    return ket_qua
