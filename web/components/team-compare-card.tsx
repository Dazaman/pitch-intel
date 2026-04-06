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
