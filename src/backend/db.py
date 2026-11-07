import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent / "finguard.db"

SEED = [
    ("FG-10432", "R. Mehta", "R. Mehta", 85000, 87, 91, "critical", "₹5,000 – ₹10,000", ["New device", "Unusual location", "4 txns / 10 min", "High-value purchase"], [["Amount", 32], ["New device", 21], ["Location", 18], ["Velocity", 12], ["History", 4]]),
    ("FG-10431", "S. Kaur", "S. Kaur", 61200, 74, 68, "high", "₹8,000 – ₹15,000", ["Unusual location", "Odd hour"], [["Location", 24], ["Time of day", 19], ["Amount", 14], ["History", 6]]),
    ("FG-10429", "R. Mehta", "R. Mehta", 22500, 48, 39, "medium", "₹3,000 – ₹9,000", ["Above typical spend", "New merchant"], [["Amount", 17], ["Merchant", 13], ["History", 5]]),
    ("FG-10428", "D. Verma", "D. Verma", 99999, 93, 95, "critical", "₹10,000 – ₹40,000", ["VPN detected", "New device", "Account age < 7 days"], [["VPN", 28], ["Account age", 24], ["Amount", 20], ["New device", 11]]),
]


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    with conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS cases(
            id TEXT PRIMARY KEY, owner TEXT, customer TEXT, amount REAL, score INT, prob INT,
            tier TEXT, normal TEXT, flags TEXT, shap TEXT, status TEXT DEFAULT 'open')""")
        c.execute("""CREATE TABLE IF NOT EXISTS audit(
            id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT, decision TEXT, by_role TEXT, at TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS transactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT, owner TEXT, features TEXT, score INT, tier TEXT,
            case_id TEXT, label INTEGER, created_at TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS model_versions(
            id INTEGER PRIMARY KEY AUTOINCREMENT, trained_at TEXT, new_labels INT, new_frauds INT,
            champion REAL, challenger REAL, promoted INT, note TEXT)""")
        if c.execute("SELECT COUNT(*) FROM cases").fetchone()[0] == 0:
            for r in SEED:
                c.execute("INSERT INTO cases VALUES(?,?,?,?,?,?,?,?,?,?,'open')",
                          (*r[:8], json.dumps(r[8]), json.dumps(r[9])))


def _case(r):
    d = dict(r)
    d["flags"], d["shap"] = json.loads(d["flags"]), json.loads(d["shap"])
    return d


def list_cases(status="open"):
    with conn() as c:
        return [_case(r) for r in c.execute("SELECT * FROM cases WHERE status=? ORDER BY score DESC", (status,))]


def decide(case_id, decision, role):
    with conn() as c:
        row = c.execute("SELECT status FROM cases WHERE id=?", (case_id,)).fetchone()
        if row is None:
            return "missing"
        if row["status"] != "open":
            return "closed"
        c.execute("UPDATE cases SET status=? WHERE id=?", (decision, case_id))
        c.execute("INSERT INTO audit(case_id,decision,by_role,at) VALUES(?,?,?,?)",
                  (case_id, decision, role, datetime.now().isoformat(timespec="seconds")))
        label = {"Confirmed fraud": 1, "False positive": 0}.get(decision)  # Escalated stays unlabelled
        if label is not None:
            c.execute("UPDATE transactions SET label=? WHERE case_id=?", (label, case_id))
    return "ok"


def list_audit():
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM audit ORDER BY id DESC")]


def list_for_owner(owner):
    with conn() as c:
        return [_case(r) for r in c.execute("SELECT * FROM cases WHERE owner=? ORDER BY id DESC", (owner,))]


def next_case_id():
    with conn() as c:
        ids = [r["id"] for r in c.execute("SELECT id FROM cases")]
    nums = [int(i.split("-")[1]) for i in ids if i.startswith("FG-") and i.split("-")[1].isdigit()]
    return f"FG-{max(nums, default=10000) + 1}"


def add_case(k):
    with conn() as c:
        c.execute("INSERT INTO cases VALUES(?,?,?,?,?,?,?,?,?,?,'open')",
                  (k["id"], k["owner"], k["customer"], k["amount"], k["score"], k["prob"], k["tier"],
                   k["normal"], json.dumps(k["flags"]), json.dumps(k["shap"])))


def add_transaction(owner, features, score, tier, case_id=None, label=None):
    with conn() as c:
        c.execute("INSERT INTO transactions(owner,features,score,tier,case_id,label,created_at) VALUES(?,?,?,?,?,?,?)",
                  (owner, json.dumps(features), score, tier, case_id, label, datetime.now().isoformat(timespec="seconds")))


def labelled_records():
    with conn() as c:
        return [(json.loads(r["features"]), r["label"]) for r in c.execute("SELECT features,label FROM transactions WHERE label IS NOT NULL")]


def all_records():
    with conn() as c:
        return [json.loads(r["features"]) for r in c.execute("SELECT features FROM transactions")]


def model_stats():
    with conn() as c:
        row = c.execute("SELECT COUNT(*) n, SUM(label IS NOT NULL) lab, SUM(label=1) fr FROM transactions").fetchone()
    n, lab, fr = row["n"], row["lab"] or 0, row["fr"] or 0
    return {"records": n, "labelled": lab, "frauds": fr, "unlabelled": n - lab}


def add_version(res):
    with conn() as c:
        c.execute("INSERT INTO model_versions(trained_at,new_labels,new_frauds,champion,challenger,promoted,note) VALUES(?,?,?,?,?,?,?)",
                  (res["trained_at"], res["new_labels"], res["new_frauds"], res.get("champion_pr_auc"),
                   res.get("challenger_pr_auc"), int(res["promoted"]), res["reason"]))


def list_versions():
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM model_versions ORDER BY id DESC LIMIT 10")]