# Testing

## Approach

| Level | What is checked | Tool |
|---|---|---|
| Unit | Risk weights, score ranges, password hashing | pytest |
| Integration | API routes, role rules, database writes, the case-to-label link | pytest with FastAPI's test client |
| Security | Forged, expired and tampered tokens, header spoofing, login rate limit | pytest |
| ML validation | Cross-validation, rules baseline, stress test, retraining check | `src/ml/train.py` and `test_learning.py` |

Each test runs against a fresh temporary database, so tests do not affect each other or the real data.

## Run the tests

```bash
pytest src/tests
```

Expect 30 passed. Two model tests are skipped until `python src/ml/train.py` has been run, and the end-to-end retraining test also needs the dataset in `src/ml/data/`.

## Test cases

The full sheet, in the course template, is available as [Excel](test-cases/FinGuard_Test_Cases.xlsx) and [PDF](test-cases/FinGuard_Test_Cases.pdf). It lists the preconditions, test data, steps, expected and actual results for each case. The summary below matches it.

| ID | Area | Scenario | Expected result |
|---|---|---|---|
| TC-01 | Scoring | Risk weights are added up | They sum to 1 |
| TC-02 | Scoring | Small daytime payment, trusted device | Score 30 or less, tier Low |
| TC-03 | Scoring | Large night payment, foreign, low trust, high velocity | Score at least 45 and 30 points above TC-02 |
| TC-04 | Scoring | Any scored transaction | Response contains `drivers` |
| TC-05 | Model | ML score for a sample transaction | Between 0 and 100 |
| TC-06 | Model | Explain a transaction | All 8 features present, shares total about 100% |
| TC-07 | API | Score with no login | `401` |
| TC-08 | API | Score as analyst, then as customer | `200`, then `403` |
| TC-09 | API | Customer lists cases | `403` |
| TC-10 | API | Decide as admin, then analyst, then analyst again | `403`, `200`, `409` |
| TC-11 | API | Analyst decides a case | Appears in the audit log with the role |
| TC-12 | API | Customer reads own cases, analyst tries the same | Only own cases, then `403` |
| TC-13 | API | Read form metadata with and without login | `200` for any user, `401` without |
| TC-14 | Auth | Correct login | Token and role returned |
| TC-15 | Auth | Wrong password, unknown user | `401` both times |
| TC-16 | Auth | Call `/auth/me` | Returns the signed-in role |
| TC-17 | Auth | Send an `x-role: admin` header, no token | `401`, header grants nothing |
| TC-18 | Auth | Token with a character changed | `401` |
| TC-19 | Auth | Expired token | `401` |
| TC-20 | Auth | Token signed with a different key | `401` |
| TC-21 | Auth | Six wrong passwords in a minute | Sixth gets `429`, even the right password waits |
| TC-22 | Auth | Inspect stored password | A 64-character salted hash, not the password |
| TC-23 | Learning | High-risk payment | Blocked or held, case appears in the queue |
| TC-24 | Learning | Low-risk payment | Approved, no case |
| TC-25 | Learning | Analyst confirms fraud | Stored record labelled 1 |
| TC-26 | Learning | Analyst marks false positive | Stored record labelled 0 |
| TC-27 | Learning | Analyst escalates | Record stays unlabelled |
| TC-28 | Learning | Analyst pays or retrains, customer views model | `403` for each |
| TC-29 | Learning | Retrain with too few labels | Refused, attempt logged |
| TC-30 | Learning | Add simulated records and retrain | Result reports both holdout scores and a decision |