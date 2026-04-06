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

export interface TeamProfile {
  reep_id: string;
  name: string;
  country?: string;
  founded?: string;
  stadium?: string;
  key_transfermarkt?: string;
  key_fbref?: string;
}

export interface TeamSeasonStats {
  season: string;
  league: string;
  source: string;
  wins?: number;
  draws?: number;
  losses?: number;
  goals_for?: number;
  goals_against?: number;
  xg?: number;
  xga?: number;
  ppda?: number;
  elo_start?: number;
  elo_end?: number;
}

export interface SquadMember {
  reep_id: string;
  name: string;
  position?: string;
  nationality?: string;
  date_of_birth?: string;
  minutes_played?: number;
  goals?: number;
  assists?: number;
  xg?: number;
}

export interface ScatterPoint {
  reep_id: string;
  name: string;
  position?: string;
  league: string;
  x_value?: number;
  y_value?: number;
}

export async function getTeam(reepId: string): Promise<TeamProfile> {
  return fetchApi<TeamProfile>(`/team/${reepId}`);
}

export async function getTeamStats(
  reepId: string,
  season?: string,
): Promise<TeamSeasonStats[]> {
  const params = season ? `?season=${season}` : "";
  return fetchApi<TeamSeasonStats[]>(`/team/${reepId}/stats${params}`);
}

export async function getTeamSquad(
  reepId: string,
  season: string,
): Promise<SquadMember[]> {
  return fetchApi<SquadMember[]>(`/team/${reepId}/squad?season=${season}`);
}

export async function getCompareTeams(
  ids: string[],
): Promise<Record<string, { name: string; seasons: TeamSeasonStats[] }>> {
  return fetchApi(`/compare/teams?ids=${ids.join(",")}`);
}

export async function getScatter(
  x: string,
  y: string,
  league?: string,
  position?: string,
): Promise<ScatterPoint[]> {
  const params = new URLSearchParams({ x, y });
  if (league) params.set("league", league);
  if (position) params.set("position", position);
  return fetchApi<ScatterPoint[]>(`/explore/scatter?${params}`);
}
