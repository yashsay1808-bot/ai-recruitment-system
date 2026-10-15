import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { loadPool, chatbot, conversation, role, first, uniqueNames } from "./helpers.mjs";

const pool50 = loadPool("benchmark50"); // 50 distinct names
const pool100 = loadPool("benchmark100"); // 50 names, each used by two different people
const pool12 = loadPool("core12");
const [a, b] = uniqueNames(pool50);

const BROKEN = /undefined|NaN%|\[object/;
const ask = (chat, q) => {
  const reply = chat.ask(q);
  assert.ok(reply.text.length > 20, `empty answer for "${q}"`);
  assert.doesNotMatch(reply.text, BROKEN, `broken text for "${q}"`);
  return reply;
};

describe("chatbot: basics", () => {
  it("greets, explains what it can do, and reports pool statistics", () => {
    const chat = conversation(pool50);
    assert.match(ask(chat, "hi").text, /hello|hi |hey/i);
    assert.match(ask(chat, "what can you do?").text, /Compare and decide/);
    const stats = ask(chat, "How many members are there in total?");
    assert.ok(stats.text.includes(String(pool50.length)));
    assert.ok(stats.suggestions.length >= 3);
  });

  it("keeps the old text-only API", () => {
    assert.equal(typeof chatbot.generateChatbotResponse({ query: "overview", candidatesPool: pool12, activeRole: role }), "string");
  });

  it("copes with an empty query and an empty pool", () => {
    assert.ok(chatbot.generateChatbotReply({ query: "", candidatesPool: pool12, activeRole: role }).text.length > 10);
    assert.match(chatbot.generateChatbotReply({ query: "hi there", candidatesPool: [], activeRole: role }).text, /No candidates are loaded/);
  });
});

describe("chatbot: conversation memory", () => {
  it("resolves 'why?', pronouns and 'interview questions for him' to the candidate just discussed", () => {
    const chat = conversation(pool50);
    assert.ok(ask(chat, `Tell me about ${a.name}`).text.includes(a.name));
    const why = ask(chat, "why?");
    assert.ok(why.text.includes(a.name) && /rated|drives|Council/.test(why.text));
    assert.match(ask(chat, "should I hire her?").text, /Yes,|Maybe|Not on this/);
    const github = ask(chat, "what about his github");
    assert.ok(/GitHub review|repository audit/.test(github.text) && github.text.includes(a.name));
    const kit = ask(chat, "interview questions for him");
    assert.ok(/interview questions for/i.test(kit.text) && kit.text.includes(a.name));
  });

  it("does not hijack pool-wide questions with the previous candidate", () => {
    const chat = conversation(pool50);
    ask(chat, `Tell me about ${a.name}`);
    const flags = ask(chat, "show red flags");
    assert.ok(!flags.text.startsWith("Here is the snapshot") && /flag/i.test(flags.text));
    assert.match(ask(chat, "how many candidates").text, /Verdicts/);
  });

  it("answers a skill question about the candidate in focus", () => {
    const chat = conversation(pool50);
    assert.match(ask(chat, `does ${a.name} know Docker?`).text, /Docker/);
  });

  it("paginates a list and says so when asked for the same list again", () => {
    const chat = conversation(pool50);
    const strong = pool50.filter((c) => c.verdict === "STRONG_HIRE").length;
    const first1 = ask(chat, "Show the strong hires");
    assert.ok(first1.text.includes(`of ${strong}`));
    assert.ok(!first1.text.includes("Lean Hire") && !first1.text.includes("Reject"));
    assert.match(ask(chat, "show more").text, /6–10/);
    const again = ask(chat, "Show the strong hires");
    assert.notEqual(again.text, first1.text);
  });

  it("resolves an ordinal against the list it just showed", () => {
    const chat = conversation(pool50);
    ask(chat, "Show the strong hires");
    const third = pool50.filter((c) => c.verdict === "STRONG_HIRE").sort((x, y) => y.matchScore - x.matchScore)[2];
    assert.ok(ask(chat, "tell me about the third one").text.includes(third.name));
  });

  it("gives a different answer when the same profile is requested twice", () => {
    const chat = conversation(pool50);
    const one = ask(chat, `Tell me about ${b.name}`);
    const two = ask(chat, `Tell me about ${b.name}`);
    assert.notEqual(one.text, two.text);
  });
});

describe("chatbot: duplicate names (100-resume pool)", () => {
  const dupName = pool100[0].name;
  const people = pool100.filter((c) => c.name === dupName);

  it("asks which person is meant and offers distinguishable choices", () => {
    const reply = ask(conversation(pool100), `Tell me about ${dupName}`);
    assert.match(reply.text, /Which one do you mean/);
    assert.ok(people.every((c) => reply.text.includes(`#${c.rank}`)));
    assert.equal(new Set(reply.suggestions).size, reply.suggestions.length);
  });

  it("accepts a rank number or 'the first one'", () => {
    const byRank = ask(conversation(pool100), `Tell me about ${dupName} #${people[1].rank}`);
    assert.ok(byRank.text.includes(people[1].title));
    const chat = conversation(pool100);
    ask(chat, `Tell me about ${dupName}`);
    const picked = ask(chat, "the first one");
    assert.ok(picked.text.includes(people[0].title) && !picked.text.includes(people[1].title));
  });

  it("asks before comparing an ambiguous name", () => {
    const other = pool100.find((c) => c.name !== dupName).name;
    assert.match(ask(conversation(pool100), `compare ${dupName} and ${other}`).text, /Which one do you mean/);
  });
});

describe("chatbot: questions about the pool", () => {
  const chat = conversation(pool50);

  it("compares two named candidates and picks a winner or calls a tie", () => {
    assert.match(ask(chat, `Compare ${a.name} and ${b.name}`).text, /leads on|evenly matched/);
  });

  it("filters by skill, years, verdict, freshers, flags and GitHub risk", () => {
    assert.match(ask(chat, "who has python and docker").text, /match|No candidates/);
    assert.match(ask(chat, "candidates with 5+ years of Python").text, /5\+ years|No candidates match/);
    assert.match(ask(chat, "list the rejected candidates").text, /Reject/);
    assert.match(ask(chat, "show freshers").text, /up to 2 years|No candidates match/);
    assert.match(ask(chat, "who has red flags and why?").text, /carry flags/);
    assert.match(ask(chat, "which candidates have skill stuffing").text, /keyword-heavy|stuff/i);
    assert.match(ask(chat, "which candidates have high github risk?").text, /GitHub risk across/);
    assert.match(ask(chat, "candidates with 40+ years of cobol").text, /No candidates match|Closest matches/);
  });

  it("ranks by a measure and builds a shortlist", () => {
    assert.match(ask(chat, "who is the most experienced candidate?").text, /years of experience/);
    assert.match(ask(chat, "lowest ATS score").text, /Lowest ATS/);
    assert.match(ask(chat, "top 3 candidates").text, /shortlist of 3/);
    assert.match(ask(chat, "top 5 by experience").text, /Highest years of experience/);
    assert.match(ask(chat, "give me a shortlist of 5").text, /shortlist of 5/);
  });

  it("covers the role, the compensation band and score definitions", () => {
    assert.match(ask(chat, "what is the compensation band?").text, /Budget band/);
    assert.match(ask(chat, `what salary does ${b.name} expect`).text, /Compensation for/);
    assert.match(ask(chat, "tell me about the role").text, /How the pool covers them/);
    assert.match(ask(chat, "what is the ATS score?").text, /ATS score:/);
  });
});

describe("chatbot: e-mail drafts", () => {
  const chat = conversation(pool50);

  it("drafts an outreach, an interview invitation and a decline e-mail", () => {
    const outreach = ask(chat, `Draft outreach email for ${b.name}`);
    assert.ok(/Subject:/.test(outreach.text) && outreach.text.includes(first(b.name)));
    assert.match(ask(chat, `draft an interview invitation for ${b.name}`).text, /invitation/i);
    const decline = ask(chat, `write a decline email for ${b.name}`);
    assert.ok(/Subject:/.test(decline.text));
    assert.doesNotMatch(decline.text, /match score|flag|GitHub/i, "a decline e-mail must not leak internal scoring");
  });

  it("asks who the e-mail is for when no candidate is named", () => {
    assert.match(ask(conversation(pool50), "draft an email").text, /Which candidate/);
  });
});

describe("chatbot: fallback and robustness", () => {
  it("is honest about what it did not understand and varies its suggestions", () => {
    const chat = conversation(pool50);
    const one = ask(chat, "blah quantum zebra");
    const two = ask(chat, "blah quantum zebra");
    assert.match(one.text, /couldn't tie/);
    assert.match(two.text, /still can't/);
    assert.notDeepEqual(one.suggestions, two.suggestions);
  });

  it("never prints undefined for candidates with missing fields (e.g. uploaded resumes)", () => {
    const bare = [{ id: "X1", name: "Bare Candidate", rank: 1, matchScore: 50, verdict: "LEAN_HIRE" }];
    const queries = [
      "tell me about Bare Candidate", "overview", "show the strong hires", "who has red flags", "top 3",
      "compare Bare Candidate and nobody", "draft outreach email for Bare Candidate", "salary for Bare Candidate",
      "github for Bare Candidate", "interview questions for Bare Candidate",
    ];
    for (const query of queries) {
      const text = chatbot.generateChatbotReply({ query, candidatesPool: bare, activeRole: { title: "R", skills: [] } }).text;
      assert.doesNotMatch(text, BROKEN, `"${query}" printed a broken value`);
    }
  });

  it("answers named queries on the 12-candidate core pool", () => {
    const chat = conversation(pool12);
    assert.ok(ask(chat, `Tell me about ${pool12[0].name}`).text.includes(pool12[0].name));
    assert.match(ask(chat, `compare ${pool12[0].name} and ${pool12[1].name}`).text, /leads on|evenly/);
  });
});

describe("chatbot: interview questions only for candidates who move forward", () => {
  it("declines to prepare a kit for a rejected candidate and offers the shortlist instead", () => {
    const rejected = pool12.find((c) => c.verdict === "REJECT");
    const chat = conversation(pool12);
    const reply = ask(chat, `interview questions for ${rejected.name}`);
    assert.match(reply.text, /was rejected/i);
    assert.doesNotMatch(reply.text, /\[Technical Verification\]|Look for:/);
    assert.ok(reply.suggestions.some((s) => /shortlist/i.test(s)));
  });

  it("still prepares the kit for a shortlisted candidate", () => {
    const strong = pool12.find((c) => c.verdict === "STRONG_HIRE");
    const reply = ask(conversation(pool12), `interview questions for ${strong.name}`);
    assert.match(reply.text, /interview questions for/i);
    assert.match(reply.text, /Look for:/);
  });
});
