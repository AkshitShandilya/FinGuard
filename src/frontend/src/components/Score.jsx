import { useEffect, useState } from "react";
import Ring from "./Ring";
import Fields, { RISKY, useForm } from "./Fields";
import { api } from "../lib/api";
import { TIERS } from "../lib/score";

export default function Score({ role }) {
  const { f, set, meta, err: metaErr } = useForm(role, RISKY);
  const [r, setR] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (!f.merchant_category) return;
    let stale = false;
    const t = setTimeout(() => {
      api.score(role, f).then((d) => { if (!stale) { setR(d); setErr(null); } }).catch((e) => !stale && setErr(e.message));
    }, 150);
    return () => { stale = true; clearTimeout(t); };
  }, [f, role]);

  const tier = r && TIERS.find((t) => t.name === r.tier);
  const max = r ? Math.max(...r.parts.map((p) => p.points), 1) : 1;
  return (
    <div className="panel demo">
      <div><Fields f={f} set={set} meta={meta} /></div>
      <div className="result">
        {(err || metaErr) && <div className="lock">{err || metaErr}</div>}
        {r && <>
          <Ring score={r.score} tier={tier} /><div className="act">{r.action}</div>
          <p className="mu">{r.probability}% fraud probability</p>
          <div className="bars">{r.parts.map((p) => (
            <div className="bar" key={p.label}><span>{p.label}</span><div className="tr"><i style={{ width: `${(p.points / max) * 100}%` }} /></div><b>+{Math.round(p.points)}</b></div>))}</div>
          {r.drivers?.length > 0 && <div className="bars"><p className="mu" style={{ marginBottom: 10 }}>What the model saw</p>
            {r.drivers.map((d) => (<div className="bar" key={d.feature}><span>{d.feature}</span><div className="tr"><i style={{ width: `${Math.abs(d.impact)}%`, background: d.impact < 0 ? "#5c5c61" : "#fff" }} /></div><b>{d.impact > 0 ? "+" : ""}{d.impact}%</b></div>))}</div>}
        </>}
      </div>
    </div>
  );
}