# Frontend — Player Module Implementation Plan (Plan 3 of 5)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Next.js frontend with home/search page and full player module (profile, stats, radar chart, shot map, player comparison).

**Architecture:** Next.js App Router with server components for data fetching, client components for interactive charts. API calls go to the FastAPI backend (Plan 2). Recharts for radar/charts, custom SVG for shot map pitch visualization.

**Tech Stack:** Next.js 16+ (App Router), TypeScript, Tailwind CSS v4, Recharts, pnpm

---

## Scope

**Included (Plan 3):**
- Next.js project setup in `web/` directory
- Home page with search bar and player/team toggle
- Player profile page with hero card, stats table, radar chart, shot map
- Player comparison page (up to 4 players, side-by-side radars)
- API client for FastAPI backend
- Responsive layout with Tailwind

**Deferred:**
- Team pages (Plan 4)
- Explore/scatter page (Plan 4)
- ML-powered features: similar players, fit analysis (Plan 5)

## File Structure

```
pitch-intel/
└── web/
    ├── package.json
    ├── next.config.ts
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── src/
    │   ├── app/
    │   │   ├── layout.tsx              # Root layout with font, metadata
    │   │   ├── page.tsx                # Home: search bar + results
    │   │   ├── player/
    │   │   │   └── [reepId]/
    │   │   │       └── page.tsx        # Player profile page
    │   │   └── compare/
    │   │       └── page.tsx            # Player comparison page
    │   ├── lib/
    │   │   └── api.ts                  # API client functions
    │   └── components/
    │       ├── search-bar.tsx          # Search input with debounce + results dropdown
    │       ├── player-hero.tsx         # Player hero card (name, bio, position)
    │       ├── stats-table.tsx         # Season stats table
    │       ├── radar-chart.tsx         # Recharts radar for percentile data
    │       ├── shot-map.tsx            # SVG pitch with shot dots colored by xG
    │       └── player-compare-card.tsx # Single player card in comparison view
    └── .env.local.example
```

---

### Task 1: Next.js Project Setup

**Files:**
- Create: `web/` directory with Next.js scaffolding
- Create: `web/.env.local.example`

- [ ] **Step 1: Scaffold Next.js project**

```bash
cd /Users/mazam1/GitHub/personal/portfolio/pitch-intel
pnpm create next-app@latest web --yes --ts --tailwind --eslint --app --turbopack --import-alias "@/*" --use-pnpm
```

This creates the full Next.js project with TypeScript, Tailwind, ESLint, App Router, and Turbopack.

- [ ] **Step 2: Install Recharts**

```bash
cd web && pnpm add recharts
```

- [ ] **Step 3: Create .env.local.example**

Create `web/.env.local.example`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

