"""Stage 06a: chan doan da cong tuyen - cot hang so, tuong quan cao, VIF.

Tach tu buoc 3-8 cua run_vif_diagnostics() trong 03_feature_selection.py.

VI SAO CAN: hai dac trung tuong quan gan 1 mang cung mot thong tin. Voi cay quyet dinh
thi khong sai ket qua, nhung lam loang tam quan trong dac trung (SHAP chia doi cong lao
cho ca hai) va lang phi bo nho. Cot HANG SO thi vo dung hoan toan.

LUU Y KHI DOC KET QUA: lag/rolling tuong quan cao voi nhau la BINH THUONG (chung deu
la lich su cua cung 1 chuoi). KHONG tu dong loai chung chi vi VIF cao.
"""
from __future__ import annotations

import gc

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from core.columns import VERSION

# Cot khong dua vao chan doan: target, khoa ID, provenance, nhan outlier, thoi gian tho
LOAI_TRU = [
    "energy_generated_kwh",
    "gen_id", "site_id", "geo_id", "date_id", "time_id", "weather_id", "weather_type_id",
    "gmm_if_outlier_flag", "gmm_if_outlier_reason", "outlier_group",
    "exclude_from_training", "exclude_reason", "energy_source", "timestamp_was_inserted",
    "timestamp", "full_date",
]

NGUONG_TUONG_QUAN_CAO = 0.95     # coi la tuong quan cao
NGUONG_TRUNG_LAP = 0.9999        # coi la cong tuyen HOAN HAO -> chi giu 1 dai dien
NGUONG_VIF_CAO = 10.0
CO_MAU_TUONG_QUAN = 200_000      # sai so he so tuong quan < 0,3% - khong doi ket luan nao
CO_MAU_VIF = 50_000


def cot_so_can_chan_doan(duong_dan) -> tuple[list[str], list[str]]:
    """Doc SCHEMA truoc (chua nap du lieu) de chi nap dung cot so can thiet.

    Bo 19 cot chuoi (campus_name, weather_description...) von chiem phan lon RAM.
    """
    schema = pq.ParquetFile(str(duong_dan)).schema_arrow
    so = [
        ten for ten, kieu in zip(schema.names, schema.types)
        if any(k in str(kieu) for k in ("double", "float", "int"))
        and ten not in LOAI_TRU and not ten.startswith(f"{VERSION}_")
    ]
    return so, [n for n in schema.names if n not in so]


def doc_float32(duong_dan, cot: list[str]) -> pd.DataFrame:
    """Doc theo tung row-group va ep float32 ngay trong Arrow.

    Neu doc thang bang pd.read_parquet roi moi astype thi co luc ton tai dong thoi
    bang Arrow float64 + DataFrame float64 + DataFrame float32 -> dinh RAM cao hon han.
    """
    schema32 = pa.schema([pa.field(c, pa.float32()) for c in cot])
    pf = pq.ParquetFile(str(duong_dan))
    phan = []
    for i in range(pf.num_row_groups):
        bang = pf.read_row_group(i, columns=cot).cast(schema32)
        phan.append(bang.to_pandas())
        del bang
        gc.collect()
    df = pd.concat(phan, ignore_index=True)
    del phan
    gc.collect()
    return df


def thong_ke_co_ban(df: pd.DataFrame, cot: list[str]) -> pd.DataFrame:
    """Phat hien cot HANG SO va cot thieu qua nhieu du lieu."""
    dong = []
    for c in cot:
        s = df[c]
        ty_le_nan = s.isna().sum() / len(s) * 100
        n_khac = s.nunique()
        phuong_sai = s.var()

        # Giu DUNG ten nhan cua ban goc de file CSV khop tung bit
        co = "OK"
        if n_khac <= 1 or phuong_sai == 0:
            co = "CONSTANT"
        elif ty_le_nan > 50.0:
            co = "HIGH_MISSING"
        dong.append({
            "feature": c, "dtype": str(s.dtype),
            "nan_pct": round(ty_le_nan, 2), "nunique": n_khac,
            "variance": round(phuong_sai, 6) if pd.notna(phuong_sai) else np.nan,
            "flag_basic": co,
        })
    return pd.DataFrame(dong)


