/**
 * Rendu partagé des séances planifiées d'un jour — source unique d'affichage
 * pour l'Agenda (plan détaillé), l'écran Jour et l'onglet Séances. Comme les
 * trois consomment les MÊMES données (/plan/day ou /plan/weekly, mêmes seeds),
 * une séance donnée est identique partout.
 *
 * Chaque séance se déplie (détail course/force/WOD/natation). En option
 * (`completable`), on peut la marquer « faite » avec son RPE → enregistrée
 * comme séance done (charge + suivi), avec invalidation du cache agenda.
 */
import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { PlanSession, StandbyInfo, api } from '../api/client';
import { RunDetail, StrengthDetail, WodDetail } from './SessionDetail';
import { RpeScale } from './RpeScale';
import { WatchMetricsForm, WatchMetricsView, WatchMetrics } from './WatchMetricsForm';
import { StrengthActualsForm, PerformedView, Performed } from './StrengthActualsForm';
import { colors, spacing, typography } from '../theme/tokens';

const TYPE_COLOR: Record<string, string> = {
  run: colors.fitness, strength: colors.readyRed, crossfit: colors.readyOrange,
  swim: colors.signal, recovery: colors.signal, rest: colors.textDisabled,
};
const TYPE_LABEL: Record<string, string> = {
  run: 'COURSE', strength: 'FORCE', crossfit: 'WOD', swim: 'NATATION',
  recovery: 'RÉCUP', rest: 'REPOS',
};
const COMPLETABLE = new Set(['run', 'strength', 'crossfit', 'swim']);

function SessionExpanded({ s }: { s: PlanSession }) {
  const d = s.detail || {};
  if (s.type === 'run' && Array.isArray(d.body)) return <RunDetail session={d} />;
  if (s.type === 'strength' && (d.main_lift || d.movements)) return <StrengthDetail session={d} />;
  if (s.type === 'crossfit' && Array.isArray(d.description)) return <WodDetail wod={d} />;
  if (s.type === 'swim' && Array.isArray(d.blocks)) {
    return <View>{d.blocks.map((b: string, i: number) => (
      <Text key={i} style={styles.detailLine}>• {b}</Text>))}</View>;
  }
  return null;
}

const METRIC_KEYS: (keyof WatchMetrics)[] = [
  'distance_km', 'hr_avg', 'hr_max', 'elevation_m', 'calories', 'cadence_spm',
  'te_aerobic', 'te_anaerobic',
];

function CompleteRow({ s, dateIso }: { s: PlanSession; dateIso: string }) {
  const [open, setOpen] = useState(false);
  const [rpe, setRpe] = useState(7);
  const [watchOpen, setWatchOpen] = useState(false);
  const [metrics, setMetrics] = useState<WatchMetrics>({ duration_min: s.duration_min });
  const [liftsOpen, setLiftsOpen] = useState(false);
  const [performed, setPerformed] = useState<Performed | null>(null);
  const [done, setDone] = useState(false);
  const isStrength = s.type === 'strength';

  const save = async () => {
    const dur = metrics.duration_min && metrics.duration_min > 0 ? metrics.duration_min : s.duration_min;
    const body: Record<string, unknown> = {
      discipline: s.type, session_date: dateIso, duration_min: dur,
      intensity_rpe: rpe, title: s.title, status: 'done', detail: s.detail ?? {},
    };
    for (const k of METRIC_KEYS) {
      const v = metrics[k];
      if (typeof v === 'number' && v > 0) body[k] = v;
    }
    if (performed && performed.sets.some(x => x.load_kg > 0 || x.reps > 0)) body.performed = performed;
    await api.saveSession(body);
    setDone(true);
  };

  if (done) {
    return (
      <View>
        <Text style={styles.doneMsg}>✓ Séance enregistrée comme faite (RPE {rpe})</Text>
        {performed ? <PerformedView p={performed} /> : null}
        <WatchMetricsView m={metrics} />
      </View>
    );
  }
  if (!COMPLETABLE.has(s.type)) return null;
  return (
    <View style={styles.completeBox}>
      {open ? (
        <>
          <Text style={styles.rpeLbl}>DIFFICULTÉ RESSENTIE (RPE)</Text>
          <RpeScale value={rpe} onChange={setRpe} />

          {isStrength && (
            <>
              <Pressable onPress={() => setLiftsOpen(o => !o)} style={styles.watchToggle}>
                <Text style={styles.watchToggleT}>
                  {liftsOpen ? '−' : '＋'} Séries réalisées (reps × charge)
                </Text>
              </Pressable>
              {liftsOpen && <StrengthActualsForm detail={s.detail} onChange={setPerformed} />}
            </>
          )}

          <Pressable onPress={() => setWatchOpen(o => !o)} style={styles.watchToggle}>
            <Text style={styles.watchToggleT}>
              {watchOpen ? '−' : '＋'} Données réelles de la montre (Garmin)
            </Text>
          </Pressable>
          {watchOpen && <WatchMetricsForm defaultDuration={s.duration_min} onChange={setMetrics} />}

          <Pressable onPress={save} style={styles.doneBtn}>
            <Text style={styles.doneBtnT}>✓ ENREGISTRER COMME FAIT</Text>
          </Pressable>
        </>
      ) : (
        <Pressable onPress={() => setOpen(true)} style={styles.markBtn}>
          <Text style={styles.markBtnT}>✓ MARQUER FAIT</Text>
        </Pressable>
      )}
    </View>
  );
}

