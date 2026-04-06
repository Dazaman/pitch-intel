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
        <h2 className="text-xl font-semibold mb-4">Squad ({currentSeason})</h2>
        <SquadTable squad={squad} />
      </section>
    </div>
  );
}
