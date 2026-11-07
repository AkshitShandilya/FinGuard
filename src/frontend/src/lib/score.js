export const TIERS = [
  { key: "low", name: "Low", range: "0–30", max: 30, color: "#34c759", action: "Approve automatically." },
  { key: "medium", name: "Medium", range: "31–60", max: 60, color: "#ff9f0a", action: "Verify with the customer and keep monitoring." },
  { key: "high", name: "High", range: "61–80", max: 80, color: "#ff6a2b", action: "Hold the transaction and alert an analyst." },
  { key: "critical", name: "Critical", range: "81–100", max: 100, color: "#ff3b30", action: "Block and open an investigation case." },
];

export const WEIGHTS = [
  { k: "ml", label: "ML model", w: 0.5, color: "#f5f5f7" },
  { k: "rules", label: "Rules", w: 0.2, color: "#ff3b30" },
  { k: "behavior", label: "Behavior", w: 0.15, color: "#ff9f0a" },
  { k: "device", label: "Device", w: 0.1, color: "#34c759" },
  { k: "geo", label: "Geography", w: 0.05, color: "#86868b" },
];

const clamp = (n) => Math.max(0, Math.min(100, n));
export const tierOf = (s) => TIERS.find((t) => s <= t.max);

// Local stand-in for POST /score. Swap for a fetch() to the FastAPI backend later.
export function computeRisk({ amount, velocity, newDevice, oddLocation }) {
  const amt = clamp(((amount - 10000) / 90000) * 100);
  const vel = clamp((velocity - 1) * 25);
  const dev = newDevice ? 100 : 5;
  const geo = oddLocation ? 100 : 5;
  const s = {
    ml: 0.45 * amt + 0.2 * vel + 0.2 * dev + 0.15 * geo,
    rules: clamp((amount > 50000 ? 40 : 0) + (velocity >= 4 ? 30 : 0) + (newDevice ? 15 : 0) + (oddLocation ? 15 : 0)),
    behavior: 0.5 * amt + 0.5 * vel,
    device: dev,
    geo,
  };
  const parts = WEIGHTS.map((w) => ({ label: w.label, points: w.w * s[w.k] }));
  const score = Math.round(parts.reduce((a, p) => a + p.points, 0));
  const probability = Math.round(100 / (1 + Math.exp(-(score - 55) / 11)));
  return { score, probability, tier: tierOf(score), parts };
}