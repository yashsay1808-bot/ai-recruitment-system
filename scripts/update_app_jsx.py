import re

# Read current App.jsx
with open("frontend/src/App.jsx", "r", encoding="utf-8") as f:
    orig = f.read()

# Let's inspect imports at the top
import_block = """import React, { useState, useMemo } from "react";
import {
  Search,
  Moon,
  Sun,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Cpu,
  Users,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  X,
  ChevronRight,
  GitBranch,
  TrendingUp,
  Terminal,
  Sliders,
  DollarSign,
  Briefcase,
  FileText,
  Clock,
  Sparkles,
  Award,
  Send,
  Download,
  Check,
  FileCode,
  Layers,
  Database,
  Lock,
  ExternalLink,
  LayoutGrid,
  List,
  Target,
  BarChart3,
  SearchCode,
  Swords,
  Mic,
  LineChart,
  Bot,
  LogOut,
  LogIn,
  KeyRound,
  Eye,
  EyeOff,
  Upload,
  ArrowRight,
  Plus,
  Trash2,
  Copy,
  CheckCheck,
  RefreshCw
} from "lucide-react";
import { DEFAULT_JOB_ROLES } from "./data/jobRoles";
import { CANDIDATES_12, CANDIDATES_50 } from "./data/candidatesData";
import { generateChatbotResponse } from "./utils/chatbotEngine";

function GithubIcon({ className = "w-5 h-5" }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
      />
    </svg>
  );
}

const MASTER_RESUME_PROMPT = `Role: You are an expert Enterprise HR Systems Architect and Principal Technical Recruiter.
Task: Generate 50 to 100 diverse, realistic, and highly detailed synthetic candidate resumes for an AI Recruitment System benchmarking evaluation.

Target Roles (Distribute evenly across):
1. Senior Machine Learning Engineer (PyTorch, FastAPI, AWS ECS, MLOps)
2. Cloud DevOps & Site Reliability Lead (Kubernetes, Terraform, AWS, Prometheus)
3. Full-Stack AI Application Engineer (React, TypeScript, FastAPI, Next.js, LangChain)
4. Data Platform & Distributed Systems Engineer (Python, Apache Spark, Kafka, Snowflake)
5. Backend Microservices Architect (Golang, Python, gRPC, Docker, PostgreSQL)
6. AI Safety, Governance & Alignment Auditor (Model Evaluation, Red Teaming, Bias Auditing)
7. Senior Business Intelligence & Data Analyst (SQL, Python, Tableau, Power BI)
8. Python Backend & API Developer (Django, FastAPI, Celery, PostgreSQL)

Distribution Profile (Must include all 5 evaluation archetypes):
- 20% Gold Standard Passes (Strong Hires): 3-7 years tenure, quantified latency/throughput metrics (e.g., "<72ms p95 latency under 50k req/day", "99.99% uptime"), authentic public GitHub repositories with original commit histories, complete education, and zero discrepancies.
- 45% Mid-Level & Lateral Transitions (Lean Hires): 2-4 years tenure, strong adjacent skills (e.g., Flask moving to FastAPI, TensorFlow moving to PyTorch, SQL moving to distributed Spark), clean work history, minor skill gaps onboardable in 30 days.
- 20% Skill Stuffing & Unverified Exaggerations (Red Flag Rejects): Under 6 months experience claiming 30+ technologies (e.g. "Kubernetes Master & CUDA Sorcerer in 4 months"), GitHub accounts with 90%+ untouched tutorial forks.
- 10% ATS Formatting & Chronology Errors (Format Rejects): Overlapping concurrent full-time employment dates in same calendar year, multi-column tables or non-standard fonts causing text extraction failures.
- 5% Missing Structural Sections (Structural Rejects): Resumes omitting mandatory sections such as Education, Employment History, or Demonstrable Projects.

Format for each resume:
- Full Name, Anonymized ID, Email, Phone, Location, GitHub handle
- Professional Summary (2-3 sentences with tenure and core focus)
- Work History (Company, Dates, Roles, 3-4 bullet points with quantified achievements)
- Technical Skills (Languages, Frameworks, Cloud, Databases, Tools)
- Education (Degree, University, Graduation Year)
- Benchmark Verification Notes (Expected Verdict: STRONG_HIRE / LEAN_HIRE / REJECT, and Red Flag Tags)
`;

const PROMPT_PILLS = [
  "Engineers with 2+ years in Python and PyTorch",
  "Backend developers who deployed with Docker and AWS",
  "Candidates with measurable latency or throughput results",
  "Who has NLP or transformer experience?"
];
"""

# Find where `export default function App() {` starts
app_start_idx = orig.find("export default function App() {")

