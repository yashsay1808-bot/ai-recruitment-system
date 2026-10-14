import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const root = path.resolve(import.meta.dirname, "..", "..");
const srcUrl = (rel) => pathToFileURL(path.join(root, "frontend", "src", rel)).href;

export const loadPool = (name) => JSON.parse(fs.readFileSync(path.join(root, "api", "seed", `${name}.json`), "utf8"));
export const interview = await import(srcUrl("utils/interviewQuestions.js"));
export const chatbot = await import(srcUrl("utils/chatbotEngine.js"));
export const DEFAULT_JOB_ROLES = (await import(srcUrl("data/jobRoles.js"))).DEFAULT_JOB_ROLES;
export const role = DEFAULT_JOB_ROLES[0];

export const first = (name) => name.split(" ")[0];

/** A tiny conversation driver: keeps the history the way App.jsx does (messages carry their meta). */
export function conversation(pool, activeRole = role) {
  const history = [];
  const base = {
    candidatesPool: pool,
    activeRole,
    recruiterName: "Yashaswini R",
    recruiterRole: "Lead Technical Recruiter",
    company: "TechCorp",
  };
  return {
    history,
    ask(query) {
      const reply = chatbot.generateChatbotReply({ ...base, query, history: [...history] });
      history.push({ sender: "user", text: query });
      history.push({ sender: "assistant", text: reply.text, meta: reply.meta, suggestions: reply.suggestions });
      return reply;
    },
  };
}

/** Candidates whose full name occurs once in the pool (the 100-resume pool reuses 50 names). */
export function uniqueNames(pool) {
  const count = {};
  pool.forEach((c) => (count[c.name] = (count[c.name] || 0) + 1));
  return pool.filter((c) => count[c.name] === 1);
}
