# FinGuard AI

## Real-Time Financial Fraud Detection System

**Arnav Kathuria** — 1024030068  
**Akshit Shandilya** — 1024030067

**Department of Computer Engineering**  
**Thapar Institute of Engineering and Technology**

---

## Overview

FinGuard AI is a real-time financial fraud detection system that combines deterministic rules, supervised machine learning, unsupervised anomaly detection, behavioral analysis, and explainable AI to identify potentially fraudulent transactions.

The system evaluates transactions in real time and generates a **0–100 risk score**, along with feature-level explanations to help analysts understand why a transaction was flagged.

---

## Why FinGuard AI?

Traditional fraud detection systems often depend heavily on static, hand-written rules.

These systems can struggle with:

- Previously unseen fraud patterns
- High false-positive rates
- Detection delays
- Manual investigation
- Limited explanation of decisions

FinGuard AI combines multiple detection approaches into a single scoring pipeline.

---

## Detection Pipeline

```text
Customer Frontend
        |
        v
   API Gateway
   JWT + RBAC
        |
        v
Transaction Service
        |
        v
Feature Extraction
        |
        v
+-----------------------------+
|     Parallel Detection      |
|                             |
|  Rule Engine                |
|  XGBoost                    |
|  Isolation Forest           |
+-----------------------------+
        |
        v
 Risk Aggregation
        |
        v
Final Risk Score (0-100)
        |
        v
 Analyst Dashboard
        |
        v
Decision Feedback
        |
        v
Model Improvement