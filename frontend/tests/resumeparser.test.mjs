import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import path from "node:path";
import { role } from "./helpers.mjs";

const root = path.resolve(import.meta.dirname, "..", "src");
const parser = await import(pathToFileURL(path.join(root, "utils", "resumeParserClient.js")).href);

const SAMPLE = `ASHA RAO
Embedded and AI Engineer
Bengaluru, India | asha.rao@example.com | github.com/asha-rao
PROJECTS
Pill Dispenser - IoT Medication System
• Built an ESP32-S3 controller with MQTT; reduced dispensing errors by 40% in tests.
EDUCATION
B.E. - Artificial Intelligence & Machine Learning | Expected: 2027
Diploma - Mechanical Engineering | 2021 - 2024
TECHNICAL SKILLS
Python, FastAPI, Docker, Git, Linux, Deep Learning
WORK EXPERIENCE
Production Intern
Example Automotive Pvt. Ltd. | Jan 2024 - Apr 2024
• Supported quality control on the manufacturing floor.
Vocational Training
Example Training Centre | May 2023 - Jul 2023
`;
const lines = SAMPLE.split("\n").map((l) => l.trim()).filter(Boolean);

describe("uploaded resume parser: name", () => {
  it("takes the name from the first line and tidies capitals", () => {
    assert.equal(parser.extractCandidateName(lines, "Asha_Rao_Resume.pdf"), "Asha Rao");
  });
  it("never uses 'Resume' or 'CV' from the file name as a surname", () => {
    assert.equal(parser.extractCandidateName(["Curriculum Vitae", "Phone: 123"], "Ravi_Kumar_Resume.pdf"), "Ravi Kumar");
    assert.equal(parser.extractCandidateName(["Skills: Python"], "Meena_Iyer_CV.pdf"), "Meena Iyer");
  });
  it("keeps accepting a 'Firstname_Lastname' file name when the text has no name line", () => {
    assert.equal(parser.extractCandidateName(["Summary of work"], "001_Gold_Standard_Senior_ML_Aakash_Deshmukh.txt"), "Aakash Deshmukh");
  });
});

describe("uploaded resume parser: experience", () => {
  const now = new Date(2026, 9, 16);
  it("counts the real months of short jobs and ignores the education dates", () => {
    // Jan-Apr 2024 (4 months) + May-Jul 2023 (3 months) = 7 months; the diploma years must not count.
    assert.equal(parser.estimateExperienceYears(SAMPLE, lines, now), 0.6);
  });
  it("lets an explicit statement win", () => {
    assert.equal(parser.estimateExperienceYears("Over 5 years of experience in ML", ["Over 5 years of experience in ML"], now), 5);
  });
  it("adds up long ranges and does not double count overlaps", () => {
    const l = ["EXPERIENCE", "Engineer | Jan 2020 - Dec 2022", "Lead | Jun 2022 - Present"];
    assert.equal(parser.estimateExperienceYears(l.join("\n"), l, now), 6.8);
  });
  it("counts a resume without any experience as 0 years, not as a default of 3", () => {
    const l = ["Asha Rao", "EDUCATION", "B.E. | 2023 - 2027"];
    assert.equal(parser.estimateExperienceYears(l.join("\n"), l, now), 0);
  });
});

describe("uploaded resume parser: skills", () => {
  it("matches whole words and aliases, not substrings", () => {
    assert.ok(parser.hasSkill("worked with sklearn and postgres", "Scikit-Learn"));
    assert.ok(parser.hasSkill("deployed on k8s", "Kubernetes"));
    assert.ok(parser.hasSkill("nlp research", "Natural Language Processing"));
    assert.ok(!parser.hasSkill("esp32-s3 microcontroller", "AWS S3"), "ESP32-S3 is not the AWS S3 service");
    assert.ok(!parser.hasSkill("a long line of reasoning", "R"));
    assert.ok(parser.hasSkill("stored files on amazon s3", "AWS S3"));
  });
});

describe("uploaded resume parser: PDF text", () => {
  it("starts a new line when the vertical position changes", () => {
    const items = [
      { str: "ASHA", transform: [1, 0, 0, 1, 10, 700] },
      { str: "RAO", transform: [1, 0, 0, 1, 60, 700] },
      { str: "PROFILE", transform: [1, 0, 0, 1, 10, 680] },
      { str: "Mechanical engineer", transform: [1, 0, 0, 1, 10, 664] },
    ];
    assert.equal(parser.pageItemsToText(items), "ASHA RAO\nPROFILE\nMechanical engineer");
  });
});

describe("uploaded resume parser: end to end", () => {
  it("parses a text resume into a candidate with the right name, tenure, evidence and flags", async () => {
    const file = new File([SAMPLE], "Asha_Rao_Resume.txt", { type: "text/plain" });
    const { candidates: [c], rejected } = await parser.parseUploadedFiles([file], role);
    assert.equal(rejected.length, 0);
    assert.equal(c.name, "Asha Rao");
    assert.equal(c.experienceYears, 0.6);
    assert.ok(c.redFlags.includes("EXPERIENCE_DEFICIT"));
    assert.match(c.evidenceSnippet, /reduced dispensing errors by 40%/);
    assert.equal(c.github.username, "asha-rao");
    assert.ok(c.matchedSkills.includes("Python") && c.matchedSkills.includes("Docker"));
  });
});

