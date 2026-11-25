# Validation

We tested the models from notebook 02 using the restaurant table from notebook 01. Following the data-preparation recommendation, we chose Indianapolis because its 4,150 restaurants were closest to the target size of 4,000 after excluding the largest metro. This choice used counts, not closure rates. The other 48,118 restaurants formed the training set. We evaluated B3 without metro dummies, since a city excluded from training has no estimable city coefficient. The constant training-rate, chain-only and concept-only models provided baselines.

We used five-fold cross-validation within the training metros, keeping whole metros together. The yes/no same-cuisine-neighbour specification had mean fold AUC 0.6724 (SD 0.0146), compared with 0.6712 for the agreed share specification. We selected the yes/no version and an F1 threshold using only these out-of-fold training predictions. The difference between the two specifications was small.

On the held-out metro, the selected model achieved AUC 0.687, compared with 0.671 for concept alone and 0.500 for the constant baseline. Its average precision was 0.485, against a test closure share of 31.7%. A bootstrap that resampled 288 two-kilometre spatial cells 1,000 times gave a 95% AUC interval of 0.672–0.704. The paired AUC gain over concept alone was 0.016 (interval 0.007–0.025). These intervals are conditional on the fitted models and this metro.

Accuracy alone overstated closure detection. At 0.5, accuracy was 69.6%, versus 68.3% for predicting every listing as open, but recall was only 13.2%. The training-chosen cutoff of 0.293 raised recall to 70.8%, with precision 43.9%; false alarms rose from 121 to 1,189. This illustrates a trade-off rather than an optimal business policy. The highest-score 20% contained 50.4% closed listings and captured 31.8% of closures, giving 1.59 times the overall closure share.

Leaving out each of the eleven metros produced mean AUC 0.672, SD 0.027, and a range of 0.614–0.710. The 250 m/1 km radius and chain-cutoff checks gave similar ranking performance. All radius-dependent price-gap variables were recomputed in those checks. Performance among independent restaurants was weaker (AUC 0.627), which matters for the intended founder audience. The supplementary probability plot compares predicted and observed proportions; it does not fit a new calibration algorithm.

These findings support modest retrospective ranking value, not reliable prediction of next-year closure. There are no verified opening/closure dates or historical feature snapshots. Notebook 02 explored the full sample before this validation, so the regional checks are exploratory rather than completely untouched confirmation. Open-neighbour counts remain descriptive only because they depend on neighbours' status labels. No sensitivity result was used to change the frozen model or cutoff.

## Result figures

- [Held-out ROC and precision–recall](../reports/figures/validation_roc_pr.png)
- [Classification errors at the two cutoffs](../reports/figures/validation_confusion_matrices.png)
- [Predicted versus observed closed proportions](../reports/figures/validation_probability_check.png)
- [Leave-one-metro-out performance](../reports/figures/validation_leave_one_metro_out.png)

## Reproduce

Run notebook 01 to generate the ignored `notebooks/outputs/restaurants_clean.csv`, then run all cells in [03_validation.ipynb](../notebooks/03_validation.ipynb). Notebook 03 refits the B3 specifications; it never tests notebook 02's full-sample fitted predictions. All aggregate result tables are regenerated in the ignored outputs folder. Raw/clean Yelp data and row-level predictions are not redistributed in the repository.
