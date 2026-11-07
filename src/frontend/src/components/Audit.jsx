export default function Audit({ audit }) {
  return (
    <div className="panel">{audit.length === 0 ? <p className="mu">No decisions recorded yet.</p> : (
      <table className="tbl"><thead><tr><th>Time</th><th>Case</th><th>Decision</th><th>By</th></tr></thead><tbody>
        {audit.map((a) => <tr key={a.id}><td>{a.at.replace("T", " ")}</td><td>{a.case_id}</td><td>{a.decision}</td><td>{a.by_role}</td></tr>)}
      </tbody></table>)}</div>
  );
}