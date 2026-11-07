import { useEffect, useState } from "react";
import { api } from "../lib/api";

export default function Model({ role, canRetrain }) {
  const [info, setInfo] = useState(null);
  const [res, setRes] = useState(null);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = () => api.model(role).then((d) => { setInfo(d); setErr(null); }).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, [role]);
  const run = async (fn) => {
    setBusy(true);
    try { setRes(await fn(role)); setErr(null); await load(); } catch (e) { setErr(e.message); }
    setBusy(false);
  };

  return (
    <div className="panel">
      {err && <div className="lock" style={{ marginBottom: 16 }}>{err}</div>}
      {info && <>
        <div style={{ display: "flex", gap: 48, flexWrap: "wrap" }}>
          <div><div className="big">{info.labelled}</div><p className="mu">labelled by analysts</p></div>
          <div><div className="big">{info.frauds}</div><p className="mu">confirmed fraud</p></div>
          <div><div className="big">{info.unlabelled}</div><p className="mu">not yet labelled</p></div>
        </div>
        {!info.trained && <div className="lock">No trained model found. Run ml/train.py first.</div>}
        {canRetrain && <>
          <div className="acts">
            <button className="btn sm" disabled={busy} onClick={() => run(api.retrain)}>{busy ? "Working…" : "Retrain now"}</button>
            <button className="btn sm ghost" disabled={busy} onClick={() => run(api.simulate)}>Simulate a new fraud pattern</button>
          </div>
          <p className="mu" style={{ marginTop: 12 }}>
            After simulating, score this in the Score tool before and after retraining: Clothing, 13:00, domestic, device trust 65, 3 transactions, amount {Math.round(info.amount_p95 * 1.2)}.
          </p>
        </>}
        {res && <div className="sep" />}
        {res && (res.added !== undefined ? <p>{res.added} simulated labelled records added.</p>
          : <p>{res.promoted ? res.reason : `Not promoted. ${res.reason}`}</p>)}
        {info.versions.length > 0 && <>
          <div className="sep" />
          <table className="tbl"><thead><tr><th>Time</th><th>Labels</th><th>Frauds</th><th>Before</th><th>After</th><th>Result</th></tr></thead><tbody>
            {info.versions.map((v) => <tr key={v.id}><td>{v.trained_at.replace("T", " ")}</td><td>{v.new_labels}</td><td>{v.new_frauds}</td>
              <td>{v.champion ?? "–"}</td><td>{v.challenger ?? "–"}</td><td>{v.promoted ? "Promoted" : "Kept old"}</td></tr>)}
          </tbody></table></>}
      </>}
    </div>
  );
}