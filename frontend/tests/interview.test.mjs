import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { loadPool, interview, role } from "./helpers.mjs";

const { buildInterviewKit, generateComprehensiveQuestions, BADGE_CLASSES } = interview;
const pools = { core12: loadPool("core12"), benchmark50: loadPool("benchmark50"), benchmark100: loadPool("benchmark100") };
const everyone = Object.values(pools).flat();

describe("interview kit", () => {
  it("gives every one of the 162 candidates a tailored kit of 15 to 30 questions", () => {
    assert.equal(everyone.length, 162);
    for (const c of everyone) {
      const kit = buildInterviewKit(c, role);
      assert.ok(kit.length >= 15 && kit.length <= 30, `${c.id} got ${kit.length} questions`);
    }
  });

  it("averages about twenty questions per candidate (the stored data had one)", () => {
    const mean = everyone.reduce((s, c) => s + buildInterviewKit(c, role).length, 0) / everyone.length;
    assert.ok(mean >= 19 && mean <= 24, `mean was ${mean.toFixed(1)}`);
  });

  it("never repeats a question or an id, and never prints broken values", () => {
    for (const c of everyone) {
      const kit = buildInterviewKit(c, role);
      assert.equal(new Set(kit.map((q) => q.id)).size, kit.length, `${c.id}: duplicate ids`);
      assert.equal(new Set(kit.map((q) => q.q)).size, kit.length, `${c.id}: duplicate questions`);
      for (const q of kit) {
        assert.ok(q.q && q.lookFor, `${c.id}: empty question or rubric`);
        assert.doesNotMatch(q.q + q.lookFor, /undefined|\[object/, `${c.id}: broken text`);
        assert.ok(BADGE_CLASSES[q.badgeColor], `${c.id}: unknown badge ${q.badgeColor}`);
      }
    }
  });

  it("is deterministic: the same candidate always gets the same kit", () => {
    for (const c of pools.benchmark50.slice(0, 10)) {
      assert.deepEqual(buildInterviewKit(c, role), buildInterviewKit(c, role));
    }
  });

  it("keeps the question already stored on the candidate", () => {
    const c = pools.benchmark50[0];
    const stored = c.interviewQuestions[0].q;
    assert.ok(buildInterviewKit(c, role).some((q) => q.q === stored));
  });

  it("asks about the candidate's own red flags and GitHub risk", () => {
    const flagged = everyone.find((c) => c.redFlags.some((f) => String(f).includes("SKILL_STUFFING")));
    assert.ok(flagged, "test data should contain a skill-stuffing candidate");
    const kit = buildInterviewKit(flagged, role);
    assert.ok(kit.some((q) => q.type === "Red-Flag Verification" && /listed skills|two of/i.test(q.q)));

    const risky = everyone.find((c) => c.github?.risk === "HIGH");
    assert.ok(buildInterviewKit(risky, role).some((q) => /GitHub review rated the profile HIGH risk/.test(q.q)));
  });

  it("uses role-family questions: a DevOps profile gets Kubernetes-style questions, an ML profile does not", () => {
    const devops = everyone.find((c) => /devops|site reliability/i.test(c.title));
    const ml = everyone.find((c) => /machine learning/i.test(c.title));
    assert.ok(buildInterviewKit(devops, role).some((q) => /Kubernetes|Terraform|SLO/.test(q.q)));
    assert.ok(!buildInterviewKit(ml, role).some((q) => /Terraform state|SLOs/.test(q.q)));
  });

  it("handles missing data without throwing or printing undefined", () => {
    assert.deepEqual(buildInterviewKit(null), []);
    assert.deepEqual(generateComprehensiveQuestions(undefined), []);
    const bare = generateComprehensiveQuestions({ name: "Bare" });
    assert.ok(bare.length >= 10);
    assert.ok(bare.every((q) => !/undefined|\[object/.test(q.q)));
  });
});