# Everything after `export default function App() {` up to `// Copilot Chat`
# We want to replace state and helper functions
state_and_helpers = """export default function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [blindMode, setBlindMode] = useState(false);

  // Authentication State
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loginEmail, setLoginEmail] = useState("recruiter@techcorp.com");
  const [loginPassword, setLoginPassword] = useState("password123");
  const [showPassword, setShowPassword] = useState(false);
  const [loginTab, setLoginTab] = useState("signin"); // "signin" | "register" | "audit"
  const [isCredentialsExpanded, setIsCredentialsExpanded] = useState(false);
  const [recruiterName, setRecruiterName] = useState("Yashashwini");
  const [authError, setAuthError] = useState("");
  const [authSuccess, setAuthSuccess] = useState("");

  // Registration Form State
  const [regName, setRegName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regCompany, setRegCompany] = useState("TechCorp Global Technologies");
  const [regRole, setRegRole] = useState("Lead Technical Recruiter");
  const [regAuthKey, setRegAuthKey] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regPasswordConfirm, setRegPasswordConfirm] = useState("");
  const [regStatus, setRegStatus] = useState(null);

  // Dynamic Job Roles State (8 Roles + Custom Roles)
  const [jobRoles, setJobRoles] = useState(DEFAULT_JOB_ROLES);
  const [activeRoleId, setActiveRoleId] = useState("role-ml");
  const activeRole = useMemo(() => {
    return jobRoles.find((r) => r.id === activeRoleId) || jobRoles[0];
  }, [jobRoles, activeRoleId]);

  const [newSkillInput, setNewSkillInput] = useState("");
  const [isCreatingRole, setIsCreatingRole] = useState(false);
  const [newRoleForm, setNewRoleForm] = useState({
    title: "",
    department: "Engineering Org",
    level: "L4/L5 Senior",
    minExperience: "3+ Years Production",
    salaryRange: "$150k - $180k",
    salaryInr: "30 - 38 LPA",
    description: "",
    skills: "Python, Docker, AWS, CI/CD, REST API"
  });

  // Candidate Pool State (12 Core Test Suite vs 50 Diverse Pool)
  const [candidatesPool, setCandidatesPool] = useState(CANDIDATES_12);
  const [is50PoolActive, setIs50PoolActive] = useState(false);
  const [isIngestingBatch, setIsIngestingBatch] = useState(false);
  const [batchProgress, setBatchProgress] = useState(0);
  const [batchStageText, setBatchStageText] = useState("");
  const [uploadedFilesCount, setUploadedFilesCount] = useState(0);
  const [showMasterPrompt, setShowMasterPrompt] = useState(false);
  const [promptCopied, setPromptCopied] = useState(false);

  // Navigation State (Exact 7 Streamlit Pages)
  const [activeNav, setActiveNav] = useState("job_management");
  const [jobMgmtTab, setJobMgmtTab] = useState("vacancy"); // "vacancy" | "auth"
  const [viewMode, setViewMode] = useState("cards"); // "cards" or "table"

  // Search & Filter
  const [searchQuery, setSearchQuery] = useState("");
  const [verdictFilter, setVerdictFilter] = useState("ALL");
  const [activePromptPill, setActivePromptPill] = useState("");

  // Slide-over Drawer
  const [selectedCandidate, setSelectedCandidate] = useState(candidatesPool[0]);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [debateStep, setDebateStep] = useState(0);

  // Council View State
  const [councilSelectedCandId, setCouncilSelectedCandId] = useState("CAN-001");
  const [councilDebateTurn, setCouncilDebateTurn] = useState(0);

  // Comparison View State
  const [compareCandAId, setCompareCandAId] = useState("CAN-001");
  const [compareCandBId, setCompareCandBId] = useState("CAN-002");

  // Interview Assistant State
  const [interviewCandId, setInterviewCandId] = useState("CAN-001");

  // Copilot Chat
  const [copilotMessages, setCopilotMessages] = useState([
    {
      sender: "assistant",
      text: `Hello Yashashwini! I'm your Talent Acquisition Copilot. ${candidatesPool.length} candidates are screened for the ${activeRole.title} vacancy. Ask me to breakdown headcount, match required skills, audit red flags, or draft candidate outreach emails.`
    }
  ]);
  const [copilotInput, setCopilotInput] = useState("");

  // Handlers for Dynamic Skills
  const handleRemoveSkill = (skillToRemove) => {
    setJobRoles((prev) =>
      prev.map((role) =>
        role.id === activeRoleId
          ? { ...role, skills: role.skills.filter((s) => s !== skillToRemove) }
          : role
      )
    );
  };

  const handleAddSkill = (e) => {
    if (e) e.preventDefault();
    const trimmed = newSkillInput.trim();
    if (!trimmed) return;
    if (activeRole.skills.includes(trimmed)) {
      setNewSkillInput("");
      return;
    }
    setJobRoles((prev) =>
      prev.map((role) =>
        role.id === activeRoleId
          ? { ...role, skills: [...role.skills, trimmed] }
          : role
      )
    );
    setNewSkillInput("");
  };

  const handleCreateCustomRole = (e) => {
    if (e) e.preventDefault();
    if (!newRoleForm.title.trim()) return;
    const newId = `role-custom-${Date.now()}`;
    const parsedSkills = newRoleForm.skills
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const createdRole = {
      id: newId,
      title: newRoleForm.title.trim(),
      department: newRoleForm.department.trim() || "Engineering Org",
      level: newRoleForm.level.trim() || "L4/L5 Senior",
      minExperience: newRoleForm.minExperience.trim() || "2+ Years Production",
      salaryRange: newRoleForm.salaryRange.trim() || "$140k - $170k",
      salaryInr: newRoleForm.salaryInr.trim() || "28 - 36 LPA",
      status: "ACCEPTING CANDIDATES",
      description: newRoleForm.description.trim() || `Enterprise hiring for ${newRoleForm.title}.`,
      skills: parsedSkills.length > 0 ? parsedSkills : ["Python", "Docker", "Git", "REST API"]
    };
    setJobRoles((prev) => [...prev, createdRole]);
    setActiveRoleId(newId);
    setIsCreatingRole(false);
    setNewRoleForm({
      title: "",
      department: "Engineering Org",
      level: "L4/L5 Senior",
      minExperience: "3+ Years Production",
      salaryRange: "$150k - $180k",
      salaryInr: "30 - 38 LPA",
      description: "",
      skills: "Python, Docker, AWS, CI/CD, REST API"
    });
  };

  // Handlers for 50-Resume Ingestion
  const handleSimulateBatchIngest = () => {
    setIsIngestingBatch(true);
    setBatchProgress(15);
    setBatchStageText("Stage 1/4: Ingesting & OCR parsing 50 candidate resumes (PDF, DOCX, TXT)...");

    setTimeout(() => {
      setBatchProgress(45);
      setBatchStageText("Stage 2/4: Computing TF-IDF vector similarity and candidate feature vectors...");
    }, 700);

    setTimeout(() => {
      setBatchProgress(75);
      setBatchStageText("Stage 3/4: Executing Four-Agent Council Cross-Examination & Fair Auditor check...");
    }, 1400);

    setTimeout(() => {
      setBatchProgress(100);
      setBatchStageText("Stage 4/4: Leaderboard calibration complete! 50 candidates indexed.");
      setTimeout(() => {
        setCandidatesPool(CANDIDATES_50);
        setIs50PoolActive(true);
        setIsIngestingBatch(false);
        setBatchProgress(0);
        setBatchStageText("");
        // Notify in chatbot
        setCopilotMessages((prev) => [
          ...prev,
          {
            sender: "assistant",
            text: `⚡ Bulk Ingestion Complete! The candidate pool has been expanded to 50 diverse candidates across 8 engineering disciplines. You can now query pool breakdown, skill coverage, or red flag summaries.`
          }
        ]);
      }, 500);
    }, 2100);
  };

  const handleTogglePool = () => {
    if (is50PoolActive) {
      setCandidatesPool(CANDIDATES_12);
      setIs50PoolActive(false);
    } else {
      setCandidatesPool(CANDIDATES_50);
      setIs50PoolActive(true);
    }
  };

  const handleCopyMasterPrompt = () => {
    navigator.clipboard.writeText(MASTER_RESUME_PROMPT);
    setPromptCopied(true);
    setTimeout(() => setPromptCopied(false), 2200);
  };

  const councilCandidate = useMemo(() => {
    return candidatesPool.find((c) => c.id === councilSelectedCandId) || candidatesPool[0];
  }, [candidatesPool, councilSelectedCandId]);

  const candA = useMemo(() => {
    return candidatesPool.find((c) => c.id === compareCandAId) || candidatesPool[0];
  }, [candidatesPool, compareCandAId]);

  const candB = useMemo(() => {
    return candidatesPool.find((c) => c.id === compareCandBId) || candidatesPool[1] || candidatesPool[0];
  }, [candidatesPool, compareCandBId]);

  const interviewCandidate = useMemo(() => {
    return candidatesPool.find((c) => c.id === interviewCandId) || candidatesPool[0];
  }, [candidatesPool, interviewCandId]);

  // Candidates filtering
  const filteredCandidates = useMemo(() => {
    const q = (activePromptPill || searchQuery).toLowerCase().trim();
    return candidatesPool.filter((cand) => {
      const displayName = blindMode ? cand.anonymizedId : cand.name;
      const matchesSearch =
        !q ||
        displayName.toLowerCase().includes(q) ||
        cand.title.toLowerCase().includes(q) ||
        cand.matchedSkills.some((s) => s.toLowerCase().includes(q)) ||
        cand.partiallyMatchedSkills.some((s) => s.toLowerCase().includes(q)) ||
        cand.missingSkills.some((s) => s.toLowerCase().includes(q)) ||
        cand.evidenceSnippet.toLowerCase().includes(q) ||
        cand.redFlags.some((f) => f.toLowerCase().includes(q));

      const matchesVerdict =
        verdictFilter === "ALL"
          ? true
          : verdictFilter === "FLAGGED"
          ? cand.redFlags.length > 0
          : cand.verdict === verdictFilter;

      return matchesSearch && matchesVerdict;
    });
  }, [candidatesPool, searchQuery, activePromptPill, verdictFilter, blindMode]);

  const totalScreened = candidatesPool.length;
  const topMatchCandidate = candidatesPool[0];
  const avgMatchScore = (
    candidatesPool.reduce((acc, c) => acc + c.matchScore, 0) / candidatesPool.length
  ).toFixed(1);
  const strongHiresCount = candidatesPool.filter((c) => c.verdict === "STRONG_HIRE").length;
  const leanHiresCount = candidatesPool.filter((c) => c.verdict === "LEAN_HIRE").length;
  const rejectCount = candidatesPool.filter((c) => c.verdict === "REJECT").length;
  const flaggedCount = candidatesPool.filter((c) => c.redFlags.length > 0).length;

  // DYNAMIC RECRUITER TALENT COPILOT HANDLER
  const handleSendCopilot = (textToSend) => {
    const q = textToSend || copilotInput;
    if (!q.trim()) return;

    const userMsg = { sender: "user", text: q };
    const reply = generateChatbotResponse({
      query: q,
      candidatesPool,
      activeRole,
      recruiterName: "Yashashwini"
    });

    setCopilotMessages((prev) => [...prev, userMsg, { sender: "assistant", text: reply }]);
    setCopilotInput("");
  };
"""

