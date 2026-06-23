/**
 * Client API — connecté au backend FastAPI (Build 12).
 * Offline-first : chaque appel passe par le cache local d'abord,
 * la file de synchronisation gère les écritures hors connexion.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';

declare const process: { env: Record<string, string | undefined> };

// Ordre de résolution de l'URL de l'API :
//  1. EXPO_PUBLIC_API_URL (web/dev)  2. app.json → extra.apiUrl (build natif)  3. localhost
const BASE_URL =
  process.env.EXPO_PUBLIC_API_URL ??
  (Constants.expoConfig?.extra?.apiUrl as string | undefined) ??
  'http://localhost:8000';

export const API_BASE_URL = BASE_URL;

type Json = Record<string, unknown>;

class ApiError extends Error {
  constructor(readonly status: number, detail: string) {
    super(`API ${status}: ${detail}`);
  }
}

// ---- Jeton d'authentification ----
const TOKEN_KEY = 'raid_coach:token';
let authToken: string | null = null;
let onUnauthorized: (() => void) | null = null;

export function setUnauthorizedHandler(fn: (() => void) | null): void { onUnauthorized = fn; }
export async function loadToken(): Promise<string | null> {
  authToken = await AsyncStorage.getItem(TOKEN_KEY);
  return authToken;
}
export async function setToken(t: string): Promise<void> {
  authToken = t; await AsyncStorage.setItem(TOKEN_KEY, t);
}
export async function clearToken(): Promise<void> {
  authToken = null; await AsyncStorage.removeItem(TOKEN_KEY);
}
function authHeaders(): Record<string, string> {
  return authToken ? { Authorization: `Bearer ${authToken}` } : {};
}
// 401 hors des routes /auth → session invalide : on prévient l'app (retour login).
function handleStatus(status: number, path: string): void {
  if (status === 401 && !path.startsWith('/auth/') && onUnauthorized) onUnauthorized();
}

async function post<T = Json>(path: string, body: Json): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text();
    handleStatus(res.status, path);
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

// ---- Cache offline (lecture) ----
async function cachedPost<T = Json>(key: string, path: string, body: Json,
                                    ttlMin = 60): Promise<T> {
  try {
    const data = await post<T>(path, body);
    await AsyncStorage.setItem(key, JSON.stringify({ t: Date.now(), data }));
    return data;
  } catch (e) {
    const raw = await AsyncStorage.getItem(key);
    if (raw) {
      const { t, data } = JSON.parse(raw);
      if (Date.now() - t < ttlMin * 60_000 * 24) return data as T; // tolérance offline 24× TTL
    }
    throw e;
  }
}

async function get<T = Json>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, { headers: authHeaders() });
  if (!res.ok) { handleStatus(res.status, path); throw new ApiError(res.status, await res.text()); }
  return res.json() as Promise<T>;
}

async function cachedGet<T = Json>(key: string, path: string, ttlMin = 60): Promise<T> {
  try {
    const data = await get<T>(path);
    await AsyncStorage.setItem(key, JSON.stringify({ t: Date.now(), data }));
    return data;
  } catch (e) {
    const raw = await AsyncStorage.getItem(key);
    if (raw) {
      const { t, data } = JSON.parse(raw);
      if (Date.now() - t < ttlMin * 60_000 * 24) return data as T;
    }
    throw e;
  }
}

async function patch<T = Json>(path: string, body: Json): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (!res.ok) { handleStatus(res.status, path); throw new ApiError(res.status, await res.text()); }
  return res.json() as Promise<T>;
}

// ---- File de synchronisation (écriture offline) ----
const SYNC_QUEUE_KEY = 'raid_coach:sync_queue';

export async function queueWrite(path: string, body: Json): Promise<void> {
  const raw = (await AsyncStorage.getItem(SYNC_QUEUE_KEY)) ?? '[]';
  const queue = JSON.parse(raw) as { path: string; body: Json; ts: number }[];
  queue.push({ path, body, ts: Date.now() });
  await AsyncStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(queue));
}

async function del<T = Json>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, { method: 'DELETE', headers: authHeaders() });
  if (!res.ok) { handleStatus(res.status, path); throw new ApiError(res.status, await res.text()); }
  return res.json() as Promise<T>;
}

async function removeCacheByPrefix(...prefixes: string[]): Promise<void> {
  try {
    const keys = await AsyncStorage.getAllKeys();
    const stale = keys.filter(k => prefixes.some(p => k === p || k.startsWith(p)));
    if (stale.length) await AsyncStorage.multiRemove(stale);
  } catch {
    /* best-effort */
  }
}

