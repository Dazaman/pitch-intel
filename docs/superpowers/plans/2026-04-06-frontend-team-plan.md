# Frontend — Team Module + Explore Implementation Plan (Plan 4 of 5)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add team profile pages, team comparison, and the scatter plot explore page to the Next.js frontend.

**Architecture:** Same pattern as Plan 3 — server components for data fetching, client components for interactive elements. Extends the existing API client with team and explore functions. Recharts for scatter plot.

**Tech Stack:** Next.js 16+ (App Router), TypeScript, Tailwind CSS v4, Recharts

---

## Scope

**Included (Plan 4):**
- Team API client functions + TypeScript interfaces
- Team profile page with hero, squad table, stats
- Team comparison page (2 teams side-by-side)
- Explore scatter plot page
- Navigation links between pages

**Deferred to Plan 5:**
- Team style radar (requires team_profiles computed data)
- Gap analysis tab (requires ML)
- UMAP cluster visualization (requires embeddings)

## File Structure

```
web/
├── lib/
│   └── api.ts                          # Add team + explore interfaces and functions
├── components/
│   ├── team-hero.tsx                   # Team hero card
│   ├── squad-table.tsx                 # Squad members table
│   ├── team-stats-table.tsx            # Team season stats table
│   ├── team-compare-card.tsx           # Team card in comparison view
│   └── scatter-plot.tsx                # Recharts scatter plot
├── app/
│   ├── team/
│   │   └── [reepId]/
│   │       └── page.tsx                # Team profile page
│   ├── compare-teams/
│   │   └── page.tsx                    # Team comparison page
│   └── explore/
│       └── page.tsx                    # Scatter plot explore page
```

---

### Task 1: Extend API Client with Team + Explore Functions

**Files:**
- Modify: `web/lib/api.ts`

- [ ] **Step 1: Add team and explore interfaces and functions**

Append to the end of `web/lib/api.ts`:

```typescript
export interface TeamProfile {
  reep_id: string;
  name: string;
  country?: string;
  founded?: string;
  stadium?: string;
  key_transfermarkt?: string;
  key_fbref?: string;
}

export interface TeamSeasonStats {
  season: string;
  league: string;
  source: string;
  wins?: number;
  draws?: number;
  losses?: number;
  goals_for?: number;
  goals_against?: number;
  xg?: number;
  xga?: number;
  ppda?: number;
  elo_start?: number;
  elo_end?: number;
}

export interface SquadMember {
  reep_id: string;
  name: string;
  position?: string;
  nationality?: string;
  date_of_birth?: string;
  minutes_played?: number;
  goals?: number;
  assists?: number;
  xg?: number;
}

export interface ScatterPoint {
  reep_id: string;
  name: string;
  position?: string;
  league: string;
  x_value?: number;
  y_value?: number;
}

export async function getTeam(reepId: string): Promise<TeamProfile> {
  return fetchApi<TeamProfile>(`/team/${reepId}`);
}

export async function getTeamStats(
  reepId: string,
  season?: string,
): Promise<TeamSeasonStats[]> {
  const params = season ? `?season=${season}` : "";
  return fetchApi<TeamSeasonStats[]>(`/team/${reepId}/stats${params}`);
}

export async function getTeamSquad(
  reepId: string,
  season: string,
): Promise<SquadMember[]> {
  return fetchApi<SquadMember[]>(`/team/${reepId}/squad?season=${season}`);
}

export async function getCompareTeams(
  ids: string[],
): Promise<Record<string, { name: string; seasons: TeamSeasonStats[] }>> {
  return fetchApi(`/compare/teams?ids=${ids.join(",")}`);
}

export async function getScatter(
  x: string,
  y: string,
  league?: string,
  position?: string,
): Promise<ScatterPoint[]> {
  const params = new URLSearchParams({ x, y });
  if (league) params.set("league", league);
  if (position) params.set("position", position);
  return fetchApi<ScatterPoint[]>(`/explore/scatter?${params}`);
}
```

- [ ] **Step 2: Type check**

Run: `cd web && npx tsc --noEmit`

- [ ] **Step 3: Commit**

