import type { SimilarPlayer } from "@/lib/api";

export default function SimilarPlayers({ players }: { players: SimilarPlayer[] }) {
  if (players.length === 0) {
    return <p className="text-gray-500">No similar players found.</p>;
  }

  return (
    <div className="space-y-2">
      {players.map((p) => (
        <a
          key={p.reep_id}
          href={`/player/${p.reep_id}`}
          className="flex items-center justify-between rounded-lg border border-gray-800 bg-gray-900 px-4 py-3 hover:bg-gray-800 transition-colors"
        >
          <div>
            <span className="font-medium">{p.name}</span>
            {p.position && (
              <span className="ml-2 text-sm text-gray-400">{p.position}</span>
            )}
          </div>
          <span className="text-sm text-blue-400">
            {(p.similarity * 100).toFixed(0)}% match
          </span>
        </a>
      ))}
    </div>
  );
}
