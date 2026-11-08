# Installation

## Requirements

- Python 3.10 or newer
- Node.js 18 or newer
- The dataset saved as `src/ml/data/creditcard_fraud.csv`

## Backend and model

Run these from the repository root.

```bash
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS and Linux

pip install -r src/backend/requirements.txt
python src/ml/train.py         # trains the models and writes src/ml/artifacts/
pytest src/tests               # expect 30 passed
```

Start the API:

```bash
cd src/backend
uvicorn main:app --reload
```

It runs on `http://localhost:8000`, and `/docs` shows every endpoint.

## Frontend

In a second terminal:

```bash
cd src/frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Demo accounts

| Username | Role | Password |
|---|---|---|
| `r.mehta` | Customer | `finguard-demo` |
| `analyst` | Fraud Analyst | `finguard-demo` |
| `risk` | Risk Manager | `finguard-demo` |
| `admin` | Administrator | `finguard-demo` |

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `FINGUARD_SECRET` | Key used to sign login tokens. **Set this before deploying.** | An insecure development key |
| `FINGUARD_DEMO_PASSWORD` | Password given to the four demo accounts when the database is created | `finguard-demo` |
| `VITE_API_URL` | Backend address the frontend calls | `http://localhost:8000` |

## Reset the demo

Stop the backend and delete `src/backend/finguard.db`. It is recreated with the sample cases and demo accounts on the next start. The trained models are not affected.

## Build these docs locally

```bash
pip install mkdocs-material
mkdocs serve
```

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| "Can't reach the backend" in the console | The API is not running on port 8000 |
| `no such table: users` | An old database. Delete `src/backend/finguard.db` |
| Merchant dropdown is empty | The API failed to start. Check its terminal for the error |
| Retrain says to run `train.py` first | `src/ml/artifacts/` or the CSV in `src/ml/data/` is missing |
| `pytest` says `tests` not found | Run it as `pytest src/tests` from the repository root |