# Now we need the JSX part. Let's find where return starts in orig
return_idx = orig.find("  return (")

# Extract everything from `  return (` to the end
jsx_body = orig[return_idx:]

# In jsx_body, replace:
# 1. Sidebar badge for leaderboard:
jsx_body = jsx_body.replace(
    '{ id: "leaderboard", label: "Screening Leaderboard", emoji: "📊", badge: "12" }',
    '{ id: "leaderboard", label: "Screening Leaderboard", emoji: "📊", badge: candidatesPool.length.toString() }'
)

# 2. In Leaderboard filter tabs:
jsx_body = jsx_body.replace(
    '{ id: "ALL", label: `ALL (${CANDIDATES_DATA.length})` },',
    '{ id: "ALL", label: `ALL (${candidatesPool.length})` },'
)
jsx_body = jsx_body.replace(
    '{ id: "LEAN_HIRE", label: "LEAN HIRE (3)" },',
    '{ id: "LEAN_HIRE", label: `LEAN HIRE (${leanHiresCount})` },'
)
jsx_body = jsx_body.replace(
    '{ id: "REJECT", label: "REJECT (7)" },',
    '{ id: "REJECT", label: `REJECT (${rejectCount})` },'
)

# 3. Replace all remaining `CANDIDATES_DATA.map` with `candidatesPool.map`
jsx_body = jsx_body.replace("CANDIDATES_DATA.map", "candidatesPool.map")

