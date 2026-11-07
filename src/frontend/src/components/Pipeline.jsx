import { WEIGHTS } from "../lib/score";
const engines = [["Rule engine", "Hand-written thresholds. Instant, deterministic and easy to audit."], ["XGBoost", "Learns fraud from labeled history and returns a probability of fraud."], ["Isolation Forest", "Needs no labels. Flags behavior nobody has seen before."]];

export default function Pipeline() {
  return (
    <section id="how" className="section alt center"><div className="wrap">
      <h2>Three minds.<br />One verdict.</h2>
      <p className="lead">All three engines run in parallel, then a single aggregated score comes out.</p>
      <div className="cols">{engines.map(([t, d]) => <div key={t}><h3>{t}</h3><p>{d}</p></div>)}</div>
      <div className="wbar">{WEIGHTS.map((w) => <i key={w.k} style={{ width: `${w.w * 100}%`, background: w.color }} />)}</div>
      <div className="wleg">{WEIGHTS.map((w) => <span key={w.k}>{w.label} {w.w * 100}%</span>)}</div>
    </div></section>
  );
}