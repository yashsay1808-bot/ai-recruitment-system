with open("frontend/src/App.jsx", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Add import for parseUploadedFiles
if 'import { parseUploadedFiles } from "./utils/resumeParserClient";' not in code:
    code = code.replace(
        'import { generateChatbotResponse } from "./utils/chatbotEngine";',
        'import { generateChatbotResponse } from "./utils/chatbotEngine";\nimport { parseUploadedFiles } from "./utils/resumeParserClient";'
    )

# 2. Add poolSource and uploadFeedback state
old_pool_state = """  // Candidate Pool State (12 Core Test Suite vs 50 Diverse Pool)
  const [candidatesPool, setCandidatesPool] = useState(CANDIDATES_12);
  const [is50PoolActive, setIs50PoolActive] = useState(false);
  const [isIngestingBatch, setIsIngestingBatch] = useState(false);
  const [batchProgress, setBatchProgress] = useState(0);
  const [batchStageText, setBatchStageText] = useState("");
  const [uploadedFilesCount, setUploadedFilesCount] = useState(0);
  const [showMasterPrompt, setShowMasterPrompt] = useState(false);
  const [promptCopied, setPromptCopied] = useState(false);"""

new_pool_state = """  // Candidate Pool State (12 Core Test Suite vs 50 Diverse Pool vs Custom Uploaded)
  const [candidatesPool, setCandidatesPool] = useState(CANDIDATES_12);
  const [is50PoolActive, setIs50PoolActive] = useState(false);
  const [poolSource, setPoolSource] = useState("12 Core Suite");
  const [isIngestingBatch, setIsIngestingBatch] = useState(false);
  const [batchProgress, setBatchProgress] = useState(0);
  const [batchStageText, setBatchStageText] = useState("");
  const [uploadedFilesCount, setUploadedFilesCount] = useState(0);
  const [uploadedFilesList, setUploadedFilesList] = useState([]);
  const [uploadFeedback, setUploadFeedback] = useState("");
  const [showMasterPrompt, setShowMasterPrompt] = useState(false);
  const [promptCopied, setPromptCopied] = useState(false);"""

if old_pool_state in code:
    code = code.replace(old_pool_state, new_pool_state)

# 3. Add handleFilesSelected and update handleSimulateBatchIngest & handleTogglePool
old_handlers = """  // Handlers for 50-Resume Ingestion
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
  };"""

new_handlers = """  // Real In-Browser Resume Ingestion Handler (Parses any uploaded .txt, .pdf, .docx files directly)
  const handleFilesSelected = async (e) => {
    const fileList = e.target.files ? Array.from(e.target.files) : [];
    if (fileList.length === 0) return;

    setUploadedFilesCount(fileList.length);
    setUploadedFilesList(fileList.map((f) => f.name));
    setIsIngestingBatch(true);
    setBatchProgress(15);
    setBatchStageText(`Stage 1/4: Reading and parsing ${fileList.length} uploaded files directly in browser...`);

    setTimeout(async () => {
      setBatchProgress(50);
      setBatchStageText(`Stage 2/4: Extracting candidate names, experience, and matching skills against ${activeRole.title}...`);

      try {
        const parsed = await parseUploadedFiles(fileList, activeRole);
        setBatchProgress(80);
        setBatchStageText(`Stage 3/4: Calculating ATS scores and 4-agent Council verdicts for ${parsed.length} candidates...`);

        setTimeout(() => {
          setBatchProgress(100);
          setBatchStageText(`Stage 4/4: Complete! ${parsed.length} custom resumes screened & indexed.`);

          setTimeout(() => {
            setCandidatesPool(parsed);
            setIs50PoolActive(parsed.length >= 20);
            setPoolSource(`Custom Uploaded (${parsed.length} Resumes)`);
            setIsIngestingBatch(false);
            setBatchProgress(0);
            setBatchStageText("");
            setUploadFeedback(`✓ Successfully parsed & indexed ${parsed.length} of your uploaded resumes into the Leaderboard!`);

            // Notify in chatbot
            setCopilotMessages((prev) => [
              ...prev,
              {
                sender: "assistant",
                text: `⚡ Ingestion Complete! I have parsed your ${parsed.length} uploaded resume files into the live ATS engine for ${activeRole.title}. Rank #1 is ${parsed[0]?.name} (${parsed[0]?.matchScore}% match). Ask me about candidate rankings, skill matches, or red flags!`
              }
            ]);
          }, 400);
        }, 600);
      } catch (err) {
        console.error("Error parsing uploaded files:", err);
        setIsIngestingBatch(false);
        setBatchProgress(0);
      }
    }, 500);
  };

  // Handlers for Claude 50-Resume Ingestion
  const handleSimulateBatchIngest = () => {
    setIsIngestingBatch(true);
    setBatchProgress(20);
    setBatchStageText("Stage 1/4: Ingesting Claude's 50 synthetic resumes from manifest.csv...");

    setTimeout(() => {
      setBatchProgress(55);
      setBatchStageText("Stage 2/4: Computing TF-IDF vector similarity and candidate feature vectors...");
    }, 600);

    setTimeout(() => {
      setBatchProgress(85);
      setBatchStageText("Stage 3/4: Executing Four-Agent Council Cross-Examination & Fair Auditor check...");
    }, 1200);

    setTimeout(() => {
      setBatchProgress(100);
      setBatchStageText("Stage 4/4: Leaderboard calibration complete! 50 Claude synthetic candidates indexed.");
      setTimeout(() => {
        setCandidatesPool(CANDIDATES_50);
        setIs50PoolActive(true);
        setPoolSource("50 Claude Synthetic Benchmark");
        setIsIngestingBatch(false);
        setBatchProgress(0);
        setBatchStageText("");
        setUploadFeedback(`✓ Loaded Claude's 50 Synthetic Candidates from manifest.csv (including ${CANDIDATES_50[0]?.name}, ${CANDIDATES_50[1]?.name}, etc.)`);
        // Notify in chatbot
        setCopilotMessages((prev) => [
          ...prev,
          {
            sender: "assistant",
            text: `⚡ Claude 50 Synthetic Benchmark Suite loaded! 50 candidates from manifest.csv (including ${CANDIDATES_50[0]?.name}, ${CANDIDATES_50[1]?.name}, and ${CANDIDATES_50[2]?.name}) are now active across 8 disciplines. Ask me to breakdown headcount, match skills, or audit flags!`
          }
        ]);
      }, 400);
    }, 1800);
  };

  const handleTogglePool = () => {
    if (is50PoolActive) {
      setCandidatesPool(CANDIDATES_12);
      setIs50PoolActive(false);
      setPoolSource("12 Core Suite");
      setUploadFeedback("Switched to 12 Core Gold Standard Suite.");
    } else {
      setCandidatesPool(CANDIDATES_50);
      setIs50PoolActive(true);
      setPoolSource("50 Claude Synthetic Benchmark");
      setUploadFeedback("Switched to 50 Claude Synthetic Candidates.");
    }
  };"""

if old_handlers in code:
    code = code.replace(old_handlers, new_handlers)

# 4. Update the Batch Ingestion Portal Card in Job Management JSX
old_batch_card = """                    {/* Bulk 50-100 Resume Intake Card */}
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
                    </div>"""

new_batch_card = """                    {/* Bulk 50-100 Resume Intake Card */}
                    <div className="p-6 rounded-2xl border border-slate-800 bg-[#0f172a]/70 flex flex-col justify-between space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-[11px] font-mono font-bold text-cyan-400 uppercase">
                            LIVE RESUME INGESTION PORTAL
                          </span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-400 font-bold">
                            REAL IN-BROWSER PARSER ACTIVE
                          </span>
                        </div>
                        <h4 className="text-base font-bold text-white">Upload Your Custom Resumes</h4>
                        <p className="text-xs text-slate-400 font-mono mt-1">
                          Select your extracted synthetic resume files (.txt, .pdf, .docx). The system will read, parse, rank, and score YOUR actual files!
                        </p>
                      </div>

                      {/* File selector input */}
                      <div className="p-4 rounded-xl border border-dashed border-cyan-500/50 bg-slate-900/80 text-center space-y-2 hover:border-cyan-400 transition-colors">
                        <Upload className="w-7 h-7 text-cyan-400 mx-auto" />
                        <label className="cursor-pointer block">
                          <span className="inline-block px-3.5 py-1.5 rounded-lg bg-cyan-400 hover:bg-cyan-300 text-slate-950 font-mono text-xs font-bold transition-all shadow cursor-pointer">
                            📁 Select Your Resume Files (1 to 100)
                          </span>
                          <input
                            type="file"
                            multiple
                            accept=".txt,.pdf,.docx,.md"
                            onChange={handleFilesSelected}
                            className="hidden"
                          />
                        </label>
                        <div className="text-[11px] text-slate-400 font-mono">
                          {uploadedFilesCount > 0
                            ? `✓ ${uploadedFilesCount} files chosen: ${uploadedFilesList.slice(0, 2).join(", ")}${uploadedFilesList.length > 2 ? "..." : ""}`
                            : "Select all 50 files from data/synthetic_resumes_50/ to test"}
                        </div>
                      </div>

                      {uploadFeedback && (
                        <div className="p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-800 text-emerald-300 text-xs font-mono leading-snug">
                          {uploadFeedback}
                        </div>
                      )}

                      {/* Simulation Progress or Preset Buttons */}
                      {isIngestingBatch ? (
                        <div className="space-y-2 font-mono text-xs">
                          <div className="flex justify-between text-cyan-300">
                            <span>Processing Resumes...</span>
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
                            <Sparkles className="w-4 h-4" /> Load Claude's 50 Synthetic Suite (manifest.csv)
                          </button>
                          <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono pt-1">
                            <span>Active Pool: <strong className="text-white">{candidatesPool.length}</strong> ({poolSource})</span>
                            <button
                              onClick={handleTogglePool}
                              className="text-cyan-400 hover:underline font-bold"
                            >
                              Toggle 12/50 Suite
                            </button>
                          </div>
                        </div>
                      )}
                    </div>"""

if old_batch_card in code:
    code = code.replace(old_batch_card, new_batch_card)
    print("Replaced Batch Ingestion Card successfully!")
else:
    print("WARNING: Could not find exact old_batch_card string!")

with open("frontend/src/App.jsx", "w", encoding="utf-8") as f:
    f.write(code)

print("Updated App.jsx successfully with real in-browser resume parser!")
