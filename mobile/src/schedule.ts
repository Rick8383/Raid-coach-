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

export type WeekType = 'big_work' | 'small_work';
export type DayCode = 'mon' | 'tue' | 'wed' | 'thu' | 'fri' | 'sat' | 'sun';

const ANCHOR_MONDAY = Date.UTC(2026, 5, 15); // 15 juin 2026 (mois 0-indexé)
const DAY_MS = 24 * 3600 * 1000;

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

export function weekTypeFor(d: Date): WeekType {
  const weeks = Math.round((mondayOf(d) - ANCHOR_MONDAY) / (7 * DAY_MS));
  // modulo positif des deux côtés de l'ancre
  return ((weeks % 2) + 2) % 2 === 0 ? 'big_work' : 'small_work';
}

export function dayCodeFor(d: Date): DayCode {
  return DAY_CODES[isoWeekdayIndex(d)];
}

export function isWorkDay(d: Date): boolean {
  const set = weekTypeFor(d) === 'big_work' ? BIG_WORK_DAYS : SMALL_WORK_DAYS;
  return set.has(dayCodeFor(d));
}

export interface TrainingIntent {
  focus: 'single' | 'double' | 'swim';
  label: string;
  load: 'light' | 'moderate' | 'high';
}

/** Miroir de engines.schedule.training_intent — intention structurelle du jour. */
export function trainingIntent(dayCode: DayCode, weekType: WeekType, workDay: boolean): TrainingIntent {
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
  intent: TrainingIntent;
}

function isoDate(ms: number): string {
  return new Date(ms).toISOString().slice(0, 10);
}

export function daySchedule(d: Date): DaySchedule {
  const weekType = weekTypeFor(d);
  const dayCode = dayCodeFor(d);
  const workDay = isWorkDay(d);
  return {
    date: isoDate(utcMidnight(d)),
    dayCode,
    weekType,
    isWorkDay: workDay,
    intent: trainingIntent(dayCode, weekType, workDay),
  };
}

/** Semaine Lundi→Dimanche contenant `d`. */
export function weekSchedule(d: Date): { weekType: WeekType; days: DaySchedule[] } {
  const monday = mondayOf(d);
  return {
    weekType: weekTypeFor(d),
    days: Array.from({ length: 7 }, (_, i) => daySchedule(new Date(monday + i * DAY_MS))),
  };
}

export const WEEK_LABEL: Record<WeekType, string> = {
  big_work: 'GRANDE SEMAINE',
  small_work: 'PETITE SEMAINE',
};
