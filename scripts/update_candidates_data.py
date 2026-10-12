with open("frontend/src/data/candidatesData.js", "r", encoding="utf-8") as f:
    content = f.read()

idx = content.find("export const CANDIDATES_50 = [")
cand_12 = content[:idx].strip()

new_content = f"""import claudeSynthetic50 from "./claude_synthetic_50.json";

{cand_12}

// Claude's 50 Synthetic Candidates from manifest.csv (Nandini Pandey, Deepa Gowda, Bhavna Ahmed, etc.)
export const CANDIDATES_50 = claudeSynthetic50;
"""

with open("frontend/src/data/candidatesData.js", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Updated candidatesData.js with claude_synthetic_50.json successfully!")