# 4. Now let's replace the Job Management Active Vacancy section (lines 1450 to 1538)
old_job_mgmt = """              {/* RENDER ACTIVE VACANCY & INTAKE (When authenticated and on vacancy tab) */}
              {isAuthenticated && jobMgmtTab === "vacancy" && (
                <div className="space-y-6">
                  <div className="p-6 rounded-2xl border border-[rgba(148,163,184,0.14)] bg-[#0f172a]/70 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                      <div className="text-[11px] font-mono tracking-widest uppercase text-cyan-400 font-bold">
                        Role Specification &amp; Resume Intake
                      </div>
                      <h1 className="text-2xl font-extrabold tracking-tight text-white mt-1">
                        🎯 Job Management &amp; Vacancies
                      </h1>
                      <p className="text-xs text-slate-400 font-mono mt-1">
                        Configure required competencies, minimum tenure thresholds, and upload candidate resumes.
                      </p>
                    </div>
                    <button
                      onClick={() => setActiveNav("leaderboard")}
                      className="px-4 py-2.5 rounded-xl bg-cyan-400 hover:bg-cyan-300 text-slate-950 font-mono text-xs font-bold transition-all shadow-md flex items-center gap-2"
                    >
                      🚀 Run Screening Engine <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Active Role Details */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="md:col-span-2 p-6 rounded-2xl border border-[rgba(148,163,184,0.14)] bg-[#0f172a]/70 space-y-4">
                      <div className="flex justify-between items-center">
                        <h3 className="text-base font-bold text-white">Active Vacancy Specification</h3>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-400 font-bold">
                          ACCEPTING CANDIDATES
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                          <span className="text-slate-400 block text-[10px]">JOB TITLE</span>
                          <span className="font-bold text-white text-sm">Machine Learning Engineer</span>
                        </div>
                        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                          <span className="text-slate-400 block text-[10px]">MINIMUM EXPERIENCE</span>
                          <span className="font-bold text-cyan-400 text-sm">2+ Years Production</span>
                        </div>
                      </div>

                      <div>
                        <label className="text-xs font-mono text-slate-400 block mb-2 font-bold">
                          Required Skills &amp; Competencies Ontology (17 Core Targets):
                        </label>
                        <div className="flex flex-wrap gap-1.5">
                          {[
                            "Python", "PyTorch", "TensorFlow", "FastAPI", "Flask",
                            "Docker", "AWS", "CI/CD", "Natural Language Processing",
                            "Deep Learning", "Machine Learning", "Scikit-Learn",
                            "Pandas", "NumPy", "Git", "REST API", "Hugging Face"
                          ].map((s) => (
                            <span
                              key={s}
                              className="text-xs font-mono px-2.5 py-1 rounded-lg bg-cyan-950/40 border border-cyan-800 text-cyan-300"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Upload Resumes Card */}
                    <div className="p-6 rounded-2xl border border-dashed border-slate-700 bg-[#0f172a]/40 flex flex-col items-center justify-center text-center space-y-3">
                      <div className="w-12 h-12 rounded-2xl bg-cyan-950/60 border border-cyan-800 text-cyan-400 flex items-center justify-center">
                        <Upload className="w-6 h-6" />
                      </div>
                      <div>
                        <div className="font-bold text-sm text-white">Upload New Resumes</div>
                        <div className="text-[11px] text-slate-400 font-mono mt-0.5">PDF, DOCX, TXT (Batch Ingestion)</div>
                      </div>
                      <p className="text-xs text-slate-500">12 verified sample candidates currently indexed in data/sample_resumes/.</p>
                      <button
                        onClick={() => setActiveNav("leaderboard")}
                        className="px-3.5 py-1.5 rounded-xl border border-slate-700 bg-slate-800 text-xs font-mono text-slate-200 hover:text-white"
                      >
                        View Indexed Candidates →
                      </button>
                    </div>
                  </div>
                </div>
              )}"""

