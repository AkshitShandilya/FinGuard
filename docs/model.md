# Machine learning

## Dataset

The models are trained on a public credit-card fraud dataset of 10,000 synthetic transactions.

| Property | Value |
|---|---|
| Rows | 10,000 |
| Fraud rows | 151 (1.51%) |
| Features used | amount, transaction hour, merchant category, foreign transaction, location mismatch, device trust score, transactions in last 24 hours, cardholder age |
| Target | `is_fraud` |

The identifier column is dropped and the merchant category is one-hot encoded. Because the data is synthetic, its labels follow a pattern a model can learn almost perfectly. The results below show that the pipeline works, not how it would perform on real bank data.

## Models

| Model | Type | Role |
|---|---|---|
| XGBoost | Supervised | Probability that a transaction is fraud |
| Isolation Forest | Unsupervised | How unusual a transaction is, with no labels needed |
| Rule engine | Deterministic | Fixed thresholds, also used as a baseline |

The ML signal combines the two models, 80% XGBoost and 20% Isolation Forest.

## Evaluation

Data is split 80/20 with stratification. The decision threshold is chosen from cross-validated predictions on the training part, never from the test part. The test set holds 30 fraud rows.

| Method | Precision | Recall |
|---|---|---|
| Rules only | 0.28 | 1.00 |
| XGBoost | 1.00 | 1.00 |

| Measure | Value |
|---|---|
| XGBoost PR-AUC (test) | 1.00 |
| XGBoost PR-AUC (5-fold cross-validation) | 0.9975 ± 0.0035 |
| Isolation Forest ROC-AUC, no labels used | 0.95 |
| Highest single-feature ROC-AUC (device trust) | 0.83 |

The rules catch every fraud but also flag most honest transactions. The model keeps the recall and removes the false alarms. A score this high on clean synthetic data is an upper bound, not a promise, which is why the stress test below exists.

## Stress test

Each level is run with five random seeds and the mean PR-AUC is shown. At level 0 there is no noise.

| Noise level | Label noise | Feature noise |
|---|---|---|
| 0.0 | 1.000 | 1.000 |
| 0.1 | 0.997 | 0.645 |
| 0.2 | 0.988 | 0.418 |
| 0.3 | 0.955 | 0.276 |
| 0.5 | 0.829 | 0.133 |

- **Label noise** hides a share of the training fraud labels and adds the same number of false alarms. The model holds up well, because the pattern in the data is strong.
- **Feature noise** blurs the test transactions with noisy amounts, shifted hours and flipped flags. Scores fall quickly, so the clean-data result depends on exact inputs.
- ROC-AUC under feature noise stays above 0.85 even at level 0.5, so the model still ranks risky transactions above safe ones. What it loses is precision at the top of the ranking.

## Explaining a decision

Every score returns two views.

1. **Signal breakdown.** How many points each of the five weighted signals contributed.
2. **Model drivers.** TreeSHAP values from XGBoost, shown as each feature's signed share of influence. A positive share pushes the score toward fraud. Merchant-category columns are merged into one driver.

## Learning from new data

The system folds analyst decisions back into the model.

1. Every payment is stored with its features.
2. When an analyst confirms fraud or marks a false positive, the stored record gets a label of 1 or 0. Escalated cases stay unlabelled.
3. An administrator triggers retraining. XGBoost trains on the original data plus the new labels, weighted five times a normal row. Isolation Forest learns from every stored transaction, labelled or not.
4. A **champion/challenger check** decides whether the new model replaces the live one. It must not lose more than 0.05 PR-AUC on the original holdout, and it must improve on a share of the new records that were held back from training.
5. If it passes, it goes live and the previous model is archived. If not, the live model is kept. Either way the attempt is logged.

Result of one run on a simulated new fraud pattern:

| Check | Live model | New model |
|---|---|---|
| Original holdout, PR-AUC | 1.000 | 0.980 |
| Held-back new records, PR-AUC | 0.790 | 1.000 |

An earlier, stricter check rejected this same model because it only compared against the original data. It would never have let the system learn anything new. Checking both sets fixed that.

## Limitations

- The dataset is synthetic, so the metrics are not evidence of real-world accuracy.
- The test set has only 30 fraud rows, so single results are noisy. Cross-validation is the more reliable figure.
- Retraining is triggered by an administrator. It is not real-time online learning.
- Only flagged cases are reviewed, so new labels lean toward suspicious transactions. The original data keeps the model anchored.
- A wrong analyst verdict becomes a wrong label. The promotion check and archived versions limit the damage.