const STANDBY_COLOR: Record<string, string> = {
  pause: colors.readyYellow, reboot: colors.signal, vacation: colors.signal,
};

export function PlannedSessions({ sessions, dateIso, completable = false, standby = null }: {
  sessions: PlanSession[];
  dateIso?: string;
  completable?: boolean;
  standby?: StandbyInfo | null;
}) {
  const [open, setOpen] = useState<number | null>(completable && sessions.length === 1 ? 0 : null);

  const banner = standby ? (
    <View style={[styles.standby, { borderLeftColor: STANDBY_COLOR[standby.mode] ?? colors.signal }]}>
      <Text style={[styles.standbyTag, { color: STANDBY_COLOR[standby.mode] ?? colors.signal }]}>
        {standby.mode === 'pause' ? '⏸ STANDBY' : standby.mode === 'reboot' ? '↩ REPRISE' : '🏝 VACANCES'}
      </Text>
      <Text style={styles.standbyMsg}>{standby.message}</Text>
    </View>
  ) : null;

  if (!sessions.length) {
    return (
      <View>
        {banner}
        {!standby && <Text style={styles.rest}>Repos — rien de prescrit aujourd'hui.</Text>}
      </View>
    );
  }
  return (
    <View>
      {banner}
      {sessions.map((s, i) => {
        const opened = open === i;
        return (
          <View key={i}>
            <Pressable onPress={() => setOpen(opened ? null : i)} style={styles.sessRow}>
              <View style={[styles.dot, { backgroundColor: TYPE_COLOR[s.type] ?? colors.textDisabled }]} />
              <View style={{ flex: 1 }}>
                <Text style={styles.sessTitle}>{s.title}</Text>
                <Text style={styles.sessMeta}>
                  {s.moment} · {TYPE_LABEL[s.type] ?? s.type} · {s.duration_min} min
                </Text>
              </View>
              <Text style={styles.chevron}>{opened ? '−' : '+'}</Text>
            </Pressable>
            {opened && (
              <View style={styles.detail}>
                <SessionExpanded s={s} />
                {completable && dateIso && <CompleteRow s={s} dateIso={dateIso} />}
              </View>
            )}
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  sessRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.s, borderTopWidth: 1, borderTopColor: colors.hairline, gap: spacing.s },
  dot: { width: 8, height: 8, borderRadius: 4 },
  sessTitle: { color: colors.textPrimary, fontSize: typography.sizes.body },
  sessMeta: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: 2 },
  chevron: { color: colors.signal, fontSize: 20, width: 20, textAlign: 'center' },
  detail: { paddingLeft: spacing.m, paddingBottom: spacing.s, gap: 2 },
  detailLine: { color: colors.textSecondary, fontSize: typography.sizes.small, lineHeight: 19 },
  rest: { color: colors.textDisabled, fontSize: typography.sizes.small, paddingVertical: spacing.m },
  standby: { borderLeftWidth: 3, paddingLeft: spacing.s, paddingVertical: spacing.xs, marginBottom: spacing.s, backgroundColor: colors.bgElevated, borderRadius: 6 },
  standbyTag: { ...typography.label, fontSize: 10 },
  standbyMsg: { color: colors.textSecondary, fontSize: typography.sizes.small, lineHeight: 18, marginTop: 2 },
  completeBox: { marginTop: spacing.m },
  markBtn: { paddingVertical: 12, borderRadius: spacing.cardRadius, borderWidth: 1, borderColor: colors.signal, alignItems: 'center' },
  markBtnT: { color: colors.signal, ...typography.label, fontSize: 11 },
  rpeLbl: { color: colors.textSecondary, ...typography.label, marginBottom: spacing.s, textAlign: 'center' },
  watchToggle: { marginTop: spacing.m, paddingVertical: spacing.s, alignItems: 'center' },
  watchToggleT: { color: colors.signal, fontSize: typography.sizes.small, ...typography.bodyBold },
  doneBtn: { backgroundColor: colors.signal, paddingVertical: 14, borderRadius: spacing.cardRadius, alignItems: 'center', marginTop: spacing.s },
  doneBtnT: { color: colors.bg, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2, letterSpacing: 1 },
  doneMsg: { color: colors.signal, fontSize: typography.sizes.small, paddingVertical: spacing.m, textAlign: 'center' },
});
