const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const KEY = "finguard_token";

// The backend reads the role from the signed token, so the `role` arguments below are ignored.
// They stay in the signatures so existing components keep working unchanged.
let onExpired = () => {};
export const setExpiredHandler = (fn) => { onExpired = fn; };
export const getToken = () => sessionStorage.getItem(KEY);
export const setToken = (t) => (t ? sessionStorage.setItem(KEY, t) : sessionStorage.removeItem(KEY));

async function call(path, opts = {}) {
  const token = getToken();
  let res;
  try {
    res = await fetch(BASE + path, {
      ...opts,
      headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(opts.headers || {}) },
    });
  } catch {
    throw new Error("Can't reach the backend. Is uvicorn running on port 8000?");
  }
  if (res.status === 401 && token) { setToken(null); onExpired(); }  // token expired or invalid
  if (!res.ok) {
    const d = await res.json().catch(() => ({}));
    throw new Error(typeof d.detail === "string" ? d.detail : `Request failed (${res.status})`);
  }
  return res.json();
}

const post = (path, body) => call(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export const api = {
  login: (username, password) => post("/auth/login", { username, password }),
  me: () => call("/auth/me"),
  meta: () => call("/meta"),
  cases: () => call("/cases"),
  audit: () => call("/audit"),
  mine: () => call("/my-cases"),
  model: () => call("/model"),
  score: (_role, body) => post("/score", body),
  pay: (_role, body) => post("/transactions", body),
  decide: (_role, id, decision) => post("/decision", { case_id: id, decision }),
  retrain: () => post("/retrain"),
  simulate: () => post("/demo/new-pattern"),
};