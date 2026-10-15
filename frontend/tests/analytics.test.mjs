import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import path from "node:path";
import { loadPool, role } from "./helpers.mjs";

const a = await import(pathToFileURL(path.resolve(import.meta.dirname, "..", "src", "utils", "analytics.js")).href);
const pool12 = loadPool("core12");
const pool100 = loadPool("benchmark100");

describe("recruiter analytics: numbers are computed from the loaded pool", () => {
  it("counts the verdicts and the shortlist of the 12-resume pool", () => {
    const s = a.cohortStats(pool12);
    assert.deepEqual(s.counts, { STRONG_HIRE: 2, LEAN_HIRE: 3, REJECT: 7 });
    assert.equal(s.n, 12);
    assert.equal(s.shortlist, 5);
    assert.equal(s.shortlistRate, 41.7);
    assert.equal(s.flagged, 10);
    assert.equal(s.flagRate, 83.3);
  });

  it("changes when another pool is loaded", () => {
    const s = a.cohortStats(pool100);
    assert.equal(s.n, 100);
    assert.equal(s.counts.STRONG_HIRE + s.counts.LEAN_HIRE + s.counts.REJECT, 100);
    assert.notEqual(s.shortlistRate, a.cohortStats(pool12).shortlistRate);
  });

  it("builds a six-axis spider web with values between 0 and 100 for every group", () => {
    assert.equal(a.RADAR_AXES.length, 6);
    for (const v of ["ALL", ...a.VERDICTS]) {
      const values = a.radarValues(a.filterCohort(pool12, v));
      assert.equal(values.length, 6);
      values.forEach((x) => assert.ok(x >= 0 && x <= 100, `${v}: ${x}`));
    }
    const strong = a.radarValues(a.filterCohort(pool12, "STRONG_HIRE"));
    const reject = a.radarValues(a.filterCohort(pool12, "REJECT"));
    assert.ok(strong[0] > reject[0], "strong hires must score higher on skill match than rejects");
  });

  it("puts every candidate in exactly one histogram bin", () => {
    const bins = a.histogram(pool100);
    assert.equal(bins.length, 10);
    assert.equal(bins.reduce((n, b) => n + b.total, 0), 100);
    bins.forEach((b) => assert.equal(b.total, b.counts.STRONG_HIRE + b.counts.LEAN_HIRE + b.counts.REJECT));
  });

  it("measures the coverage of the skills that the role asks for", () => {
    const cov = a.skillCoverage(pool12, role);
    assert.equal(cov.length, role.skills.length);
    cov.forEach((r) => assert.ok(r.pct >= 0 && r.pct <= 100));
    for (let i = 1; i < cov.length; i++) assert.ok(cov[i - 1].count >= cov[i].count, "sorted by coverage");
  });

  it("lists the most frequent red flags first", () => {
    const flags = a.flagFrequency(pool12);
    assert.equal(flags[0].code, "REQUIRED_SKILLS_MISSING");
    assert.equal(flags[0].count, 10);
    for (let i = 1; i < flags.length; i++) assert.ok(flags[i - 1].count >= flags[i].count);
  });

  it("returns one scatter point per candidate and copes with an empty pool", () => {
    assert.equal(a.scatterPoints(pool12).length, 12);
    const empty = a.cohortStats([]);
    assert.equal(empty.n, 0);
    assert.equal(empty.shortlistRate, 0);
    assert.deepEqual(a.radarValues([]), [0, 0, 0, 0, 0, 0]);
  });
});
