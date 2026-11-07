export default function Ring({ score, tier }) {
  const C = 2 * Math.PI * 88;
  return (
    <div className="ring">
      <svg width="200" height="200" viewBox="0 0 200 200">
        <circle cx="100" cy="100" r="88" fill="none" stroke="#262626" strokeWidth="10" />
        <circle cx="100" cy="100" r="88" fill="none" stroke={tier.color} strokeWidth="10" strokeLinecap="round"
          strokeDasharray={C} strokeDashoffset={C * (1 - score / 100)} style={{ transition: "stroke-dashoffset .5s ease" }} />
      </svg>
      <div className="c"><span className="n">{score}</span><span className="t">{tier.name}</span></div>
    </div>
  );
}