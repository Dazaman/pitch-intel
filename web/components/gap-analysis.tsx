import type { GapAnalysisItem } from "@/lib/api";

const RISK_COLORS: Record<string, string> = {
  thin: "text-red-400",
  aging: "text-yellow-400",
  ok: "text-green-400",
};

export default function GapAnalysis({ gaps }: { gaps: GapAnalysisItem[] }) {
  if (gaps.length === 0) {
    return <p className="text-gray-500">No gap analysis available.</p>;
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {gaps.map((g) => (
        <div
          key={g.position_group}
          className="rounded-lg border border-gray-800 bg-gray-900 p-4 text-center"
        >
          <div className="text-lg font-bold">{g.position_group}</div>
          <div className="text-2xl font-semibold mt-1">{g.depth}</div>
          <div className="text-sm text-gray-400">players</div>
          <div className={`mt-2 text-sm font-medium ${RISK_COLORS[g.risk] ?? "text-gray-400"}`}>
            {g.risk === "thin" ? "Needs depth" : g.risk === "aging" ? "Aging" : "OK"}
          </div>
        </div>
      ))}
    </div>
  );
}
