import { inr } from "./money";
/**
 * AI Interview Question Synthesis Engine
 * Builds a tailored interview kit for one candidate: resume verification, role-family system design and
 * hands-on exercises, skill deep-dives, red-flag and GitHub-risk probes, incident forensics, behavioral
 * and logistics questions. Pure and deterministic: the same candidate always gets the same kit.
 */

function cleanSnippet(snippet) {
  if (!snippet) return "";
  let clean = snippet.trim();
  if (clean.endsWith("...")) clean = clean.slice(0, -3).trim();
  if (clean.endsWith("... ?")) clean = clean.slice(0, -5).trim();
  if (clean.endsWith("?")) clean = clean.slice(0, -1).trim();
  return clean;
}

// Stable 32-bit hash so each candidate gets a consistent (but different) selection of rotating questions.
function hashString(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function pickRotating(items, count, seed) {
  const start = hashString(seed) % items.length;
  return Array.from({ length: Math.min(count, items.length) }, (_, i) => items[(start + i) % items.length]);
}

/* -------------------------------------------------------------------------------------------- */
/* Categories (type -> badge colour). The classes are written out in full so Tailwind can see them.  */
/* -------------------------------------------------------------------------------------------- */
export const BADGE_CLASSES = {
  indigo: "bg-indigo-50 text-indigo-700 border-indigo-200",
  sky: "bg-sky-50 text-sky-700 border-sky-200",
  amber: "bg-amber-50 text-amber-800 border-amber-200",
  rose: "bg-rose-50 text-rose-700 border-rose-200",
  emerald: "bg-emerald-50 text-emerald-700 border-emerald-200",
  violet: "bg-violet-50 text-violet-700 border-violet-200",
  teal: "bg-teal-50 text-teal-700 border-teal-200",
  slate: "bg-slate-100 text-slate-700 border-slate-200",
};

const TYPES = {
  verify: { type: "Technical Verification", badgeColor: "indigo" },
  arch: { type: "Architecture & Scalability", badgeColor: "sky" },
  gap: { type: "Skill Gap Probing", badgeColor: "amber" },
  mastery: { type: "Advanced Domain Mastery", badgeColor: "amber" },
  skill: { type: "Skill Deep-Dive", badgeColor: "violet" },
  design: { type: "System Design", badgeColor: "sky" },
  exercise: { type: "Hands-on Exercise", badgeColor: "teal" },
  quality: { type: "Quality & Security", badgeColor: "teal" },
  flag: { type: "Red-Flag Verification", badgeColor: "rose" },
  incident: { type: "Incident Forensics", badgeColor: "rose" },
  behavior: { type: "Behavioral & Collaboration", badgeColor: "emerald" },
  leadership: { type: "Ownership & Leadership", badgeColor: "emerald" },
  logistics: { type: "Motivation & Logistics", badgeColor: "slate" },
};

/* -------------------------------------------------------------------------------------------- */
/* Role families                                                                                  */
/* -------------------------------------------------------------------------------------------- */
const FAMILY_RULES = [
  ["safety", /safety|governance|alignment|auditor/],
  ["bi", /business intelligence|\bbi\b|analyst/],
  ["devops", /devops|\bsre\b|site reliability|cloud/],
  ["data", /data platform|distributed|data engineer|big data/],
  ["backend", /backend|microservice|\bapi\b/],
  ["fullstack", /full.?stack/],
  ["ml", /machine learning|\bml\b|\bai\b|deep learning|data scien/],
];

function familyOf(...titles) {
  for (const title of titles) {
    const t = (title || "").toLowerCase();
    for (const [family, re] of FAMILY_RULES) if (re.test(t)) return family;
  }
  return "general";
}

const FAMILY = {
  ml: {
    arch: {
      q: "When scaling model inference under high concurrent QPS, how do you balance batching latency against throughput, and what do you use for quantization or caching?",
      lookFor: "Dynamic batching (Triton/TorchServe), ONNX/TensorRT optimization, GPU memory limits, and p95/p99 latency management.",
    },
    design: [
      {
        q: "Design a real-time recommendation or ranking service that must refresh its model daily without downtime. Walk through training, validation, rollout and rollback.",
        lookFor: "Feature store consistency, shadow and canary deployment, offline versus online metrics, and a defined rollback trigger.",
      },
      {
        q: "How would you detect and respond to data drift and silent model degradation in production?",
        lookFor: "Input and prediction drift monitoring, delayed-label evaluation, alert thresholds, retraining triggers, and ownership of the on-call response.",
      },
    ],
    exercise: {
      q: "Live exercise: you have a classifier with 0.94 AUC offline that performs poorly in production. List, in order, what you would check and how you would confirm each hypothesis.",
      lookFor: "Train/serve skew, label leakage, population shift, threshold and calibration issues, and a disciplined, evidence-first debugging order.",
    },
    quality: [
      {
        q: "How do you test an ML pipeline beyond unit tests: data validation, model regression tests, and reproducibility?",
        lookFor: "Schema and distribution checks, golden datasets, seeded and versioned training runs, and CI gates on evaluation metrics.",
      },
      {
        q: "What privacy, bias and security risks do you review before shipping a model that scores people or sensitive content?",
        lookFor: "PII handling, fairness metrics across groups, adversarial inputs, model and data access control, and documented sign-off.",
      },
    ],
  },
  devops: {
    arch: {
      q: "In a multi-region deployment, how do you architect zero-downtime canary rollouts and automated rollback triggers during a critical failure?",
      lookFor: "Traffic splitting, blue/green strategy, error-budget thresholds, and state or schema synchronization across regions.",
    },
    design: [
      {
        q: "Design the CI/CD and infrastructure workflow for 40 microservices owned by 10 teams, with strong guardrails but fast delivery.",
        lookFor: "GitOps, reusable pipeline templates, environment promotion, policy-as-code, secrets handling, and developer self-service.",
      },
      {
        q: "Define SLOs and an alerting strategy for a customer-facing API. How do you avoid alert fatigue while still catching real incidents?",
        lookFor: "SLIs tied to user experience, burn-rate alerts, runbooks linked to alerts, and a regular alert-quality review.",
      },
    ],
    exercise: {
      q: "Live exercise: pods in a production Kubernetes cluster are restarting every few minutes and latency is climbing. Describe your exact diagnostic steps and commands.",
      lookFor: "Events, logs and previous container logs, resource limits and OOMKills, probes, node pressure, recent deploys, and a safe mitigation before root cause.",
    },
    quality: [
      {
        q: "How do you manage infrastructure drift and protect Terraform state, secrets and production credentials?",
        lookFor: "Remote locked state, least-privilege roles, secret managers, drift detection, and reviewed plans before apply.",
      },
      {
        q: "Describe your disaster recovery plan and how you actually test it. What are your RTO and RPO targets and how were they chosen?",
        lookFor: "Regular game days and restore tests, backup verification, documented failover, and targets that follow business impact.",
      },
    ],
  },
  data: {
    arch: {
      q: "How do you handle partition skew and state rebalancing when processing multi-terabyte streaming pipelines under high throughput?",
      lookFor: "Partition key strategy, consumer-group lag mitigation, watermark handling, and exactly-once processing guarantees.",
    },
    design: [
      {
        q: "Design a lakehouse that serves both daily batch reports and sub-minute dashboards from the same events. Where do you draw the batch and streaming boundary?",
        lookFor: "Lambda versus kappa trade-offs, table formats and compaction, late and out-of-order data, and cost-aware storage tiers.",
      },
      {
        q: "How would you design data contracts and lineage so a schema change in one team does not break ten downstream consumers?",
        lookFor: "Versioned schemas, compatibility checks in CI, ownership, lineage tooling, and a deprecation process.",
      },
    ],
    exercise: {
      q: "Live exercise: a nightly Spark job that used to take 40 minutes now takes 4 hours. How do you find the cause and what would you change?",
      lookFor: "Spark UI stages, data skew, shuffle size, small files, join strategy, caching, and a before/after measurement.",
    },
    quality: [
      {
        q: "How do you test and monitor data quality in pipelines: freshness, volume, duplicates, and silent schema changes?",
        lookFor: "Automated expectations (dbt tests, Great Expectations), anomaly alerts, quarantine of bad records, and incident ownership.",
      },
      {
        q: "How do you handle PII, retention and access control across a shared warehouse?",
        lookFor: "Column-level masking, role-based access, retention policies, audit logs, and GDPR-style deletion workflows.",
      },
    ],
  },
  backend: {
    arch: {
      q: "How do you structure communication between asynchronous workers and synchronous APIs so one slow dependency does not cause cascading failures?",
      lookFor: "Circuit breakers, backpressure, idempotent endpoints, timeouts and retries with jitter, and dead-letter queues.",
    },
    design: [
      {
        q: "Design an API for a payments-style workflow where requests can be retried and must never be processed twice.",
        lookFor: "Idempotency keys, transactional outbox, state machine design, exactly-once effects versus at-least-once delivery, and reconciliation.",
      },
      {
        q: "How would you split a growing monolith into services? How do you decide the boundaries and handle shared data?",
        lookFor: "Domain boundaries, strangler pattern, data ownership per service, contract testing, and a realistic migration order.",
      },
    ],
    exercise: {
      q: "Live exercise: an endpoint returns in 80 ms in staging but 3 seconds in production under load. What do you investigate first, and how do you prove it?",
      lookFor: "N+1 queries, missing indexes, connection pool exhaustion, lock contention, profiling and tracing, and verifying the fix under load.",
    },
    quality: [
      {
        q: "What is your approach to API security: authentication, authorization, input validation and rate limiting?",
        lookFor: "OAuth/JWT pitfalls, object-level authorization checks, parameterized queries, rate limits, and secrets management.",
      },
      {
        q: "How do you test a service with many dependencies: unit, contract, integration and load tests, and what do you mock?",
        lookFor: "A test pyramid, contract tests, realistic fixtures, load-test baselines, and avoiding over-mocking.",
      },
    ],
  },
  fullstack: {
    arch: {
      q: "How do you structure a React and API application so that state, caching and loading or error handling stay predictable as the app grows?",
      lookFor: "Server versus client state separation, data-fetching libraries, error boundaries, optimistic updates, and bundle or route-level code splitting.",
    },
    design: [
      {
        q: "Design a chat or copilot feature backed by an LLM: streaming responses, conversation history, cost controls and failure handling.",
        lookFor: "Streaming transport (SSE/WebSocket), token and rate limits, retrieval or context management, timeouts and fallbacks, and abuse protection.",
      },
      {
        q: "How would you design authentication and session handling across a web frontend, an API and a mobile client?",
        lookFor: "Token storage trade-offs, refresh flow, CSRF/XSS defenses, logout and revocation, and least-privilege scopes.",
      },
    ],
    exercise: {
      q: "Live exercise: a page re-renders constantly and feels sluggish after a new feature. How do you find and fix the cause?",
      lookFor: "React profiler, unstable props and effects, memoization used with evidence, list virtualization, and measuring the result.",
    },
    quality: [
      {
        q: "How do you test a full-stack feature end to end, and what do you deliberately not test through the UI?",
        lookFor: "Component and API tests, a small stable end-to-end suite, test data strategy, and flaky-test discipline.",
      },
      {
        q: "Which web security issues do you check before releasing, and how do you handle user-supplied content and LLM output?",
        lookFor: "XSS and output encoding, CSRF, dependency scanning, prompt-injection awareness, and safe rendering of generated text.",
      },
    ],
  },
  bi: {
    arch: {
      q: "How do you design a metrics layer so that every dashboard uses the same definition of a core KPI?",
      lookFor: "A semantic or metrics layer, governed definitions, versioning, ownership, and reconciliation across tools.",
    },
    design: [
      {
        q: "Design an executive dashboard for revenue and retention. How do you choose metrics, grain and refresh cadence?",
        lookFor: "Decision-driven metrics, correct aggregation grain, cohort views, performance and refresh trade-offs, and clear definitions on the page.",
      },
      {
        q: "A KPI drops 15% overnight on the dashboard. How do you decide whether it is a real change or a data problem?",
        lookFor: "Checks of upstream freshness and volume, definition changes, segment breakdowns, and a communication plan while investigating.",
      },
    ],
    exercise: {
      q: "Live exercise: write the SQL (or describe it) to calculate month-over-month active users and a 30-day retention rate from an events table.",
      lookFor: "Correct grouping and window functions, handling of duplicates and time zones, and clear assumptions about definitions.",
    },
    quality: [
      {
        q: "How do you validate a report before sharing it with executives?",
        lookFor: "Reconciliation to source, sanity checks, peer review, documented definitions, and known limitations stated up front.",
      },
      {
        q: "How do you manage access to sensitive metrics and personal data in shared dashboards?",
        lookFor: "Row- and column-level security, aggregation thresholds, audit trails, and role-based sharing.",
      },
    ],
  },
  safety: {
    arch: {
      q: "How would you design an evaluation pipeline that continuously tests a deployed model for bias, harmful output and regressions?",
      lookFor: "Versioned eval suites, red-team prompts, automated gating, human review on borderline cases, and tracked metrics over time.",
    },
    design: [
      {
        q: "Design an audit process for an AI system that scores job candidates. What evidence do you collect and how do you report findings?",
        lookFor: "Fairness metrics across groups, documentation (model cards), data provenance, reproducible tests, and actionable remediation.",
      },
      {
        q: "How would you structure a red-teaming program for a new LLM feature before launch?",
        lookFor: "Threat modeling, diverse testers, severity rubrics, fixes verified by retest, and launch go/no-go criteria.",
      },
    ],
    exercise: {
      q: "Live exercise: a model approves loans at very different rates for two groups. How do you determine whether that is unlawful bias, and what do you recommend?",
      lookFor: "Choice of fairness definition and its trade-offs, confounders, statistical testing, legal context, and mitigation options with their cost.",
    },
    quality: [
      {
        q: "Which governance controls do you require before a high-risk AI system goes live?",
        lookFor: "Risk classification, human oversight, logging and traceability, incident response, and periodic re-audit.",
      },
      {
        q: "How do you handle disagreement when a product team wants to ship over your unresolved safety concern?",
        lookFor: "Clear risk communication, documented decisions, escalation path, and proposing a mitigated alternative rather than only blocking.",
      },
    ],
  },
  general: {
    arch: {
      q: "How do you design a service so it degrades gracefully when a dependency is slow or unavailable?",
      lookFor: "Timeouts, retries with backoff, circuit breakers, fallbacks, and clear user-facing behavior.",
    },
    design: [
      {
        q: "Design a system that ingests uploaded files, processes them asynchronously and reports progress to the user.",
        lookFor: "Queueing, idempotent workers, status tracking, failure handling, and scaling the workers independently.",
      },
      {
        q: "How would you make a slow, important report faster without changing the data model?",
        lookFor: "Profiling first, caching, pre-aggregation, query optimization, and measuring the improvement.",
      },
    ],
    exercise: {
      q: "Live exercise: a production job has started failing intermittently since last week. How do you narrow down the cause?",
      lookFor: "Timeline of changes, logs and metrics, reproducing the failure, bisecting, and a safe mitigation.",
    },
    quality: [
      {
        q: "How do you decide what to test and how much, given limited time?",
        lookFor: "Risk-based prioritization, a test pyramid, automation of regressions, and honest coverage metrics.",
      },
      {
        q: "What security basics do you apply to every service you ship?",
        lookFor: "Least privilege, secret handling, dependency updates, input validation, and logging without sensitive data.",
      },
    ],
  },
};

/* -------------------------------------------------------------------------------------------- */
/* Skill deep-dives (lower-case skill -> question). Unknown skills fall back to a template.          */
/* -------------------------------------------------------------------------------------------- */
const SKILL_BANK = {
  python: {
    q: "Python: explain a performance or memory problem you solved. How did you profile it, and what did the GIL, generators or async change?",
    lookFor: "Profiling tools, a measured before/after, understanding of the GIL and I/O versus CPU-bound work, and clean fixes over micro-tricks.",
  },
  pytorch: {
    q: "PyTorch: how do you debug a training run whose loss plateaus or becomes NaN?",
    lookFor: "Learning rate and initialization checks, gradient clipping, data and label sanity checks, mixed-precision pitfalls, and small-batch overfit tests.",
  },
  tensorflow: {
    q: "TensorFlow: when do you choose eager versus graph execution, and how do you serve a model from it in production?",
    lookFor: "tf.function tracing costs, SavedModel and TF Serving or alternatives, input pipelines with tf.data, and versioned deployments.",
  },
  "scikit-learn": {
    q: "scikit-learn: how do you build a pipeline that avoids data leakage between preprocessing, cross-validation and the final model?",
    lookFor: "Pipelines and ColumnTransformer, fitting transformers only on training folds, proper CV strategy, and metric choice for imbalanced data.",
  },
  "machine learning": {
    q: "How do you choose between a simple baseline and a complex model, and what evidence would make you move up in complexity?",
    lookFor: "Baselines first, error analysis, cost of complexity, metric and business alignment, and ablation evidence.",
  },
  "model evaluation": {
    q: "How do you evaluate a model when the classes are imbalanced and the cost of a false negative is high?",
    lookFor: "Precision/recall trade-offs, PR curves, threshold selection by cost, calibration, and evaluation on realistic slices.",
  },
  docker: {
    q: "Docker: how do you keep images small and secure, and what causes a container to behave differently from your laptop?",
    lookFor: "Multi-stage builds, non-root users, pinned base images, layer caching, environment and volume differences, and image scanning.",
  },
  kubernetes: {
    q: "Kubernetes: how do you set resource requests and limits, and what happens to your service when a node is drained?",
    lookFor: "QoS classes, HPA, PodDisruptionBudgets, readiness and liveness probes, and graceful termination handling.",
  },
  terraform: {
    q: "Terraform: how do you structure modules and state for several environments and teams without stepping on each other?",
    lookFor: "Remote state with locking, module versioning, workspaces or separate states, review of plans, and handling of drift and imports.",
  },
  aws: {
    q: "AWS: how do you design IAM and networking for a new production workload, and how do you control its cost?",
    lookFor: "Least-privilege roles, VPC and subnet design, security groups, tagging and budgets, and right-sizing with data.",
  },
  azure: {
    q: "Azure: how do you manage identity, secrets and networking for a production application, and keep costs visible?",
    lookFor: "Managed identities, Key Vault, private endpoints, cost management and tagging, and policy-based guardrails.",
  },
  gcp: {
    q: "GCP: which services would you pick for a streaming pipeline with a dashboard, and why those over the alternatives?",
    lookFor: "Pub/Sub, Dataflow, BigQuery trade-offs, IAM design, and cost and latency considerations.",
  },
  sql: {
    q: "SQL: how do you diagnose and fix a slow query, and when does an index make things worse?",
    lookFor: "EXPLAIN plans, selectivity, composite index order, write overhead, statistics, and rewriting versus indexing.",
  },
  postgresql: {
    q: "PostgreSQL: how do you handle a hot table with heavy writes and long-running queries (bloat, locking and vacuum)?",
    lookFor: "MVCC and bloat, autovacuum tuning, lock behavior, partitioning, connection pooling, and monitoring.",
  },
  redis: {
    q: "Redis: how do you decide what to cache, and how do you handle invalidation and a cache stampede?",
    lookFor: "TTL and key design, write-through versus cache-aside, request coalescing, eviction policies, and failure behavior when Redis is down.",
  },
  kafka: {
    q: "Kafka: how do you guarantee ordering and avoid duplicates, and what do you do when a consumer group falls far behind?",
    lookFor: "Partition keys, idempotent producers and consumers, offset management, lag monitoring, and scaling consumers.",
  },
  "apache spark": {
    q: "Spark: how do you recognise and fix data skew and an expensive shuffle?",
    lookFor: "Spark UI diagnosis, salting or broadcast joins, repartitioning, adaptive query execution, and file layout.",
  },
  snowflake: {
    q: "Snowflake: how do you control warehouse cost while keeping query performance acceptable?",
    lookFor: "Warehouse sizing and auto-suspend, clustering and pruning, result caching, resource monitors, and query profiling.",
  },
  fastapi: {
    q: "FastAPI: how do you handle blocking calls, dependency injection and validation in a high-traffic service?",
    lookFor: "Async versus sync endpoints, thread-pool pitfalls, Pydantic validation, dependency lifetimes, and background tasks versus a real queue.",
  },
  django: {
    q: "Django: how do you avoid N+1 queries and keep migrations safe on a large production table?",
    lookFor: "select_related and prefetch_related, query inspection, backwards-compatible migrations, and zero-downtime deploy steps.",
  },
  react: {
    q: "React: how do you decide where state lives, and how do you track down unnecessary re-renders?",
    lookFor: "Lifting state versus context versus a store, derived state, the profiler, memoization used sparingly, and effect hygiene.",
  },
  typescript: {
    q: "TypeScript: how do you type an API boundary so runtime data cannot silently break your types?",
    lookFor: "Runtime validation (zod or similar), narrowing, discriminated unions, avoiding any, and shared types between client and server.",
  },
  "next.js": {
    q: "Next.js: how do you choose between server rendering, static generation and client rendering for different pages?",
    lookFor: "Data freshness requirements, caching and revalidation, SEO needs, and server versus client component boundaries.",
  },
  golang: {
    q: "Go: how do you manage goroutines safely, and how do you diagnose a goroutine leak?",
    lookFor: "Contexts and cancellation, channel and mutex usage, the race detector, pprof, and bounded concurrency.",
  },
  grpc: {
    q: "gRPC: how do you evolve a protobuf schema without breaking clients, and how do you handle deadlines and retries?",
    lookFor: "Field numbering and compatibility rules, deadlines propagation, idempotent retries, and streaming trade-offs.",
  },
  microservices: {
    q: "Microservices: how do you handle a transaction that spans three services?",
    lookFor: "Sagas, outbox pattern, compensating actions, idempotency, and when a single service would have been simpler.",
  },
  "ci/cd": {
    q: "CI/CD: how do you make a 40-minute pipeline fast and reliable without lowering the quality bar?",
    lookFor: "Parallelization, caching, test selection, flaky-test policy, and staged gates with clear ownership.",
  },
  linux: {
    q: "Linux: a server is slow and the load average is high. Walk through the commands you use and how you interpret them.",
    lookFor: "top/htop, vmstat, iostat, CPU versus I/O wait, memory and swap, network checks, and isolating the offending process.",
  },
  git: {
    q: "Git: how do you recover from a bad merge or a force-push that overwrote a teammate's work?",
    lookFor: "Reflog, reverting versus resetting, communication with the team, and branch protection to prevent repeats.",
  },
  langchain: {
    q: "LangChain or agent frameworks: where have they helped you, and where did you decide to write the logic yourself?",
    lookFor: "Honest assessment of abstraction cost, debugging and observability, version churn, and retrieval and prompt evaluation practices.",
  },
  tableau: {
    q: "Tableau: how do you keep a heavy dashboard fast and its numbers trustworthy for different audiences?",
    lookFor: "Extracts versus live connections, LOD expressions, filter design, governed data sources, and documented definitions.",
  },
  "power bi": {
    q: "Power BI: how do you design the data model and DAX measures so reports stay fast and correct?",
    lookFor: "Star schema, measures versus calculated columns, context transition, incremental refresh, and row-level security.",
  },
  "red teaming": {
    q: "Red teaming: how do you design adversarial tests for an LLM, and how do you decide a finding is serious enough to block a release?",
    lookFor: "Threat model, jailbreak and injection classes, severity rubric, reproducible cases, and retest after the fix.",
  },
  "bias auditing": {
    q: "Bias auditing: which metrics do you use to compare outcomes across groups, and what are their limits?",
    lookFor: "Demographic parity versus equalized odds, small-sample issues, intersectionality, and the trade-offs between metrics.",
  },
  "ai safety": {
    q: "AI safety: what is a concrete risk you would raise about deploying an LLM in a customer-facing workflow, and what control would you add?",
    lookFor: "A specific, realistic risk, a proportionate control, monitoring after launch, and a clear escalation path.",
  },
};

function skillQuestion(skill, roleTitle) {
  const hit = SKILL_BANK[skill.toLowerCase()];
  if (hit) return hit;
  return {
    q: `${skill}: describe the hardest problem you solved with it. What did you try first, what failed, and how would you do it differently now?`,
    lookFor: `Hands-on depth in ${skill} for a ${roleTitle}: concrete trade-offs, mistakes owned, and measurable results.`,
  };
}

/* -------------------------------------------------------------------------------------------- */
/* Rotating behavioral / leadership / logistics prompts (a few are picked per candidate)             */
/* -------------------------------------------------------------------------------------------- */
const BEHAVIORAL = [
  {
    q: "Tell us about a strong technical disagreement with a peer or tech lead over architecture. How did you present the trade-offs and reach a decision?",
    lookFor: "Constructive communication, data-driven proposals, openness to being wrong, and prioritising the team's outcome over ego.",
  },
  {
    q: "Describe a project that failed or missed its goal. What was your part in it and what changed in how you work afterwards?",
    lookFor: "Ownership without blame-shifting, specific lessons, and a process change that stuck.",
  },
  {
    q: "Tell us about a time requirements were vague or kept changing. How did you create clarity and still deliver?",
    lookFor: "Asking the right questions, small verifiable increments, stakeholder alignment, and written assumptions.",
  },
  {
    q: "Describe a time you had to deliver under a tight deadline. What did you cut, what did you protect, and how did you communicate it?",
    lookFor: "Clear prioritisation, protecting quality and safety, honest communication about risk, and follow-up on the deferred work.",
  },
  {
    q: "How do you explain a complex technical trade-off to a non-technical stakeholder? Give a real example.",
    lookFor: "Plain language, outcome and risk focus, the use of examples or visuals, and checking understanding.",
  },
  {
    q: "Tell us about a time you received critical feedback that you initially disagreed with.",
    lookFor: "Listening before defending, separating fact from tone, acting on the valid part, and thanking the giver.",
  },
];

const LEADERSHIP = [
  {
    q: "How have you mentored a less experienced engineer, and how did you know it worked?",
    lookFor: "Specific coaching methods, growth in the mentee's independence, and balancing teaching with delivery.",
  },
  {
    q: "Describe a decision you drove that other people were hesitant about. How did you build alignment and what was the result?",
    lookFor: "Influence without authority, a written proposal or RFC, handling objections, and measuring the outcome.",
  },
  {
    q: "Tell us about something you owned end to end, from idea to production support. What did you learn about operating it?",
    lookFor: "Full lifecycle ownership, on-call or support experience, metrics after launch, and the follow-up improvements.",
  },
];

function logisticsQuestions(candidate, roleTitle) {
  return [
    {
      q: `What attracts you to this ${roleTitle} role specifically, and what would make you leave it in two years?`,
      lookFor: "A reasoned, role-specific motivation (not generic), realistic expectations, and growth goals that fit the team.",
    },
    {
      q: `Your profile suggests a band around ${
        inr(candidate) === "n/a" ? "the advertised range" : inr(candidate)
      }. What are your CTC expectations, notice period and any constraints on start date or location?`,
      lookFor: "Transparent expectations, flexibility, notice period and relocation or remote constraints, and any competing offers or deadlines.",
    },
  ];
}

/* -------------------------------------------------------------------------------------------- */
/* Red-flag and GitHub-risk probes                                                                  */
/* -------------------------------------------------------------------------------------------- */
function flagQuestions(candidate, matched) {
  const out = [];
  const flags = (candidate.redFlags || []).map((f) => (typeof f === "string" ? f : JSON.stringify(f))).join(" | ").toUpperCase();
  const topSkills = matched.slice(0, 3).join(", ") || "your listed skills";

  if (flags.includes("EXPERIENCE_DEFICIT") || flags.includes("LEVEL_MISMATCH")) {
    out.push({
      q: `Your resume shows ${candidate.experienceYears} years of experience for a role at this level. Which responsibilities have you already owned that a more senior engineer would normally own?`,
      lookFor: "Concrete examples of senior-scope work (design ownership, on-call, mentoring, cross-team decisions), not just years or titles.",
    });
  }
  if (flags.includes("UNVERIFIED_SKILL_CLAIMS") || flags.includes("SKILL_STUFFING")) {
    out.push({
      q: `Pick any two of ${topSkills} and walk us through a feature or system where you used them, including what you personally wrote.`,
      lookFor: "Fluent, specific detail (files, commands, trade-offs, bugs) rather than buzzwords. Probe follow-ups until you reach the edge of their experience.",
    });
  }
  if (flags.includes("NO_QUANTIFIED_IMPACT")) {
    out.push({
      q: "Your resume describes the work but few results. For your most significant project, what number changed (latency, cost, revenue, errors, time saved) and how was it measured?",
      lookFor: "A believable baseline and result, how it was measured, and an honest account of what the candidate versus the team contributed.",
    });
  }
  if (flags.includes("DATE_INCONSISTENCY")) {
    out.push({
      q: "Can you walk us through your career timeline in order, including any gaps or overlaps in dates, and what you were doing in each?",
      lookFor: "A coherent timeline, plausible explanations for gaps or overlaps, and consistency with the dates on the resume.",
    });
  }
  if (flags.includes("REQUIRED_SKILLS_MISSING")) {
    out.push({
      q: "Several skills the role requires do not appear on your resume. Which of them have you used in practice but not listed, and which are genuinely new to you?",
      lookFor: "Honesty about gaps, evidence for any unlisted skills, and a credible plan for the rest.",
    });
  }

  const gh = candidate.github;
  if (gh && (gh.risk === "HIGH" || gh.risk === "MEDIUM")) {
    out.push({
      q: `Our GitHub review rated the profile ${gh.risk} risk (${gh.authenticRepos ?? "?"} of ${gh.reposAnalyzed ?? "?"} analysed repositories look original). Walk us through one repository you wrote yourself, including its design decisions and your commit history.`,
      lookFor: "Clear authorship of the code, ability to explain design choices and tests, and a reasonable account of any forked or tutorial-derived repositories.",
    });
  }
  if (typeof candidate.atsScore === "number" && candidate.atsScore < 70) {
    out.push({
      q: "Parts of your resume were hard for our parser to read. Can you summarise your three most recent roles, the dates, and your main responsibility in each?",
      lookFor: "A consistent verbal summary that matches the document, and a quick check that nothing important is missing or misparsed.",
    });
  }
  return out;
}

/* -------------------------------------------------------------------------------------------- */
/* Public API                                                                                       */
/* -------------------------------------------------------------------------------------------- */
export function generateComprehensiveQuestions(candidate, activeRole = {}) {
  if (!candidate) return [];

  const roleTitle = activeRole.title || candidate.title || "Software Engineer";
  const family = familyOf(candidate.title, roleTitle);
  const bank = FAMILY[family] || FAMILY.general;
  const matched = candidate.matchedSkills || [];
  const missing = candidate.missingSkills || [];
  const primarySkill = matched[0] || "Python";
  const secondarySkill = matched[1] || matched[0] || "cloud architecture";
  const missingSkill = missing[0] || null;
  const rawSnippet = cleanSnippet(candidate.evidenceSnippet || "");
  const seed = String(candidate.id || candidate.name || "candidate");

  const questions = [];
  const seen = new Set();
  const add = (kind, q, lookFor, idHint) => {
    const text = (q || "").trim();
    if (!text || seen.has(text)) return;
    seen.add(text);
    const meta = TYPES[kind];
    questions.push({
      id: `q-${idHint || kind}-${questions.length + 1}`,
      type: meta.type,
      badgeColor: meta.badgeColor,
      q: text,
      lookFor,
    });
  };

  // 1. Technical verification from the resume evidence
  const stored = candidate.interviewQuestions?.[0];
  if (stored?.q && stored.q.length > 25) {
    add("verify", stored.q, stored.lookFor || "Architecture clarity, verifiable metrics, and production trade-offs.", "verify");
  } else if (rawSnippet) {
    add(
      "verify",
      `Walk us through the implementation details and engineering decisions behind: "${rawSnippet}".`,
      "Clarity on architecture, latency or throughput constraints, and verifiable production metrics.",
      "verify",
    );
  } else {
    add(
      "verify",
      `How have you used ${primarySkill} in your most challenging production deployment, and what metrics measured success?`,
      "Concrete business impact, profiling methodology, and measurable improvements.",
      "verify",
    );
  }
  if (rawSnippet && stored?.q && stored.q.length > 25) {
    add(
      "verify",
      `Follow-up on "${rawSnippet}": what was the hardest obstacle, what did you personally decide, and what would you change if you did it again?`,
      "Personal contribution versus team contribution, honest hindsight, and consistent detail with the resume.",
      "verify-followup",
    );
  }

  // 2. Architecture for the role family
  add("arch", bank.arch.q, bank.arch.lookFor);

  // 3. Skill gap or advanced mastery
  if (missingSkill) {
    add(
      "gap",
      `The ${roleTitle} role relies on ${missingSkill}, which is not clearly on your resume. How would your strength in ${primarySkill} transfer, and what is your 30-day plan to become productive in ${missingSkill}?`,
      `Fast conceptual transfer from ${primarySkill} to ${missingSkill}, a proactive learning habit, and a concrete practice project.`,
    );
  } else {
    add(
      "mastery",
      `You cover the required skills, including ${primarySkill} and ${secondarySkill}. What is an obscure edge case or runtime quirk you diagnosed that the documentation does not cover?`,
      "Depth in runtime internals, memory or concurrency traps, and battle-tested troubleshooting.",
    );
  }

  // 4. Skill deep-dives for up to three matched skills
  matched.slice(0, 3).forEach((skill) => {
    const s = skillQuestion(skill, roleTitle);
    add("skill", s.q, s.lookFor, `skill-${skill.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`);
  });

  // 5. Role-family system design and a hands-on exercise
  bank.design.forEach((d) => add("design", d.q, d.lookFor));
  add("exercise", bank.exercise.q, bank.exercise.lookFor);

  // 6. Quality, testing and security
  bank.quality.forEach((d) => add("quality", d.q, d.lookFor));

  // 7. Red flags and GitHub risk specific to this candidate
  flagQuestions(candidate, matched).forEach((f) => add("flag", f.q, f.lookFor));

  // 8. Incident forensics
  add(
    "incident",
    "Describe the most severe production outage or data-corruption defect you directly investigated. How did you isolate the root cause under pressure, and what did you add afterwards so it could not recur silently?",
    "Structured triage (logs, traces, metrics), composure, blameless post-mortem ownership, and regression guardrails.",
  );

  // 9. Behavioral and leadership (a stable, candidate-specific selection)
  pickRotating(BEHAVIORAL, 3, `${seed}:behavior`).forEach((b) => add("behavior", b.q, b.lookFor));
  pickRotating(LEADERSHIP, 1, `${seed}:leadership`).forEach((b) => add("leadership", b.q, b.lookFor));

  // 10. Motivation and logistics
  logisticsQuestions(candidate, roleTitle).forEach((l) => add("logistics", l.q, l.lookFor));

  return questions;
}

/**
 * Merge the questions stored on the candidate with the generated kit, dropping duplicates. Stored
 * questions keep their position so existing data is never lost.
 */
export function buildInterviewKit(candidate, activeRole = {}) {
  if (!candidate) return [];
  const generated = generateComprehensiveQuestions(candidate, activeRole);
  const seen = new Set(generated.map((g) => g.q.trim().toLowerCase()));
  const extra = (candidate.interviewQuestions || [])
    .filter((s) => s?.q && !seen.has(s.q.trim().toLowerCase()))
    .map((s, i) => ({
      id: `q-stored-${i + 1}`,
      type: s.type || "Technical Verification",
      badgeColor: "indigo",
      q: s.q,
      lookFor: s.lookFor || "",
    }));
  return [...extra, ...generated].map((q, i) => ({ ...q, id: `${q.id}#${i}` }));
}
