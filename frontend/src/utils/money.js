/** Money is shown in Indian rupees only (annual, in lakhs per annum). */

/** "INR 35 - 42 LPA" for a candidate or role object, or "n/a" when the band is unknown. */
const hasBand = (x) => Boolean(x) && /\d/.test(String(x.salaryInr || ""));

export const inr = (x) => (hasBand(x) ? `INR ${x.salaryInr}` : "n/a");

const USD_RANGE = /\$\s?[\d,.]+\s?k?\s*(?:-|\u2013|to)\s*\$?\s?[\d,.]+\s?k?/gi;

/**
 * Returns the candidate with its compensation band expressed in INR only. Stored candidates (including the ones
 * already in the database) still carry a USD range, so it is replaced here, in one place, when a pool is loaded.
 */
export function inrOnly(c) {
  if (!c || typeof c !== "object") return c;
  const label = inr(c);
  const out = { ...c, salaryRange: label };
  // "Senior" (and "Staff") are kept only for candidates with 5 or more years of experience.
  const years = Number(c.experienceYears);
  if (Number.isFinite(years) && years < 5) {
    const plain = (t) => (typeof t === "string" ? t.replace(/\b(?:Senior\s+Staff|Senior|Staff)\s+/gi, "") : t);
    out.title = plain(c.title);
    out.level = plain(c.level);
  }
  const fb = c.council?.seniorityComp?.feedback;
  if (hasBand(c) && typeof fb === "string") {
    out.council = { ...c.council, seniorityComp: { ...c.council.seniorityComp, feedback: fb.replace(USD_RANGE, label) } };
  }
  return out;
}

export const inrOnlyPool = (pool) => (Array.isArray(pool) ? pool.map(inrOnly) : pool);
