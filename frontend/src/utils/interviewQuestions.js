/**
 * AI Interview Question Synthesis Engine
 * Generates tailored, multi-dimensional technical, architectural,
 * gap-probing, incident forensics, and behavioral interview kits.
 */

function cleanSnippet(snippet) {
  if (!snippet) return "";
  let clean = snippet.trim();
  if (clean.endsWith("...")) clean = clean.slice(0, -3).trim();
  if (clean.endsWith("... ?")) clean = clean.slice(0, -5).trim();
  if (clean.endsWith("?")) clean = clean.slice(0, -1).trim();
  return clean;
}

export function generateComprehensiveQuestions(candidate, activeRole = {}) {
  if (!candidate) return [];

  const roleTitle = activeRole.title || candidate.title || "Software Engineer";
  const matched = candidate.matchedSkills || [];
  const missing = candidate.missingSkills || [];
  const primarySkill = matched[0] || "Python";
  const secondarySkill = matched[1] || matched[0] || "cloud architecture";
  const missingSkill = missing[0] || null;
  const rawSnippet = cleanSnippet(candidate.evidenceSnippet || "");

  const questions = [];

  // 1. Technical Verification (Based on Resume Evidence / Projects)
  const baseQ1 = candidate.interviewQuestions?.[0]?.q;
  const baseLookFor1 = candidate.interviewQuestions?.[0]?.lookFor;

  if (baseQ1 && baseQ1.length > 25) {
    questions.push({
      id: "q-tech-verify",
      type: "Technical Verification",
      badgeColor: "indigo",
      q: baseQ1,
      lookFor: baseLookFor1 || "Architecture clarity, verifiable metrics, and production tradeoffs."
    });
  } else if (rawSnippet) {
    questions.push({
      id: "q-tech-verify",
      type: "Technical Verification",
      badgeColor: "indigo",
      q: `Can you walk us through your implementation details and engineering decisions regarding: "${rawSnippet}"?`,
      lookFor: "Clarity on architecture, latency/throughput constraints, and verifiable production metrics."
    });
  } else {
    questions.push({
      id: "q-tech-verify",
      type: "Technical Verification",
      badgeColor: "indigo",
      q: `How have you leveraged ${primarySkill} in your most challenging production deployment, and what specific metrics measured success?`,
      lookFor: "Evidence of concrete business impact, profiling methodology, and measurable performance improvements."
    });
  }

  // 2. System Architecture & High-Scale Design
  const titleLower = (candidate.title || "").toLowerCase();
  if (titleLower.includes("devops") || titleLower.includes("cloud") || titleLower.includes("sre")) {
    questions.push({
      id: "q-arch-scale",
      type: "Architecture & Scalability",
      badgeColor: "sky",
      q: `In a multi-region deployment running on ${primarySkill}, how do you architect zero-downtime canary rollouts and automated rollback triggers during critical failure states?`,
      lookFor: "Understanding of traffic splitting, blue/green strategies, Prometheus error-budget thresholds, and state synchronization."
    });
  } else if (titleLower.includes("ml") || titleLower.includes("machine learning") || titleLower.includes("ai")) {
    questions.push({
      id: "q-arch-scale",
      type: "Architecture & Scalability",
      badgeColor: "sky",
      q: `When scaling model inference under high concurrent QPS, how do you balance batching latency vs throughput, and what strategies do you use for model quantization or caching?`,
      lookFor: "Knowledge of dynamic batching (Triton/TorchServe), ONNX/TensorRT optimization, GPU memory bounds, and p95/p99 latency management."
    });
  } else if (titleLower.includes("data") || titleLower.includes("distributed")) {
    questions.push({
      id: "q-arch-scale",
      type: "Architecture & Scalability",
      badgeColor: "sky",
      q: `How do you handle distributed partition skew and state rebalancing when processing multi-terabyte streaming pipelines under high throughput?`,
      lookFor: "Partition key strategies, consumer group lag mitigation, watermark handling, and exactly-once processing guarantees."
    });
  } else {
    questions.push({
      id: "q-arch-scale",
      type: "Architecture & Scalability",
      badgeColor: "sky",
      q: `How do you structure microservices communication between asynchronous workers and synchronous APIs to prevent cascading failures under heavy traffic?`,
      lookFor: "Circuit breakers, backpressure management, idempotent endpoints, and message queue dead-letter routing."
    });
  }

  // 3. Skill Gap Probing OR Advanced Specialization
  if (missingSkill) {
    questions.push({
      id: "q-gap-probe",
      type: "Skill Gap Probing",
      badgeColor: "amber",
      q: `The ${roleTitle} role heavily leverages ${missingSkill}, which is not explicitly highlighted on your resume. How do your strong competencies in ${primarySkill} translate, and what is your 30-day onboarding strategy for ${missingSkill}?`,
      lookFor: `Fast conceptual transfer from ${primarySkill} to ${missingSkill}, proactive learning mindset, and practical toy/side project readiness.`
    });
  } else {
    questions.push({
      id: "q-gap-probe",
      type: "Advanced Domain Mastery",
      badgeColor: "amber",
      q: `You demonstrate complete coverage of the required skills including ${primarySkill} and ${secondarySkill}. What is an obscure edge case or runtime quirk you diagnosed that standard documentation overlooks?`,
      lookFor: "Deep mastery of underlying runtime internals, memory layout, GC/concurrency traps, and battle-tested troubleshooting."
    });
  }

  // 4. Incident Forensics & Production Debugging
  questions.push({
    id: "q-incident-debug",
    type: "Incident Forensics",
    badgeColor: "rose",
    q: `Describe the most severe production outage or data-corruption defect you directly investigated. How did you isolate root cause under pressure, and what preventative telemetry did you install afterwards?`,
    lookFor: "Structured triage methodology (logs, distributed traces, metrics), composure under fire, blameless post-mortem ownership, and CI/CD regression guardrails."
  });

  // 5. Behavioral & Engineering Collaboration
  questions.push({
    id: "q-culture-leadership",
    type: "Behavioral & Collaboration",
    badgeColor: "emerald",
    q: `Can you share a situation where you had a strong technical disagreement with a peer or tech lead over architecture design? How did you present your trade-offs and reach a collaborative consensus?`,
    lookFor: "Constructive communication, openness to feedback, data-driven RFC proposals, and prioritizing team velocity over personal ego."
  });

  return questions;
}
