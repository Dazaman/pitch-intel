const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface PersonSummary {
  reep_id: string;
  type: string;
  name: string;
  nationality?: string;
  position?: string;
  date_of_birth?: string;
}

export interface TeamSummary {
  reep_id: string;
  name: string;
  country?: string;
  stadium?: string;
}

export interface SearchResponse {
  results: (PersonSummary | TeamSummary)[];
  count: number;
}

export interface PlayerProfile {
  reep_id: string;
  type: string;
  name: string;
  full_name?: string;
  date_of_birth?: string;
  nationality?: string;
  position?: string;
  height_cm?: number;
  key_transfermarkt?: string;
  key_fbref?: string;
}

export interface PlayerSeasonStats {
  season: string;
  league: string;
  source: string;
  minutes_played?: number;
  games?: number;
  starts?: number;
  goals?: number;
  assists?: number;
  xg?: number;
  npxg?: number;
  xa?: number;
  shots?: number;
  shots_on_target?: number;
  key_passes?: number;
  passes_completed?: number;
  passes_attempted?: number;
  progressive_passes?: number;
  progressive_carries?: number;
  tackles?: number;
  interceptions?: number;
  pressures?: number;
  take_ons_attempted?: number;
  take_ons_succeeded?: number;
  yellow_cards?: number;
  red_cards?: number;
}

export interface ShotData {
  id: number;
  minute?: number;
  result?: string;
  x?: number;
  y?: number;
  xg?: number;
  situation?: string;
  shot_type?: string;
}

export interface RadarData {
  reep_id: string;
  season: string;
  league: string;
  position_group: string;
  minutes_played: number;
  stats: Record<string, number | null>;
  percentiles: Record<string, number | null>;
}

async function fetchApi<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function searchPlayers(
  query: string,
  type?: "player" | "team",
): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query });
  if (type) params.set("type", type);
  return fetchApi<SearchResponse>(`/search?${params}`);
}

export async function getPlayer(reepId: string): Promise<PlayerProfile> {
  return fetchApi<PlayerProfile>(`/player/${reepId}`);
}

export async function getPlayerStats(
  reepId: string,
  season?: string,
): Promise<PlayerSeasonStats[]> {
  const params = season ? `?season=${season}` : "";
  return fetchApi<PlayerSeasonStats[]>(`/player/${reepId}/stats${params}`);
}

export async function getPlayerShots(
  reepId: string,
  season?: string,
): Promise<ShotData[]> {
  const params = season ? `?season=${season}` : "";
  return fetchApi<ShotData[]>(`/player/${reepId}/shots${params}`);
}

export async function getPlayerRadar(
  reepId: string,
  season?: string,
): Promise<RadarData | null> {
  const params = season ? `?season=${season}` : "";
  return fetchApi<RadarData | null>(`/player/${reepId}/radar${params}`);
}
