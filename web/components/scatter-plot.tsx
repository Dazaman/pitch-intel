"use client";

import { useRouter } from "next/navigation";
import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { ScatterPoint } from "@/lib/api";

const POSITION_COLORS: Record<string, string> = {
  "centre-forward": "#ef4444",
  "second striker": "#f97316",
  "left winger": "#eab308",
  "right winger": "#eab308",
  "attacking midfielder": "#22c55e",
  "central midfield": "#3b82f6",
  "defensive midfield": "#6366f1",
  "left-back": "#8b5cf6",
  "right-back": "#8b5cf6",
  "centre-back": "#a855f7",
  goalkeeper: "#ec4899",
};

function formatStatLabel(stat: string): string {
  return stat
    .replace(/_per90$/, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

interface Props {
  data: ScatterPoint[];
  xStat: string;
  yStat: string;
}

export default function ScatterPlotChart({ data, xStat, yStat }: Props) {
  const router = useRouter();

  if (data.length === 0) {
    return <p className="text-gray-500">No data for the selected filters.</p>;
  }

  const chartData = data.map((p) => ({
    x: p.x_value ?? 0,
    y: p.y_value ?? 0,
    name: p.name,
    position: p.position ?? "unknown",
    reep_id: p.reep_id,
    fill: POSITION_COLORS[p.position ?? ""] ?? "#6b7280",
  }));

  return (
    <ResponsiveContainer width="100%" height={500}>
      <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis
          type="number"
          dataKey="x"
          name={formatStatLabel(xStat)}
          tick={{ fill: "#9ca3af", fontSize: 11 }}
          label={{
            value: formatStatLabel(xStat),
            position: "bottom",
            fill: "#9ca3af",
            fontSize: 12,
          }}
        />
        <YAxis
          type="number"
          dataKey="y"
          name={formatStatLabel(yStat)}
          tick={{ fill: "#9ca3af", fontSize: 11 }}
          label={{
            value: formatStatLabel(yStat),
            angle: -90,
            position: "left",
            fill: "#9ca3af",
            fontSize: 12,
          }}
        />
        <ZAxis range={[40, 40]} />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1f2937",
            border: "1px solid #374151",
            borderRadius: "8px",
          }}
          labelStyle={{ color: "#f3f4f6" }}
        />
        <Scatter
          data={chartData}
          onClick={(point: unknown) => {
            const p = point as { reep_id?: string } | null;
            if (p?.reep_id) router.push(`/player/${p.reep_id}`);
          }}
          cursor="pointer"
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