describe("uploaded resume parser: only resumes are accepted", () => {
  const INVOICE = `INVOICE 2026-0042
Bill to: Example Traders Pvt. Ltd., Bengaluru
Item            Qty    Rate     Amount
Printer paper   10     250      2500
Toner           2      3200     6400
Total due: 8900. Payment within 15 days to account number on file. Thank you for your business.
`.repeat(3);

  it("recognises a resume and rejects an invoice, a short note and a scanned (empty) file", async () => {
    assert.ok(parser.looksLikeResume(SAMPLE));
    assert.ok(!parser.looksLikeResume(INVOICE));
    assert.ok(!parser.looksLikeResume("Meeting notes: call the vendor tomorrow."));
    const files = [
      new File([SAMPLE], "Asha_Rao_Resume.txt", { type: "text/plain" }),
      new File([INVOICE], "invoice_0042.txt", { type: "text/plain" }),
      new File([""], "scan.txt", { type: "text/plain" }),
      new File([SAMPLE], "photo.png", { type: "image/png" }),
    ];
    const { candidates, rejected } = await parser.parseUploadedFiles(files, role);
    assert.deepEqual(candidates.map((c) => c.name), ["Asha Rao"]);
    assert.deepEqual(rejected.map((r) => r.name).sort(), ["invoice_0042.txt", "photo.png", "scan.txt"]);
    assert.match(rejected.find((r) => r.name === "invoice_0042.txt").reason, /not look like a resume/);
  });

  it("accepts every .txt resume of the project's own sample sets", async () => {
    const fs = await import("node:fs");
    const base = path.resolve(import.meta.dirname, "..", "..", "data");
    const dirs = ["sample_resumes", "synthetic_resumes_50", "synthetic_resumes_100"];
    let n = 0;
    for (const dir of dirs) {
      for (const f of fs.readdirSync(path.join(base, dir)).filter((x) => x.endsWith(".txt"))) {
        assert.ok(parser.looksLikeResume(fs.readFileSync(path.join(base, dir, f), "utf8")), `${dir}/${f} rejected`);
        n += 1;
      }
    }
    assert.ok(n >= 100, `only ${n} files checked`);
  });
});

/** A minimal valid PDF whose pages each carry the same lines of text. */
function makePdf(pageCount, lines) {
  const esc = (t) => t.replace(/[\\()]/g, (m) => "\\" + m);
  const body = lines.map((l, i) => `BT /F1 10 Tf 40 ${780 - i * 14} Td (${esc(l)}) Tj ET`).join("\n");
  const objs = [];
  const kids = Array.from({ length: pageCount }, (_, i) => `${4 + i * 2} 0 R`).join(" ");
  objs.push("<< /Type /Catalog /Pages 2 0 R >>");
  objs.push(`<< /Type /Pages /Kids [${kids}] /Count ${pageCount} >>`);
  objs.push("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>");
  for (let i = 0; i < pageCount; i++) {
    objs.push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents ${5 + i * 2} 0 R >>`);
    objs.push(`<< /Length ${body.length} >>\nstream\n${body}\nendstream`);
  }
  let out = "%PDF-1.4\n";
  const offsets = [];
  objs.forEach((o, i) => {
    offsets.push(out.length);
    out += `${i + 1} 0 obj\n${o}\nendobj\n`;
  });
  const xref = out.length;
  out += `xref\n0 ${objs.length + 1}\n0000000000 65535 f \n` + offsets.map((o) => String(o).padStart(10, "0") + " 00000 n \n").join("");
  out += `trailer\n<< /Size ${objs.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF`;
  return out;
}

describe("uploaded resume parser: resumes are at most two pages", () => {
  const resumeLines = SAMPLE.split("\n").map((l) => l.replace(/[^\x20-\x7e]/g, "-")).slice(0, 18);

  it("accepts a two-page PDF and rejects a three-page PDF", async () => {
    const two = new File([makePdf(2, resumeLines)], "two_pages.pdf", { type: "application/pdf" });
    const three = new File([makePdf(3, resumeLines)], "three_pages.pdf", { type: "application/pdf" });
    const { candidates, rejected } = await parser.parseUploadedFiles([two, three], role);
    assert.deepEqual(candidates.length, 1, JSON.stringify(rejected));
    assert.equal(rejected.length, 1);
    assert.equal(rejected[0].name, "three_pages.pdf");
    assert.match(rejected[0].reason, /3 pages; the maximum is 2/);
  });

  it("rejects a TXT resume that is far longer than two pages", async () => {
    const long = new File([SAMPLE + "\n" + "Delivered a measurable improvement in the team's delivery process. ".repeat(160)], "long.txt", { type: "text/plain" });
    const { candidates, rejected } = await parser.parseUploadedFiles([long], role);
    assert.equal(candidates.length, 0);
    assert.match(rejected[0].reason, /too long/);
  });

  it("explains when the text in a photo cannot be read", async () => {
    const photo = new File(["x"], "resume_photo.jpg", { type: "image/jpeg" });
    const { rejected } = await parser.parseUploadedFiles([photo], role);
    assert.match(rejected[0].reason, /Could not read the text in this photo/);
  });
});
