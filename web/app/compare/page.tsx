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
