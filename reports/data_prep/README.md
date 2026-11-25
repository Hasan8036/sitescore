# Data preparation summaries

Summary tables from [notebook 01](../../notebooks/01_data_prep.ipynb), for the report's data section and appendix. They contain no restaurant-level Yelp data.

| File | Contents |
|---|---|
| `data_dictionary.csv` | Every variable in `restaurants_clean.csv`: how it is built, type, missing values, an example |
| `decisions_log.md` | Every data-preparation judgment call, plus data prep's recommended model inputs |
| `missing_values.csv` | Missing values per model variable |
| `density_check_open_vs_all.csv` | Closed share by density quintile, counting all neighbours vs open neighbours only |
| `metro_sizes.csv` | Restaurants and closed share per metro (used to choose the held-out metro) |

**Note on the model inputs.** The "Recommended model inputs" at the end of `decisions_log.md` were data prep's starting point (same-cuisine *share* and *metro*). Modelling refined them: the final SiteScore model ([notebook 02](../../notebooks/02_modelling.ipynb), Step 8) uses a yes/no "any same-cuisine restaurant within 500 m" flag and no metro dummies, so it can score cities it was not trained on.

**Updating these files.** Notebook 01 writes fresh copies to `notebooks/outputs/`, which git ignores. If notebook 01 changes, copy the new versions here and commit them.
