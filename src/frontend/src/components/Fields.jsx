import { useEffect, useState } from "react";
import { api } from "../lib/api";

// Keys match the dataset columns and the backend's ScoreRequest.
export const RISKY = { amount: 600, transaction_hour: 3, merchant_category: "", foreign_transaction: true,
  location_mismatch: true, device_trust_score: 20, velocity_last_24h: 6, cardholder_age: 35 };
export const NORMAL = { amount: 120, transaction_hour: 14, merchant_category: "", foreign_transaction: false,
  location_mismatch: false, device_trust_score: 80, velocity_last_24h: 1, cardholder_age: 40 };

export function useForm(role, initial) {
  const [f, setF] = useState(initial);
  const [meta, setMeta] = useState({ categories: [], amount_max: 2000 });
  const [err, setErr] = useState(null);
  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));
  useEffect(() => {
    api.meta(role).then((m) => {
      setMeta(m);
      setF((p) => ({ ...p, merchant_category: m.categories.includes(p.merchant_category) ? p.merchant_category : m.categories.includes("Electronics") ? "Electronics" : m.categories[0] }));
    }).catch((e) => setErr(e.message));
  }, [role]);
  return { f, set, meta, err };
}

const Slider = ({ label, value, min, max, step = 1, show, onChange }) => (
  <div className="ctl tight"><div className="row">{label} <span>{show ? show(value) : value}</span></div>
    <input type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(+e.target.value)} /></div>
);
const Switch = ({ label, on, onChange }) => (
  <div className="sw">{label}<button className={on ? "on" : ""} onClick={() => onChange(!on)} aria-label={label} /></div>
);

export default function Fields({ f, set, meta }) {
  const hour = (h) => `${String(h).padStart(2, "0")}:00`;
  return (
    <>
      <Slider label="Amount" value={f.amount} min={1} max={meta.amount_max} step={meta.amount_max > 1000 ? 10 : 1} show={(v) => `₹${v.toLocaleString("en-IN")}`} onChange={(v) => set("amount", v)} />
      <Slider label="Hour of day" value={f.transaction_hour} min={0} max={23} show={hour} onChange={(v) => set("transaction_hour", v)} />
      <div className="ctl tight"><div className="row">Merchant category</div>
        <select value={f.merchant_category} onChange={(e) => set("merchant_category", e.target.value)}>
          {meta.categories.map((c) => <option key={c}>{c}</option>)}</select></div>
      <Slider label="Device trust" value={f.device_trust_score} min={0} max={100} show={(v) => `${v} / 100`} onChange={(v) => set("device_trust_score", v)} />
      <Slider label="Transactions in 24h" value={f.velocity_last_24h} min={0} max={12} onChange={(v) => set("velocity_last_24h", v)} />
      <Slider label="Cardholder age" value={f.cardholder_age} min={18} max={90} onChange={(v) => set("cardholder_age", v)} />
      <Switch label="Foreign transaction" on={f.foreign_transaction} onChange={(v) => set("foreign_transaction", v)} />
      <Switch label="Location mismatch" on={f.location_mismatch} onChange={(v) => set("location_mismatch", v)} />
    </>
  );
}
