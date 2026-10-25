import { useEffect, useMemo, useState } from "react";
import { ArrowRight, BarChart3, Upload } from "lucide-react";
import CandidateHover from "./CandidateHover";
import { cohortStats, verdictOf } from "../utils/analytics";

const AVATAR_TONES = ["bg-pink-400", "bg-emerald-400", "bg-violet-400", "bg-amber-400", "bg-sky-400"];
const ringColor = (s) => (s >= 75 ? "#4fd1ae" : s >= 55 ? "#ffb84d" : "#ff7a9c");
const initials = (name) => name.split(/\s+/).map((w) => w[0]).slice(0, 2).join("").toUpperCase();

/** Counts up to `value` once on mount and again whenever it changes (skipped when the user prefers reduced motion). */
function useCountUp(value, decimals = 0) {
  const [shown, setShown] = useState(0);
  useEffect(() => {
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) {
      setShown(value);
      return undefined;
    }
    let raf;
    const start = performance.now();
    const tick = (now) => {
      const t = Math.min(1, (now - start) / 700);
      setShown(value * (1 - (1 - t) ** 3));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value]);
  return shown.toFixed(decimals);
}

function Kpi({ label, value, decimals = 0, suffix = "", note, onClick }) {
  const shown = useCountUp(value, decimals);
  return (
    <button
      type="button"
      onClick={onClick}
      className="group rounded-3xl bg-white p-5 text-left shadow-[0_14px_34px_rgba(11,42,111,0.08)] transition duration-200 hover:-translate-y-1 hover:shadow-[0_22px_44px_rgba(11,42,111,0.14)]"
    >
      <span className="text-xs font-semibold text-slate-500">{label}</span>
      <span className="mt-1 block text-4xl font-extrabold tracking-tight text-slate-900">
        {shown}
        {suffix}
      </span>
      <span className="mt-0.5 flex items-center gap-1 text-xs font-bold text-emerald-600">
        {note}
        <ArrowRight className="h-3 w-3 -translate-x-1 opacity-0 transition group-hover:translate-x-0 group-hover:opacity-100" />
      </span>
    </button>
  );
}

function Ring({ score }) {
  return (
    <span
      className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full"
      style={{ background: `conic-gradient(${ringColor(score)} ${score}%, #e9f0fb 0)` }}
    >
      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-[11px] font-extrabold text-slate-900">
        {Math.round(score)}
      </span>
    </span>
  );
}

/**
 * Top of the home screen: a greeting, the numbers that matter, a clickable hiring funnel and the best three
 * candidates (hover a name for the Explainable AI summary, click to open the deep dive).
 */
export default function DashboardOverview({ firstName, pool, activeRole, roleCount, blind, setActiveNav, onOpenCandidate, onUpload }) {
  const stats = useMemo(() => cohortStats(pool), [pool]);
  const top = useMemo(() => [...pool].sort((a, b) => (b.matchScore || 0) - (a.matchScore || 0)).slice(0, 3), [pool]);
  const funnel = [
    { label: "Screened", n: stats.n, tone: "from-sky-300 to-indigo-500" },
    { label: "Shortlisted", n: stats.shortlist, tone: "from-indigo-400 to-indigo-600" },
    { label: "Strong hire", n: stats.counts.STRONG_HIRE, tone: "from-emerald-300 to-emerald-500" },
  ];

  return (
    <div className="space-y-5">
      <div className="grid items-stretch gap-5 lg:grid-cols-[1.1fr_1fr]">
        <div className="flex flex-col justify-center py-2">
          <h1 className="text-4xl font-extrabold leading-[1.05] tracking-tight text-slate-900 sm:text-5xl">
            Hello {firstName}, let&apos;s find your next hire.
          </h1>
          <p className="mt-4 max-w-lg text-base leading-relaxed text-slate-600">
            Hiring for <b className="text-slate-900">{activeRole.title}</b>. Upload resumes and every candidate is ranked with a plain-English reason, so
            decisions are quick and easy to defend.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={onUpload}
              className="inline-flex items-center gap-2 rounded-full bg-indigo-600 px-6 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-600/25 transition hover:-translate-y-0.5 hover:bg-indigo-700"
            >
              <Upload className="h-4 w-4" /> Upload resumes
            </button>
            <button
              type="button"
              onClick={() => setActiveNav("leaderboard")}
              className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-6 py-3 text-sm font-bold text-slate-900 transition hover:-translate-y-0.5 hover:bg-slate-50"
            >
              <BarChart3 className="h-4 w-4" /> Open leaderboard
            </button>
          </div>
        </div>

        <div className="relative rounded-[28px] bg-gradient-to-br from-sky-400 via-sky-200 to-white p-6 shadow-[0_14px_34px_rgba(11,42,111,0.1)]">
          <h2 className="mb-3 text-xl font-extrabold text-white drop-shadow">Top of the shortlist</h2>
          {top.length === 0 ? (
            <p className="rounded-2xl bg-white/90 p-4 text-sm text-slate-600">No candidates yet. Upload resumes or load a ready-made pool to see the best matches here.</p>
          ) : (
            <ul className="space-y-2.5">
              {top.map((c, i) => (
                <li key={c.id} className="flex items-center gap-3 rounded-2xl bg-white p-3 shadow-sm transition hover:shadow-lg">
                  <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-extrabold text-white ${AVATAR_TONES[i % AVATAR_TONES.length]}`}>
                    {blind ? "#" : initials(c.name)}
                  </span>
                  <span className="min-w-0 flex-1 text-sm font-bold text-slate-900">
                    <CandidateHover cand={c} role={activeRole} blind={blind} onOpen={onOpenCandidate}>
                      {blind ? c.anonymizedId : c.name}
                    </CandidateHover>
                    <span className="block truncate text-xs font-medium text-slate-500">
                      {(c.title || c.role || activeRole.title).toString()} · {verdictOf(c).replace("_", " ").toLowerCase()}
                    </span>
                  </span>
                  <Ring score={c.matchScore || 0} />
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Kpi label="Open roles" value={roleCount} note="View roles" onClick={onUpload} />
        <Kpi label="Resumes screened" value={stats.n} note="Open leaderboard" onClick={() => setActiveNav("leaderboard")} />
        <Kpi label="Shortlisted" value={stats.shortlist} note={`${stats.shortlistRate}% of the pool`} onClick={() => setActiveNav("leaderboard")} />
        <Kpi label="Average match" value={stats.meanMatch} decimals={1} suffix="%" note="See analytics" onClick={() => setActiveNav("analytics")} />
      </div>

      <section className="rounded-3xl bg-white p-6 shadow-[0_14px_34px_rgba(11,42,111,0.08)]">
        <h2 className="text-lg font-extrabold text-slate-900">Hiring funnel</h2>
        <p className="text-sm text-slate-500">How many candidates make it through each stage. Click a bar to see them.</p>
        <div className="mt-4 space-y-3">
          {funnel.map((f) => (
            <button key={f.label} type="button" onClick={() => setActiveNav("leaderboard")} className="group block w-full text-left">
              <div className="mb-1 flex justify-between text-sm font-semibold text-slate-700">
                <span>{f.label}</span>
                <span>{f.n}</span>
              </div>
              <div className="h-3.5 overflow-hidden rounded-full bg-slate-100">
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${f.tone} transition-all duration-700 group-hover:brightness-110`}
                  style={{ width: `${stats.n ? Math.max(f.n ? 4 : 0, (f.n / stats.n) * 100) : 0}%` }}
                />
              </div>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