new_job_mgmt = """              {/* RENDER ACTIVE VACANCY & INTAKE (When authenticated and on vacancy tab) */}
              {isAuthenticated && jobMgmtTab === "vacancy" && (
                <div className="space-y-6">
                  {/* Top Bar with Run Button */}
                  <div className="p-6 rounded-2xl border border-[rgba(148,163,184,0.14)] bg-[#0f172a]/70 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                      <div className="text-[11px] font-mono tracking-widest uppercase text-cyan-400 font-bold">
                        Dynamic Role Specification &amp; Batch Intake
                      </div>
                      <h1 className="text-2xl font-extrabold tracking-tight text-white mt-1">
                        🎯 Job Management &amp; Vacancy Architecture
                      </h1>
                      <p className="text-xs text-slate-400 font-mono mt-1">
                        Switch between {jobRoles.length} active enterprise roles, customize competency ontologies, or batch ingest 50–100 candidate resumes.
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={handleTogglePool}
                        className={`px-3 py-2 rounded-xl text-xs font-mono font-bold border transition-all ${
                          is50PoolActive
                            ? "bg-purple-950/40 border-purple-600 text-purple-300"
                            : "bg-slate-800 border-slate-700 text-slate-300 hover:text-white"
                        }`}
                      >
                        {is50PoolActive ? "⚡ 50 Pool Active (Switch to 12)" : "Switch to 50 Candidates"}
                      </button>
                      <button
                        onClick={() => setActiveNav("leaderboard")}
                        className="px-4 py-2.5 rounded-xl bg-cyan-400 hover:bg-cyan-300 text-slate-950 font-mono text-xs font-bold transition-all shadow-md flex items-center gap-2"
                      >
                        🚀 Run Screening Engine <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* 1. DYNAMIC JOB ROLES SELECTOR TABS */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs font-mono text-slate-400">
                      <span className="font-bold text-white flex items-center gap-1.5">
                        <Briefcase className="w-4 h-4 text-cyan-400" /> SELECT ACTIVE VACANCY ({jobRoles.length} POSITIONS OPEN):
                      </span>
                      <button
                        onClick={() => setIsCreatingRole(!isCreatingRole)}
                        className="px-2.5 py-1 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 font-bold transition-all flex items-center gap-1"
                      >
                        <Plus className="w-3.5 h-3.5" /> Create Custom Vacancy
                      </button>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      {jobRoles.map((role) => {
                        const isSelected = role.id === activeRoleId;
                        return (
                          <button
                            key={role.id}
                            onClick={() => setActiveRoleId(role.id)}
                            className={`p-3 rounded-xl border text-left transition-all relative overflow-hidden ${
                              isSelected
                                ? "bg-cyan-950/40 border-cyan-400/80 shadow-[0_0_16px_rgba(56,189,248,0.2)] text-white"
                                : "bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                            }`}
                          >
                            {isSelected && (
                              <div className="absolute top-0 left-0 right-0 h-1 bg-cyan-400" />
                            )}
                            <div className="text-xs font-bold truncate">{role.title}</div>
                            <div className="text-[10px] font-mono text-slate-500 truncate mt-0.5">
                              {role.department}
                            </div>
                            <div className="text-[10px] font-mono text-cyan-400 font-semibold mt-1">
                              {role.salaryRange}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* CUSTOM VACANCY CREATION FORM */}
                  {isCreatingRole && (
                    <div className="p-6 rounded-2xl border border-cyan-500/40 bg-slate-900/90 space-y-4 shadow-xl">
                      <div className="flex justify-between items-center">
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                          <Sparkles className="w-4 h-4 text-cyan-400" /> Define New Custom Role Vacancy
                        </h3>
                        <button
                          onClick={() => setIsCreatingRole(false)}
                          className="text-slate-400 hover:text-white"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono">
                        <div>
                          <label className="text-slate-400 block mb-1">Job Title</label>
                          <input
                            type="text"
                            value={newRoleForm.title}
                            onChange={(e) => setNewRoleForm({ ...newRoleForm, title: e.target.value })}
                            placeholder="e.g. Lead Distributed Systems Engineer"
                            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-white outline-none focus:border-cyan-400"
                          />
                        </div>
                        <div>
                          <label className="text-slate-400 block mb-1">Department / Org</label>
                          <input
                            type="text"
                            value={newRoleForm.department}
                            onChange={(e) => setNewRoleForm({ ...newRoleForm, department: e.target.value })}
                            placeholder="e.g. Core Infrastructure"
                            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-white outline-none focus:border-cyan-400"
                          />
                        </div>
                        <div>
                          <label className="text-slate-400 block mb-1">Minimum Tenure Requirement</label>
                          <input
                            type="text"
                            value={newRoleForm.minExperience}
                            onChange={(e) => setNewRoleForm({ ...newRoleForm, minExperience: e.target.value })}
                            placeholder="e.g. 4+ Years Production"
                            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-white outline-none focus:border-cyan-400"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
                        <div>
                          <label className="text-slate-400 block mb-1">Salary Range USD</label>
                          <input
                            type="text"
                            value={newRoleForm.salaryRange}
                            onChange={(e) => setNewRoleForm({ ...newRoleForm, salaryRange: e.target.value })}
                            placeholder="$160k - $190k"
                            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-white outline-none focus:border-cyan-400"
                          />
                        </div>
                        <div>
                          <label className="text-slate-400 block mb-1">Salary Range INR (Annual)</label>
                          <input
                            type="text"
                            value={newRoleForm.salaryInr}
                            onChange={(e) => setNewRoleForm({ ...newRoleForm, salaryInr: e.target.value })}
                            placeholder="35 - 42 LPA"
                            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-white outline-none focus:border-cyan-400"
                          />
                        </div>
                      </div>

                      <div className="text-xs font-mono">
                        <label className="text-slate-400 block mb-1">
                          Required Competencies &amp; Skills (Comma separated)
                        </label>
                        <input
                          type="text"
                          value={newRoleForm.skills}
                          onChange={(e) => setNewRoleForm({ ...newRoleForm, skills: e.target.value })}
                          placeholder="e.g. Golang, Kubernetes, gRPC, Docker, Kafka, PostgreSQL"
                          className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-white outline-none focus:border-cyan-400"
                        />
                      </div>

                      <button
                        onClick={handleCreateCustomRole}
                        className="px-4 py-2.5 rounded-xl bg-cyan-400 text-slate-950 font-mono font-bold text-xs hover:bg-cyan-300 transition-all shadow"
                      >
                        ✨ Deploy Vacancy to Screening Engine
                      </button>
                    </div>
                  )}

                  {/* 2. ACTIVE ROLE SPECIFICATION & RESUME INTAKE */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    {/* Vacancy Card */}
                    <div className="lg:col-span-2 p-6 rounded-2xl border border-[rgba(148,163,184,0.14)] bg-[#0f172a]/70 space-y-4">
                      <div className="flex justify-between items-center">
                        <div>
                          <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                            ACTIVE VACANCY #{activeRole.id}
                          </div>
                          <h3 className="text-lg font-bold text-white mt-0.5">{activeRole.title}</h3>
                          <div className="text-xs text-slate-400 font-mono">{activeRole.department}</div>
                        </div>
                        <span className="text-[10px] font-mono px-2.5 py-1 rounded-md bg-emerald-950/60 border border-emerald-800 text-emerald-400 font-bold">
                          {activeRole.status}
                        </span>
                      </div>

                      <p className="text-xs text-slate-300 font-sans leading-relaxed">
                        {activeRole.description}
                      </p>

                      <div className="grid grid-cols-3 gap-3 text-xs font-mono">
                        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                          <span className="text-slate-400 block text-[10px]">MIN TENURE</span>
                          <span className="font-bold text-cyan-400">{activeRole.minExperience}</span>
                        </div>
                        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                          <span className="text-slate-400 block text-[10px]">COMPENSATION USD</span>
                          <span className="font-bold text-white">{activeRole.salaryRange}</span>
                        </div>
                        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                          <span className="text-slate-400 block text-[10px]">COMPENSATION INR</span>
                          <span className="font-bold text-amber-400">{activeRole.salaryInr}</span>
                        </div>
                      </div>

                      {/* EDITABLE SKILLS ONTOLOGY */}
                      <div className="space-y-2 pt-2 border-t border-slate-800">
                        <div className="flex items-center justify-between">
                          <label className="text-xs font-mono text-slate-300 font-bold">
                            Required Competencies Ontology ({activeRole.skills.length} Targets):
                          </label>
                          <span className="text-[11px] font-mono text-slate-500">
                            Click × to remove, or add new below
                          </span>
                        </div>

                        <div className="flex flex-wrap gap-1.5">
                          {activeRole.skills.map((s) => (
                            <span
                              key={s}
                              className="text-xs font-mono px-2.5 py-1 rounded-lg bg-cyan-950/40 border border-cyan-800 text-cyan-300 flex items-center gap-1.5"
                            >
                              <span>{s}</span>
                              <button
                                onClick={() => handleRemoveSkill(s)}
                                className="text-cyan-500 hover:text-rose-400 transition-colors ml-0.5"
                                title={`Remove ${s}`}
                              >
                                ×
                              </button>
                            </span>
                          ))}
                        </div>

                        {/* Add Skill Input */}
                        <form onSubmit={handleAddSkill} className="flex gap-2 pt-2">
                          <input
                            type="text"
                            value={newSkillInput}
                            onChange={(e) => setNewSkillInput(e.target.value)}
                            placeholder="Add required competency (e.g. Redis, PyTorch, Kubernetes)..."
                            className="flex-1 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white outline-none focus:border-cyan-400 font-mono"
                          />
                          <button
                            type="submit"
                            className="px-3.5 py-1.5 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold transition-all"
                          >
                            + Add Skill
                          </button>
                        </form>
                      </div>
                    </div>

                    {/* Bulk 50-100 Resume Intake Card */}
                    <div className="p-6 rounded-2xl border border-slate-800 bg-[#0f172a]/70 flex flex-col justify-between space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-[11px] font-mono font-bold text-cyan-400 uppercase">
                            BATCH INGESTION PORTAL
                          </span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                            50–100 CAPACITY
                          </span>
                        </div>
                        <h4 className="text-base font-bold text-white">Bulk Resume Intake</h4>
                        <p className="text-xs text-slate-400 font-mono mt-1">
                          Ingest multiple candidate resumes in batch (.pdf, .docx, .txt) with automated multi-agent screening.
                        </p>
                      </div>

                      {/* File selector input */}
                      <div className="p-4 rounded-xl border border-dashed border-slate-700 bg-slate-900/60 text-center space-y-2">
                        <Upload className="w-6 h-6 text-cyan-400 mx-auto" />
                        <label className="cursor-pointer block">
                          <span className="text-xs font-mono font-bold text-cyan-300 hover:underline">
                            Select 50–100 resumes
                          </span>
                          <input
                            type="file"
                            multiple
                            accept=".pdf,.docx,.txt"
                            onChange={(e) => {
                              if (e.target.files) {
                                setUploadedFilesCount(e.target.files.length);
                              }
                            }}
                            className="hidden"
                          />
                        </label>
                        <div className="text-[11px] text-slate-500 font-mono">
                          {uploadedFilesCount > 0
                            ? `✓ ${uploadedFilesCount} files ready for batch processing`
                            : "or drag files into this dropzone"}
                        </div>
                      </div>

                      {/* Simulation Progress or Trigger */}
                      {isIngestingBatch ? (
                        <div className="space-y-2 font-mono text-xs">
                          <div className="flex justify-between text-cyan-300">
                            <span>Screening Batch...</span>
                            <span>{batchProgress}%</span>
                          </div>
                          <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                            <div
                              className="h-full bg-cyan-400 transition-all duration-500 rounded-full"
                              style={{ width: `${batchProgress}%` }}
                            />
                          </div>
                          <div className="text-[10px] text-slate-400 truncate">{batchStageText}</div>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <button
                            onClick={handleSimulateBatchIngest}
                            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-400 hover:to-emerald-400 text-slate-950 font-mono font-bold text-xs transition-all shadow flex items-center justify-center gap-1.5"
                          >
                            <Sparkles className="w-4 h-4" /> Ingest &amp; Screen 50 Diverse Pool
                          </button>
                          <div className="text-[10px] text-slate-500 font-mono text-center">
                            Currently indexing: {candidatesPool.length} active candidates
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* 3. MASTER PROMPT ACCORDION FOR 50-100 RESUMES */}
                  <div className="rounded-2xl border border-slate-800 bg-[#0f172a]/50 overflow-hidden">
                    <button
                      onClick={() => setShowMasterPrompt(!showMasterPrompt)}
                      className="w-full p-4 flex items-center justify-between text-left hover:bg-slate-800/30 transition-colors"
                    >
                      <div className="flex items-center gap-2.5">
                        <span className="text-base">📋</span>
                        <div>
                          <div className="text-xs font-bold text-white font-mono">
                            Master Prompt for Generating 50–100 Synthetic Resumes
                          </div>
                          <div className="text-[11px] text-slate-400 font-mono">
                            Use this prompt in Claude or ChatGPT to generate rich, diverse candidate benchmark sets.
                          </div>
                        </div>
                      </div>
                      <span className="text-xs font-mono text-cyan-400 font-bold">
                        {showMasterPrompt ? "▲ Collapse" : "▼ View Prompt"}
                      </span>
                    </button>

                    {showMasterPrompt && (
                      <div className="p-4 border-t border-slate-800 space-y-3 bg-slate-950/80">
                        <div className="flex justify-between items-center">
                          <span className="text-[11px] font-mono text-slate-400">
                            Copy and paste this into Claude 3.7 / GPT-4o:
                          </span>
                          <button
                            onClick={handleCopyMasterPrompt}
                            className="px-3 py-1.5 rounded-lg bg-cyan-400 hover:bg-cyan-300 text-slate-950 font-mono font-bold text-xs transition-all flex items-center gap-1.5"
                          >
                            {promptCopied ? <CheckCheck className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                            {promptCopied ? "✓ Copied!" : "Copy Master Prompt"}
                          </button>
                        </div>
                        <pre className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-300 whitespace-pre-wrap max-h-64 overflow-y-auto leading-relaxed">
                          {MASTER_RESUME_PROMPT}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              )}"""

