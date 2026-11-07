from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import db
from detection import ml, retrain
import simulate
from detection.aggregator import aggregate
from schemas import DecisionRequest, ScoreRequest, ScoreResponse

app = FastAPI(title="FinGuard AI")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
db.init()

# Placeholder for JWT: the role arrives in a header. Swap for a verified token claim later.
CAN_SCORE = {"analyst", "risk", "admin"}
CAN_VIEW_CASES = {"analyst", "risk", "admin"}
CAN_DECIDE = {"analyst"}
DECISIONS = {"Confirmed fraud", "False positive", "Escalated"}


def need(role: str | None, allowed: set):
    if role not in allowed:
        raise HTTPException(403, "This role is not allowed to do that")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/score", response_model=ScoreResponse)
def score(req: ScoreRequest, x_role: str | None = Header(None)):
    need(x_role, CAN_SCORE)
    return aggregate(req)


@app.get("/cases")
def cases(status: str = "open", x_role: str | None = Header(None)):
    need(x_role, CAN_VIEW_CASES)
    return db.list_cases(status)


@app.post("/decision")
def decision(body: DecisionRequest, x_role: str | None = Header(None)):
    need(x_role, CAN_DECIDE)
    if body.decision not in DECISIONS:
        raise HTTPException(422, f"decision must be one of {sorted(DECISIONS)}")
    result = db.decide(body.case_id, body.decision, x_role)
    if result == "missing":
        raise HTTPException(404, "Case not found")
    if result == "closed":
        raise HTTPException(409, "Case already decided")
    return {"case_id": body.case_id, "decision": body.decision, "by": x_role}


@app.get("/audit")
def audit(x_role: str | None = Header(None)):
    need(x_role, CAN_VIEW_CASES)
    return db.list_audit()


@app.get("/my-cases")
def my_cases(x_role: str | None = Header(None), x_user: str | None = Header(None)):
    need(x_role, {"customer"})
    if not x_user:
        raise HTTPException(400, "x-user header required")
    return db.list_for_owner(x_user)  # placeholder: take the user from the JWT later


@app.get("/meta")
def meta(x_role: str | None = Header(None)):
    need(x_role, CAN_SCORE | {"customer"})
    m = ml.meta()
    return {"categories": m["categories"], "amount_max": m["amount_max"],
            "amount_p95": m["amount_p95"], "trained": m.get("trained", False)}


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
def pay(req: ScoreRequest, x_role: str | None = Header(None), x_user: str | None = Header(None)):
    """A customer payment: score it, store it, and open a case if it is High or Critical.
    The stored record gets its label later, from the analyst's decision."""
    need(x_role, {"customer"})
    user = x_user or "Customer"
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
def model_info(x_role: str | None = Header(None)):
    need(x_role, {"admin", "risk"})
    return {**db.model_stats(), "amount_p95": ml.meta()["amount_p95"],
            "trained": ml.meta().get("trained", False), "versions": db.list_versions()}


@app.post("/retrain")
def do_retrain(x_role: str | None = Header(None)):
    need(x_role, {"admin"})
    res = retrain.retrain(db.labelled_records(), db.all_records())
    db.add_version(res)
    return res


@app.post("/demo/new-pattern")
def demo_new_pattern(x_role: str | None = Header(None)):
    need(x_role, {"admin"})
    rows = simulate.new_pattern()
    for f, label in rows:
        db.add_transaction("simulation", f, 0, "n/a", None, label)
    return {"added": len(rows)}