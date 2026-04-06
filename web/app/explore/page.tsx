"use client";

import { useEffect, useState } from "react";
import { getScatter, getClusters, type ScatterPoint, type ClusterPoint } from "@/lib/api";
import ScatterPlotChart from "@/components/scatter-plot";
import ClusterMap from "@/components/cluster-map";

const STATS = [
  "goals_per90",
  "xg_per90",
  "assists_per90",
  "xa_per90",
  "shots_per90",
  "key_passes_per90",
  "progressive_passes_per90",
  "progressive_carries_per90",
  "tackles_per90",
  "interceptions_per90",
  "pressures_per90",
  "take_ons_per90",
];

const LEAGUES = [
  "Premier League",
  "La Liga",
  "Serie A",
  "Bundesliga",
  "Ligue 1",
];

const POSITIONS = ["FW", "MF", "DF", "GK"];

function formatLabel(stat: string): string {
  return stat
    .replace(/_per90$/, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function ExplorePage() {
  const [tab, setTab] = useState<"scatter" | "clusters">("scatter");
  const [xStat, setXStat] = useState("xg_per90");
  const [yStat, setYStat] = useState("goals_per90");
  const [league, setLeague] = useState("");
  const [position, setPosition] = useState("");
  const [data, setData] = useState<ScatterPoint[]>([]);
  const [clusterData, setClusterData] = useState<ClusterPoint[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (tab !== "scatter") return;
    setIsLoading(true);
    getScatter(xStat, yStat, league || undefined, position || undefined)
      .then(setData)
      .catch(() => setData([]))
      .finally(() => setIsLoading(false));
  }, [tab, xStat, yStat, league, position]);

  useEffect(() => {
    if (tab !== "clusters") return;
    setIsLoading(true);
    getClusters("2024-2025")
      .then(setClusterData)
      .catch(() => setClusterData([]))
      .finally(() => setIsLoading(false));
  }, [tab]);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Explore Players</h1>

      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setTab("scatter")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            tab === "scatter"
              ? "bg-blue-600 text-white"
              : "border border-gray-700 text-gray-400 hover:bg-gray-800"
          }`}
        >
          Scatter
        </button>
        <button
          onClick={() => setTab("clusters")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            tab === "clusters"
              ? "bg-blue-600 text-white"
              : "border border-gray-700 text-gray-400 hover:bg-gray-800"
          }`}
        >
          Clusters
        </button>
      </div>

      {tab === "scatter" && (
        <>
          <div className="flex flex-wrap gap-4 mb-6">
            <div>
              <label className="block text-sm text-gray-400 mb-1">X Axis</label>
              <select
                value={xStat}
                onChange={(e) => setXStat(e.target.value)}
                className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm"
              >
                {STATS.map((s) => (
                  <option key={s} value={s}>{formatLabel(s)}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Y Axis</label>
              <select
                value={yStat}
                onChange={(e) => setYStat(e.target.value)}
                className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm"
              >
                {STATS.map((s) => (
                  <option key={s} value={s}>{formatLabel(s)}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">League</label>
              <select
                value={league}
                onChange={(e) => setLeague(e.target.value)}
                className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm"
              >
                <option value="">All Leagues</option>
                {LEAGUES.map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Position</label>
              <select
                value={position}
                onChange={(e) => setPosition(e.target.value)}
                className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm"
              >
                <option value="">All Positions</option>
                {POSITIONS.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          </div>

          {isLoading ? (
            <p className="text-gray-500">Loading...</p>
          ) : (
            <ScatterPlotChart data={data} xStat={xStat} yStat={yStat} />
          )}

          <p className="mt-4 text-sm text-gray-500">
            {data.length} players shown. Click a point to view player profile.
          </p>
        </>
      )}

      {tab === "clusters" && (
        <>
          {isLoading ? (
            <p className="text-gray-500">Loading...</p>
          ) : (
            <ClusterMap data={clusterData} />
          )}
        </>
      )}
    </div>
  );
}
