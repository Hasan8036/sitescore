"""SiteScore demo: compare the closure risk of two candidate sites for the same restaurant concept.

Run from the repository root (after notebook 01 has created notebooks/outputs/restaurants_clean.csv):
    streamlit run demo/app.py
"""
from pathlib import Path

import folium
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

import sitescore as ss

GREEN, RUST, AMBER, GREY = "#1f4e3d", "#b5543c", "#c98a1b", "#8a8a8a"
BAND_COLOUR = {"Low": GREEN, "Medium": AMBER, "High": RUST}
SITE_COLOUR = {"A": "#1d4ed8", "B": "#7c3aed"}

st.set_page_config(page_title="SiteScore", page_icon="📍", layout="wide")


# ------------------------------------------------------------------ data and model (cached)
@st.cache_resource(show_spinner="Fitting the SiteScore model on 52,268 restaurants…")
def get_model():
    path = ss.find_data(Path(__file__).resolve().parent)
    formula, source = ss.read_formula(path)
    df = ss.load_restaurants(path)
    return ss.fit(df, formula, source)


try:
    model = get_model()
except (FileNotFoundError, ValueError) as e:
    st.error(str(e))
    st.stop()

df = model.data


@st.cache_data
def metro_centres(_n: int) -> pd.DataFrame:
    # Start each city at the median restaurant location, which sits in the main restaurant district
    return df.groupby("metro")[["latitude", "longitude"]].median()


centres = metro_centres(len(df))
metros = df["metro"].value_counts().index.tolist()
cuisines = sorted(df["cuisine_group"].unique())

# ------------------------------------------------------------------ sidebar: the concept
st.sidebar.title("📍 SiteScore")
st.sidebar.caption("Compare two candidate sites for the same restaurant concept.")

metro = st.sidebar.selectbox("City", metros, index=0)
st.sidebar.subheader("Your concept")
cuisine = st.sidebar.selectbox("Cuisine", cuisines,
                               index=cuisines.index("Italian") if "Italian" in cuisines else 0)
price_tier = st.sidebar.selectbox("Price level", ["1", "2", "3", "4"], index=1,
                                  format_func=lambda t: ss.PRICE_LABELS[t])
chain = st.sidebar.toggle("Part of a chain (5+ locations)", value=False)

st.sidebar.subheader("Place your sites")
placing = st.sidebar.radio("Clicking the map places", ["Site A", "Site B"], horizontal=True)
st.sidebar.caption("Click anywhere on the map. Switch to Site B and click again to compare.")

# Reset the pins when the city changes
if st.session_state.get("metro") != metro:
    c = centres.loc[metro]
    st.session_state.update(metro=metro, sites={"A": (float(c.latitude), float(c.longitude)), "B": None},
                            last_click=None)
if st.sidebar.button("Clear Site B"):
    st.session_state["sites"]["B"] = None

sites = st.session_state["sites"]

# ------------------------------------------------------------------ score the sites
results = {}
for key, loc in sites.items():
    if loc is None:
        continue
    feats = ss.site_features(model, loc[0], loc[1], cuisine, price_tier, int(chain))
    results[key] = {"feats": feats, "score": ss.score(model, feats), "drivers": ss.location_drivers(model, feats)}

# ------------------------------------------------------------------ layout
st.title("SiteScore")
st.markdown(f"**{cuisine}**, {ss.PRICE_LABELS[price_tier]}, "
            f"{'chain' if chain else 'independent'} · {metro}")

left, right = st.columns([1.25, 1], gap="large")

