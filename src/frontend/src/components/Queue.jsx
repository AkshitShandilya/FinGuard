import { useState } from "react";
import { TIERS } from "../lib/score";

const shade = (k) => TIERS.find((t) => t.key === k).color;

export default function Queue({ cases, canDecide, onDecide }) {
  const [sel, setSel] = useState(cases[0]?.id);
  const c = cases.find((x) => x.id === sel) || cases[0];
  if (!c) return <div className="panel mu">Queue is clear.</div>;
  return (
    <div className="split">
      <div className="panel">{cases.map((x) => (
        <div key={x.id} className={`case ${x.id === c.id ? "on" : ""}`} onClick={() => setSel(x.id)}>
          <span className="sq" style={{ background: shade(x.tier) }} /><span className="id">{x.id}</span>
          <span className="nm">{x.customer}</span><span>₹{x.amount.toLocaleString("en-IN")}</span><span className="sc">{x.score}</span>
        </div>))}</div>
      <div className="panel">
        <div className="big">₹{c.amount.toLocaleString("en-IN")}</div>{c.normal !== "n/a" && <p className="mu">Normal range {c.normal}</p>}
        <div className="sep" /><p className="mu">Fraud probability {c.prob}% · Risk score {c.score}/100</p>
        <div className="tags">{c.flags.map((f) => <span key={f}>{f}</span>)}</div>
        <div className="sep" />
        {c.shap.map(([l, v]) => (
          <div className="bar" key={l}><span>{l}</span><div className="tr"><i style={{ width: `${(Math.abs(v) / Math.max(...c.shap.map((x) => Math.abs(x[1])), 1)) * 100}%` }} /></div><b>+{v}</b></div>))}
        {canDecide ? (
          <div className="acts">
            <button className="btn sm" onClick={() => onDecide(c, "Confirmed fraud")}>Confirm fraud</button>
            <button className="btn sm ghost" onClick={() => onDecide(c, "False positive")}>False positive</button>
            <button className="btn sm ghost" onClick={() => onDecide(c, "Escalated")}>Escalate</button>
          </div>
        ) : <div className="lock">Read only. Only a Fraud Analyst can record decisions.</div>}
      </div>
    </div>
  );
}