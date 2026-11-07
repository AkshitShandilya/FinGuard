import { useCallback, useEffect, useState } from "react";
import Nav from "./components/Nav";
import Hero from "./components/Hero";
import Pipeline from "./components/Pipeline";
import RiskScale from "./components/RiskScale";
import Footer from "./components/Footer";
import Login from "./components/Login";
import Console from "./components/Console";
import { api } from "./lib/api";

export default function App() {
  const [view, setView] = useState("site");
  const [role, setRole] = useState(null);
  const [data, setData] = useState({ cases: [], audit: [], mine: [] });
  const [error, setError] = useState(null);

  const refresh = useCallback(async (r) => {
    try {
      if (r === "customer") setData({ cases: [], audit: [], mine: await api.mine(r) });
      else {
        const [cases, audit] = await Promise.all([api.cases(r), api.audit(r)]);
        setData({ cases, audit, mine: [] });
      }
      setError(null);
    } catch (e) { setError(e.message); }
  }, []);

  useEffect(() => { if (role) refresh(role); }, [role, refresh]);

  const decide = async (c, label) => {
    try { await api.decide(role, c.id, label); await refresh(role); }
    catch (e) { setError(e.message); }
  };
  const signOut = () => { setRole(null); setView("site"); setError(null); };

  return (
    <>
      <Nav session={role} go={setView} onSignOut={signOut} />
      {role ? <Console key={role} role={role} data={data} error={error} onDecide={decide} onRefresh={() => refresh(role)} />
        : view === "login" ? <Login onLogin={(r) => { setRole(r); setView("console"); }} />
        : <><Hero go={setView} /><Pipeline /><RiskScale /><Footer /></>}
    </>
  );
}