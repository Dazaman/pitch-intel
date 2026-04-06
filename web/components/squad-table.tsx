import type { SquadMember } from "@/lib/api";

function calculateAge(dob: string): number | null {
  const birth = new Date(dob);
  if (isNaN(birth.getTime())) return null;
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const m = today.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
  return age;
}

export default function SquadTable({ squad }: { squad: SquadMember[] }) {
  if (squad.length === 0) {
    return <p className="text-gray-500">No squad data available.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-800 text-left text-gray-400">
            <th className="px-3 py-2 font-medium">Name</th>
            <th className="px-3 py-2 font-medium">Position</th>
            <th className="px-3 py-2 font-medium">Nationality</th>
            <th className="px-3 py-2 font-medium">Age</th>
            <th className="px-3 py-2 font-medium text-right">Min</th>
            <th className="px-3 py-2 font-medium text-right">G</th>
            <th className="px-3 py-2 font-medium text-right">A</th>
            <th className="px-3 py-2 font-medium text-right">xG</th>
          </tr>
        </thead>
        <tbody>
          {squad.map((p) => (
            <tr key={p.reep_id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
              <td className="px-3 py-2">
                <a href={`/player/${p.reep_id}`} className="text-blue-400 hover:underline">
                  {p.name}
                </a>
              </td>
              <td className="px-3 py-2 text-gray-400">{p.position ?? "-"}</td>
              <td className="px-3 py-2 text-gray-400">{p.nationality ?? "-"}</td>
              <td className="px-3 py-2 text-gray-400">
                {p.date_of_birth ? calculateAge(p.date_of_birth) ?? "-" : "-"}
              </td>
              <td className="px-3 py-2 text-right">{p.minutes_played ?? "-"}</td>
              <td className="px-3 py-2 text-right">{p.goals ?? "-"}</td>
              <td className="px-3 py-2 text-right">{p.assists ?? "-"}</td>
              <td className="px-3 py-2 text-right">
                {p.xg !== undefined && p.xg !== null ? p.xg.toFixed(1) : "-"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
