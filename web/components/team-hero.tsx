import type { TeamProfile } from "@/lib/api";

export default function TeamHero({ team }: { team: TeamProfile }) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
      <div className="flex items-start gap-6">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gray-800 text-2xl font-bold text-gray-500">
          {team.name.charAt(0)}
        </div>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">{team.name}</h1>
          <div className="mt-3 flex flex-wrap gap-3">
            {team.country && (
              <span className="rounded-full bg-gray-800 px-3 py-1 text-sm text-gray-300">
                {team.country}
              </span>
            )}
            {team.stadium && (
              <span className="rounded-full bg-gray-800 px-3 py-1 text-sm text-gray-300">
                {team.stadium}
              </span>
            )}
            {team.founded && (
              <span className="rounded-full bg-gray-800 px-3 py-1 text-sm text-gray-300">
                Est. {team.founded}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
