# API reference

The API is served by FastAPI. When the backend is running, interactive documentation is at `http://localhost:8000/docs`.

## Authentication

Sign in with `POST /auth/login` to get a token, then send it on every other request.

```http
POST /auth/login
{"username": "analyst", "password": "finguard-demo"}
```

```json
{"token": "eyJ...", "role": "analyst", "name": "Neha Kapoor"}
```

```http
Authorization: Bearer eyJ...
```

| Rule | Behavior |
|---|---|
| Missing, expired, tampered or wrongly signed token | `401` |
| Valid token, role not allowed | `403` |
| Five wrong passwords for one username within a minute | `429` |
| Role | Read from the database on every request, never from the client |

## Endpoints

| Method | Path | Allowed roles | Purpose |
|---|---|---|---|
| `GET` | `/health` | Anyone | Check the server is running |
| `POST` | `/auth/login` | Anyone | Exchange a username and password for a token |
| `GET` | `/auth/me` | Any signed-in user | Return the current user and role |
| `GET` | `/meta` | Any signed-in user | Merchant categories and amount range for the forms |
| `POST` | `/score` | Analyst, Risk Manager, Administrator | Score a transaction without storing it |
| `POST` | `/transactions` | Customer | Make a payment: score it, store it, open a case if High or Critical |
| `GET` | `/my-cases` | Customer | The customer's own cases |
| `GET` | `/cases` | Analyst, Risk Manager, Administrator | Open cases, highest score first |
| `POST` | `/decision` | Analyst | Record Confirmed fraud, False positive or Escalated |
| `GET` | `/audit` | Analyst, Risk Manager, Administrator | Every decision with the role that made it |
| `GET` | `/model` | Risk Manager, Administrator | Label counts and retraining history |
| `POST` | `/retrain` | Administrator | Retrain and apply the champion/challenger check |
| `POST` | `/demo/new-pattern` | Administrator | Add simulated labelled records for a demo |

## Scoring a transaction

Request fields use the dataset's column names.

```http
POST /score
```

```json
{
  "amount": 900,
  "transaction_hour": 3,
  "merchant_category": "Electronics",
  "foreign_transaction": true,
  "location_mismatch": true,
  "device_trust_score": 20,
  "velocity_last_24h": 6,
  "cardholder_age": 35
}
```

The response has the score, the tier, the recommended action, the contribution of each signal, and the model drivers. The numbers below are an example.

```json
{
  "score": 90,
  "probability": 96,
  "tier": "Critical",
  "action": "Block and open an investigation case.",
  "parts": [{"label": "ML model", "points": 46.2}, {"label": "Rules", "points": 20.0}],
  "drivers": [{"feature": "Device trust", "impact": 34}, {"feature": "Amount", "impact": 22}]
}
```
