import { useState } from "react";

export default function Login({ onLogin, notice }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState(notice || null);
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try { await onLogin(username.trim(), password); } catch (x) { setErr(x.message); }
    setBusy(false);
  };

  return (
    <div className="login">
      <h2>Sign in</h2>
      <form className="form" onSubmit={submit}>
        <label htmlFor="u">Username</label>
        <input id="u" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" autoFocus />
        <label htmlFor="p">Password</label>
        <input id="p" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
        {err && <div className="lock" style={{ marginTop: 20 }}>{err}</div>}
        <button className="btn" type="submit" disabled={busy || !username || !password}>{busy ? "Signing in…" : "Sign in"}</button>
      </form>
      <p className="demo-hint">Demo accounts: r.mehta (customer), analyst, risk, admin.<br />Password: finguard-demo</p>
    </div>
  );
}