// Vide les entrées de cache dépendant des séances (agenda, historique,
// analytics) après une écriture, pour éviter d'afficher un agenda périmé.
export async function invalidateAgendaCaches(): Promise<void> {
  await removeCacheByPrefix('cache:agenda:', 'cache:history', 'cache:analytics');
}

// Le mode standby change tout le plan : on vide aussi les caches de plan.
export async function invalidatePlanCaches(): Promise<void> {
  await removeCacheByPrefix('cache:agenda:', 'cache:history', 'cache:analytics',
    'cache:planday:', 'cache:weekly:');
}

export async function flushSyncQueue(): Promise<number> {
  const raw = (await AsyncStorage.getItem(SYNC_QUEUE_KEY)) ?? '[]';
  const queue = JSON.parse(raw) as { path: string; body: Json; ts: number }[];
  const remaining: typeof queue = [];
  for (const item of queue) {
    try {
      await post(item.path, item.body);
    } catch (e) {
      // Erreur client (payload invalide) : inutile de réessayer, on jette l'item.
      // Erreur réseau ou serveur : on garde pour la prochaine synchro.
      if (!(e instanceof ApiError && e.status >= 400 && e.status < 500)) {
        remaining.push(item);
      }
    }
  }
  await AsyncStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(remaining));
  return queue.length - remaining.length;
}

// ---- Endpoints typés ----
export interface DailyDecision {
  best_action: string;
  secondary_action: string | null;
  duration_min: number;
  intensity_cap: number;
  reason: string;
  alternatives: string[];
  safety_notes: string[];
}

export interface SessionItem {
  name: string;
  prescription: string;
  meta: string;
  notes: string;
}

export interface SessionPhase {
  kind: 'warmup' | 'main' | 'cooldown' | 'finisher';
  label: string;
  items: SessionItem[];
}

export interface DetailedSession {
  discipline: string;
  title: string;
  headline: string;
  duration_min: number;
  intensity_cap: number;
  phases: SessionPhase[];
  targets: string[];
  safety_notes: string[];
  alternatives: string[];
  coach_reason: string;
}

export interface AdaptiveContext {
  budget_consumed_pct: number;
  days_since_rest: number;
  last_two_disciplines: string[];
  week_type?: string;
  consumed_su?: number;
  budget_su?: number;
  acute_7d_su?: number;
  acwr?: number;
  acwr_label?: string;
}

export interface RunInterval {
  label?: string;
  pace_kmh?: number; pace_min_km?: string; pct_vma?: number;
  fc_bpm?: number; pct_fcmax?: number; zone?: string;
  reps?: number; series?: number; distance_m?: number; duration_min?: number;
  recovery_type?: string; recovery_sec?: number; recovery_min?: number;
  structure?: string; note?: string; effort?: string; pente?: string;
  fc_attendue_fin?: string; detail?: string;
}

export interface RunSession {
  seed: string; type: string; title: string; difficulty: number;
  duration_min: number; distance_km: number; calories: number;
  warmup: RunInterval; body: RunInterval[]; cooldown: RunInterval;
  sciatic_note: string;
}

export interface Wod {
  name: string; format: string; format_key: string; duration_or_cap: string;
  description: string[]; target_score: string; muscles: string;
  difficulty: number; lumbar_note: string; lumbar_safe: boolean; seed: string;
}

export interface Strength531Set {
  pct_tm: number; reps: string; load_kg: number; rest_sec: number; amrap: boolean;
}
export interface Strength531Accessory {
  name: string; sets: number; reps: string; load_kg: number | null;
  tempo: string; rest_sec: number; notes: string;
}
export interface Strength531 {
  day: string; week: number; cycle: number; is_deload: boolean;
  warmup_mcgill: { name: string; prescription: string; notes?: string }[];
  main_lift: { lift: string; name: string; training_max: number; sets: Strength531Set[]; note: string };
  accessories: Strength531Accessory[];
  finisher_wod: Wod;
  notes: string[];
  grease_the_groove?: string;
}

