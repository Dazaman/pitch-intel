"use client";

import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart as RechartsRadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { RadarData } from "@/lib/api";

const RADAR_STATS = [
  { key: "goals_pctile", label: "Goals" },
  { key: "xg_pctile", label: "xG" },
  { key: "assists_pctile", label: "Assists" },
  { key: "xa_pctile", label: "xA" },
  { key: "shots_pctile", label: "Shots" },
  { key: "key_passes_pctile", label: "Key Passes" },
  { key: "progressive_passes_pctile", label: "Prog Pass" },
  { key: "progressive_carries_pctile", label: "Prog Carry" },
  { key: "tackles_pctile", label: "Tackles" },
  { key: "interceptions_pctile", label: "Int" },
  { key: "pressures_pctile", label: "Pressures" },
  { key: "take_ons_pctile", label: "Take-Ons" },
];

interface Props {
  radar: RadarData;
  color?: string;
}

export default function RadarChartComponent({ radar, color = "#3b82f6" }: Props) {
  const data = RADAR_STATS.map((stat) => ({
    stat: stat.label,
    value: radar.percentiles[stat.key] ?? 0,
  }));

  return (
    <div>
      <div className="mb-2 text-sm text-gray-400">
        {radar.season} · {radar.league} · {radar.position_group} · {radar.minutes_played} min
      </div>
      <ResponsiveContainer width="100%" height={400}>
        <RechartsRadarChart data={data}>
          <PolarGrid stroke="#374151" />
          <PolarAngleAxis dataKey="stat" tick={{ fill: "#9ca3af", fontSize: 11 }} />
          <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: "#6b7280", fontSize: 10 }} />
          <Radar dataKey="value" stroke={color} fill={color} fillOpacity={0.2} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "8px",
            }}
            labelStyle={{ color: "#f3f4f6" }}
          />
        </RechartsRadarChart>
      </ResponsiveContainer>
    </div>
  );
}
