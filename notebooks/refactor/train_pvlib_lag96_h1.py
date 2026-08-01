from pathlib import Path
import pickle
import numpy as np
import pandas as pd
import pvlib
from lightgbm import LGBMRegressor

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/model/v3/05_selected"
OUT = ROOT / "data/model/v3/06_20_pvlib_lag96_h1"
OUT.mkdir(parents=True, exist_ok=True)
WEATHER = ["shortwave_radiation", "diffuse_solar_radiation",
           "direct_normal_irradiance", "temperature_c"]
STATIC = ["site_id_enc", "number_of_panels", "capacity_kw", "inverter_enc"]
FEATURES = WEATHER + ["lag_96", "pv_elevation", "pv_azimuth",
                      "pv_sin_elevation"] + STATIC
META = pd.read_parquet(
    ROOT / "data/mlmart_base/v3_final_cleaned.parquet",
    columns=["site_id", "latitude", "longitude"],
).drop_duplicates("site_id")


def prepare(name):
    cols = ["site_id", "timestamp", "energy_generated_kwh", "energy_source",
            "is_daylight", "exclude_from_training", "lag_96"] + WEATHER + STATIC
    df = pd.read_parquet(DATA / name, columns=cols).sort_values(["site_id", "timestamp"])
    df["target"] = df.groupby("site_id", sort=False)["energy_generated_kwh"].shift(-1)
    df = df[df["target"].notna()].merge(META, on="site_id", validate="many_to_one")
    target_time = pd.to_datetime(df["timestamp"]) + pd.Timedelta(minutes=15)
    for _, idx in df.groupby("site_id", sort=False).groups.items():
        row = df.loc[idx[0]]
        times = pd.DatetimeIndex(target_time.loc[idx]).tz_localize(
            "Australia/Sydney", ambiguous=False, nonexistent="shift_forward"
        )
        pos = pvlib.solarposition.get_solarposition(
            times, float(row.latitude), float(row.longitude), method="nrel_numpy"
        )
        df.loc[idx, "pv_elevation"] = pos["apparent_elevation"].to_numpy()
        df.loc[idx, "pv_azimuth"] = pos["azimuth"].to_numpy()
    df["pv_sin_elevation"] = np.clip(np.sin(np.radians(df["pv_elevation"])), 0, None)
    return df


train = prepare("v3_development_selected.parquet")
test = prepare("v3_test_selected.parquet")
mask = ~train["exclude_from_training"].fillna(False).astype(bool)
medians = train.loc[mask, FEATURES].median().fillna(0)
model = LGBMRegressor(
    objective="huber", n_estimators=700, learning_rate=0.035, num_leaves=31,
    min_child_samples=80, reg_alpha=0.1, reg_lambda=1.0, n_jobs=2, verbosity=-1,
)
model.fit(train.loc[mask, FEATURES].fillna(medians).astype("float32"),
          train.loc[mask, "target"].astype("float32"))
prediction = model.predict(test[FEATURES].fillna(medians).astype("float32"))
source = pd.to_datetime(test["timestamp"])
target = source + pd.Timedelta(minutes=15)
audit = pd.DataFrame({
    "site_id": test["site_id"], "timestamp": source,
    "source_timestamp_h1": source, "target_timestamp_h1": target,
    "plot_timestamp_h1": target, "energy_source": test["energy_source"],
    "is_daylight": test["is_daylight"], "y_true_h1": test["target"],
    "y_pred_h1": prediction,
})
audit["residual_h1"] = audit["y_true_h1"] - audit["y_pred_h1"]
audit.to_parquet(OUT / "prediction_audit_h1.parquet", index=False)
with (OUT / "model_h1.pkl").open("wb") as handle:
    pickle.dump({"model": model, "features": FEATURES, "medians": medians.to_dict()}, handle)
print("rows", len(audit), "wape",
      np.abs(audit.residual_h1).sum() / np.abs(audit.y_true_h1).sum() * 100)
