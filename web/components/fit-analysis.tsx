import type { FitAnalysis } from "@/lib/api";

export default function FitAnalysisCard({ fit }: { fit: FitAnalysis }) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
      <h3 className="text-lg font-semibold mb-3">
        {fit.player_name} → {fit.team_name}
      </h3>

      {fit.position_rank !== null && fit.position_rank !== undefined && (
        <div className="mb-3">
          <span className="text-2xl font-bold text-blue-400">
            #{fit.position_rank}
          </span>
          <span className="text-gray-400 ml-1">
            of {fit.position_total} at position
          </span>
        </div>
      )}

      {fit.style_notes.length > 0 && (
        <div className="space-y-1">
          {fit.style_notes.map((note, i) => (
            <p key={i} className="text-sm text-gray-400">
              • {note}
            </p>
          ))}
        </div>
      )}

      {fit.style_notes.length === 0 && fit.position_rank === null && (
        <p className="text-sm text-gray-500">Not enough data for fit analysis.</p>
      )}
    </div>
  );
}
