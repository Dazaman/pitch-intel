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
