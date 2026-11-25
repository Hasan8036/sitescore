"""SiteScore scoring logic, kept separate from the Streamlit interface so it can be tested.

The model is the validated SiteScore specification from notebook 02, Step 8: no metro dummies
(so it can score any city) and a yes/no "any same-cuisine restaurant within 500 m" competitor flag.
It is refitted here on notebook 01's restaurants_clean.csv, so the demo and notebook 02 always agree.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.neighbors import BallTree

RADIUS_M = 500
EARTH_RADIUS_M = 6_371_000

# Same formula as notebook 02, Step 8. If notebook 02 has written its formula to model_formula.txt,
# that one is used instead, so a change to the model in 02 flows through to the demo.
DEFAULT_FORMULA = (
    "closed ~ C(price_tier, Treatment('1')) + C(cuisine_group, Treatment('Burgers & Fast Food')) + is_chain"
    " + log_n_rest_500m + has_same_cuisine_nbr + abs_price_gap + price_gap_missing"
)
FORMULA_PREFIX = "SiteScore (validated, used by the demo): "

PRICE_LABELS = {"1": "$", "2": "$$", "3": "$$$", "4": "$$$$", "Missing": "Not listed"}


def find_data(start: Path) -> Path:
    """Locate notebook 01's output, whether the app is run from the repo root or the demo folder."""
    for base in [start, start.parent, Path.cwd(), Path.cwd().parent]:
        p = base / "notebooks" / "outputs" / "restaurants_clean.csv"
        if p.is_file():
            return p
    raise FileNotFoundError(
        "Could not find notebooks/outputs/restaurants_clean.csv. Run notebook 01 first (see the README)."
    )


def read_formula(data_path: Path) -> tuple[str, str]:
    """Return (formula, where it came from)."""
    f = data_path.parent / "model_formula.txt"
    if f.is_file():
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith(FORMULA_PREFIX):
                return line[len(FORMULA_PREFIX):].strip(), "notebook 02 (model_formula.txt)"
    return DEFAULT_FORMULA, "built-in copy of notebook 02, Step 8"


def load_restaurants(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"price_tier": str})
    needed = ["latitude", "longitude", "metro", "closed", "price_tier", "price_num", "cuisine_group",
              "is_chain", "n_rest_500m", "n_same_cuisine_500m", "log_n_rest_500m",
              "abs_price_gap", "price_gap_missing"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"restaurants_clean.csv is missing {missing}. Re-run notebook 01 (v2).")
    df["has_same_cuisine_nbr"] = (df["n_same_cuisine_500m"] > 0).astype(int)
    return df


@dataclass
class SiteScoreModel:
    result: object            # fitted statsmodels GLM
    formula: str
    formula_source: str
    tree: BallTree            # all restaurants, haversine
    coords_rad: np.ndarray
    data: pd.DataFrame
    risk_cutoffs: tuple       # predicted-risk tertiles across existing restaurants
    insample_risk: np.ndarray

    @property
    def coef(self) -> pd.Series:
        return self.result.params


def fit(df: pd.DataFrame, formula: str, formula_source: str = "") -> SiteScoreModel:
    result = smf.glm(formula, data=df, family=sm.families.Binomial()).fit()
    coords = np.radians(df[["latitude", "longitude"]].to_numpy())
    p = np.asarray(result.fittedvalues, dtype=float)
    cutoffs = tuple(float(x) for x in np.quantile(p, [1 / 3, 2 / 3]))
    return SiteScoreModel(result, formula, formula_source, BallTree(coords, metric="haversine"),
                          coords, df, cutoffs, p)


