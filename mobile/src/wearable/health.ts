/**
 * Couche wearable — lecture des métriques de santé (HRV, FC repos, sommeil).
 *
 * Deux sources, sélectionnées automatiquement :
 *  1. Apple Santé (HealthKit) via `react-native-health` — actif uniquement dans
 *     un build natif (dev client / EAS). Le module est chargé dynamiquement pour
 *     ne pas casser Expo Go, où il est absent.
 *  2. Simulation — repli pour Expo Go / démo, valeurs plausibles et cohérentes,
 *     clairement étiquetées comme simulées.
 *
 * L'écran de check-in consomme `readHealthSnapshot()` sans se soucier de la source.
 */

export type HealthSource = 'apple_health' | 'garmin' | 'simulated' | 'manual';

export interface HealthSnapshot {
  hrv_ms: number | null;        // HRV SDNN en millisecondes
  resting_hr: number | null;    // FC de repos (bpm)
  sleep_hours: number | null;   // durée de sommeil (h)
  sleep_quality: number | null; // qualité dérivée 0-100
  source: HealthSource;
  source_label: string;
  measured_at: string;          // ISO
}

export function sleepQualityFromHours(hours: number): number {
  const ratio = Math.min(1, hours / 8);
  return Math.round(40 + ratio * 60);
}

/** Charge le module natif seulement s'il existe (jamais en Expo Go). */
function loadAppleHealth(): any | null {
  try {
    // eslint-disable-next-line no-eval -- require dynamique : évite que Metro
    // tente de résoudre un module natif absent en Expo Go.
    const dynamicRequire = eval('require') as (m: string) => any;
    const mod = dynamicRequire('react-native-health');
    return mod?.default ?? mod ?? null;
  } catch {
    return null;
  }
}

async function readApple(health: any): Promise<HealthSnapshot | null> {
  const perms = {
    permissions: {
      read: ['HeartRateVariabilitySDNN', 'RestingHeartRate', 'SleepAnalysis'],
      write: [],
    },
  };
  const init = () => new Promise<boolean>((resolve) => {
    health.initHealthKit(perms, (err: unknown) => resolve(!err));
  });
  const ok = await init();
  if (!ok) return null;

  const opts = { startDate: new Date(Date.now() - 36 * 3600 * 1000).toISOString() };
  const last = <T,>(fn: string): Promise<number | null> => new Promise((resolve) => {
    health[fn](opts, (err: unknown, res: any) => {
      if (err || !res) return resolve(null);
      const sample = Array.isArray(res) ? res[res.length - 1] : res;
      resolve(typeof sample?.value === 'number' ? sample.value : null);
    });
  });

  const hrvSec = await last('getHeartRateVariabilitySamples'); // secondes
  const rhr = await last('getRestingHeartRate');
  const sleepHours = await last('getSleepSamples'); // approx; réel = somme des phases
  return {
    hrv_ms: hrvSec != null ? Math.round(hrvSec * 1000) : null,
    resting_hr: rhr != null ? Math.round(rhr) : null,
    sleep_hours: sleepHours,
    sleep_quality: sleepHours != null ? sleepQualityFromHours(sleepHours) : null,
    source: 'apple_health',
    source_label: 'Apple Santé',
    measured_at: new Date().toISOString(),
  };
}

/** Simulation déterministe-ish basée sur le jour (cohérente sur une journée). */
function readSimulated(): HealthSnapshot {
  const day = new Date();
  const seed = day.getUTCFullYear() * 366 + day.getUTCMonth() * 31 + day.getUTCDate();
  const wob = (n: number, span: number) => ((seed * 9301 + n * 49297) % 233280) / 233280 * span;
  const sleepHours = Math.round((6.8 + wob(1, 1.6)) * 10) / 10; // 6.8–8.4 h
  return {
    hrv_ms: Math.round(55 + wob(2, 25)),     // 55–80 ms
    resting_hr: Math.round(45 + wob(3, 8)),   // 45–53 bpm
    sleep_hours: sleepHours,
    sleep_quality: sleepQualityFromHours(sleepHours),
    source: 'simulated',
    source_label: 'Simulation (démo)',
    measured_at: day.toISOString(),
  };
}

export async function readHealthSnapshot(): Promise<HealthSnapshot> {
  const apple = loadAppleHealth();
  if (apple) {
    try {
      const snap = await readApple(apple);
      if (snap) return snap;
    } catch {
      /* échec HealthKit → repli simulation */
    }
  }
  return readSimulated();
}