```bash
git add lib/api.ts
git commit -m "feat: add team and explore API client functions"
```

---

### Task 2: Team Hero Card

**Files:**
- Create: `web/components/team-hero.tsx`

- [ ] **Step 1: Create team hero component**

Create `web/components/team-hero.tsx`:

```tsx
import type { TeamProfile } from "@/lib/api";

export default function TeamHero({ team }: { team: TeamProfile }) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
      <div className="flex items-start gap-6">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gray-800 text-2xl font-bold text-gray-500">
          {team.name.charAt(0)}
        </div>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">{team.name}</h1>
          <div className="mt-3 flex flex-wrap gap-3">
            {team.country && (
              <span className="rounded-full bg-gray-800 px-3 py-1 text-sm text-gray-300">
                {team.country}
              </span>
            )}
            {team.stadium && (
              <span className="rounded-full bg-gray-800 px-3 py-1 text-sm text-gray-300">
                {team.stadium}
              </span>
            )}
            {team.founded && (
              <span className="rounded-full bg-gray-800 px-3 py-1 text-sm text-gray-300">
                Est. {team.founded}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Type check + commit**

```bash
cd web && npx tsc --noEmit
git add components/team-hero.tsx
git commit -m "feat: team hero card component"
```

---

### Task 3: Squad Table + Team Stats Table

**Files:**
- Create: `web/components/squad-table.tsx`
- Create: `web/components/team-stats-table.tsx`

- [ ] **Step 1: Create squad table**

Create `web/components/squad-table.tsx`:

```tsx
import type { SquadMember } from "@/lib/api";

function calculateAge(dob: string): number | null {
  const birth = new Date(dob);
  if (isNaN(birth.getTime())) return null;
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const m = today.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
  return age;
}

