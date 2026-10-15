import { useState } from "react";
import {
  ArrowRight,
  BarChart3,
  Bot,
  Briefcase,
  CheckCheck,
  ChevronDown,
  Copy,
  Mic,
  Plus,
  Sparkles,
  Swords,
  Upload,
  X,
  Zap,
} from "lucide-react";

const PREVIEW_SKILLS = 6;

const inputClass =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 " +
  "outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100";

const primaryBtn =
  "inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:opacity-60";
const outlineBtn =
  "inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-60";

function Step({ n, title, hint, action, children }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6">
      <header className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-xs font-semibold text-white">
            {n}
          </span>
          <div>
            <h2 className="text-base font-semibold text-slate-900">{title}</h2>
            {hint && <p className="mt-0.5 text-sm text-slate-500">{hint}</p>}
          </div>
        </div>
        {action}
      </header>
      {children}
    </section>
  );
}

function Fact({ label, value }) {
  return (
    <div>
      <dt className="text-xs text-slate-500">{label}</dt>
      <dd className="mt-0.5 text-sm font-medium text-slate-900">{value}</dd>
    </div>
  );
}

const NEXT_STEPS = [
  { id: "leaderboard", title: "Screening Leaderboard", text: "Review ranked candidates and match scores", Icon: BarChart3 },
  { id: "comparison", title: "Candidate Comparison", text: "Compare top contenders side-by-side", Icon: Swords },
  { id: "interview", title: "Interview Assistant", text: "Generate targeted interview questions", Icon: Mic },
  { id: "chatbot", title: "Recruiter Chatbot", text: "Ask AI about candidate strengths and talent gaps", Icon: Bot },
];

/**
 * Home screen, laid out as three guided steps:
 *   1. choose the role   2. load candidates   3. go to the next screen
 * Everything from the previous Job Management screen is still here; advanced controls are just tucked
 * behind a disclosure until they are needed.
 */