Create `web/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

- [ ] **Step 4: Add .env.local to web/.gitignore**

Append to `web/.gitignore`:
```
.env.local
```

- [ ] **Step 5: Verify it runs**

```bash
cd web && pnpm dev
```

Visit http://localhost:3000 — should show the Next.js welcome page.
Kill the dev server.

- [ ] **Step 6: Commit**

```bash
cd /Users/mazam1/GitHub/personal/portfolio/pitch-intel
git add web/
git commit -m "chore: scaffold Next.js frontend with Tailwind and Recharts"
```

---

### Task 2: API Client

**Files:**
- Create: `web/src/lib/api.ts`

- [ ] **Step 1: Create the API client**

Create `web/src/lib/api.ts`:

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface PersonSummary {
  reep_id: string;
  type: string;
  name: string;
  nationality?: string;
  position?: string;
  date_of_birth?: string;
}

export interface TeamSummary {
  reep_id: string;
  name: string;
  country?: string;
  stadium?: string;
}

export interface SearchResponse {
  results: (PersonSummary | TeamSummary)[];
  count: number;
}

export interface PlayerProfile {
  reep_id: string;
  type: string;
  name: string;
  full_name?: string;
  date_of_birth?: string;
  nationality?: string;
  position?: string;
  height_cm?: number;
  key_transfermarkt?: string;
  key_fbref?: string;
}

export interface PlayerSeasonStats {
  season: string;
  league: string;
  source: string;
  minutes_played?: number;
  games?: number;
  starts?: number;
  goals?: number;
  assists?: number;
  xg?: number;
  npxg?: number;
  xa?: number;
  shots?: number;
  shots_on_target?: number;
  key_passes?: number;
  passes_completed?: number;
  passes_attempted?: number;
  progressive_passes?: number;
  progressive_carries?: number;
  tackles?: number;
  interceptions?: number;
  pressures?: number;
  take_ons_attempted?: number;
  take_ons_succeeded?: number;
  yellow_cards?: number;
  red_cards?: number;
}

export interface ShotData {
  id: number;
  minute?: number;
  result?: string;
  x?: number;
  y?: number;
  xg?: number;
  situation?: string;
  shot_type?: string;
}

export interface RadarData {
  reep_id: string;
  season: string;
  league: string;
  position_group: string;
  minutes_played: number;
  stats: Record<string, number | null>;
  percentiles: Record<string, number | null>;
}

async function fetchApi<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function searchPlayers(
  query: string,
  type?: "player" | "team",
): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query });
  if (type) params.set("type", type);
  return fetchApi<SearchResponse>(`/search?${params}`);
}

export async function getPlayer(reepId: string): Promise<PlayerProfile> {
  return fetchApi<PlayerProfile>(`/player/${reepId}`);
}

export async function getPlayerStats(
  reepId: string,
  season?: string,
): Promise<PlayerSeasonStats[]> {
  const params = season ? `?season=${season}` : "";
  return fetchApi<PlayerSeasonStats[]>(`/player/${reepId}/stats${params}`);
}

export async function getPlayerShots(
  reepId: string,
  season?: string,
): Promise<ShotData[]> {
  const params = season ? `?season=${season}` : "";
  return fetchApi<ShotData[]>(`/player/${reepId}/shots${params}`);
}

export async function getPlayerRadar(
  reepId: string,
  season?: string,
): Promise<RadarData | null> {
  const params = season ? `?season=${season}` : "";
  return fetchApi<RadarData | null>(`/player/${reepId}/radar${params}`);
}
```

- [ ] **Step 2: Type check**

```bash
cd web && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add web/src/lib/api.ts
git commit -m "feat: API client with TypeScript interfaces"
```

---

### Task 3: Root Layout + Home Page with Search

**Files:**
- Modify: `web/src/app/layout.tsx`
- Modify: `web/src/app/page.tsx`
- Create: `web/src/components/search-bar.tsx`

- [ ] **Step 1: Update root layout**

Replace `web/src/app/layout.tsx`:

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Pitch Intel",
  description: "Football intelligence platform — player and team analytics",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-950 text-gray-100 antialiased`}>
        <header className="border-b border-gray-800 px-6 py-4">
          <a href="/" className="text-xl font-bold tracking-tight">
            Pitch Intel
          </a>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
```

- [ ] **Step 2: Create search bar component**

Create `web/src/components/search-bar.tsx`:

```tsx
"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { searchPlayers, type PersonSummary, type TeamSummary } from "@/lib/api";

export default function SearchBar() {
  const [query, setQuery] = useState("");
  const [type, setType] = useState<"player" | "team">("player");
  const [results, setResults] = useState<(PersonSummary | TeamSummary)[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    if (timeoutRef.current) clearTimeout(timeoutRef.current);

    timeoutRef.current = setTimeout(async () => {
      setIsLoading(true);
      try {
        const data = await searchPlayers(query, type);
        setResults(data.results);
        setIsOpen(true);
      } catch {
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [query, type]);

  function handleSelect(item: PersonSummary | TeamSummary) {
    setIsOpen(false);
    setQuery("");
    if ("type" in item && (item as PersonSummary).type) {
      router.push(`/player/${item.reep_id}`);
    } else {
      router.push(`/team/${item.reep_id}`);
    }
  }

  return (
    <div className="relative w-full max-w-xl">
      <div className="flex gap-2 mb-2">
        <button
          onClick={() => setType("player")}
          className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
            type === "player"
              ? "bg-blue-600 text-white"
              : "bg-gray-800 text-gray-400 hover:text-gray-200"
          }`}
        >
          Players
        </button>
        <button
          onClick={() => setType("team")}
          className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
            type === "team"
              ? "bg-blue-600 text-white"
              : "bg-gray-800 text-gray-400 hover:text-gray-200"
          }`}
        >
          Teams
        </button>
      </div>

      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={`Search ${type}s...`}
        className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-3 text-lg placeholder-gray-500 focus:border-blue-500 focus:outline-none"
      />

      {isLoading && (
        <div className="absolute right-3 top-[52px] text-gray-500 text-sm">Loading...</div>
      )}

      {isOpen && results.length > 0 && (
        <ul className="absolute z-10 mt-1 w-full rounded-lg border border-gray-700 bg-gray-900 shadow-lg max-h-80 overflow-y-auto">
          {results.map((item) => (
            <li key={item.reep_id}>
              <button
                onClick={() => handleSelect(item)}
                className="w-full px-4 py-3 text-left hover:bg-gray-800 flex justify-between items-center"
              >
                <span className="font-medium">{item.name}</span>
                {"position" in item && item.position && (
                  <span className="text-sm text-gray-500">{item.position}</span>
                )}
                {"country" in item && item.country && (
                  <span className="text-sm text-gray-500">{item.country}</span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Update home page**

Replace `web/src/app/page.tsx`:

```tsx
import SearchBar from "@/components/search-bar";

