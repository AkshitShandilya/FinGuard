const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const CUSTOMER_NAME = "R. Mehta"; // placeholder until the JWT carries the user

async function call(path, role, opts = {}) {
  let res;
  try {
    res = await fetch(BASE + path, {
      ...opts,
      headers: { "Content-Type": "application/json", "x-role": role, ...(opts.headers || {}) },
    });
  } catch {
    throw new Error("Can't reach the backend. Is uvicorn running on port 8000?");
  }
  if (!res.ok) {
    const d = await res.json().catch(() => ({}));
    throw new Error(typeof d.detail === "string" ? d.detail : `Request failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  meta: (role) => call("/meta", role),
  cases: (role) => call("/cases", role),
  audit: (role) => call("/audit", role),
  mine: (role) => call("/my-cases", role, { headers: { "x-user": CUSTOMER_NAME } }),
  score: (role, body) => call("/score", role, { method: "POST", body: JSON.stringify(body) }),
  pay: (role, body) => call("/transactions", role, { method: "POST", body: JSON.stringify(body), headers: { "x-user": CUSTOMER_NAME } }),
  model: (role) => call("/model", role),
  retrain: (role) => call("/retrain", role, { method: "POST" }),
  simulate: (role) => call("/demo/new-pattern", role, { method: "POST" }),
  decide: (role, id, decision) => call("/decision", role, { method: "POST", body: JSON.stringify({ case_id: id, decision }) }),
};