export default function JobHome({
  jobRoles,
  activeRole,
  activeRoleId,
  setActiveRoleId,
  isCreatingRole,
  setIsCreatingRole,
  newRoleForm,
  setNewRoleForm,
  handleCreateCustomRole,
  handleRemoveSkill,
  handleAddSkill,
  newSkillInput,
  setNewSkillInput,
  candidatesPool,
  poolSource,
  is50PoolActive,
  isIngestingBatch,
  batchProgress,
  batchStageText,
  uploadedFilesCount,
  uploadedFilesList,
  uploadFeedback,
  handleFilesSelected,
  handleLoadCorePool,
  handleSimulateBatchIngest,
  handleLoad100Pool,
  handleTogglePool,
  showMasterPrompt,
  setShowMasterPrompt,
  promptCopied,
  handleCopyMasterPrompt,
  masterPrompt,
  setActiveNav,
}) {
  const [skillsOpen, setSkillsOpen] = useState(false);
  const skills = activeRole.skills;
  const setForm = (key) => (e) => setNewRoleForm({ ...newRoleForm, [key]: e.target.value });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Get started</h1>
        <p className="mt-1 text-sm text-slate-500">
          Pick the role you are hiring for, load candidates, then review the results.
        </p>
      </div>

      {/* ------------------------------ Step 1: role ------------------------------ */}
      <Step
        n={1}
        title="Active role"
        hint="The vacancy candidates are scored against."
        action={
          <div className="flex flex-wrap items-center gap-2">
            <label className="sr-only" htmlFor="role-select">
              Change role
            </label>
            <div className="relative">
              <Briefcase className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <select
                id="role-select"
                value={activeRoleId}
                onChange={(e) => setActiveRoleId(e.target.value)}
                className="appearance-none rounded-lg border border-slate-300 bg-white py-2 pl-9 pr-9 text-sm text-slate-900 outline-none transition hover:border-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
              >
                {jobRoles.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.title}
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            </div>
            <button onClick={() => setIsCreatingRole(!isCreatingRole)} className={outlineBtn}>
              <Plus className="h-4 w-4" /> Create Custom Role
            </button>
          </div>
        }
      >
        <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-5">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">{activeRole.title}</h3>
              <p className="text-sm text-slate-500">{activeRole.department}</p>
            </div>
            <span className="rounded-md border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
              {activeRole.status}
            </span>
          </div>

          <p className="mt-3 text-sm leading-relaxed text-slate-600">{activeRole.description}</p>

          <dl className="mt-4 grid grid-cols-1 gap-4 border-t border-slate-200 pt-4 sm:grid-cols-3">
            <Fact label="Minimum tenure" value={activeRole.minExperience} />
            <Fact label="Compensation (INR)" value={activeRole.salaryInr} />
          </dl>

          <div className="mt-4 border-t border-slate-200 pt-4">
            <div className="mb-2 text-xs text-slate-500">Key competencies</div>
            <div className="flex flex-wrap gap-1.5">
              {skills.slice(0, PREVIEW_SKILLS).map((s) => (
                <span key={s} className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-700">
                  {s}
                </span>
              ))}
              {skills.length > PREVIEW_SKILLS && (
                <span className="px-1 py-1 text-xs text-slate-500">+{skills.length - PREVIEW_SKILLS} more</span>
              )}
            </div>

            <button
              onClick={() => setSkillsOpen(!skillsOpen)}
              aria-expanded={skillsOpen}
              className="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-indigo-600 hover:text-indigo-700"
            >
              <ChevronDown className={`h-4 w-4 transition-transform ${skillsOpen ? "rotate-180" : ""}`} />
              {skillsOpen ? "Hide competencies" : `Edit competencies (${skills.length})`}
            </button>

            {skillsOpen && (
              <div className="mt-3 space-y-3 rounded-lg border border-slate-200 bg-white p-4">
                <div className="text-xs text-slate-500">
                  Required Competencies Ontology ({skills.length} targets). Click × to remove, or add a new one below.
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {skills.map((s) => (
                    <span
                      key={s}
                      className="flex items-center gap-1.5 rounded-md border border-indigo-100 bg-indigo-50 px-2 py-1 text-xs text-indigo-700"
                    >
                      {s}
                      <button
                        onClick={() => handleRemoveSkill(s)}
                        title={`Remove ${s}`}
                        aria-label={`Remove ${s}`}
                        className="text-indigo-400 transition hover:text-rose-600"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <form onSubmit={handleAddSkill} className="flex gap-2">
                  <input
                    type="text"
                    value={newSkillInput}
                    onChange={(e) => setNewSkillInput(e.target.value)}
                    placeholder="Add a required competency (e.g. Redis, Kubernetes)"
                    className={inputClass}
                  />
                  <button type="submit" className={`${outlineBtn} shrink-0`}>
                    <Plus className="h-4 w-4" /> Add Skill
                  </button>
                </form>
              </div>
            )}
          </div>
        </div>

        {isCreatingRole && (
          <div className="mt-4 space-y-4 rounded-lg border border-indigo-200 bg-white p-5">
            <div className="flex items-center justify-between">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                <Sparkles className="h-4 w-4 text-indigo-600" /> Define a new custom role
              </h3>
              <button
                onClick={() => setIsCreatingRole(false)}
                aria-label="Close"
                className="text-slate-500 hover:text-slate-900"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <div>
                <label className="mb-1 block text-xs text-slate-600">Job title</label>
                <input
                  type="text"
                  value={newRoleForm.title}
                  onChange={setForm("title")}
                  placeholder="e.g. Lead Distributed Systems Engineer"
                  className={inputClass}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-slate-600">Department / org</label>
                <input
                  type="text"
                  value={newRoleForm.department}
                  onChange={setForm("department")}
                  placeholder="e.g. Core Infrastructure"
                  className={inputClass}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-slate-600">Minimum tenure</label>
                <input
                  type="text"
                  value={newRoleForm.minExperience}
                  onChange={setForm("minExperience")}
                  placeholder="e.g. 4+ Years Production"
                  className={inputClass}
                />
              </div>
            </div>

            <div>
              <label className="mb-1 block text-xs text-slate-600">Salary range (INR, annual)</label>
              <input
                type="text"
                value={newRoleForm.salaryInr}
                onChange={setForm("salaryInr")}
                placeholder="35 - 42 LPA"
                className={inputClass}
              />
            </div>

            <div>
              <label className="mb-1 block text-xs text-slate-600">Required competencies (comma separated)</label>
              <input
                type="text"
                value={newRoleForm.skills}
                onChange={setForm("skills")}
                placeholder="e.g. Golang, Kubernetes, gRPC, Docker, Kafka, PostgreSQL"
                className={inputClass}
              />
            </div>

            <button onClick={handleCreateCustomRole} className={primaryBtn}>
              <Sparkles className="h-4 w-4" /> Deploy Vacancy to Screening Engine
            </button>
          </div>
        )}
      </Step>

      {/* ------------------------------ Step 2: candidates ------------------------------ */}
      <Step
        n={2}
        title="Candidate intake"
        hint="Upload your own resumes, or start from a ready-made pool."
        action={
          <span className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-700">
            <span className="h-1.5 w-1.5 rounded-full bg-indigo-600" />
            <strong className="font-semibold text-slate-900">{candidatesPool.length}</strong> candidates loaded
            <span className="text-slate-400">·</span>
            <span className="text-slate-500">{poolSource}</span>
          </span>
        }
      >
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <label className="group flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-slate-300 bg-slate-50/60 px-4 py-8 text-center transition hover:border-indigo-400 hover:bg-indigo-50/40 focus-within:ring-2 focus-within:ring-indigo-100">
            <Upload className="h-6 w-6 text-slate-400 transition group-hover:text-indigo-600" />
            <span className="text-sm font-medium text-slate-900">Upload your own resumes</span>
            <span className="text-xs text-slate-500">
              {uploadedFilesCount > 0
                ? `${uploadedFilesCount} file${uploadedFilesCount === 1 ? "" : "s"} chosen: ${uploadedFilesList
                    .slice(0, 2)
                    .join(", ")}${uploadedFilesList.length > 2 ? "…" : ""}`
                : "PDF, DOCX or TXT · up to 100 files, parsed in your browser"}
            </span>
            <span className={`${primaryBtn} mt-1 pointer-events-none`}>Select resume files</span>
            <input type="file" multiple accept=".txt,.pdf,.docx,.md" onChange={handleFilesSelected} className="sr-only" />
          </label>

          <div className="flex flex-col gap-3">
            <div className="text-xs text-slate-500">Or load a benchmark pool</div>
            {isIngestingBatch ? (
              <div className="space-y-2 rounded-lg border border-slate-200 bg-slate-50/60 p-4 text-sm">
                <div className="flex justify-between text-slate-700">
                  <span>Processing resumes…</span>
                  <span>{batchProgress}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                  <div
                    className="h-full rounded-full bg-indigo-600 transition-all duration-500"
                    style={{ width: `${batchProgress}%` }}
                  />
                </div>
                <div className="truncate text-xs text-slate-500">{batchStageText}</div>
              </div>
            ) : (
              <>
                <button onClick={handleLoadCorePool} className={outlineBtn}>
                  <Zap className="h-4 w-4 text-indigo-600" /> Load 12 Core Resumes
                </button>
                <button onClick={handleSimulateBatchIngest} className={outlineBtn}>
                  <Zap className="h-4 w-4 text-indigo-600" /> Load 50 Benchmark Pool
                </button>
                <button onClick={handleLoad100Pool} className={outlineBtn}>
                  <Sparkles className="h-4 w-4 text-indigo-600" /> Load 100 Enterprise Suite (all 8 roles)
                </button>
                <button
                  onClick={handleTogglePool}
                  className="self-start text-xs font-medium text-indigo-600 hover:underline"
                >
                  {is50PoolActive ? "Toggle back to the 12-resume core suite" : "Toggle 12/50"}
                </button>
              </>
            )}
          </div>
        </div>

        {uploadFeedback && (
          <div role="status" className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
            {uploadFeedback}
          </div>
        )}

        <div className="mt-5 flex justify-end border-t border-slate-200 pt-4">
          <button onClick={() => setActiveNav("leaderboard")} className={primaryBtn}>
            Run Screening Engine <ArrowRight className="h-4 w-4" />
          </button>
        </div>

        {/* Advanced: master prompt for generating synthetic resumes */}
        <div className="mt-4 overflow-hidden rounded-lg border border-slate-200">
          <button
            onClick={() => setShowMasterPrompt(!showMasterPrompt)}
            aria-expanded={showMasterPrompt}
            className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left transition hover:bg-slate-50"
          >
            <div>
              <div className="text-sm font-medium text-slate-900">Need sample resumes? Master prompt</div>
              <div className="text-xs text-slate-500">
                Generate 50–100+ diverse synthetic benchmark resumes with your own LLM.
              </div>
            </div>
            <span className="flex shrink-0 items-center gap-1 text-xs font-medium text-indigo-600">
              {showMasterPrompt ? "Collapse" : "View prompt"}
              <ChevronDown className={`h-4 w-4 transition-transform ${showMasterPrompt ? "rotate-180" : ""}`} />
            </span>
          </button>

          {showMasterPrompt && (
            <div className="space-y-3 border-t border-slate-200 bg-slate-50 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-xs text-slate-500">Paste this into your LLM to generate candidate batches:</span>
                <button onClick={handleCopyMasterPrompt} className={primaryBtn}>
                  {promptCopied ? <CheckCheck className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                  {promptCopied ? "Copied" : "Copy Master Prompt"}
                </button>
              </div>
              <pre className="max-h-64 overflow-y-auto whitespace-pre-wrap rounded-lg border border-slate-200 bg-white p-4 text-xs leading-relaxed text-slate-700">
                {masterPrompt}
              </pre>
            </div>
          )}
        </div>
      </Step>

      {/* ------------------------------ Step 3: launchpad ------------------------------ */}
      <Step n={3} title="Where to go next" hint="Pick up from here once candidates are loaded.">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {NEXT_STEPS.map(({ id, title, text, Icon }) => (
            <button
              key={id}
              onClick={() => setActiveNav(id)}
              className="group flex flex-col items-start rounded-lg border border-slate-200 bg-white p-4 text-left transition hover:border-indigo-300 hover:shadow-sm"
            >
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
                <Icon className="h-5 w-5" />
              </span>
              <span className="mt-3 text-sm font-semibold text-slate-900">{title}</span>
              <span className="mt-1 text-sm leading-snug text-slate-500">{text}</span>
              <span className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-indigo-600">
                Open <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
              </span>
            </button>
          ))}
        </div>
      </Step>
    </div>
  );
}
