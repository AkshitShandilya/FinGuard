from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import auth
import db
import simulate
from detection import ml, retrain
from detection.aggregator import aggregate
from schemas import DecisionRequest, LoginRequest, ScoreRequest, ScoreResponse

app = FastAPI(title="FinGuard AI")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])
db.init()

STAFF = ("analyst", "risk", "admin")
DECISIONS = {"Confirmed fraud", "False positive", "Escalated"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/login")
def login(body: LoginRequest):
    user = auth.authenticate(body.username, body.password)
    return {"token": auth.make_token(user), "role": user["role"], "name": user["name"]}


@app.get("/auth/me")
def me(user: dict = Depends(auth.current_user)):
    return {"username": user["username"], "name": user["name"], "role": user["role"]}


@app.post("/score", response_model=ScoreResponse)
def score(req: ScoreRequest, user: dict = Depends(auth.require(*STAFF))):
    return aggregate(req)


@app.get("/meta")
def meta(user: dict = Depends(auth.current_user)):
    m = ml.meta()
    return {"categories": m["categories"], "amount_max": m["amount_max"],
            "amount_p95": m["amount_p95"], "trained": m.get("trained", False)}


@app.get("/cases")
def cases(status: str = "open", user: dict = Depends(auth.require(*STAFF))):
    return db.list_cases(status)


@app.get("/my-cases")
def my_cases(user: dict = Depends(auth.require("customer"))):
    return db.list_for_owner(user["name"])


@app.post("/decision")
def decision(body: DecisionRequest, user: dict = Depends(auth.require("analyst"))):
    if body.decision not in DECISIONS:
        raise HTTPException(422, f"decision must be one of {sorted(DECISIONS)}")
    result = db.decide(body.case_id, body.decision, user["role"])
    if result == "missing":
        raise HTTPException(404, "Case not found")
    if result == "closed":
        raise HTTPException(409, "Case already decided")
    return {"case_id": body.case_id, "decision": body.decision, "by": user["role"]}


@app.get("/audit")
def audit(user: dict = Depends(auth.require(*STAFF))):
    return db.list_audit()


def _flags(req):
    f = []
    if req.foreign_transaction: f.append("Foreign transaction")
    if req.location_mismatch: f.append("Location mismatch")
    if req.transaction_hour <= 5: f.append("Night-time")
    if req.device_trust_score < 40: f.append("Low device trust")
    if req.velocity_last_24h >= 5: f.append("High velocity")
    if req.amount >= ml.meta()["amount_p95"]: f.append("Unusually large")
    return f or ["No single flag"]


@app.post("/transactions")
def pay(req: ScoreRequest, customer: dict = Depends(auth.require("customer"))):
    """A customer payment: score it, store it, and open a case if it is High or Critical.
    The stored record gets its label later, from the analyst's decision."""
    user = customer["name"]
    r = aggregate(req)
    case_id = None
    if r["tier"] in ("High", "Critical"):
        case_id = db.next_case_id()
        shap = ([[d["feature"], d["impact"]] for d in r["drivers"] if d["impact"] > 0][:4]
                or [[p["label"], round(p["points"])] for p in r["parts"] if p["points"] >= 1])
        db.add_case(dict(id=case_id, owner=user, customer=user, amount=req.amount, score=r["score"],
                         prob=r["probability"], tier=r["tier"].lower(), normal="n/a", flags=_flags(req), shap=shap))
    db.add_transaction(user, req.model_dump(), r["score"], r["tier"], case_id)
    status = {"Low": "approved", "Medium": "verify", "High": "held", "Critical": "blocked"}[r["tier"]]
    return {"status": status, "message": r["action"], "case_id": case_id}


@app.get("/model")
def model_info(user: dict = Depends(auth.require("admin", "risk"))):
    return {**db.model_stats(), "amount_p95": ml.meta()["amount_p95"],
            "trained": ml.meta().get("trained", False), "versions": db.list_versions()}


@app.post("/retrain")
def do_retrain(user: dict = Depends(auth.require("admin"))):
    res = retrain.retrain(db.labelled_records(), db.all_records())
    db.add_version(res)
    return res


@app.post("/demo/new-pattern")
def demo_new_pattern(user: dict = Depends(auth.require("admin"))):
    rows = simulate.new_pattern()
    for f, label in rows:
        db.add_transaction("simulation", f, 0, "n/a", None, label)
    return {"added": len(rows)}