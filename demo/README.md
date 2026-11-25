# SiteScore demo

An interactive tool for the question a founder actually faces: **for my restaurant concept, which of two candidate sites is riskier?**

Pick a city and a concept (cuisine, price level, chain or independent), click the map to place **Site A**, then switch to **Site B** and click again. For each site the demo shows:

- a **risk band** (Low / Medium / High: the bottom, middle and top thirds of predicted risk across existing restaurants), the estimated chance of being closed, and how it ranks against existing restaurants;
- **what drives it**: how density, a same-cuisine rival within 500 m, and price versus the area each change the odds, compared with a typical site;
- a **verdict**: the odds of closure at Site B relative to Site A for the same concept.

The map shows the 500 m radius around each site, with existing restaurants of the same cuisine in rust and the rest in grey.

## How to run

The demo needs notebook 01's output (`notebooks/outputs/restaurants_clean.csv`), because it counts the restaurants around each pin. The Yelp data is not in the repository, so run notebook 01 first.

From the repository root:

```bash
pip install -r requirements.txt
streamlit run demo/app.py
```

It opens in your browser at `http://localhost:8501`. The first load takes a few seconds while the model is fitted; after that every click is instant. An internet connection is needed for the map tiles.

## The model

The demo fits **the SiteScore model from notebook 02, Step 8** on all 52,268 restaurants when it starts: price tier, cuisine group, chain flag, log(1 + restaurants within 500 m), any same-cuisine restaurant within 500 m, and the absolute price gap to the neighbourhood (with its missing flag). It has no metro dummies, so it can score a city it was not trained on.

If notebook 02 has been run, the demo reads the formula from `notebooks/outputs/model_formula.txt`, so a change to the model in notebook 02 carries through. Otherwise it uses the same formula built into `sitescore.py`. The source in use is shown under "How SiteScore works" at the bottom of the page.

For a new site, every existing restaurant within 500 m counts as a neighbour; in the training data a restaurant does not count itself.

## Files

| File | What it does |
|---|---|
| `app.py` | The Streamlit interface |
| `sitescore.py` | Model fitting, site features, scoring, drivers and comparison (no interface code, so it can be tested on its own) |

## Limits

The score ranks sites better than chance (held-out AUC 0.687; 0.614–0.710 across cities) but is far from certain, and it is weaker for independent restaurants. Yelp shows whether a restaurant is closed now, not when it closed, so this is not a "chance of closing within 3 years". Rent, management and capital are not in the data. Use it to compare sites and ask better questions, not as a lease decision on its own.