def cap_tuong_quan_cao(df: pd.DataFrame, cot: list[str], seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tra ve (ma tran tuong quan, bang cac cap |r| >= nguong).

    Tinh tren mau chu khong tren toan bo 1,79 trieu dong x 68 cot (ton ~1,5 GB va
    ~4 ty phep tinh) - sai so duoi 0,3%, khong doi ket luan nao.
    """
    mau = df.sample(n=min(CO_MAU_TUONG_QUAN, len(df)), random_state=seed)
    ma_tran = mau.corr(method="pearson")

    cap = []
    for i in range(len(cot)):
        for j in range(i + 1, len(cot)):
            f1, f2 = cot[i], cot[j]
            r = ma_tran.loc[f1, f2]
            if abs(r) >= NGUONG_TUONG_QUAN_CAO:
                cap.append({"feature_1": f1, "feature_2": f2, "correlation": round(r, 4)})
    return ma_tran, pd.DataFrame(cap)


def gom_nhom_trung_lap(ma_tran: pd.DataFrame, cot: list[str]) -> tuple[list[str], dict]:
    """Gom cac dac trung cong tuyen HOAN HAO, chi giu 1 dai dien moi nhom.

    Vi du thuc te trong du lieu nay:
      - 10 cot *_missing giong het nhau (metadata thieu theo ca cum)
      - day_of_week trung day_of_week_model, month trung month_model (s01 va s03 cung sinh)
      - minute_of_day = quarter_hour * 15
    Trong nhom cong tuyen hoan hao, cac cot mang DUNG cung mot thong tin nen giu cot nao
    cung nhu nhau - dai dien chon theo thu tu xuat hien.
    """
    da_gan, nhom = set(), {}
    for c in cot:
        if c in da_gan:
            continue
        cung_nhom = [
            k for k in cot
            if k != c and k not in da_gan and abs(ma_tran.loc[c, k]) >= NGUONG_TRUNG_LAP
        ]
        da_gan.add(c)
        if cung_nhom:
            nhom[c] = cung_nhom
            da_gan.update(cung_nhom)
    giu = [c for c in cot if c not in {x for ds in nhom.values() for x in ds}]
    return giu, nhom


VIF_TOI_DA = 9999.0        # cap khi phu thuoc tuyen tinh HOAN HAO (r2 >= 0.999999)
NGUONG_STD = 1e-6          # cot khong bien thien trong mau thi bo khoi phep tinh VIF


def tinh_vif(df: pd.DataFrame, cot: list[str], seed: int = 42, n_thread: int = 6):
    """VIF = 1/(1-R2) khi hoi quy 1 dac trung theo TAT CA dac trung con lai.

    Dung LinearRegression cua sklearn (khong dung statsmodels) de khop dung ban goc.
    VIF > 10 nghia la dac trung do gan nhu suy ra duoc tu cac dac trung khac.

    Tra ve (bang VIF, ma tran mau da impute, danh sach cot hop le) - hai thu sau dung
    lai cho PLS de khong phai lay mau va impute lan nua.
    """
    from sklearn.linear_model import LinearRegression
    from threadpoolctl import threadpool_limits

    mau = df[cot].sample(n=min(CO_MAU_VIF, len(df)), random_state=seed)
    mau = mau.fillna(mau.median())
    hop_le = [c for c in cot if mau[c].std() > NGUONG_STD]

    X = mau[hop_le].values
    ket = {}
    # CO DINH SO THREAD BLAS = n_thread (mac dinh 6, dung bang runtime.yaml: threads.n_jobs).
    #
    # VI SAO PHAI CO DINH: ma tran o day GAN SUY BIEN (R2 toi 0,99978, VIF ~4.500) nen sai
    # so lam tron bi khuech dai rat manh. LAPACK chia viec cho nhieu thread -> thu tu cong
    # doi theo so thread -> VIF doi theo. Da do thuc te 2026-08-07 tren cung du lieu:
    #     1 thread  -> day_of_year = 4517,29
    #     4 thread  -> 4525,82
    #     6 thread  -> 4524,60   <- KHOP moc tham chieu 31/07 (notebook 04 set n_jobs = 6)
    #     8 thread  -> 4524,60 (nhung sin_elevation lai lech)
    #     12 thread -> 4517,29
    # Dat bang threadpool_limits (API luc chay) thay vi chi dua vao bien moi truong: bien
    # moi truong chi co tac dung neu duoc dat TRUOC khi numpy nap, de bi vo hieu ngam.
    with threadpool_limits(limits=n_thread):
        for i, c in enumerate(hop_le):
            y = X[:, i]
            con_lai = np.delete(X, i, axis=1)
            lr = LinearRegression()
            lr.fit(con_lai, y)
            r2 = lr.score(con_lai, y)
            v = VIF_TOI_DA if r2 >= 0.999999 else 1.0 / (1.0 - r2)
            ket[c] = round(v, 2)
    bang = pd.DataFrame({"feature": cot, "vif": [ket.get(c) for c in cot]})
    return bang, mau, hop_le


def tinh_pls_vip(mau: pd.DataFrame, hop_le: list[str], y: np.ndarray) -> dict:
    """VIP (Variable Importance in Projection) tu PLS - danh gia suc manh du bao
    that su cua tung dac trung, dong thoi xu ly duoc da cong tuyen."""
    from sklearn.cross_decomposition import PLSRegression

    X = mau[hop_le].values
    pls = PLSRegression(n_components=min(5, len(hop_le)))
    pls.fit(X, y)
    t, w, q = pls.x_scores_, pls.x_weights_, pls.y_loadings_
    p_, h = w.shape
    s = np.diag(t.T @ t @ q.T @ q).reshape(h, -1)
    tong = np.sum(s)
    vip = np.zeros((p_,))
    for i in range(p_):
        trong_so = np.array([(w[i, j] / np.linalg.norm(w[:, j])) ** 2 for j in range(h)])
        vip[i] = np.sqrt(p_ * (s.T @ trong_so) / tong)[0]
    return {c: round(float(vip[i]), 3) for i, c in enumerate(hop_le)}