export default function SquadTable({ squad }: { squad: SquadMember[] }) {
  if (squad.length === 0) {
    return <p className="text-gray-500">No squad data available.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-800 text-left text-gray-400">
            <th className="px-3 py-2 font-medium">Name</th>
            <th className="px-3 py-2 font-medium">Position</th>
            <th className="px-3 py-2 font-medium">Nationality</th>
            <th className="px-3 py-2 font-medium">Age</th>
            <th className="px-3 py-2 font-medium text-right">Min</th>
            <th className="px-3 py-2 font-medium text-right">G</th>
            <th className="px-3 py-2 font-medium text-right">A</th>
            <th className="px-3 py-2 font-medium text-right">xG</th>
          </tr>
        </thead>
        <tbody>
          {squad.map((p) => (
            <tr key={p.reep_id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
              <td className="px-3 py-2">
                <a
                  href={`/player/${p.reep_id}`}
                  className="text-blue-400 hover:underline"
                >
                  {p.name}
                </a>
              </td>
              <td className="px-3 py-2 text-gray-400">{p.position ?? "-"}</td>
              <td className="px-3 py-2 text-gray-400">{p.nationality ?? "-"}</td>
              <td className="px-3 py-2 text-gray-400">
                {p.date_of_birth ? calculateAge(p.date_of_birth) ?? "-" : "-"}
              </td>
              <td className="px-3 py-2 text-right">{p.minutes_played ?? "-"}</td>
              <td className="px-3 py-2 text-right">{p.goals ?? "-"}</td>
              <td className="px-3 py-2 text-right">{p.assists ?? "-"}</td>
              <td className="px-3 py-2 text-right">
                {p.xg !== undefined && p.xg !== null ? p.xg.toFixed(1) : "-"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 2: Create team stats table**

Create `web/components/team-stats-table.tsx`:

```tsx
import type { TeamSeasonStats } from "@/lib/api";

const COLUMNS: { key: keyof TeamSeasonStats; label: string; align?: "right" }[] = [
  { key: "season", label: "Season" },
  { key: "league", label: "League" },
  { key: "wins", label: "W", align: "right" },
  { key: "draws", label: "D", align: "right" },
  { key: "losses", label: "L", align: "right" },
  { key: "goals_for", label: "GF", align: "right" },
  { key: "goals_against", label: "GA", align: "right" },
  { key: "xg", label: "xG", align: "right" },
  { key: "xga", label: "xGA", align: "right" },
  { key: "ppda", label: "PPDA", align: "right" },
  { key: "elo_end", label: "Elo", align: "right" },
];

function fmt(value: unknown): string {
  if (value === null || value === undefined) return "-";
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(1);
  }
  return String(value);
}

export default function TeamStatsTable({ stats }: { stats: TeamSeasonStats[] }) {
  if (stats.length === 0) {
    return <p className="text-gray-500">No stats available.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-800 text-left text-gray-400">
            {COLUMNS.map((col) => (
              <th
                key={col.key}
                className={`px-2 py-2 font-medium whitespace-nowrap ${col.align === "right" ? "text-right" : ""}`}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {stats.map((row, i) => (
            <tr key={i} className="border-b border-gray-800/50 hover:bg-gray-800/30">
              {COLUMNS.map((col) => (
                <td
                  key={col.key}
                  className={`px-2 py-2 whitespace-nowrap ${col.align === "right" ? "text-right" : ""}`}
                >
                  {fmt(row[col.key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 3: Type check + commit**

```bash
cd web && npx tsc --noEmit
git add components/squad-table.tsx components/team-stats-table.tsx
git commit -m "feat: squad table and team stats table components"
```

---

### Task 4: Team Profile Page

**Files:**
- Create: `web/app/team/[reepId]/page.tsx`

- [ ] **Step 1: Create the team profile page**

Create `web/app/team/[reepId]/page.tsx`:

```tsx
import { getTeam, getTeamStats, getTeamSquad } from "@/lib/api";
import TeamHero from "@/components/team-hero";
import TeamStatsTable from "@/components/team-stats-table";
import SquadTable from "@/components/squad-table";

interface Props {
  params: Promise<{ reepId: string }>;
  searchParams: Promise<{ season?: string }>;
}

export default async function TeamPage({ params, searchParams }: Props) {
  const { reepId } = await params;
  const { season } = await searchParams;
  const currentSeason = season || "2025-2026";

  let team, stats, squad;
  try {
    [team, stats, squad] = await Promise.all([
      getTeam(reepId),
      getTeamStats(reepId),
      getTeamSquad(reepId, currentSeason),
    ]);
  } catch {
    return (
      <div className="text-center py-20">
        <h1 className="text-2xl font-bold text-gray-400">Team not found</h1>
        <p className="text-gray-500 mt-2">Could not load data for {reepId}</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <TeamHero team={team} />

      <section>
        <h2 className="text-xl font-semibold mb-4">Season Stats</h2>
        <TeamStatsTable stats={stats} />
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-4">
          Squad ({currentSeason})
        </h2>
        <SquadTable squad={squad} />
      </section>
    </div>
  );
}
```

- [ ] **Step 2: Type check + commit**

```bash
cd web && npx tsc --noEmit
git add app/team/
git commit -m "feat: team profile page with stats and squad"
```

---

### Task 5: Team Comparison Page

**Files:**
- Create: `web/components/team-compare-card.tsx`
- Create: `web/app/compare-teams/page.tsx`

- [ ] **Step 1: Create team compare card**

Create `web/components/team-compare-card.tsx`:

```tsx
import type { TeamSeasonStats } from "@/lib/api";
import TeamStatsTable from "./team-stats-table";

interface Props {
  name: string;
  seasons: TeamSeasonStats[];
}

export default function TeamCompareCard({ name, seasons }: Props) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
      <h3 className="text-lg font-semibold mb-3">{name}</h3>
      <TeamStatsTable stats={seasons} />
    </div>
  );
}
```

- [ ] **Step 2: Create team comparison page**

Create `web/app/compare-teams/page.tsx`:

```tsx
import { getCompareTeams } from "@/lib/api";
import TeamCompareCard from "@/components/team-compare-card";

interface Props {
  searchParams: Promise<{ t?: string | string[] }>;
}

export default async function CompareTeamsPage({ searchParams }: Props) {
  const sp = await searchParams;
  const rawIds = sp.t;
  const ids = Array.isArray(rawIds) ? rawIds : rawIds ? [rawIds] : [];

  if (ids.length === 0) {
    return (
      <div className="text-center py-20">
        <h1 className="text-2xl font-bold">Compare Teams</h1>
        <p className="text-gray-400 mt-2">
          Add teams via URL: /compare-teams?t=reep_id1&amp;t=reep_id2
        </p>
      </div>
    );
  }

  let data;
  try {
    data = await getCompareTeams(ids.slice(0, 2));
  } catch {
    return (
      <div className="text-center py-20">
        <h1 className="text-2xl font-bold text-gray-400">Could not load team data</h1>
      </div>
    );
  }

  const entries = Object.entries(data);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Compare Teams</h1>
      <div className="grid gap-6 grid-cols-1 md:grid-cols-2">
        {entries.map(([reepId, team]) => (
          <TeamCompareCard
            key={reepId}
            name={team.name}
            seasons={team.seasons}
          />
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Type check + commit**

```bash
cd web && npx tsc --noEmit
git add components/team-compare-card.tsx app/compare-teams/
git commit -m "feat: team comparison page"
```

---

### Task 6: Scatter Plot Component

**Files:**
- Create: `web/components/scatter-plot.tsx`

- [ ] **Step 1: Create the scatter plot component**

Create `web/components/scatter-plot.tsx`:

```tsx
"use client";

import { useRouter } from "next/navigation";
import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { ScatterPoint } from "@/lib/api";

const POSITION_COLORS: Record<string, string> = {
  "centre-forward": "#ef4444",
  "second striker": "#f97316",
  "left winger": "#eab308",
  "right winger": "#eab308",
  "attacking midfielder": "#22c55e",
  "central midfield": "#3b82f6",
  "defensive midfield": "#6366f1",
  "left-back": "#8b5cf6",
  "right-back": "#8b5cf6",
  "centre-back": "#a855f7",
  goalkeeper: "#ec4899",
};

function formatStatLabel(stat: string): string {
  return stat
    .replace(/_per90$/, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

interface Props {
  data: ScatterPoint[];
  xStat: string;
  yStat: string;
}

export default function ScatterPlotChart({ data, xStat, yStat }: Props) {
  const router = useRouter();

  if (data.length === 0) {
    return <p className="text-gray-500">No data for the selected filters.</p>;
  }

  const chartData = data.map((p) => ({
    x: p.x_value ?? 0,
    y: p.y_value ?? 0,
    name: p.name,
    position: p.position ?? "unknown",
    reep_id: p.reep_id,
    fill: POSITION_COLORS[p.position ?? ""] ?? "#6b7280",
  }));

  return (
    <ResponsiveContainer width="100%" height={500}>
      <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis
          type="number"
          dataKey="x"
          name={formatStatLabel(xStat)}
          tick={{ fill: "#9ca3af", fontSize: 11 }}
          label={{
            value: formatStatLabel(xStat),
            position: "bottom",
            fill: "#9ca3af",
            fontSize: 12,
          }}
        />
        <YAxis
          type="number"
          dataKey="y"
          name={formatStatLabel(yStat)}
          tick={{ fill: "#9ca3af", fontSize: 11 }}
          label={{
            value: formatStatLabel(yStat),
            angle: -90,
            position: "left",
            fill: "#9ca3af",
            fontSize: 12,
          }}
        />
        <ZAxis range={[40, 40]} />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1f2937",
            border: "1px solid #374151",
            borderRadius: "8px",
          }}
          labelStyle={{ color: "#f3f4f6" }}
          formatter={(value: number) => value.toFixed(2)}
          labelFormatter={(_: unknown, payload: Array<{ payload?: { name?: string } }>) =>
            payload?.[0]?.payload?.name ?? ""
          }
        />
        <Scatter
          data={chartData}
          onClick={(point) => {
            if (point?.reep_id) router.push(`/player/${point.reep_id}`);
          }}
          cursor="pointer"
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
```

- [ ] **Step 2: Type check + commit**

```bash
cd web && npx tsc --noEmit
git add components/scatter-plot.tsx
git commit -m "feat: scatter plot component with Recharts"
```

---

### Task 7: Explore Page

**Files:**
- Create: `web/app/explore/page.tsx`

- [ ] **Step 1: Create the explore page**

Create `web/app/explore/page.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { getScatter, type ScatterPoint } from "@/lib/api";
import ScatterPlotChart from "@/components/scatter-plot";

const STATS = [
  "goals_per90",
  "xg_per90",
  "assists_per90",
  "xa_per90",
  "shots_per90",
  "key_passes_per90",
  "progressive_passes_per90",
  "progressive_carries_per90",
  "tackles_per90",
  "interceptions_per90",
  "pressures_per90",
  "take_ons_per90",
];

const LEAGUES = [
  "Premier League",
  "La Liga",
  "Serie A",
  "Bundesliga",
  "Ligue 1",
];

const POSITIONS = ["FW", "MF", "DF", "GK"];

function formatLabel(stat: string): string {
  return stat
    .replace(/_per90$/, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function ExplorePage() {
  const [xStat, setXStat] = useState("xg_per90");
  const [yStat, setYStat] = useState("goals_per90");
  const [league, setLeague] = useState("");
  const [position, setPosition] = useState("");
  const [data, setData] = useState<ScatterPoint[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setIsLoading(true);
    getScatter(
      xStat,
      yStat,
      league || undefined,
      position || undefined,
    )
      .then(setData)
      .catch(() => setData([]))
      .finally(() => setIsLoading(false));
  }, [xStat, yStat, league, position]);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Explore Players</h1>

      <div className="flex flex-wrap gap-4 mb-6">
        <div>
          <label className="block text-sm text-gray-400 mb-1">X Axis</label>
          <select
            value={xStat}
            onChange={(e) => setXStat(e.target.value)}
            className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm"
          >
            {STATS.map((s) => (
              <option key={s} value={s}>
                {formatLabel(s)}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-1">Y Axis</label>
          <select
            value={yStat}
            onChange={(e) => setYStat(e.target.value)}
            className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm"
          >
            {STATS.map((s) => (
              <option key={s} value={s}>
                {formatLabel(s)}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-1">League</label>
          <select
            value={league}
            onChange={(e) => setLeague(e.target.value)}
            className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm"
          >
            <option value="">All Leagues</option>
            {LEAGUES.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-1">Position</label>
          <select
            value={position}
            onChange={(e) => setPosition(e.target.value)}
            className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm"
          >
            <option value="">All Positions</option>
            {POSITIONS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
      </div>

      {isLoading ? (
        <p className="text-gray-500">Loading...</p>
      ) : (
        <ScatterPlotChart data={data} xStat={xStat} yStat={yStat} />
      )}

      <p className="mt-4 text-sm text-gray-500">
        {data.length} players shown. Click a point to view player profile.
      </p>
    </div>
  );
}
```

- [ ] **Step 2: Type check + commit**

```bash
cd web && npx tsc --noEmit
git add app/explore/
git commit -m "feat: explore page with scatter plot builder"
```

---

### Task 8: Build Verification

- [ ] **Step 1: TypeScript check**

Run: `cd web && npx tsc --noEmit`

- [ ] **Step 2: ESLint**

Run: `cd web && pnpm lint`

Fix any issues.

- [ ] **Step 3: Production build**

Run: `cd web && pnpm build`

Expected: Build succeeds with routes for /, /team/[reepId], /compare-teams, /explore.

- [ ] **Step 4: Commit any fixes + push**

```bash
cd /Users/mazam1/GitHub/personal/portfolio/pitch-intel
git add -A && git commit -m "fix: lint and build adjustments"
git push origin main
```

---

## Summary

| Task | What it builds | Verification |
|------|---------------|--------------|
| 1 | Team + explore API functions | `tsc` |
| 2 | Team hero card | `tsc` |
| 3 | Squad table + team stats table | `tsc` |
| 4 | Team profile page | `tsc` + visual |
| 5 | Team comparison page | `tsc` + visual |
| 6 | Scatter plot component | `tsc` |
| 7 | Explore page | `tsc` + visual |
| 8 | Full build verification | `pnpm build` |

**After this plan:** All frontend pages are built except ML-powered features (similar players, fit analysis, team style radar, gap analysis, UMAP clusters) which are Plan 5.
