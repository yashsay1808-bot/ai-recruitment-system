import React, { useRef, useState } from "react";
import { explainCandidate } from "../utils/explain";
import { VERDICT_META, verdictOf } from "../utils/analytics";

const AGENTS = [
  ["techLead", "Tech Lead"],
  ["culture", "Culture"],
  ["fairAuditor", "Fair Auditor"],
  ["seniorityComp", "Seniority"],
];
const TONE = { good: "text-emerald-700", warn: "text-amber-700", bad: "text-rose-700" };
const MARK = { good: "✓", warn: "!", bad: "✕" };

/**
 * Wraps a candidate name. Hovering (or tapping) it opens a summary of the deep dive: council scores, the reasons
 * behind the verdict (Explainable AI) and a button to the full dossier. The card is fixed-positioned so that parents
 * with overflow hidden cannot clip it.
 */
export default function CandidateHover({ cand, role, blind, onOpen, children }) {
  const [pos, setPos] = useState(null);
  const ref = useRef(null);
  const timer = useRef(null);
  const meta = VERDICT_META[verdictOf(cand)];

  const show = () => {
    clearTimeout(timer.current);
    const r = ref.current.getBoundingClientRect();
    const width = Math.min(360, window.innerWidth - 24);
    const below = window.innerHeight - r.bottom > 380;
    setPos({
      left: Math.max(12, Math.min(r.left, window.innerWidth - width - 12)),
      top: below ? r.bottom + 6 : Math.max(12, r.top - 6 - 380),
      width,
    });
  };
  const hide = () => {
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setPos(null), 180);
  };
  const { reasons, verdictText } = pos ? explainCandidate(cand, role) : { reasons: [], verdictText: "" };

  return (
    <span ref={ref} className="inline-block" onMouseEnter={show} onMouseLeave={hide} onFocus={show} onBlur={hide}>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          if (pos) setPos(null);
          else show();
        }}
        className="cursor-pointer border-b border-dashed border-indigo-300 text-left hover:text-indigo-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-300"
        aria-haspopup="dialog"
        aria-expanded={Boolean(pos)}
      >
        {children}
      </button>
      {pos && (
        <div
          role="dialog"
          aria-label={`Deep dive summary of ${blind ? cand.anonymizedId : cand.name}`}
          style={{ position: "fixed", left: pos.left, top: pos.top, width: pos.width, zIndex: 60 }}
          className="rounded-xl border border-slate-200 bg-white p-4 text-left font-sans shadow-2xl shadow-slate-900/20"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-sm font-bold text-slate-900">{blind ? cand.anonymizedId : cand.name}</div>
              <div className="text-xs text-slate-500">
                #{cand.rank} · {cand.title} · {cand.experienceYears} yrs
              </div>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold" style={{ color: meta.color }}>
                {Number(cand.matchScore).toFixed(1)}%
              </div>
              <div className="rounded-full px-2 py-0.5 text-[10px] font-bold" style={{ background: meta.soft, color: meta.color }}>
                {meta.label}
              </div>
            </div>
          </div>

          <div className="mt-3 grid grid-cols-4 gap-2">
            {AGENTS.map(([key, label]) => {
              const v = cand.council?.[key]?.score ?? 0;
              return (
                <div key={key} className="rounded-lg bg-slate-50 p-2 text-center">
                  <div className="text-sm font-bold text-slate-900">{v}</div>
                  <div className="text-[9px] uppercase tracking-wide text-slate-500">{label}</div>
                </div>
              );
            })}
          </div>

          <div className="mt-3 text-[11px] font-bold uppercase tracking-wide text-indigo-600">Explainable AI: why this verdict</div>
          <p className="mt-1 text-xs leading-snug text-slate-600">{verdictText}</p>
          <ul className="mt-2 space-y-1">
            {reasons.slice(0, 4).map((r, i) => (
              <li key={i} className={`flex gap-1.5 text-xs leading-snug ${TONE[r.tone]}`}>
                <span className="font-bold">{MARK[r.tone]}</span>
                <span className="text-slate-700">{r.text}</span>
              </li>
            ))}
          </ul>

          <button
            type="button"
            onClick={() => {
              setPos(null);
              onOpen(cand);
            }}
            className="mt-3 w-full rounded-lg bg-indigo-600 px-3 py-2 text-xs font-semibold text-white hover:bg-indigo-700"
          >
            Open full deep dive
          </button>
        </div>
      )}
    </span>
  );
}
