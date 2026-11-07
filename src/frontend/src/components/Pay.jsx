import { useState } from "react";
import Fields, { NORMAL, useForm } from "./Fields";
import { api } from "../lib/api";

const COPY = { approved: "Payment approved.", verify: "We need to verify this payment with you.",
  held: "Payment held while our team reviews it.", blocked: "Payment blocked and sent for investigation." };

export default function Pay({ role, onDone }) {
  const { f, set, meta, err: metaErr } = useForm(role, NORMAL);
  const [res, setRes] = useState(null);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  const send = async () => {
    setBusy(true);
    try { setRes(await api.pay(role, f)); setErr(null); onDone?.(); } catch (e) { setErr(e.message); }
    setBusy(false);
  };
  return (
    <div className="panel demo">
      <div><Fields f={f} set={set} meta={meta} /></div>
      <div className="result">
        {(err || metaErr) && <div className="lock">{err || metaErr}</div>}
        <button className="btn" disabled={busy || !f.merchant_category} onClick={send}>Send payment</button>
        {res && <>
          <div className="act" style={{ marginTop: 28 }}>{COPY[res.status]}</div>
          {res.case_id && <p className="mu" style={{ marginTop: 8 }}>Reference {res.case_id}</p>}
        </>}
        <p className="mu" style={{ marginTop: 28, textAlign: "center" }}>Every payment is stored. If an analyst reviews it, their verdict becomes a training label.</p>
      </div>
    </div>
  );
}
