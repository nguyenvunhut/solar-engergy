"""Cac buoc cua pipeline, danh so theo thu tu chay.

Quy uoc:
  - Moi stage nhan Ctx (hoac Cfg) vao, tra ket qua ra - KHONG dung bien toan cuc.
  - Ten file sXX_<viec>.py; stage lon tach thanh sXXa/sXXb/... khi qua 200 dong.
  - File sXX_<ten>.py khong co hau to chu cai la file DIEU PHOI cua stage do.

Thu tu:
  s01 reindex -> s02 split -> s03 features_time -> s04 spatial -> s05 aggregate
  -> s06 vif -> s07 select -> s08 train -> s09 final_test -> s10 shap -> s11 phase_lag
"""