export default function Home() {
  return (
    <div className="flex flex-col items-center pt-20">
      <h1 className="text-4xl font-bold mb-2">Pitch Intel</h1>
      <p className="text-gray-400 mb-8">
        Football intelligence — player and team analytics
      </p>
      <SearchBar />
    </div>
  );
}
```

- [ ] **Step 4: Verify**

```bash
cd web && npx tsc --noEmit && pnpm dev
```

Visit http://localhost:3000 — should show centered search with Players/Teams toggle.

- [ ] **Step 5: Commit**

```bash
git add web/src/
git commit -m "feat: home page with search bar and debounced autocomplete"
```

---

### Task 4: Player Hero Card

**Files:**
- Create: `web/src/components/player-hero.tsx`

- [ ] **Step 1: Create the hero card component**

Create `web/src/components/player-hero.tsx`:

```tsx
import type { PlayerProfile } from "@/lib/api";

function calculateAge(dob: string): number | null {
  const birth = new Date(dob);
  if (isNaN(birth.getTime())) return null;
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const m = today.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
  return age;
}

export default function PlayerHero({ player }: { player: PlayerProfile }) {
  const age = player.date_of_birth ? calculateAge(player.date_of_birth) : null;

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
      <div className="flex items-start gap-6">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gray-800 text-2xl font-bold text-gray-500">
          {player.name.charAt(0)}
        </div>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">{player.name}</h1>
          {player.full_name && player.full_name !== player.name && (
            <p className="text-gray-400">{player.full_name}</p>
          )}
          <div className="mt-3 flex flex-wrap gap-3">
            {player.position && (
              <span className="rounded-full bg-blue-900/50 px-3 py-1 text-sm text-blue-300">
                {player.position}
              </span>
            )}
            {player.nationality && (
              <span className="rounded-full bg-gray-800 px-3 py-1 text-sm text-gray-300">
                {player.nationality}
              </span>
            )}
            {age !== null && (
              <span className="rounded-full bg-gray-800 px-3 py-1 text-sm text-gray-300">
                {age} years old
              </span>
            )}
            {player.height_cm && (
              <span className="rounded-full bg-gray-800 px-3 py-1 text-sm text-gray-300">
                {player.height_cm} cm
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Type check**

```bash
cd web && npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add web/src/components/player-hero.tsx
git commit -m "feat: player hero card component"
```

---

### Task 5: Stats Table Component

**Files:**
- Create: `web/src/components/stats-table.tsx`

- [ ] **Step 1: Create the stats table**

Create `web/src/components/stats-table.tsx`:

```tsx
import type { PlayerSeasonStats } from "@/lib/api";

const STAT_COLUMNS: { key: keyof PlayerSeasonStats; label: string }[] = [
  { key: "season", label: "Season" },
  { key: "league", label: "League" },
  { key: "games", label: "GP" },
  { key: "starts", label: "GS" },
  { key: "minutes_played", label: "Min" },
  { key: "goals", label: "G" },
  { key: "assists", label: "A" },
  { key: "xg", label: "xG" },
  { key: "xa", label: "xA" },
  { key: "shots", label: "Sh" },
  { key: "key_passes", label: "KP" },
  { key: "progressive_passes", label: "PrgP" },
  { key: "progressive_carries", label: "PrgC" },
  { key: "tackles", label: "Tkl" },
  { key: "interceptions", label: "Int" },
  { key: "pressures", label: "Press" },
];

function formatStat(value: unknown): string {
  if (value === null || value === undefined) return "-";
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(1);
  }
  return String(value);
}

export default function StatsTable({ stats }: { stats: PlayerSeasonStats[] }) {
  if (stats.length === 0) {
    return <p className="text-gray-500">No stats available.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-800 text-left text-gray-400">
            {STAT_COLUMNS.map((col) => (
              <th key={col.key} className="px-2 py-2 font-medium whitespace-nowrap">
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {stats.map((row, i) => (
            <tr key={i} className="border-b border-gray-800/50 hover:bg-gray-800/30">
              {STAT_COLUMNS.map((col) => (
                <td key={col.key} className="px-2 py-2 whitespace-nowrap">
                  {formatStat(row[col.key])}
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

- [ ] **Step 2: Type check + commit**

```bash
cd web && npx tsc --noEmit
git add web/src/components/stats-table.tsx
git commit -m "feat: player season stats table component"
```

---

### Task 6: Radar Chart Component

**Files:**
- Create: `web/src/components/radar-chart.tsx`

- [ ] **Step 1: Create the radar chart**

Create `web/src/components/radar-chart.tsx`:

```tsx
"use client";

import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart as RechartsRadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { RadarData } from "@/lib/api";

const RADAR_STATS = [
  { key: "goals_pctile", label: "Goals" },
  { key: "xg_pctile", label: "xG" },
  { key: "assists_pctile", label: "Assists" },
  { key: "xa_pctile", label: "xA" },
  { key: "shots_pctile", label: "Shots" },
  { key: "key_passes_pctile", label: "Key Passes" },
  { key: "progressive_passes_pctile", label: "Prog Pass" },
  { key: "progressive_carries_pctile", label: "Prog Carry" },
  { key: "tackles_pctile", label: "Tackles" },
  { key: "interceptions_pctile", label: "Int" },
  { key: "pressures_pctile", label: "Pressures" },
  { key: "take_ons_pctile", label: "Take-Ons" },
];

interface Props {
  radar: RadarData;
  color?: string;
}

export default function RadarChartComponent({ radar, color = "#3b82f6" }: Props) {
  const data = RADAR_STATS.map((stat) => ({
    stat: stat.label,
    value: radar.percentiles[stat.key] ?? 0,
  }));

  return (
    <div>
      <div className="mb-2 text-sm text-gray-400">
        {radar.season} · {radar.league} · {radar.position_group} · {radar.minutes_played} min
      </div>
      <ResponsiveContainer width="100%" height={400}>
        <RechartsRadarChart data={data}>
          <PolarGrid stroke="#374151" />
          <PolarAngleAxis
            dataKey="stat"
            tick={{ fill: "#9ca3af", fontSize: 11 }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fill: "#6b7280", fontSize: 10 }}
          />
          <Radar
            dataKey="value"
            stroke={color}
            fill={color}
            fillOpacity={0.2}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "8px",
            }}
            labelStyle={{ color: "#f3f4f6" }}
          />
        </RechartsRadarChart>
      </ResponsiveContainer>
    </div>
  );
}
```

- [ ] **Step 2: Type check + commit**

```bash
cd web && npx tsc --noEmit
git add web/src/components/radar-chart.tsx
git commit -m "feat: radar chart component with Recharts"
```

---

### Task 7: Shot Map Component

**Files:**
- Create: `web/src/components/shot-map.tsx`

- [ ] **Step 1: Create the shot map**

Create `web/src/components/shot-map.tsx`:

```tsx
"use client";

