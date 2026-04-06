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
  type ScatterPointItem,
} from "recharts";
import type { ClusterPoint } from "@/lib/api";

const CLUSTER_COLORS = [
  "#ef4444", "#3b82f6", "#22c55e", "#f59e0b",
  "#8b5cf6", "#ec4899", "#14b8a6", "#f97316",
];

export default function ClusterMap({ data }: { data: ClusterPoint[] }) {
  const router = useRouter();

  if (data.length === 0) {
    return <p className="text-gray-500">No cluster data available.</p>;
  }

  const chartData = data.map((p) => ({
    x: p.umap_x,
    y: p.umap_y,
    name: p.name,
    cluster: p.cluster_label,
    reep_id: p.reep_id,
    fill: CLUSTER_COLORS[p.cluster_id % CLUSTER_COLORS.length],
  }));

  const uniqueLabels = [...new Set(data.map((p) => p.cluster_label))];

  return (
    <div>
      <ResponsiveContainer width="100%" height={500}>
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis type="number" dataKey="x" tick={{ fill: "#6b7280", fontSize: 10 }} />
          <YAxis type="number" dataKey="y" tick={{ fill: "#6b7280", fontSize: 10 }} />
          <ZAxis range={[30, 30]} />
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
            onClick={(point: ScatterPointItem) => {
              const p = point as ScatterPointItem & { reep_id?: string };
              if (p?.reep_id) router.push(`/player/${p.reep_id}`);
            }}
            cursor="pointer"
          />
        </ScatterChart>
      </ResponsiveContainer>
      <div className="mt-4 flex flex-wrap gap-3">
        {uniqueLabels.map((label, i) => (
          <span key={label} className="flex items-center gap-1 text-xs text-gray-400">
            <span
              className="inline-block h-3 w-3 rounded-full"
              style={{ backgroundColor: CLUSTER_COLORS[i % CLUSTER_COLORS.length] }}
            />
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}
