/**
 * Planning police 3/2/2/3 — miroir offline de engines/schedule/police_schedule.py.
 *
 * Doit rester strictement aligné sur le backend (même ancre, mêmes jours).
 * Calculé localement pour fonctionner hors connexion (le calendrier est
 * déterministe : pure arithmétique de dates).
 *
 * Ancre verrouillée le 13/06/2026 : la semaine du lundi 15/06/2026 est une
 * GRANDE semaine. Les semaines alternent ensuite.
 */

export type WeekType = 'big_work' | 'small_work' | 'weekly';
export type DayCode = 'mon' | 'tue' | 'wed' | 'thu' | 'fri' | 'sat' | 'sun';

// Rythme de travail PAR ATHLÈTE (miroir de engines/schedule/user_schedule.py).
export type ScheduleConfig =
  | { type: 'police_3223'; anchor_big_week_monday?: string }
  | { type: 'weekly'; training_days: DayCode[] };

const DEFAULT_ANCHOR_ISO = '2026-06-15';
const ANCHOR_MONDAY = Date.UTC(2026, 5, 15); // 15 juin 2026 (mois 0-indexé) — défaut propriétaire
const DAY_MS = 24 * 3600 * 1000;

/** Normalise un work_schedule (profil) en config exploitable. */
export function configFrom(ws: any): ScheduleConfig {
  if (ws && ws.type === 'weekly' && Array.isArray(ws.training_days)) {
    return { type: 'weekly', training_days: ws.training_days as DayCode[] };
  }
  return { type: 'police_3223', anchor_big_week_monday: ws?.anchor_big_week_monday ?? DEFAULT_ANCHOR_ISO };
}

function anchorMs(config?: ScheduleConfig): number {
  if (config && config.type === 'police_3223' && config.anchor_big_week_monday) {
    const [y, m, d] = config.anchor_big_week_monday.split('-').map(Number);
    return Date.UTC(y, m - 1, d);
  }
  return ANCHOR_MONDAY;
}

export const DAY_CODES: DayCode[] = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];
export const DAY_LABELS: Record<DayCode, string> = {
  mon: 'LUN', tue: 'MAR', wed: 'MER', thu: 'JEU', fri: 'VEN', sat: 'SAM', sun: 'DIM',
};

const BIG_WORK_DAYS = new Set<DayCode>(['mon', 'tue', 'fri', 'sat', 'sun']);
const SMALL_WORK_DAYS = new Set<DayCode>(['wed', 'thu']);

/** Indice du jour (0 = lundi) en UTC, indépendant du fuseau local. */
function isoWeekdayIndex(d: Date): number {
  return (d.getUTCDay() + 6) % 7; // JS: 0=dimanche → 0=lundi
}

function utcMidnight(d: Date): number {
  return Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate());
}

function mondayOf(d: Date): number {
  return utcMidnight(d) - isoWeekdayIndex(d) * DAY_MS;
}

export function weekTypeFor(d: Date, config?: ScheduleConfig): WeekType {
  if (config && config.type === 'weekly') return 'weekly';
  const weeks = Math.round((mondayOf(d) - anchorMs(config)) / (7 * DAY_MS));
  // modulo positif des deux côtés de l'ancre
  return ((weeks % 2) + 2) % 2 === 0 ? 'big_work' : 'small_work';
}

export function dayCodeFor(d: Date): DayCode {
  return DAY_CODES[isoWeekdayIndex(d)];
}

export function isWorkDay(d: Date, config?: ScheduleConfig): boolean {
  if (config && config.type === 'weekly') return false;
  const set = weekTypeFor(d, config) === 'big_work' ? BIG_WORK_DAYS : SMALL_WORK_DAYS;
  return set.has(dayCodeFor(d));
}

/** Jour d'entraînement ? Police = tous les jours ; weekly = jours choisis. */
export function trainsOn(d: Date, config?: ScheduleConfig): boolean {
  if (config && config.type === 'weekly') return config.training_days.includes(dayCodeFor(d));
  return true;
}

export interface TrainingIntent {
  focus: 'single' | 'double' | 'swim' | 'rest';
  label: string;
  load: 'light' | 'moderate' | 'high';
}

/** Miroir de engines.schedule.training_intent — intention structurelle du jour. */
export function trainingIntent(dayCode: DayCode, weekType: WeekType, workDay: boolean,
                               trains = true): TrainingIntent {
  if (weekType === 'weekly') {
    return trains
      ? { focus: 'single', label: 'Séance du jour', load: 'moderate' }
      : { focus: 'rest', label: 'Repos', load: 'light' };
  }
  if (!workDay && dayCode === 'sun' && weekType === 'small_work') {
    return { focus: 'swim', label: 'Natation récup + apnée', load: 'light' };
  }
  if (workDay) return { focus: 'single', label: 'Séance courte qualité', load: 'moderate' };
  return { focus: 'double', label: 'Double séance (course + force)', load: 'high' };
}

export interface DaySchedule {
  date: string;          // YYYY-MM-DD
  dayCode: DayCode;
  weekType: WeekType;
  isWorkDay: boolean;
  trains: boolean;
  intent: TrainingIntent;
}

function isoDate(ms: number): string {
  return new Date(ms).toISOString().slice(0, 10);
}

export function daySchedule(d: Date, config?: ScheduleConfig): DaySchedule {
  const weekType = weekTypeFor(d, config);
  const dayCode = dayCodeFor(d);
  const workDay = isWorkDay(d, config);
  const trains = trainsOn(d, config);
  return {
    date: isoDate(utcMidnight(d)),
    dayCode,
    weekType,
    isWorkDay: workDay,
    trains,
    intent: trainingIntent(dayCode, weekType, workDay, trains),
  };
}

/** Semaine Lundi→Dimanche contenant `d`. */
export function weekSchedule(d: Date, config?: ScheduleConfig): { weekType: WeekType; days: DaySchedule[] } {
  const monday = mondayOf(d);
  return {
    weekType: weekTypeFor(d, config),
    days: Array.from({ length: 7 }, (_, i) => daySchedule(new Date(monday + i * DAY_MS), config)),
  };
}

export const WEEK_LABEL: Record<WeekType, string> = {
  big_work: 'GRANDE SEMAINE',
  small_work: 'PETITE SEMAINE',
  weekly: 'HEBDOMADAIRE',
};

/** Index de semaine absolu depuis l'ancre (0 = semaine du 15/06/2026). */
export function currentWeekIndex(d: Date = new Date()): number {
  return Math.max(0, Math.round((mondayOf(d) - ANCHOR_MONDAY) / (7 * DAY_MS)));
}
