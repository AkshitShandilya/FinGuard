# Prototype

The prototype is a working end-to-end system: customers pay, payments are scored, analysts review, and decisions feed back into the model.

## Walkthrough

Start the backend and frontend as described in [Installation](installation.md), then follow one case through the whole system.

1. **Customer.** Sign in as `r.mehta`, open *Make a payment*, and send a normal payment. It is approved. Then send a suspicious one: late hour, foreign transaction, location mismatch, low device trust. It is held or blocked and returns a case reference.
2. **Fraud Analyst.** Sign in as `analyst`. The case is in the queue with its score, flags and the model's reasons. Confirm fraud. The stored payment now has a training label.
3. **Administrator.** Sign in as `admin`, open *Model*, and see the labelled count rise. Add simulated records, then retrain. The page reports whether the new model was promoted and the before and after scores.
4. **Permissions.** Sign in as `risk`. The case buttons are read-only. A customer cannot open the queue, the score tool or the model page.

## What is implemented

| Area | Included |
|---|---|
| Scoring | Rules, XGBoost, Isolation Forest, weighted aggregator, four risk tiers |
| Explainability | Signal breakdown and TreeSHAP model drivers |
| Security | Password hashing, signed tokens, server-side roles, rate-limited login |
| Workflow | Case queue, analyst decisions, audit log |
| Learning | Stored payments, label capture, retraining with promotion check and model archive |
| Quality | 30 automated tests, stress test, rules-only baseline |

## Known limitations

- The dataset is synthetic, so accuracy figures describe the dataset only.
- Retraining is triggered by an administrator and is not continuous.
- The login token is kept in browser session storage. A production system would use secure cookies and HTTPS.
- There is no password reset or user-management screen. The four accounts are seeded.
- SQLite replaces the proposed PostgreSQL and Redis, and there is no message queue.