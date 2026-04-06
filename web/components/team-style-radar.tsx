"use client";

import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { TeamStyleProfile } from "@/lib/api";

export default function TeamStyleRadar({ profile }: { profile: TeamStyleProfile }) {
  const data = [
    { stat: "Possession", value: profile.possession_score ?? 0 },
    { stat: "Pressing", value: profile.pressing_score ?? 0 },
    { stat: "Directness", value: profile.directness_score ?? 0 },
  ];

  return (
    <div>
      <div className="mb-2 text-sm text-gray-400">
        {profile.season} · {profile.league}
        {profile.avg_age && ` · Avg age: ${profile.avg_age}`}
        {profile.squad_size && ` · Squad: ${profile.squad_size}`}
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <RadarChart data={data}>
          <PolarGrid stroke="#374151" />
          <PolarAngleAxis dataKey="stat" tick={{ fill: "#9ca3af", fontSize: 12 }} />
          <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: "#6b7280", fontSize: 10 }} />
          <Radar dataKey="value" stroke="#22c55e" fill="#22c55e" fillOpacity={0.2} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "8px",
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
      <div className="mt-3 grid grid-cols-4 gap-2 text-center text-sm">
        <div>
          <div className="text-lg font-semibold">{profile.fw_depth ?? 0}</div>
          <div className="text-gray-400">FW</div>
        </div>
        <div>
          <div className="text-lg font-semibold">{profile.mf_depth ?? 0}</div>
          <div className="text-gray-400">MF</div>
        </div>
        <div>
          <div className="text-lg font-semibold">{profile.df_depth ?? 0}</div>
          <div className="text-gray-400">DF</div>
        </div>
        <div>
          <div className="text-lg font-semibold">{profile.gk_depth ?? 0}</div>
          <div className="text-gray-400">GK</div>
        </div>
      </div>
    </div>
  );
}