import { useState } from "react";
import type { ShotData } from "@/lib/api";

const PITCH_WIDTH = 680;
const PITCH_HEIGHT = 440;
const HALF_WIDTH = PITCH_WIDTH / 2;

function xgToColor(xg: number): string {
  if (xg >= 0.5) return "#ef4444";
  if (xg >= 0.2) return "#f97316";
  if (xg >= 0.1) return "#eab308";
  return "#6b7280";
}

function xgToRadius(xg: number): number {
  return 4 + xg * 12;
}

interface Props {
  shots: ShotData[];
}

export default function ShotMap({ shots }: Props) {
  const [hoveredShot, setHoveredShot] = useState<ShotData | null>(null);

  if (shots.length === 0) {
    return <p className="text-gray-500">No shot data available.</p>;
  }

  // Understat coords: x 0-1 (left to right), y 0-1 (top to bottom)
  // We show only the attacking half (x > 0.5)
  const attackingShots = shots.filter((s) => s.x !== undefined && s.x >= 0.5);

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${HALF_WIDTH} ${PITCH_HEIGHT}`} className="w-full max-w-lg">
        {/* Pitch background */}
        <rect width={HALF_WIDTH} height={PITCH_HEIGHT} fill="#1a472a" rx={4} />

        {/* Penalty box */}
        <rect
          x={HALF_WIDTH - 165}
          y={PITCH_HEIGHT / 2 - 132}
          width={165}
          height={264}
          fill="none"
          stroke="#2d6b3f"
          strokeWidth={1.5}
        />

        {/* 6-yard box */}
        <rect
          x={HALF_WIDTH - 55}
          y={PITCH_HEIGHT / 2 - 66}
          width={55}
          height={132}
          fill="none"
          stroke="#2d6b3f"
          strokeWidth={1.5}
        />

        {/* Goal line */}
        <line
          x1={HALF_WIDTH}
          y1={0}
          x2={HALF_WIDTH}
          y2={PITCH_HEIGHT}
          stroke="#2d6b3f"
          strokeWidth={2}
        />

        {/* Goal */}
        <rect
          x={HALF_WIDTH - 2}
          y={PITCH_HEIGHT / 2 - 36}
          width={4}
          height={72}
          fill="#ffffff"
          opacity={0.3}
        />

        {/* Shots */}
        {attackingShots.map((shot) => {
          const cx = (shot.x! - 0.5) * 2 * HALF_WIDTH;
          const cy = shot.y! * PITCH_HEIGHT;
          const isGoal = shot.result === "Goal";

          return (
            <circle
              key={shot.id}
              cx={cx}
              cy={cy}
              r={xgToRadius(shot.xg ?? 0)}
              fill={isGoal ? xgToColor(shot.xg ?? 0) : "transparent"}
              stroke={xgToColor(shot.xg ?? 0)}
              strokeWidth={isGoal ? 0 : 2}
              opacity={0.85}
              onMouseEnter={() => setHoveredShot(shot)}
              onMouseLeave={() => setHoveredShot(null)}
              className="cursor-pointer transition-opacity hover:opacity-100"
            />
          );
        })}
      </svg>

      {/* Tooltip */}
      {hoveredShot && (
        <div className="mt-2 rounded border border-gray-700 bg-gray-900 p-3 text-sm">
          <div className="font-medium">
            {hoveredShot.result} · {hoveredShot.minute}&apos;
          </div>
          <div className="text-gray-400">
            xG: {hoveredShot.xg?.toFixed(2)} · {hoveredShot.situation} · {hoveredShot.shot_type}
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="mt-3 flex gap-4 text-xs text-gray-400">
        <span>● Goal</span>
        <span>○ No goal</span>
        <span className="text-red-500">● High xG (&ge;0.5)</span>
        <span className="text-orange-500">● Medium xG</span>
        <span className="text-gray-500">● Low xG</span>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Type check + commit**

```bash
cd web && npx tsc --noEmit
git add web/src/components/shot-map.tsx
git commit -m "feat: shot map SVG pitch visualization"
```

---

### Task 8: Player Profile Page

**Files:**
- Create: `web/src/app/player/[reepId]/page.tsx`

- [ ] **Step 1: Create the player profile page**

Create `web/src/app/player/[reepId]/page.tsx`:

```tsx
import { getPlayer, getPlayerRadar, getPlayerShots, getPlayerStats } from "@/lib/api";
import PlayerHero from "@/components/player-hero";
import StatsTable from "@/components/stats-table";
import RadarChartComponent from "@/components/radar-chart";
import ShotMap from "@/components/shot-map";

interface Props {
  params: Promise<{ reepId: string }>;
}

export default async function PlayerPage({ params }: Props) {
  const { reepId } = await params;

  let player, stats, radar, shots;
  try {
    [player, stats, radar, shots] = await Promise.all([
      getPlayer(reepId),
      getPlayerStats(reepId),
      getPlayerRadar(reepId),
      getPlayerShots(reepId),
    ]);
  } catch {
    return (
      <div className="text-center py-20">
        <h1 className="text-2xl font-bold text-gray-400">Player not found</h1>
        <p className="text-gray-500 mt-2">Could not load data for {reepId}</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <PlayerHero player={player} />

      <section>
        <h2 className="text-xl font-semibold mb-4">Season Stats</h2>
        <StatsTable stats={stats} />
      </section>

      {radar && (
        <section>
          <h2 className="text-xl font-semibold mb-4">Percentile Radar</h2>
          <RadarChartComponent radar={radar} />
        </section>
      )}

      {shots.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-4">Shot Map</h2>
          <ShotMap shots={shots} />
        </section>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Type check + verify**

```bash
cd web && npx tsc --noEmit && pnpm dev
```

Visit http://localhost:3000/player/reep_p2804f5db — should show the player page (will show error state if API isn't running, which is fine for now).

- [ ] **Step 3: Commit**

```bash
git add web/src/app/player/
git commit -m "feat: player profile page with stats, radar, and shot map"
```

---

### Task 9: Player Comparison Page

**Files:**
- Create: `web/src/components/player-compare-card.tsx`
- Create: `web/src/app/compare/page.tsx`

- [ ] **Step 1: Create comparison card component**

Create `web/src/components/player-compare-card.tsx`:

```tsx
import type { PlayerProfile, RadarData } from "@/lib/api";
import RadarChartComponent from "./radar-chart";

const COLORS = ["#3b82f6", "#ef4444", "#22c55e", "#f59e0b"];

interface Props {
  player: PlayerProfile;
  radar: RadarData | null;
  index: number;
}

export default function PlayerCompareCard({ player, radar, index }: Props) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
      <h3 className="text-lg font-semibold mb-1">{player.name}</h3>
      <p className="text-sm text-gray-400 mb-3">
        {player.position} · {player.nationality}
      </p>
      {radar ? (
        <RadarChartComponent radar={radar} color={COLORS[index % COLORS.length]} />
      ) : (
        <p className="text-gray-500 text-sm">No radar data available</p>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create comparison page**

Create `web/src/app/compare/page.tsx`:

```tsx
import { getPlayer, getPlayerRadar } from "@/lib/api";
import PlayerCompareCard from "@/components/player-compare-card";

interface Props {
  searchParams: Promise<{ p?: string | string[] }>;
}

export default async function ComparePage({ searchParams }: Props) {
  const sp = await searchParams;
  const rawIds = sp.p;
  const ids = Array.isArray(rawIds) ? rawIds : rawIds ? [rawIds] : [];

  if (ids.length === 0) {
    return (
      <div className="text-center py-20">
        <h1 className="text-2xl font-bold">Compare Players</h1>
        <p className="text-gray-400 mt-2">
          Add players via URL: /compare?p=reep_id1&amp;p=reep_id2
        </p>
      </div>
    );
  }

  const players = await Promise.all(
    ids.slice(0, 4).map(async (id) => {
      try {
        const [player, radar] = await Promise.all([
          getPlayer(id),
          getPlayerRadar(id),
        ]);
        return { player, radar };
      } catch {
        return null;
      }
    }),
  );

  const valid = players.filter(Boolean) as {
    player: Awaited<ReturnType<typeof getPlayer>>;
    radar: Awaited<ReturnType<typeof getPlayerRadar>>;
  }[];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Compare Players</h1>
      <div className={`grid gap-6 ${valid.length <= 2 ? "grid-cols-1 md:grid-cols-2" : "grid-cols-1 md:grid-cols-2 lg:grid-cols-4"}`}>
        {valid.map(({ player, radar }, i) => (
          <PlayerCompareCard
            key={player.reep_id}
            player={player}
            radar={radar}
            index={i}
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
git add web/src/components/player-compare-card.tsx web/src/app/compare/
git commit -m "feat: player comparison page with side-by-side radars"
```

---

### Task 10: Type Check + Build Verification

- [ ] **Step 1: Run TypeScript check**

```bash
cd web && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 2: Run ESLint**

```bash
cd web && pnpm lint
```

Fix any issues found.

- [ ] **Step 3: Run production build**

```bash
cd web && pnpm build
```

Expected: Build succeeds.

- [ ] **Step 4: Final commit if any fixes**

```bash
git add -A && git commit -m "fix: lint and build adjustments"
```

---

## Summary

| Task | What it builds | Verification |
|------|---------------|--------------|
| 1 | Next.js project scaffold | Dev server starts |
| 2 | API client + TypeScript types | `tsc --noEmit` |
| 3 | Home page + search bar | Visual + `tsc` |
| 4 | Player hero card | `tsc` |
| 5 | Stats table | `tsc` |
| 6 | Radar chart (Recharts) | `tsc` |
| 7 | Shot map (SVG pitch) | `tsc` |
| 8 | Player profile page | Visual + `tsc` |
| 9 | Player comparison page | Visual + `tsc` |
| 10 | Full build verification | `pnpm build` |

**After this plan:** The frontend has a working search, player profiles with stats/radar/shots, and player comparison. Plan 4 adds team pages and the explore scatter view.
