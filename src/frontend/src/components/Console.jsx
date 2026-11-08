import { useState } from "react";
import { ROLES, TAB_LABELS } from "../lib/roles";
import Queue from "./Queue";
import Score from "./Score";
import Audit from "./Audit";
import Pay from "./Pay";
import Model from "./Model";

export default function Console({ role, name, data, error, onDecide, onRefresh }) {
  const r = ROLES[role];
  const [tab, setTab] = useState(r.tabs[0]);
  return (
    <div className="con">
      <div className="conhead"><div><h2>{r.label}</h2><p>{name} · {r.blurb}</p></div></div>
      {error && <div className="lock" style={{ marginBottom: 20 }}>{error}</div>}
      <div className="tabs">{r.tabs.map((t) => <button key={t} className={`tab ${tab === t ? "on" : ""}`} onClick={() => setTab(t)}>{TAB_LABELS[t]}</button>)}</div>
      {tab === "queue" && <Queue cases={data.cases} canDecide={r.decide} onDecide={onDecide} />}
      {tab === "score" && <Score role={role} />}
      {tab === "audit" && <Audit audit={data.audit} />}
      {tab === "pay" && <Pay role={role} onDone={onRefresh} />}
      {tab === "model" && <Model role={role} canRetrain={r.retrain} />}
      {tab === "activity" && (
        <div className="panel"><table className="tbl"><thead><tr><th>Case</th><th>Amount</th><th>Status</th></tr></thead><tbody>
          {data.mine.map((c) => (
            <tr key={c.id}><td>{c.id}</td><td>₹{c.amount.toLocaleString("en-IN")}</td><td>{c.status === "open" ? "Under review" : c.status}</td></tr>
          ))}
        </tbody></table></div>
      )}
    </div>
  );
}