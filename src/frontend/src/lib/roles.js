// Mirrors the use-case diagram. Swap for the role claim inside the JWT later.
export const ROLES = {
  customer: { label: "Customer", blurb: "Make payments and follow your own alerts", tabs: ["activity", "pay"], decide: false },
  analyst: { label: "Fraud Analyst", blurb: "Review alerts and record decisions", tabs: ["queue", "score", "audit"], decide: true },
  risk: { label: "Risk Manager", blurb: "Risk analytics and thresholds (read only)", tabs: ["queue", "score", "audit", "model"], decide: false },
  admin: { label: "Administrator", blurb: "Users, rules, models and audit trail", tabs: ["queue", "audit", "model"], decide: false, retrain: true },
};
export const TAB_LABELS = { activity: "My activity", pay: "Make a payment", queue: "Case queue", score: "Score tool", audit: "Audit log", model: "Model" };