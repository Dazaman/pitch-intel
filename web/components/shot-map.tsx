"use client";

import { useState } from "react";
import type { ShotData } from "@/lib/api";

const PITCH_WIDTH = 680;
const PITCH_HEIGHT = 440;
const HALF_WIDTH = PITCH_WIDTH / 2;

function xgToColor(xg: number): string {
  if (xg >= 0.5) return "#ef4444";
  if (xg >= 0.2) return "#f97316";
  if (xg >= 0.1) return "#eab308";
  return "#6b7280";
}

function xgToRadius(xg: number): number {
  return 4 + xg * 12;
}

interface Props {
  shots: ShotData[];
}

export default function ShotMap({ shots }: Props) {
  const [hoveredShot, setHoveredShot] = useState<ShotData | null>(null);

  if (shots.length === 0) {
    return <p className="text-gray-500">No shot data available.</p>;
  }

  const attackingShots = shots.filter((s) => s.x !== undefined && s.x >= 0.5);

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${HALF_WIDTH} ${PITCH_HEIGHT}`} className="w-full max-w-lg">
        <rect width={HALF_WIDTH} height={PITCH_HEIGHT} fill="#1a472a" rx={4} />
        <rect
          x={HALF_WIDTH - 165}
          y={PITCH_HEIGHT / 2 - 132}
          width={165}
          height={264}
          fill="none"
          stroke="#2d6b3f"
          strokeWidth={1.5}
        />
        <rect
          x={HALF_WIDTH - 55}
          y={PITCH_HEIGHT / 2 - 66}
          width={55}
          height={132}
          fill="none"
          stroke="#2d6b3f"
          strokeWidth={1.5}
        />
        <line
          x1={HALF_WIDTH}
          y1={0}
          x2={HALF_WIDTH}
          y2={PITCH_HEIGHT}
          stroke="#2d6b3f"
          strokeWidth={2}
        />
        <rect
          x={HALF_WIDTH - 2}
          y={PITCH_HEIGHT / 2 - 36}
          width={4}
          height={72}
          fill="#ffffff"
          opacity={0.3}
        />
        {attackingShots.map((shot) => {
          const cx = (shot.x! - 0.5) * 2 * HALF_WIDTH;
          const cy = shot.y! * PITCH_HEIGHT;
          const isGoal = shot.result === "Goal";
          return (
            <circle
              key={shot.id}
              cx={cx}
              cy={cy}
              r={xgToRadius(shot.xg ?? 0)}
              fill={isGoal ? xgToColor(shot.xg ?? 0) : "transparent"}
              stroke={xgToColor(shot.xg ?? 0)}
              strokeWidth={isGoal ? 0 : 2}
              opacity={0.85}
              onMouseEnter={() => setHoveredShot(shot)}
              onMouseLeave={() => setHoveredShot(null)}
              className="cursor-pointer transition-opacity hover:opacity-100"
            />
          );
        })}
      </svg>

      {hoveredShot && (
        <div className="mt-2 rounded border border-gray-700 bg-gray-900 p-3 text-sm">
          <div className="font-medium">
            {hoveredShot.result} · {hoveredShot.minute}&apos;
          </div>
          <div className="text-gray-400">
            xG: {hoveredShot.xg?.toFixed(2)} · {hoveredShot.situation} · {hoveredShot.shot_type}
          </div>
        </div>
      )}

      <div className="mt-3 flex gap-4 text-xs text-gray-400">
        <span>● Goal</span>
        <span>○ No goal</span>
        <span className="text-red-500">● High xG (≥0.5)</span>
        <span className="text-orange-500">● Medium xG</span>
        <span className="text-gray-500">● Low xG</span>
      </div>
    </div>
  );
}
