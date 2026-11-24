# Data

This folder is where the Yelp data goes when you run the notebooks locally. **Nothing in it is committed** (see `.gitignore`): the Yelp Open Dataset is licensed for educational use and should not be redistributed.

## Getting the data

**Option 1: let notebook 01 download it (recommended).** Set `DATA_SOURCE = "kaggle"` in Step 0. It downloads only `yelp_academic_dataset_business.json` (about 120 MB) from the [Kaggle mirror](https://www.kaggle.com/datasets/yelp-dataset/yelp-dataset). You need a free Kaggle account; if asked to sign in, run `kagglehub.login()` once.

**Option 2: download it yourself.** Get the dataset from [Yelp](https://business.yelp.com/data/resources/open-dataset/) or Kaggle, put `yelp_academic_dataset_business.json` in this folder, and set `DATA_SOURCE = "local"` and `LOCAL_PATH = "../data/yelp_academic_dataset_business.json"`.

## Expected file

| File | Size | Used by |
|---|---|---|
| `yelp_academic_dataset_business.json` | ~120 MB | Notebook 01 |

Notebook 01 checks its result against the numbers in our pitch deck: 52,268 restaurants, 17,281 closed, 7,784 with no price tier.
