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
