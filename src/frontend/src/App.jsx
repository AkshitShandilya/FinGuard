import { useCallback, useEffect, useState } from "react";
import Nav from "./components/Nav";
import Hero from "./components/Hero";
import Pipeline from "./components/Pipeline";
import RiskScale from "./components/RiskScale";
import Footer from "./components/Footer";
import Login from "./components/Login";
import Console from "./components/Console";
import { api, getToken, setExpiredHandler, setToken } from "./lib/api";

export default function App() {
  const [view, setView] = useState("site");
  const [session, setSession] = useState(null); // { role, name } from the server, never from the browser
  const [booting, setBooting] = useState(!!getToken());
  const [notice, setNotice] = useState(null);
  const [data, setData] = useState({ cases: [], audit: [], mine: [] });
  const [error, setError] = useState(null);
  const role = session?.role;

  useEffect(() => {
    setExpiredHandler(() => { setSession(null); setNotice("Your session expired. Sign in again."); setView("login"); });
    if (getToken()) {
      api.me().then((u) => setSession({ role: u.role, name: u.name })).catch(() => {}).finally(() => setBooting(false));
    }
  }, []);

  const refresh = useCallback(async (r) => {
    try {
      if (r === "customer") setData({ cases: [], audit: [], mine: await api.mine() });
      else {
        const [cases, audit] = await Promise.all([api.cases(), api.audit()]);
        setData({ cases, audit, mine: [] });
      }
      setError(null);
    } catch (e) { setError(e.message); }
  }, []);

  useEffect(() => { if (role) refresh(role); }, [role, refresh]);

  const login = async (username, password) => {
    const d = await api.login(username, password);
    setToken(d.token);
    setNotice(null);
    setSession({ role: d.role, name: d.name });
  };
  const decide = async (c, label) => {
    try { await api.decide(role, c.id, label); await refresh(role); }
    catch (e) { setError(e.message); }
  };
  const signOut = () => { setToken(null); setSession(null); setView("site"); setError(null); };

  if (booting) return null;
  return (
    <>
      <Nav session={role} go={setView} onSignOut={signOut} />
      {session ? <Console key={role} role={role} name={session.name} data={data} error={error} onDecide={decide} onRefresh={() => refresh(role)} />
        : view === "login" ? <Login onLogin={login} notice={notice} />
        : <><Hero go={setView} /><Pipeline /><RiskScale /><Footer /></>}
    </>
  );
}