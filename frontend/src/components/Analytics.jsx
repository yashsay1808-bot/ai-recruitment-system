import React, { useMemo, useState } from "react";
import {
  VERDICTS,
  VERDICT_META,
  RADAR_AXES,
  cohortStats,
  filterCohort,
  radarValues,
  histogram,
  skillCoverage,
  flagFrequency,
  scatterPoints,
} from "../utils/analytics";

const COHORTS = [{ id: "ALL", label: "Whole pool", color: "#4f46e5", soft: "#e0e7ff" }, ...VERDICTS.map((v) => ({ id: v, ...VERDICT_META[v] }))];

function Card({ title, hint, children, className = "" }) {
  return (
    <section className={`rounded-xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}>
      <h3 className="text-sm font-bold text-slate-900">{title}</h3>
      {hint && <p className="mt-0.5 text-xs text-slate-500">{hint}</p>}
      <div className="mt-4">{children}</div>
    </section>
  );
}

function Kpi({ label, value, sub, color }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="text-[11px] font-mono uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1.5 text-3xl font-bold" style={{ color }}>
        {value}
      </div>
      <div className="mt-0.5 text-xs text-slate-500">{sub}</div>
    </div>
  );
}

/* ---------------------------------------------------------------- donut: how many candidates get which verdict */
function Donut({ stats, cohort, onPick }) {
  const [hover, setHover] = useState(null);
  const R = 70;
  const C = 2 * Math.PI * R;
  const lens = VERDICTS.map((v) => (stats.n ? stats.counts[v] / stats.n : 0) * C);
  const starts = lens.map((_, i) => lens.slice(0, i).reduce((a, b) => a + b, 0));
  const shown = hover || (cohort !== "ALL" ? cohort : null);
  return (
    <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-center">
      <svg viewBox="0 0 200 200" className="h-48 w-48 shrink-0" role="img" aria-label="Verdict split of the pool">
        <circle cx="100" cy="100" r={R} fill="none" stroke="#f1f5f9" strokeWidth="26" />
        {VERDICTS.map((v, i) => {
          const len = lens[i];
          const offset = starts[i];
          return (
            <circle
              key={v}
              cx="100"
              cy="100"
              r={R}
              fill="none"
              stroke={VERDICT_META[v].color}
              strokeWidth={shown === v ? 32 : 26}
              strokeDasharray={`${len} ${C - len}`}
              strokeDashoffset={-offset}
              transform="rotate(-90 100 100)"
              opacity={cohort !== "ALL" && cohort !== v ? 0.3 : 1}
              style={{ cursor: "pointer", transition: "stroke-width .15s, opacity .15s" }}
              onMouseEnter={() => setHover(v)}
              onMouseLeave={() => setHover(null)}
              onClick={() => onPick(cohort === v ? "ALL" : v)}
            >
              <title>{`${VERDICT_META[v].label}: ${stats.counts[v]} of ${stats.n}`}</title>
            </circle>
          );
        })}
        <text x="100" y="96" textAnchor="middle" className="fill-slate-900" style={{ fontSize: 30, fontWeight: 700 }}>
          {shown ? stats.counts[shown] : stats.n}
        </text>
        <text x="100" y="116" textAnchor="middle" className="fill-slate-500" style={{ fontSize: 11 }}>
          {shown ? VERDICT_META[shown].label : "candidates"}
        </text>
      </svg>
      <ul className="w-full space-y-2 text-sm">
        {VERDICTS.map((v) => (
          <li key={v}>
            <button
              onClick={() => onPick(cohort === v ? "ALL" : v)}
              onMouseEnter={() => setHover(v)}
              onMouseLeave={() => setHover(null)}
              className={`flex w-full items-center justify-between rounded-lg border px-3 py-2 text-left transition ${
                cohort === v ? "border-slate-400 bg-slate-50" : "border-slate-200 hover:bg-slate-50"
              }`}
            >
              <span className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-full" style={{ background: VERDICT_META[v].color }} />
                {VERDICT_META[v].label}
              </span>
              <span className="font-mono text-xs text-slate-600">
                {stats.counts[v]} ({stats.n ? Math.round((stats.counts[v] / stats.n) * 100) : 0}%)
              </span>
            </button>
          </li>
        ))}
        <li className="pt-1 text-xs text-slate-500">Click a verdict to focus every chart on that group.</li>
      </ul>
    </div>
  );
}

/* ---------------------------------------------------------------- spider web: strengths of each group */
function Radar({ pool, hoverAxis, setHoverAxis }) {
  const [visible, setVisible] = useState({ ALL: true, STRONG_HIRE: true, LEAN_HIRE: true, REJECT: true });
  const series = useMemo(
    () =>
      COHORTS.map((c) => {
        const list = filterCohort(pool, c.id);
        return { ...c, size: list.length, values: radarValues(list) };
      }).filter((s) => s.size > 0),
    [pool],
  );
  const W = 520;
  const H = 340;
  const cx = W / 2;
  const cy = 168;
  const R = 112;
  const n = RADAR_AXES.length;
  const angle = (i) => (-90 + (360 / n) * i) * (Math.PI / 180);
  const point = (i, v) => [cx + Math.cos(angle(i)) * R * (v / 100), cy + Math.sin(angle(i)) * R * (v / 100)];
  const ring = (v) => RADAR_AXES.map((_, i) => point(i, v).join(",")).join(" ");
  return (
    <div className="space-y-3">
      <div>
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Spider web of average scores by verdict group">
          {[25, 50, 75, 100].map((v) => (
            <polygon key={v} points={ring(v)} fill={v === 100 ? "#f8fafc" : "none"} stroke="#e2e8f0" strokeWidth="1" />
          ))}
          {[25, 50, 75, 100].map((v) => (
            <text key={v} x={cx + 4} y={cy - (R * v) / 100 + 11} className="fill-slate-400" style={{ fontSize: 9 }}>
              {v}
            </text>
          ))}
          {RADAR_AXES.map((a, i) => {
            const [x, y] = point(i, 100);
            const [lx, ly] = [cx + Math.cos(angle(i)) * (R + 20), cy + Math.sin(angle(i)) * (R + 20)];
            const anchor = Math.abs(lx - cx) < 8 ? "middle" : lx > cx ? "start" : "end";
            return (
              <g key={a.key} onMouseEnter={() => setHoverAxis(i)} onMouseLeave={() => setHoverAxis(null)} style={{ cursor: "default" }}>
                <line x1={cx} y1={cy} x2={x} y2={y} stroke={hoverAxis === i ? "#94a3b8" : "#e2e8f0"} strokeWidth={hoverAxis === i ? 1.6 : 1} />
                <text x={lx} y={ly + 4} textAnchor={anchor} className={hoverAxis === i ? "fill-slate-900" : "fill-slate-600"} style={{ fontSize: 12.5, fontWeight: hoverAxis === i ? 700 : 500 }}>
                  {a.label}
                </text>
              </g>
            );
          })}
          {series
            .filter((s) => visible[s.id])
            .map((s) => (
              <g key={s.id}>
                <polygon
                  points={s.values.map((v, i) => point(i, v).join(",")).join(" ")}
                  fill={s.color}
                  fillOpacity={s.id === "ALL" ? 0.08 : 0.16}
                  stroke={s.color}
                  strokeWidth={s.id === "ALL" ? 2 : 2.2}
                  strokeDasharray={s.id === "ALL" ? "5 4" : undefined}
                />
                {s.values.map((v, i) => {
                  const [x, y] = point(i, v);
                  return (
                    <circle key={i} cx={x} cy={y} r={hoverAxis === i ? 5.5 : 3.5} fill="#fff" stroke={s.color} strokeWidth="2" onMouseEnter={() => setHoverAxis(i)} onMouseLeave={() => setHoverAxis(null)}>
                      <title>{`${s.label}: ${RADAR_AXES[i].label} ${v}`}</title>
                    </circle>
                  );
                })}
              </g>
            ))}
        </svg>
        <div className="flex flex-wrap gap-2">
          {series.map((s) => (
            <button
              key={s.id}
              onClick={() => setVisible((v) => ({ ...v, [s.id]: !v[s.id] }))}
              className={`flex items-center gap-2 rounded-full border px-3 py-1 text-xs transition ${visible[s.id] ? "border-slate-300 bg-white" : "border-slate-200 bg-slate-50 text-slate-400"}`}
            >
              <span className="h-2.5 w-2.5 rounded-full" style={{ background: visible[s.id] ? s.color : "#cbd5e1" }} />
              {s.label} ({s.size})
            </button>
          ))}
        </div>
      </div>
      <div className="min-h-[4.5rem] rounded-lg bg-slate-50 p-3 text-xs">
        <div className="mb-2 font-bold text-slate-700">{hoverAxis !== null ? RADAR_AXES[hoverAxis].label : "Hover an axis"}</div>
        {hoverAxis !== null ? (
          <ul className="grid grid-cols-2 gap-x-6 gap-y-1.5">
            {series
              .filter((s) => visible[s.id])
              .map((s) => (
                <li key={s.id} className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full" style={{ background: s.color }} />
                    {s.label}
                  </span>
                  <span className="font-mono font-bold">{s.values[hoverAxis]}</span>
                </li>
              ))}
          </ul>
        ) : (
          <p className="leading-relaxed text-slate-500">
            Each corner is one score out of 100. The further a shape reaches towards a corner, the stronger that group is on it. Compare the green
            (Strong Hire) and red (Reject) shapes to see exactly where rejected candidates fall short.
          </p>
        )}
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- histogram: where the scores fall */
function Histogram({ pool, cohort }) {
  const [hover, setHover] = useState(null);
  const bins = useMemo(() => histogram(pool), [pool]);
  const W = 520;
  const H = 230;
  const m = { l: 30, r: 8, t: 14, b: 28 };
  const maxTotal = Math.max(1, ...bins.map((b) => b.total));
  const bw = (W - m.l - m.r) / bins.length;
  const y = (v) => m.t + (H - m.t - m.b) * (1 - v / maxTotal);
  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Distribution of match scores">
        {[0, 0.5, 1].map((f) => (
          <g key={f}>
            <line x1={m.l} x2={W - m.r} y1={y(maxTotal * f)} y2={y(maxTotal * f)} stroke="#e2e8f0" />
            <text x={m.l - 5} y={y(maxTotal * f) + 3} textAnchor="end" className="fill-slate-400" style={{ fontSize: 9 }}>
              {Math.round(maxTotal * f)}
            </text>
          </g>
        ))}
        {bins.map((b, i) => {
          let acc = 0;
          return (
            <g key={b.from} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}>
              <rect x={m.l + i * bw} y={m.t} width={bw} height={H - m.t - m.b} fill={hover === i ? "#f1f5f9" : "transparent"} />
              {[...VERDICTS].reverse().map((v) => {
                const h = ((H - m.t - m.b) * b.counts[v]) / maxTotal;
                const top = y(0) - acc - h;
                acc += h;
                return h > 0 ? (
                  <rect key={v} x={m.l + i * bw + 5} y={top} width={bw - 10} height={h} rx="2" fill={VERDICT_META[v].color} opacity={cohort !== "ALL" && cohort !== v ? 0.18 : 1} />
                ) : null;
              })}
              <text x={m.l + i * bw + bw / 2} y={H - 10} textAnchor="middle" className="fill-slate-500" style={{ fontSize: 9 }}>
                {b.from}
              </text>
            </g>
          );
        })}
        <text x={W - m.r} y={H - 1} textAnchor="end" className="fill-slate-400" style={{ fontSize: 9 }}>
          match score (%)
        </text>
      </svg>
      <div className="min-h-[2.5rem] rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
        {hover === null ? (
          "Hover a bar to see how many candidates scored in that range and who they are."
        ) : (
          <>
            <b>
              {bins[hover].from}-{bins[hover].to}%:
            </b>{" "}
            {bins[hover].total === 0
              ? "nobody"
              : `${bins[hover].total} candidate${bins[hover].total > 1 ? "s" : ""} (${VERDICTS.filter((v) => bins[hover].counts[v]).map((v) => `${bins[hover].counts[v]} ${VERDICT_META[v].label}`).join(", ")}) - ${bins[hover].names.slice(0, 4).join(", ")}${bins[hover].names.length > 4 ? ", ..." : ""}`}
          </>
        )}
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- scatter: experience against match score */
function Scatter({ pool, cohort }) {
  const [hover, setHover] = useState(null);
  const [pinned, setPinned] = useState(null);
  const pts = useMemo(() => scatterPoints(pool), [pool]);
  const W = 520;
  const H = 260;
  const m = { l: 34, r: 12, t: 12, b: 32 };
  const maxX = Math.max(6, Math.ceil(Math.max(...pts.map((p) => p.x), 0) + 0.5));
  const x = (v) => m.l + ((W - m.l - m.r) * v) / maxX;
  const y = (v) => m.t + (H - m.t - m.b) * (1 - v / 100);
  const active = pts.find((p) => p.id === (hover ?? pinned));
  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Experience against match score">
        {[0, 25, 50, 75, 100].map((v) => (
          <g key={v}>
            <line x1={m.l} x2={W - m.r} y1={y(v)} y2={y(v)} stroke="#e2e8f0" />
            <text x={m.l - 5} y={y(v) + 3} textAnchor="end" className="fill-slate-400" style={{ fontSize: 9 }}>
              {v}
            </text>
          </g>
        ))}
        {Array.from({ length: maxX + 1 }, (_, i) => i).map((v) => (
          <text key={v} x={x(v)} y={H - 14} textAnchor="middle" className="fill-slate-400" style={{ fontSize: 9 }}>
            {v}
          </text>
        ))}
        <text x={W - m.r} y={H - 2} textAnchor="end" className="fill-slate-400" style={{ fontSize: 9 }}>
          years of experience
        </text>
        {pts.map((p) => {
          const dim = cohort !== "ALL" && cohort !== p.verdict;
          const on = p.id === active?.id;
          return (
            <circle
              key={p.id}
              cx={x(p.x)}
              cy={y(p.y)}
              r={on ? 8 : 5.5}
              fill={VERDICT_META[p.verdict].color}
              fillOpacity={dim ? 0.15 : 0.8}
              stroke="#fff"
              strokeWidth="1.5"
              style={{ cursor: "pointer", transition: "r .12s" }}
              onMouseEnter={() => setHover(p.id)}
              onMouseLeave={() => setHover(null)}
              onClick={() => setPinned(pinned === p.id ? null : p.id)}
            />
          );
        })}
      </svg>
      <div className="min-h-[2.5rem] rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
        {active ? (
          <>
            <b className="text-slate-900">{active.name}</b>: {VERDICT_META[active.verdict].label}, {active.y}% match, {active.x} yrs of experience
            {active.flags.length ? `, flags: ${active.flags.map((f) => f.replace(/_/g, " ").toLowerCase()).join(", ")}` : ", no red flags"}
          </>
        ) : (
          "Hover a dot to see the candidate; click it to keep it selected."
        )}
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- horizontal bars */
function Bars({ rows, color, empty }) {
  if (!rows.length) return <p className="text-sm text-slate-500">{empty}</p>;
  return (
    <ul className="space-y-2.5">
      {rows.map((r) => (
        <li key={r.label}>
          <div className="flex justify-between text-xs text-slate-700">
            <span className="truncate pr-2">{r.label}</span>
            <span className="shrink-0 font-mono text-slate-500">
              {r.count} ({r.pct}%)
            </span>
          </div>
          <div className="mt-1 h-2.5 overflow-hidden rounded-full bg-slate-100">
            <div className="h-full rounded-full transition-all duration-500" style={{ width: `${Math.max(r.pct, r.count ? 3 : 0)}%`, background: r.color || color }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

/* ---------------------------------------------------------------- average match score of each group */
function GroupAverages({ pool }) {
  const rows = VERDICTS.map((v) => {
    const list = filterCohort(pool, v);
    return { v, size: list.length, avg: list.length ? Math.round((list.reduce((a, c) => a + Number(c.matchScore || 0), 0) / list.length) * 10) / 10 : 0 };
  }).filter((r) => r.size > 0);
  return (
    <div className="mt-6 border-t border-slate-100 pt-4">
      <div className="mb-2 text-xs font-bold text-slate-700">Average match score of each group</div>
      <ul className="space-y-2.5">
        {rows.map((r) => (
          <li key={r.v}>
            <div className="flex justify-between text-xs text-slate-600">
              <span>{VERDICT_META[r.v].label}</span>
              <span className="font-mono">{r.avg}%</span>
            </div>
            <div className="mt-1 h-2.5 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full rounded-full transition-all duration-500" style={{ width: `${r.avg}%`, background: VERDICT_META[r.v].color }} />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function Analytics({ pool, role }) {
  const [cohort, setCohort] = useState("ALL");
  const [hoverAxis, setHoverAxis] = useState(null);
  const [allSkills, setAllSkills] = useState(false);
  const stats = useMemo(() => cohortStats(pool), [pool]);
  const focus = useMemo(() => filterCohort(pool, cohort), [pool, cohort]);
  const coverage = useMemo(() => skillCoverage(focus, role), [focus, role]);
  const flags = useMemo(() => flagFrequency(focus), [focus]);
  const focusLabel = COHORTS.find((c) => c.id === cohort).label;

  if (!pool.length) {
    return <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-600">Load a candidate pool to see the analytics.</div>;
  }
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="text-[11px] font-mono font-bold uppercase tracking-widest text-indigo-600">Talent acquisition intelligence</div>
        <h1 className="mt-0.5 text-2xl font-extrabold tracking-tight">Recruiter Analytics & Cohort Metrics</h1>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-600">
          <b>What is this page for?</b> It shows the whole applicant pool at a glance, so you can decide where to spend interview time. A cohort is a
          group of candidates with the same verdict, for example all Strong Hires or all Rejects. The charts compare these groups: how many there are,
          what each group is good or weak at, which required skills the pool lacks, and which red flags keep appearing.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="mr-1 text-xs font-mono text-slate-500">Focus on:</span>
          {COHORTS.map((c) => (
            <button
              key={c.id}
              onClick={() => setCohort(c.id)}
              className={`rounded-full border px-3 py-1 text-xs font-medium transition ${cohort === c.id ? "text-white" : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"}`}
              style={cohort === c.id ? { background: c.color, borderColor: c.color } : undefined}
            >
              {c.label} ({c.id === "ALL" ? stats.n : stats.counts[c.id]})
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <Kpi label="Candidates screened" value={stats.n} sub={role?.title || "active role"} color="#0f172a" />
        <Kpi label="Shortlist rate" value={`${stats.shortlistRate}%`} sub={`${stats.shortlist} of ${stats.n} move forward`} color="#059669" />
        <Kpi label="Median match score" value={`${stats.medianMatch}%`} sub={`average ${stats.meanMatch}%`} color="#4f46e5" />
        <Kpi label="Red-flag rate" value={`${stats.flagRate}%`} sub={`${stats.flagged} of ${stats.n} flagged`} color="#d97706" />
        <Kpi label="Clean resume format" value={`${stats.cleanFormatRate}%`} sub={`${stats.cleanFormat} of ${stats.n} parse cleanly`} color="#0891b2" />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card title="Who gets which verdict" hint="The share of the pool in each group. Click a slice to focus the charts below.">
          <Donut stats={stats} cohort={cohort} onPick={setCohort} />
          <GroupAverages pool={pool} />
        </Card>
        <Card title="Spider web: what each group is strong at" hint="Average of six scores for every group. Hover a corner to read the numbers.">
          <Radar pool={pool} hoverAxis={hoverAxis} setHoverAxis={setHoverAxis} />
        </Card>
        <Card title="Score distribution" hint="How many candidates fall in each match-score range, coloured by verdict.">
          <Histogram pool={pool} cohort={cohort} />
        </Card>
        <Card title="Experience against match score" hint="Each dot is a candidate. More experience does not always mean a better match.">
          <Scatter pool={pool} cohort={cohort} />
        </Card>
        <Card title={`Skill coverage: ${focusLabel.toLowerCase()}`} hint={`Share of candidates who show each skill that the ${role?.title || "role"} requires. Short bars are gaps in the pool.`}>
          <Bars
            rows={(allSkills ? coverage : coverage.slice(0, 8)).map((s) => ({ label: s.skill, count: s.count, pct: s.pct, color: s.pct < 25 ? "#e11d48" : s.pct < 50 ? "#d97706" : "#4f46e5" }))}
            empty="No skills are defined for this role."
          />
          {coverage.length > 8 && (
            <button onClick={() => setAllSkills((v) => !v)} className="mt-3 text-xs font-medium text-indigo-600 hover:underline">
              {allSkills ? "Show fewer skills" : `Show all ${coverage.length} skills`}
            </button>
          )}
        </Card>
        <Card title={`Most common red flags: ${focusLabel.toLowerCase()}`} hint="The problems the audit finds most often in this group.">
          <Bars rows={flags.map((f) => ({ label: f.label, count: f.count, pct: f.pct }))} color="#e11d48" empty="No red flags in this group." />
        </Card>
      </div>
    </div>
  );
}
