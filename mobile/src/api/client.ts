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

export const api = {
  health: () => fetch(`${BASE_URL}/health`).then(r => r.ok),

  dailyDecision: (ctx: Json) =>
    cachedPost<DailyDecision>('cache:daily', '/coach/daily-decision', ctx, 60),

  weeklyBudget: (body: Json) =>
    cachedPost('cache:budget', '/coach/weekly-budget', body, 30),

  strengthSession: (body: Json) =>
    cachedPost('cache:strength', '/strength/generate', body, 120),

  raidStrengthReport: (body: Json) =>
    cachedPost('cache:raid_report', '/raid/strength-report', body, 720),

  paceTable: (body: Json) =>
    cachedPost('cache:paces', '/run/pace-table', body, 1440),

  dailyMacros: (body: Json) =>
    cachedPost('cache:macros', '/nutrition/daily-macros', body, 240),

  // Écritures (passent par la file si offline)
  recordMetrics: (body: Json) => queueWrite('/metrics/record', body),
  completeSession: (body: Json) => queueWrite('/sessions/complete', body),
  recordBenchmark: (body: Json) => queueWrite('/benchmarks/record', body),
};
