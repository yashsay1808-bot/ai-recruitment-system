with open("frontend/src/App.jsx", "r", encoding="utf-8") as f:
    text = f.read()

# Replace Claude mentions with clean, professional enterprise terminology
text = text.replace(
    'setBatchStageText("Stage 1/4: Ingesting Claude\'s 50 synthetic resumes from manifest.csv...");',
    'setBatchStageText("Stage 1/4: Ingesting 50 benchmark candidate resumes from verified dataset...");'
)
text = text.replace(
    'setBatchStageText("Stage 4/4: Leaderboard calibration complete! 50 Claude synthetic candidates indexed.");',
    'setBatchStageText("Stage 4/4: Leaderboard calibration complete! 50 benchmark candidates indexed.");'
)
text = text.replace(
    'setPoolSource("50 Claude Synthetic Benchmark");',
    'setPoolSource("50 Benchmark Resumes Pool");'
)
text = text.replace(
    '`✓ Loaded Claude\'s 50 Synthetic Candidates from manifest.csv (including ${CANDIDATES_50[0]?.name}, ${CANDIDATES_50[1]?.name}, etc.)`',
    '`✓ Loaded 50 Benchmark Candidates (including ${CANDIDATES_50[0]?.name}, ${CANDIDATES_50[1]?.name}, etc.)`'
)
text = text.replace(
    'text: `⚡ Claude 50 Synthetic Benchmark Suite loaded! 50 candidates from manifest.csv (including ${CANDIDATES_50[0]?.name}, ${CANDIDATES_50[1]?.name}, and ${CANDIDATES_50[2]?.name}) are now active across 8 disciplines. Ask me to breakdown headcount, match skills, or audit flags!`',
    'text: `⚡ 50 Benchmark Candidate Resumes loaded! 50 verified profiles (including ${CANDIDATES_50[0]?.name}, ${CANDIDATES_50[1]?.name}, and ${CANDIDATES_50[2]?.name}) are now active across 8 disciplines. Ask me to breakdown headcount, match skills, or audit flags!`'
)
text = text.replace(
    'setUploadFeedback("Switched to 50 Claude Synthetic Candidates.");',
    'setUploadFeedback("Switched to 50 Benchmark Candidate Resumes.");'
)
text = text.replace(
    '<Sparkles className="w-4 h-4" /> Load Claude\'s 50 Synthetic Suite (manifest.csv)',
    '<Sparkles className="w-4 h-4" /> Load 50 Benchmark Resumes (Pre-Screened Suite)'
)
text = text.replace(
    'Use this prompt in Claude or ChatGPT to generate rich, diverse candidate benchmark sets.',
    'Use this prompt to generate rich, diverse synthetic candidate benchmark batches (50 to 100+ resumes).'
)
text = text.replace(
    'Copy and paste this into Claude 3.7 / GPT-4o:',
    'Copy and paste this into your LLM to generate candidate resume batches:'
)

with open("frontend/src/App.jsx", "w", encoding="utf-8") as f:
    f.write(text)

print("Replaced all Claude references in App.jsx successfully!")
