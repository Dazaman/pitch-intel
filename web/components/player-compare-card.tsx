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