export interface ProgressionPoint {
  cycle: number; training_max: number; top_set_kg: number; est_1rm: number;
}
export interface StrengthProgression {
  lift: string; name: string; increment: number; goal_1rm?: number; points: ProgressionPoint[];
}
export interface BenchmarkProgression {
  benchmark_id: string;
  results: { test_date: string; result_value: number; result_unit: string }[];
}

export interface SessionToday {
  decision: DailyDecision;
  session: DetailedSession;
  context: AdaptiveContext;
}

export interface PlanSession {
  moment: string; type: string; title: string; duration_min: number; detail: any;
}
export interface StandbyInfo { mode: string; message: string }

export interface PlanDay {
  date: string; day_of_week: string; is_work_day: boolean; week_type: string;
  week_index?: number;
  sessions: PlanSession[];
  standby?: StandbyInfo | null;
}

export interface StandbyState {
  mode: 'pause' | 'vacation' | null;
  start_date: string | null;
  end_date: string | null;
  params: { sessions_per_day?: number; equipment?: string };
  plan_shift_weeks: number;
}
export interface PlanWeek {
  week_index: number; monday: string; week_type: string; days: PlanDay[];
}
export interface WeeklyPlan { from_week: number; n: number; weeks: PlanWeek[]; }

export interface AthleteProfile {
  name?: string;
  birth_date?: string;
  height_cm?: number;
  weight_kg?: number;
  target_weight_kg?: number;
  body_fat_pct?: number;
  fc_max?: number;
  vma_kmh?: number;
  main_goal?: string;
  goal_date?: string;
  injuries?: { zone: string; type: string; note?: string }[];
  current: Record<string, number>;
}

export interface SessionScore {
  type: 'time' | 'reps';
  value: number;
  label: string | null;
  capped: boolean;
  cap_sec: number | null;
}

export interface SessionRow {
  session_date: string;
  discipline: string;
  duration_min: number;
  intensity_rpe?: number;
  stress_units?: number;
  status: string;
  family_id?: string | null;
  score?: SessionScore;
}

export interface AgendaDay {
  date: string;
  day_of_week: string;
  is_work_day: boolean;
  intent: { focus: string; label: string; load: string };
  done: { discipline: string; duration_min: number; status: string;
          title?: string | null; score_label?: string | null } | null;
}

export interface AgendaWeek {
  monday: string;
  week_type: 'big_work' | 'small_work';
  work_days: string[];
  off_days: string[];
  days: AgendaDay[];
}

export interface AnalyticsSnapshot {
  status: string;
  message?: string;
  fitness?: number;
  fatigue?: number;
  acwr?: number;
  readiness?: number;
  readiness_trend?: string;
  performance?: number;
  performance_source?: 'wod' | 'readiness_proxy';
  wods_scored?: number;
  risk?: string;
  risk_reasons?: string[];
  sessions_logged?: number;
}

export interface ChatReply {
  reply: string;
  topic: string;
  suggestions: string[];
}

export interface AuthUser { id: number; email: string; is_owner: boolean }
export interface AuthResponse { token: string; user: AuthUser }

export interface RoadmapBlock {
  phase: string;
  week_start: number;
  week_end: number;
  focus: string;
  weekly_su: number[];
  is_current: boolean;
}

export interface Roadmap {
  weeks_total: number;
  selection_week: number;
  current_week: number;
  current_phase: string;
  current_focus: string;
  blocks: RoadmapBlock[];
  milestones: string[];
}

export interface HRZone {
  zone: string;
  min_bpm: number;
  max_bpm: number;
  description: string;
}

export interface HRProfile {
  fc_max: number;
  method: string;
  zones: HRZone[];
}

export interface PaceTarget {
  zone: string;
  pace_fast: string;
  pace_slow: string;
}

export interface PaceTable {
  vma_kmh: number;
  terrain: string;
  targets: PaceTarget[];
}

export interface MacroTarget {
  day_type: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  water_l: number;
  notes: string[];
}

