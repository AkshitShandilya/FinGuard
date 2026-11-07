export default function Nav({ session, go, onSignOut }) {
  return (
    <header className="nav"><div className="wrap">
      <b onClick={() => go("site")}>FinGuard</b>
      {!session && <nav><a href="#how" onClick={() => go("site")}>How it works</a><a href="#tiers" onClick={() => go("site")}>Risk tiers</a></nav>}
      {session ? <button className="pill" onClick={onSignOut}>Sign out</button> : <button className="pill" onClick={() => go("login")}>Sign in</button>}
    </div></header>
  );
}