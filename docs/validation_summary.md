# Validation

We held out Indianapolis (4,150 restaurants) and trained on the other 48,118 restaurants. Five-fold cross-validation kept whole metros together. Model choice and the F1 cutoff used only training predictions. We tested B3 without metro dummies, since a city excluded from training has no fitted city coefficient.

The selected yes/no same-cuisine-neighbour model had test AUC **0.687**, versus **0.671** for concept alone. The share version was nearly tied at **0.6866**. A spatial bootstrap gave a conditional 95% AUC interval of **0.672–0.704**. At the default 0.5 cutoff, recall was **13.2%**. The training-selected cutoff of 0.293 raised recall to **70.8%**, with **43.9% precision**; false alarms rose from 121 to 1,189.

Across eleven held-out metros, mean AUC was **0.672** (range **0.614–0.710**). Alternative radii and chain cutoffs gave similar results. Independent-restaurant AUC was lower at **0.627**. The score provides modest ranking value, with weaker performance for individual founders. It does not establish future closure risk: dates and historical features are unavailable, and notebook 02 already explored the full sample.

Code, outputs and figures: [03_validation.ipynb](../notebooks/03_validation.ipynb). Run notebook 01 first, then run all cells in 03.