export interface SupplementItem { name: string; dose: string; with: string; evidence: string; why: string; }
export interface SupplementSchedule {
  session_type: string; context: string;
  groups: { when: string; label: string; items: SupplementItem[] }[];
}
export interface FoodItem { id: string; name: string; p: number; c: number; f: number; kcal: number; cat: string; state: string; }
export interface PortionItem { id: string; name: string; grams: number; p: number; c: number; f: number; kcal: number; }
export interface Portions {
  target: { p: number; c: number; f: number };
  items: PortionItem[];
  totals: { p: number; c: number; f: number; kcal: number };
  note: string;
}
export interface Synergy { combo: string; evidence: string; why: string; example: string; }
export interface AntiSynergy { pair: string; mechanism: string; magnitude: string; delay: string; }
export interface Guardrail { code: string; level: string; message: string; }

export const api = {
  health: () => fetch(`${BASE_URL}/health`).then(r => r.ok),

  dailyDecision: (ctx: Json) =>
    cachedPost<DailyDecision>('cache:daily', '/coach/daily-decision', ctx, 60),

  sessionToday: (ctx: Json) =>
    cachedPost<SessionToday>('cache:session', '/coach/session', ctx, 60),

  // Générateur dédié d'une page (course/force/wod) — toujours frais, pas de cache.
  generate: (body: Json) => post<DetailedSession>('/generate', body),

  // Mission 2 — générateur Run (700 séances)
  generateRun: (type: string, seed: number, vma?: number, fcmax?: number) =>
    get<RunSession>(`/generate/run?type=${type}&seed=${seed}` +
      (vma ? `&vma=${vma}` : '') + (fcmax ? `&fcmax=${fcmax}` : '')),

  // Mission 3 — générateur WOD (15 formats)
  generateWod: (body: Json) => post<Wod>('/generate/wod', body),
  randomWod: (excludeLumbar = true) =>
    get<Wod>(`/generate/wod/random?exclude_lumbar=${excludeLumbar}`),

  // Mission 4 — force 5/3/1
  strength531: (day: string, week: number, cycle = 0) =>
    get<Strength531>(`/generate/strength?day=${day}&week=${week}&cycle=${cycle}`),
  strengthProgression: (lift: string, cycles = 6) =>
    cachedGet<StrengthProgression>(`cache:prog:${lift}`, `/strength/progression?lift=${lift}&cycles=${cycles}`, 720),
  benchmarkProgression: (id: string) =>
    cachedGet<BenchmarkProgression>(`cache:bench:${id}`, `/benchmarks/${id}/progression`, 60),

  weeklyBudget: (body: Json) =>
    cachedPost('cache:budget', '/coach/weekly-budget', body, 30),

  strengthSession: (body: Json) =>
    cachedPost('cache:strength', '/strength/generate', body, 120),

  raidStrengthReport: (body: Json) =>
    cachedPost('cache:raid_report', '/raid/strength-report', body, 720),

  hrProfile: (body: Json) =>
    cachedPost<HRProfile>('cache:hr', '/run/hr-profile', body, 1440),

  paceTable: (body: Json) =>
    cachedPost<PaceTable>(`cache:paces:${JSON.stringify(body)}`, '/run/pace-table', body, 1440),

  dailyMacros: (body: Json) =>
    cachedPost<MacroTarget>('cache:macros', '/nutrition/daily-macros', body, 240),

  // Nutrition+ (compléments, aliments→grammes, synergies, garde-fous)
  nutritionSupplements: (sessionType: string) =>
    cachedGet<SupplementSchedule>(`cache:supp:${sessionType}`, `/nutrition/supplements?session_type=${sessionType}`, 1440),
  nutritionFoods: () => cachedGet<{ foods: FoodItem[] }>('cache:foods', '/nutrition/foods', 1440),
  nutritionSynergies: () => cachedGet<{ synergies: Synergy[]; anti_synergies: AntiSynergy[] }>('cache:syn', '/nutrition/synergies', 1440),
  nutritionPortions: (body: Json) => post<Portions>('/nutrition/portions', body),
  nutritionGuardrails: (body: Json) => post<{ guardrails: Guardrail[] }>('/nutrition/guardrails', body),

  // Garmin Connect (OAuth serveur)
  garminStatus: () => get<{ configured: boolean; connected: boolean }>('/garmin/status'),
  garminConnect: () => get<{ authorize_url: string }>('/garmin/connect'),
  garminSync: () => post<{ status: string; date: string; metrics: Record<string, number> }>('/garmin/sync', {}),
  garminDisconnect: () => post('/garmin/disconnect', {}),

  weeklyPlan: (fromWeek: number, n = 4, vma?: number, fcmax?: number) =>
    cachedGet<WeeklyPlan>(`cache:weekly:${fromWeek}:${n}`,
      `/plan/weekly?from_week=${fromWeek}&n=${n}` +
      (vma ? `&vma=${vma}` : '') + (fcmax ? `&fcmax=${fcmax}` : ''), 720),

  // Séance(s) planifiée(s) pour une date — même source que weeklyPlan → l'écran
  // Jour, l'onglet Séances et l'Agenda affichent la même séance pour un jour.
  planDay: (date: string, vma?: number, fcmax?: number) =>
    cachedGet<PlanDay>(`cache:planday:${date}`,
      `/plan/day?date=${date}` +
      (vma ? `&vma=${vma}` : '') + (fcmax ? `&fcmax=${fcmax}` : ''), 720),

  profile: () => cachedGet<AthleteProfile>('cache:profile', '/profile', 720),
  roadmap: (weeksToSelection: number, currentWeek = 0) =>
    cachedPost<Roadmap>('cache:roadmap', '/roadmap',
      { weeks_to_selection: weeksToSelection, current_week: currentWeek }, 720),
  agendaWeek: (date: string) =>
    cachedPost<AgendaWeek>(`cache:agenda:${date}`, '/agenda/week', { date }, 60),
  analytics: () =>
    cachedGet<AnalyticsSnapshot>('cache:analytics', '/analytics/snapshot', 30),
  recentSessions: (n = 30) =>
    cachedGet<{ sessions: SessionRow[] }>('cache:history', `/sessions/recent?n=${n}`, 30),

  // Mise à jour profil (interactive) — met à jour le cache au passage
  updateProfile: async (body: Json): Promise<AthleteProfile> => {
    const data = await patch<AthleteProfile>('/profile', body);
    await AsyncStorage.setItem('cache:profile', JSON.stringify({ t: Date.now(), data }));
    return data;
  },

  // Authentification (inscription par code d'invitation, 1er inscrit = propriétaire)
  register: (email: string, password: string, inviteCode?: string, name?: string) =>
    post<AuthResponse>('/auth/register', {
      email, password, invite_code: inviteCode ?? null, name: name ?? null }),
  login: (email: string, password: string) =>
    post<AuthResponse>('/auth/login', { email, password }),
  me: () => get<{ user: AuthUser; registration_open: boolean }>('/auth/me'),

  // Coach Chat — assistant déterministe (pas de cache : réponses contextuelles).
  chat: (message: string, date?: string) =>
    post<ChatReply>('/coach/chat', date ? { message, date } : { message }),

  // Mode standby / vacances (par athlète)
  getStandby: () => get<StandbyState>('/standby'),
  setStandby: async (body: Json): Promise<StandbyState> => {
    const res = await post<StandbyState>('/standby', body);
    await invalidatePlanCaches();
    return res;
  },
  clearStandby: async (): Promise<StandbyState> => {
    const res = await del<StandbyState>('/standby');
    await invalidatePlanCaches();
    return res;
  },

  // Sauvegarde d'une séance générée (planifiée/faite) → tentée en direct,
  // mise en file si hors connexion. Invalide le cache agenda/historique pour
  // que la séance (ex. force « marquée comme faite ») s'y reflète tout de suite.
  saveSession: async (body: Json): Promise<{ session_id?: number; queued?: boolean }> => {
    try {
      const res = await post<{ session_id?: number }>('/sessions/save', body);
      await invalidateAgendaCaches();
      return res;
    } catch {
      await queueWrite('/sessions/save', body);
      await invalidateAgendaCaches();
      return { queued: true };
    }
  },

  // Écritures (passent par la file si offline)
  recordMetrics: (body: Json) => queueWrite('/metrics/record', body),
  completeSession: async (body: Json) => {
    await queueWrite('/sessions/complete', body);
    await invalidateAgendaCaches();
  },
  recordBenchmark: (body: Json) => queueWrite('/benchmarks/record', body),
};
