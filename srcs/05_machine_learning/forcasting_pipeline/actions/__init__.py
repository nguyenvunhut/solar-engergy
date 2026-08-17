"""Cac hanh dong chay RIENG, KHONG nam trong pipeline chuan (`run.py --stage all`).

Dat o day nhung viec:
  - Ton nhieu thoi gian nhung khong can chay lai moi lan (tune_optuna: ~1 tieng).
  - Khong sinh ra dau vao cho stage nao (baseline_prophet: chi la moc doi chieu).
  - Chi de kiem chung, khong thuoc luong san xuat (validate_model_selection).

Nho tach nhu vay, `run.py --stage all` chay duoc trong buoi demo ma khong phai ngoi cho
Optuna - day la yeu cau ro rang cua chu nhiem du an.
"""
