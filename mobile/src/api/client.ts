/**
 * Client API — connecté au backend FastAPI (Build 12).
 * Offline-first : chaque appel passe par le cache local d'abord,
 * la file de synchronisation gère les écritures hors connexion.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

declare const process: { env: Record<string, string | undefined> };
const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';

type Json = Record<string, unknown>;

class ApiError extends Error {
  constructor(readonly status: number, detail: string) {
    super(`API ${status}: ${detail}`);
  }
}

async function post<T = Json>(path: string, body: Json): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text();
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
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) throw new ApiError(res.status, await res.text());
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
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new ApiError(res.status, await res.text());
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

export interface SessionToday {
  decision: DailyDecision;
  session: DetailedSession;
}

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

export interface AgendaDay {
  date: string;
  day_of_week: string;
  is_work_day: boolean;
  intent: { focus: string; label: string; load: string };
  done: { discipline: string; duration_min: number; status: string } | null;
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
  risk?: string;
  risk_reasons?: string[];
  sessions_logged?: number;
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

export const api = {
  health: () => fetch(`${BASE_URL}/health`).then(r => r.ok),

  dailyDecision: (ctx: Json) =>
    cachedPost<DailyDecision>('cache:daily', '/coach/daily-decision', ctx, 60),

  sessionToday: (ctx: Json) =>
    cachedPost<SessionToday>('cache:session', '/coach/session', ctx, 60),

  weeklyBudget: (body: Json) =>
    cachedPost('cache:budget', '/coach/weekly-budget', body, 30),

  strengthSession: (body: Json) =>
    cachedPost('cache:strength', '/strength/generate', body, 120),

  raidStrengthReport: (body: Json) =>
    cachedPost('cache:raid_report', '/raid/strength-report', body, 720),

  paceTable: (body: Json) =>
    cachedPost('cache:paces', '/run/pace-table', body, 1440),

  dailyMacros: (body: Json) =>
    cachedPost<MacroTarget>('cache:macros', '/nutrition/daily-macros', body, 240),

  profile: () => cachedGet<AthleteProfile>('cache:profile', '/profile', 720),
  agendaWeek: (date: string) =>
    cachedPost<AgendaWeek>(`cache:agenda:${date}`, '/agenda/week', { date }, 60),
  analytics: () =>
    cachedGet<AnalyticsSnapshot>('cache:analytics', '/analytics/snapshot', 30),
  recentSessions: (n = 30) =>
    cachedGet<{ sessions: AgendaDay['done'][] }>('cache:history', `/sessions/recent?n=${n}`, 30),

  // Mise à jour profil (interactive) — met à jour le cache au passage
  updateProfile: async (body: Json): Promise<AthleteProfile> => {
    const data = await patch<AthleteProfile>('/profile', body);
    await AsyncStorage.setItem('cache:profile', JSON.stringify({ t: Date.now(), data }));
    return data;
  },

  // Écritures (passent par la file si offline)
  recordMetrics: (body: Json) => queueWrite('/metrics/record', body),
  completeSession: (body: Json) => queueWrite('/sessions/complete', body),
  recordBenchmark: (body: Json) => queueWrite('/benchmarks/record', body),
};