if old_job_mgmt in jsx_body:
    jsx_body = jsx_body.replace(old_job_mgmt, new_job_mgmt)
    print("Replaced Job Management section successfully!")
else:
    print("WARNING: Could not find exact old_job_mgmt string in jsx_body!")

# 5. Now replace Chatbot section (around lines 2306-2372)
old_chatbot = """          {/* PAGE 7: RECRUITER CHATBOT (🤖 Recruiter Chatbot)                  */}
          {/* ================================================================ */}
          {activeNav === "chatbot" && (
            <div className="space-y-6">
              <div className="p-5 rounded-2xl border border-[rgba(148,163,184,0.14)] bg-[#0f172a]/70 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="text-[11px] font-mono tracking-widest uppercase text-amber-400 font-bold">
                    Natural Language Talent Retrieval
                  </div>
                  <h1 className="text-2xl font-extrabold tracking-tight mt-0.5">
                    🤖 Recruiter Chatbot (Talent Copilot)
                  </h1>
                  <p className="text-xs text-slate-400 font-mono mt-1">
                    Grounded in the 12 candidate resumes, four-agent council scorecards, and salary leveling bands.
                  </p>
                </div>
                <button
                  onClick={() => alert("Session exported to markdown report.")}
                  className="px-3.5 py-2 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-white font-mono text-xs flex items-center gap-1.5"
                >
                  <Download className="w-4 h-4" /> Export Report (.md)
                </button>
              </div>

              {/* Chat Container */}
              <div className="rounded-2xl border border-[rgba(148,163,184,0.14)] bg-[#0f172a]/40 flex flex-col h-[520px] overflow-hidden">
                <div className="flex-1 p-6 overflow-y-auto space-y-4">
                  {copilotMessages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex gap-3 max-w-2xl ${msg.sender === "user" ? "ml-auto justify-end" : ""}`}
                    >
                      {msg.sender === "assistant" && (
                        <div className="w-8 h-8 rounded-lg bg-emerald-950/60 border border-emerald-800 text-emerald-400 flex items-center justify-center shrink-0 font-mono text-xs font-bold">
                          AI
                        </div>
                      )}
                      <div
                        className={`p-4 rounded-2xl text-xs leading-relaxed ${
                          msg.sender === "user"
                            ? "bg-cyan-500 text-slate-950 font-bold"
                            : "bg-slate-900/90 border border-slate-800 text-slate-200"
                        }`}
                      >
                        <div className="whitespace-pre-wrap font-sans">{msg.text}</div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="p-4 border-t border-slate-800 bg-[#090d16] flex items-center gap-3">
                  <input
                    type="text"
                    placeholder="Ask Yashashwini's AI Copilot anything about the candidate pool..."
                    value={copilotInput}
                    onChange={(e) => setCopilotInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSendCopilot()}
                    className="flex-1 bg-transparent text-xs outline-none font-sans text-white placeholder:text-slate-500"
                  />
                  <button
                    onClick={() => handleSendCopilot()}
                    className="px-4 py-2 rounded-xl bg-cyan-400 text-slate-950 font-mono text-xs font-bold hover:bg-cyan-300 transition-colors flex items-center gap-1.5"
                  >
                    <Send className="w-3.5 h-3.5" /> Send
                  </button>
                </div>
              </div>
            </div>
          )}"""

