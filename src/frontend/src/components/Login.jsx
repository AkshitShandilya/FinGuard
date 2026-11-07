import { ROLES } from "../lib/roles";

export default function Login({ onLogin }) {
  return (
    <div className="login">
      <h2>Sign in</h2>
      <p className="lead" style={{ fontSize: 17 }}>Demo access. Pick a role to see what it is allowed to do.</p>
      <div className="roles">{Object.entries(ROLES).map(([k, r]) => (
        <button key={k} onClick={() => onLogin(k)}>{r.label}<span>{r.blurb}</span></button>
      ))}</div>
      <p className="mu" style={{ marginTop: 20 }}>Placeholder for JWT login against the FastAPI backend.</p>
    </div>
  );
}