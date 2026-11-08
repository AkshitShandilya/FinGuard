# FinGuard AI

<p class="lead">Real-time financial fraud detection that explains every decision it makes.</p>

FinGuard scores each transaction from 0 to 100 using three independent signals: fixed rules, a trained machine-learning model and an anomaly detector. It shows a fraud analyst exactly why a payment was flagged, and it learns from the analyst's verdicts.

[Run it locally](installation.md){ .md-button .md-button--primary }
[Read the design](architecture.md){ .md-button }

## The problem

Traditional fraud systems check transactions against a fixed rulebook. That fails in three predictable ways.

| Weakness | Consequence |
|---|---|
| Rules only catch patterns someone has already written down | New fraud goes undetected until a rule is added by hand |
| Every signal is weighed the same regardless of context | Honest customers are blocked as often as fraudsters |
| The system cannot say why it blocked a payment | Analysts must reconstruct the evidence manually |

## What FinGuard does

- **Scores every payment** from 0 to 100 and maps it to one of four actions: approve, verify, hold or block.
- **Combines three signals.** A rule engine, an XGBoost classifier and an Isolation Forest run together, and a weighted aggregator produces one score.
- **Explains the result.** Each score comes with a breakdown by signal and the model's own feature attributions (TreeSHAP).
- **Separates duties.** Customers, fraud analysts, risk managers and administrators each see only what their role allows, enforced on the server.
- **Learns from decisions.** Analyst verdicts become training labels. An administrator can retrain the model, and the new version goes live only if it passes a champion/challenger check.

## Status

| Part | State |
|---|---|
| Scoring API, roles and audit log | Built and tested (30 automated tests) |
| Models trained on a public synthetic dataset | Built, with stress tests |
| Web console for all four roles | Built |
| Continuous learning with promotion gate | Built |
| Deployment | In progress |

!!! note "Scope"
    This is an educational prototype. The dataset is synthetic, so the reported metrics describe that dataset and not real-world performance. See [Machine learning](model.md) for the limitations.

## Team

| Name | Roll number |
|---|---|
| Arnav Kathuria | 1024030068 |
| Akshit Shandilya | 1024030067 |

Department of Computer Engineering, Thapar Institute of Engineering and Technology.