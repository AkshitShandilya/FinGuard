import Ring from "./Ring";
import { tierOf } from "../lib/score";

export default function Hero({ go }) {
  return (
    <section className="hero center"><div className="wrap">
      <p className="eyebrow">FinGuard AI</p>
      <h1>Fraud, caught<br /><span className="dim">before it clears.</span></h1>
      <p className="lead">Rules, machine learning and anomaly detection score every transaction in real time, and explain every decision.</p>
      <div className="cta"><button className="btn" onClick={() => go("login")}>Sign in to console</button><a className="link" href="#how">See how it works</a></div>
      <div className="stage">
        <Ring score={87} tier={tierOf(87)} />
        <div className="facts"><div className="big">₹85,000</div>
          <p>Customer normally spends ₹5,000 to ₹10,000. New device, unusual location, four transactions in ten minutes.</p>
          <p><b style={{ color: "#fff" }}>Held. Analyst alerted.</b></p></div>
      </div>
    </div></section>
  );
}