new_chatbot = """          {/* PAGE 7: RECRUITER CHATBOT (🤖 Recruiter Chatbot)                  */}
          {/* ================================================================ */}
          {activeNav === "chatbot" && (
            <div className="space-y-6">
              <div className="p-5 rounded-2xl border border-[rgba(148,163,184,0.14)] bg-[#0f172a]/70 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="text-[11px] font-mono tracking-widest uppercase text-amber-400 font-bold">
                    Natural Language Talent Retrieval &amp; Explainable RAG
                  </div>
                  <h1 className="text-2xl font-extrabold tracking-tight mt-0.5">
                    🤖 Recruiter Chatbot (Talent Copilot)
                  </h1>
                  <p className="text-xs text-slate-400 font-mono mt-1">
                    Grounded dynamically in the {candidatesPool.length} active candidates, four-agent council debriefs, and {activeRole.title} leveling bands.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      setCopilotMessages([
                        {
                          sender: "assistant",
                          text: `Chat session reset. ${candidatesPool.length} candidates loaded for ${activeRole.title}. Ask me to breakdown headcount, match required skills, audit red flags, or draft candidate outreach emails.`
                        }
                      ]);
                    }}
                    className="px-3 py-1.5 rounded-xl border border-slate-700 bg-slate-800 text-slate-400 hover:text-white font-mono text-xs flex items-center gap-1"
                  >
                    <RefreshCw className="w-3.5 h-3.5" /> Clear History
                  </button>
                  <button
                    onClick={() => alert("Session exported to markdown dossier.")}
                    className="px-3.5 py-1.5 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-white font-mono text-xs flex items-center gap-1.5"
                  >
                    <Download className="w-4 h-4" /> Export Report (.md)
                  </button>
                </div>
              </div>

              {/* Dynamic Suggested Question Pills */}
              <div className="flex flex-wrap gap-2 text-xs font-mono">
                {[
                  "📊 How many members are there in total?",
                  "🎯 Which candidate has the required skills?",
                  "🚨 Who has red flags and why?",
                  "⚔️ Compare Karthik Menon and Rahul Nair",
                  "✉️ Draft outreach email for Karthik",
                  "💰 What is the compensation band?"
                ].map((pill, pIdx) => (
                  <button
                    key={pIdx}
                    onClick={() => handleSendCopilot(pill)}
                    className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-cyan-300 hover:border-cyan-500/60 hover:bg-cyan-950/30 transition-all text-xs"
                  >
                    {pill}
                  </button>
                ))}
              </div>

              {/* Chat Container */}
              <div className="rounded-2xl border border-[rgba(148,163,184,0.14)] bg-[#0f172a]/40 flex flex-col h-[520px] overflow-hidden">
                <div className="flex-1 p-6 overflow-y-auto space-y-4">
                  {copilotMessages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex gap-3 max-w-2xl ${msg.sender === "user" ? "ml-auto justify-end" : ""}`}
                    >
                      {msg.sender === "assistant" && (
                        <div className="w-8 h-8 rounded-lg bg-emerald-950/60 border border-emerald-800 text-emerald-400 flex items-center justify-center shrink-0 font-mono text-xs font-bold">
                          AI
                        </div>
                      )}
                      <div
                        className={`p-4 rounded-2xl text-xs leading-relaxed ${
                          msg.sender === "user"
                            ? "bg-cyan-500 text-slate-950 font-bold"
                            : "bg-slate-900/90 border border-slate-800 text-slate-200"
                        }`}
                      >
                        <div className="whitespace-pre-wrap font-sans">{msg.text}</div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="p-4 border-t border-slate-800 bg-[#090d16] flex items-center gap-3">
                  <input
                    type="text"
                    placeholder="Ask Yashashwini's Talent Copilot anything about the candidate pool or skills..."
                    value={copilotInput}
                    onChange={(e) => setCopilotInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSendCopilot()}
                    className="flex-1 bg-transparent text-xs outline-none font-sans text-white placeholder:text-slate-500"
                  />
                  <button
                    onClick={() => handleSendCopilot()}
                    className="px-4 py-2 rounded-xl bg-cyan-400 text-slate-950 font-mono text-xs font-bold hover:bg-cyan-300 transition-colors flex items-center gap-1.5"
                  >
                    <Send className="w-3.5 h-3.5" /> Send
                  </button>
                </div>
              </div>
            </div>
          )}"""

if old_chatbot in jsx_body:
    jsx_body = jsx_body.replace(old_chatbot, new_chatbot)
    print("Replaced Chatbot section successfully!")
else:
    print("WARNING: Could not find exact old_chatbot string in jsx_body!")

# Combine all into new App.jsx
final_content = import_block + "\n" + state_and_helpers + "\n" + jsx_body

with open("frontend/src/App.jsx", "w", encoding="utf-8") as f:
    f.write(final_content)

print(f"Updated App.jsx successfully! Total size: {len(final_content)} bytes")
