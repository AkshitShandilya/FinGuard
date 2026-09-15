# Architecture

## System Architecture

FinGuard AI follows a layered architecture in which transactions move through authentication, processing, feature extraction, parallel detection, risk aggregation, and analyst review.

```text
┌──────────────────────┐
│  Customer Frontend   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│     API Gateway      │
│     JWT + RBAC       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Transaction Service  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Feature Extraction  │
└──────────┬───────────┘
           │
           ▼
     ┌─────────────┐
     │   Parallel  │
     │  Detection  │
     └──────┬──────┘
            │
      ┌─────┼──────────────┐
      ▼     ▼              ▼
   Rules  XGBoost   Isolation Forest
      │     │              │
      └─────┼──────────────┘
            ▼
┌──────────────────────┐
│  Risk Aggregation    │
│     Score 0–100      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Analyst Dashboard    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Decision Feedback DB │
└──────────┬───────────┘
           │
           ▼
     Model Improvement