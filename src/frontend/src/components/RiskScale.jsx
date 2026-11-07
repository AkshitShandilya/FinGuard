import { TIERS } from "../lib/score";
const dots = ["#c7c7cc", "#8a8a8e", "#444", "#000"];

export default function RiskScale() {
  return (
    <section id="tiers" className="section light center"><div className="wrap">
      <h2>Four tiers.<br /><span style={{ color: "#8a8a8e" }}>One clear action each.</span></h2>
      <div className="tiers">{TIERS.map((t, i) => (
        <div key={t.key} className="tier"><div className="dot" style={{ background: dots[i] }} />
          <div className="r">{t.range}</div><h4>{t.name}</h4><p>{t.action}</p></div>
      ))}</div>
    </div></section>
  );
}