with left:
    centre = sites["A"] if sites["B"] is None else tuple(np.mean([sites["A"], sites["B"]], axis=0))
    m = folium.Map(location=centre, zoom_start=15 if sites["B"] is None else 14, tiles="OpenStreetMap")
    for key, r in results.items():
        f = r["feats"]
        lat, lon = f["latitude"], f["longitude"]
        folium.Circle((lat, lon), radius=ss.RADIUS_M, color=SITE_COLOUR[key], weight=2, fill=True,
                      fill_opacity=0.05).add_to(m)
        nbrs = df.iloc[f["neighbour_index"]]
        for _, nb in nbrs.iterrows():
            same = nb["cuisine_group"] == cuisine
            folium.CircleMarker((nb["latitude"], nb["longitude"]), radius=4 if same else 2.5,
                                color=RUST if same else GREY, fill=True, fill_opacity=0.9 if same else 0.5,
                                weight=0, tooltip=f"{nb['name']} ({nb['cuisine_group']})" if "name" in nb else None
                                ).add_to(m)
        folium.Marker((lat, lon), tooltip=f"Site {key}",
                      icon=folium.Icon(color="blue" if key == "A" else "purple", icon="star", prefix="fa")).add_to(m)
    out = st_folium(m, height=560, use_container_width=True, returned_objects=["last_clicked"],
                    key=f"map_{metro}")
    st.caption("Circles: 500 m around each site. Rust dots: existing restaurants with the same cuisine. "
               "Grey dots: other restaurants.")

    click = (out or {}).get("last_clicked")
    if click and click != st.session_state.get("last_click"):
        st.session_state["last_click"] = click
        sites["A" if placing == "Site A" else "B"] = (click["lat"], click["lng"])
        st.rerun()


def site_card(key: str, r: dict):
    s, f = r["score"], r["feats"]
    colour = BAND_COLOUR[s["band"]]
    st.markdown(
        f"<div style='border-left:6px solid {colour};padding:6px 12px;margin-bottom:6px'>"
        f"<div style='font-size:0.9rem;color:{GREY}'>Site {key}</div>"
        f"<div style='font-size:1.6rem;font-weight:600;color:{colour}'>{s['band']} risk</div>"
        f"<div>Estimated chance of being closed: <b>{s['probability']:.0%}</b> · "
        f"riskier than {s['percentile']:.0f}% of existing restaurants</div></div>",
        unsafe_allow_html=True)
    d = r["drivers"].copy()
    d["effect"] = d["odds_multiplier"].map(lambda x: f"×{x:.2f}")
    st.dataframe(d[["factor", "this site", "effect"]], hide_index=True, width="stretch")


with right:
    for key in ["A", "B"]:
        if key in results:
            site_card(key, results[key])

    if "A" in results and "B" in results:
        ratio = ss.compare(model, results["A"]["feats"], results["B"]["feats"])
        pa, pb = results["A"]["score"]["probability"], results["B"]["score"]["probability"]
        safer = "A" if pa < pb else "B"
        st.subheader("Verdict")
        headline = ("**The two sites are about equally risky** for this concept."
                    if abs(ratio - 1) < 0.05 else f"For this concept, **Site {safer} is the safer location.**")
        st.markdown(
            f"{headline} "
            f"Site B's odds of closure are **×{ratio:.2f}** Site A's "
            f"({abs(ratio - 1):.0%} {'higher' if ratio > 1 else 'lower'}), "
            f"{pb:.0%} vs {pa:.0%} estimated chance of being closed.")
    elif "A" in results:
        st.info("Switch to **Site B** in the sidebar and click the map to compare a second location.")
    if results:
        typical_n = float(df["n_rest_500m"].median())
        st.caption(f"Effect: how each factor changes the odds of being closed compared with a typical site "
                   f"({typical_n:,.0f} restaurants within 500 m, the median; no same-cuisine competitor; priced in line "
                   "with the area). ×1.00 = no difference; above 1 = higher risk.")

with st.expander("How SiteScore works, and what it can't tell you"):
    st.markdown(f"""
**Model.** A logistic regression fitted on {len(df):,} restaurants in 11 metro areas from the Yelp Open Dataset
(notebook 02, Step 8). Inputs: cuisine, price level, chain status, the number of restaurants within 500 m,
whether any of them share your cuisine, and how far your price sits from theirs.
Formula source: {model.formula_source}.

**Risk bands.** Low, Medium and High are the bottom, middle and top thirds of predicted risk across existing
restaurants (cut-offs {model.risk_cutoffs[0]:.0%} and {model.risk_cutoffs[1]:.0%}).

**How well it works (notebook 03).** Trained without Indianapolis and tested on it, AUC is 0.687
(0.671 for concept alone); across all 11 held-out cities AUC ranges from 0.614 to 0.710.
It ranks sites better than chance but is far from certain, and it is weaker for independent restaurants (AUC 0.627).

**Limits.** Yelp shows whether a restaurant is closed *now*, not when it closed, so this is not a
"chance of closing within 3 years". Rent, management and capital are not in the data. Use the score to
compare sites and ask better questions, not as a lease decision on its own.
""")
