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
          <TeamCompareCard key={reepId} name={team.name} seasons={team.seasons} />
        ))}
      </div>
    </div>
  );
}
