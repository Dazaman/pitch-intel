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
