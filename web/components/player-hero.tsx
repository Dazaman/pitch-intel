import type { PlayerProfile } from "@/lib/api";

function calculateAge(dob: string): number | null {
  const birth = new Date(dob);
  if (isNaN(birth.getTime())) return null;
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const m = today.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
  return age;
}

export default function PlayerHero({ player }: { player: PlayerProfile }) {
  const age = player.date_of_birth ? calculateAge(player.date_of_birth) : null;

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
      <div className="flex items-start gap-6">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gray-800 text-2xl font-bold text-gray-500">
          {player.name.charAt(0)}
        </div>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">{player.name}</h1>
          {player.full_name && player.full_name !== player.name && (
            <p className="text-gray-400">{player.full_name}</p>
          )}
          <div className="mt-3 flex flex-wrap gap-3">
            {player.position && (
              <span className="rounded-full bg-blue-900/50 px-3 py-1 text-sm text-blue-300">
                {player.position}
              </span>
            )}
            {player.nationality && (
              <span className="rounded-full bg-gray-800 px-3 py-1 text-sm text-gray-300">
                {player.nationality}
              </span>
            )}
            {age !== null && (
              <span className="rounded-full bg-gray-800 px-3 py-1 text-sm text-gray-300">
                {age} years old
              </span>
            )}
            {player.height_cm && (
              <span className="rounded-full bg-gray-800 px-3 py-1 text-sm text-gray-300">
                {player.height_cm} cm
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