def site_features(model: SiteScoreModel, lat: float, lon: float, cuisine: str,
                  price_tier: str, is_chain: int) -> dict:
    """Inputs for a NEW restaurant at (lat, lon): every existing restaurant within 500 m is a neighbour."""
    df = model.data
    pt = np.radians([[lat, lon]])
    idx = model.tree.query_radius(pt, r=RADIUS_M / EARTH_RADIUS_M)[0]
    nbrs = df.iloc[idx]
    n_rest = len(nbrs)
    n_same = int((nbrs["cuisine_group"] == cuisine).sum())
    nbr_prices = nbrs["price_num"].dropna()
    nbr_mean_price = float(nbr_prices.mean()) if len(nbr_prices) else np.nan
    own_price = float(price_tier) if price_tier in {"1", "2", "3", "4"} else np.nan
    gap = own_price - nbr_mean_price
    gap_missing = int(not np.isfinite(gap))
    return {
        "latitude": lat, "longitude": lon,
        "cuisine_group": cuisine, "price_tier": price_tier, "is_chain": int(is_chain),
        "n_rest_500m": n_rest, "n_same_cuisine_500m": n_same,
        "log_n_rest_500m": float(np.log1p(n_rest)),
        "has_same_cuisine_nbr": int(n_same > 0),
        "nbr_mean_price_500m": nbr_mean_price,
        "price_gap": gap if not gap_missing else np.nan,
        "abs_price_gap": 0.0 if gap_missing else float(abs(gap)),
        "price_gap_missing": gap_missing,
        "neighbour_index": idx,
    }


def score(model: SiteScoreModel, feats: dict) -> dict:
    row = pd.DataFrame([{k: v for k, v in feats.items() if k != "neighbour_index"}])
    p = float(np.asarray(model.result.predict(row))[0])
    lo, hi = model.risk_cutoffs
    band = "Low" if p < lo else ("Medium" if p < hi else "High")
    percentile = float((model.insample_risk < p).mean() * 100)
    return {"probability": p, "band": band, "percentile": percentile}


def location_drivers(model: SiteScoreModel, feats: dict) -> pd.DataFrame:
    """How each LOCATION factor moves the odds, versus a typical site for the same concept.

    Reference site: the median number of restaurants within 500 m, no same-cuisine competitor,
    and priced in line with the neighbourhood. Concept terms (cuisine, price tier, chain) are the
    founder's choice and cancel out when two sites are compared, so they are not listed here.
    """
    b = model.coef
    median_n = float(model.data["n_rest_500m"].median())
    rows = []

    d = b["log_n_rest_500m"] * (feats["log_n_rest_500m"] - np.log1p(median_n))
    rows.append({"factor": "Density (500 m)",
                 "this site": f"{feats['n_rest_500m']:,} restaurants",
                 "typical site": f"{median_n:,.0f} restaurants",
                 "log_odds": d})

    s = b["has_same_cuisine_nbr"] * feats["has_same_cuisine_nbr"]
    rows.append({"factor": "Same-cuisine rival",
                 "this site": f"{feats['n_same_cuisine_500m']:,} nearby" if feats["has_same_cuisine_nbr"] else "None",
                 "typical site": "None",
                 "log_odds": s})

    if feats["price_gap_missing"]:
        g = b["price_gap_missing"]
        this = "Unknown (no priced neighbours)"
    else:
        g = b["abs_price_gap"] * feats["abs_price_gap"]
        direction = "above" if feats["price_gap"] > 0 else "below"
        this = f"{feats['abs_price_gap']:.1f} tiers {direction}" if feats["abs_price_gap"] >= 0.05 else "In line"
    rows.append({"factor": "Price vs area", "this site": this, "typical site": "In line with the area",
                 "log_odds": g})

    out = pd.DataFrame(rows)
    out["odds_multiplier"] = np.exp(out["log_odds"])
    return out


def compare(model: SiteScoreModel, feats_a: dict, feats_b: dict) -> float:
    """Odds of closure at site B relative to site A, same concept (odds ratio B / A)."""
    pa, pb = score(model, feats_a)["probability"], score(model, feats_b)["probability"]
    return (pb / (1 - pb)) / (pa / (1 - pa))
