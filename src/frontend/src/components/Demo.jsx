import { useState } from "react";
import Ring from "./Ring";
import { computeRisk } from "../lib/score";

const fmt = (n) => "₹" + n.toLocaleString("en-IN");

export default function Demo() {
  const [f, setF] = useState({ amount: 85000, velocity: 4, newDevice: true, oddLocation: true });
  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));
  const r = computeRisk(f);
  const max = Math.max(...r.parts.map((p) => p.points), 1);

  return (
    <section id="demo" className="section center">
      <div className="wrap">
        <h2 className="reveal">Score a transaction.</h2>
        <p className="lead reveal">Change the inputs and watch the verdict and its reasons update.</p>
        <div className="demo reveal">
          <div>
            <div className="ctl">
              <div className="row">Amount <span>{fmt(f.amount)}</span></div>
              <input type="range" min="500" max="100000" step="500" value={f.amount} onChange={(e) => set("amount", +e.target.value)} />
            </div>
            <div className="ctl">
              <div className="row">Velocity <span>{f.velocity} in 10 min</span></div>
              <input type="range" min="1" max="8" value={f.velocity} onChange={(e) => set("velocity", +e.target.value)} />
            </div>
            <div className="sw">New device<button className={f.newDevice ? "on" : ""} onClick={() => set("newDevice", !f.newDevice)} aria-label="New device" /></div>
            <div className="sw">Unusual location<button className={f.oddLocation ? "on" : ""} onClick={() => set("oddLocation", !f.oddLocation)} aria-label="Unusual location" /></div>
          </div>
          <div className="result">
            <Ring score={r.score} tier={r.tier} />
            <div className="act">{r.tier.action}</div>
            <p style={{ color: "#6e6e73", fontSize: 15, marginTop: 6 }}>{r.probability}% fraud probability</p>
            <div className="bars">
              {r.parts.map((p) => (
                <div className="bar" key={p.label}>
                  <span>{p.label}</span>
                  <div className="tr"><i style={{ width: `${(p.points / max) * 100}%`, background: r.tier.color }} /></div>
                  <b>+{Math.round(p.points)}</b>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}