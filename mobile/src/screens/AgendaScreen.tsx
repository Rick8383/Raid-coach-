/**
 * Agenda — la semaine d'entraînement calée sur le planning 3/2/2/3.
 * Navigation semaine par semaine, intention par jour (service / OFF / double),
 * séances réalisées cochées, et un encart "état de forme" (analytics).
 */
import React, { useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { AgendaWeek, AnalyticsSnapshot, AthleteProfile, DoneEntry, api } from '../api/client';
import { ReadinessBar } from '../components/ReadinessBar';
import { PlanView } from '../components/PlanView';
import { WatchMetricsView } from '../components/WatchMetricsForm';
import { PerformedView } from '../components/StrengthActualsForm';
import { WodScoreSheet, WodScoreInput, modeForFormatKey } from '../components/WodScoreSheet';
import { Card, Tag } from '../components/ui';
import { DAY_LABELS, DayCode, WEEK_LABEL, todayLocalAsUTC, localISODate } from '../schedule';
import {
  colors, disciplineLabel, ReadinessLevel, spacing, typography,
} from '../theme/tokens';

const DAY_MS = 24 * 3600 * 1000;

function mondayISO(offsetWeeks: number): string {
  const now = todayLocalAsUTC();   // date CALENDRIER LOCAL (pas UTC)
  const utc = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  const isoWeekday = (now.getUTCDay() + 6) % 7;
  return new Date(utc - isoWeekday * DAY_MS + offsetWeeks * 7 * DAY_MS)
    .toISOString().slice(0, 10);
}

const STATUS_META: Record<string, { label: string; color: string }> = {
  CLEAR: { label: 'Voie libre', color: colors.signal },
  PROGRESSING: { label: 'En progression', color: colors.signal },
  WEAKNESS_FOCUS: { label: 'Focus point faible', color: colors.readyYellow },
  RISK_CONTROL: { label: 'Maîtrise du risque', color: colors.readyOrange },
  warming_up: { label: 'Mise en route', color: colors.textSecondary },
};

export function AgendaScreen({ profile }: { profile?: AthleteProfile | null }) {
  const [view, setView] = useState<'plan' | 'suivi'>('plan');
  const [offset, setOffset] = useState(0);
  const [week, setWeek] = useState<AgendaWeek | null>(null);
  const [stats, setStats] = useState<AnalyticsSnapshot | null>(null);
  const todayIso = mondayISO(0); // lundi de la semaine courante (pour repère)

  const reload = () => api.agendaWeek(mondayISO(offset)).then(setWeek).catch(() => setWeek(null));
  useEffect(() => { reload(); }, [offset]); // eslint-disable-line react-hooks/exhaustive-deps

  // Séance CrossFit dont on saisit/corrige le score (fenêtre modale).
  const [editing, setEditing] = useState<DoneEntry | null>(null);

  const submitScore = async (s: WodScoreInput) => {
    if (!editing?.id) return null;
    const res = await api.updateWodScore(editing.id, s as unknown as Record<string, unknown>);
    await reload();
    return res.assessment;
  };

  const removeDone = async (id?: number) => {
    if (!id) return;
    try { await api.deleteSession(id); await reload(); } catch { /* ignore */ }
  };

  useEffect(() => {
    api.analytics().then(setStats).catch(() => {});
  }, []);

  const nowIso = localISODate();

  return (
    <ScrollView style={styles.root} contentContainerStyle={{ padding: spacing.m }}>
      {/* État de forme */}
      {stats && <FormCard stats={stats} />}

      {/* Bascule Plan détaillé / Suivi */}
      <View style={styles.viewToggle}>
        {(['plan', 'suivi'] as const).map(v => (
          <Pressable key={v} onPress={() => setView(v)}
            style={[styles.viewBtn, view === v && styles.viewBtnOn]}>
            <Text style={[styles.viewText, view === v && styles.viewTextOn]}>
              {v === 'plan' ? 'PLAN DÉTAILLÉ' : 'SUIVI / RÉALISÉ'}
            </Text>
          </Pressable>
        ))}
      </View>

      {view === 'plan' && <PlanView profile={profile ?? null} />}

      {view === 'suivi' && (<>
      {/* Sélecteur de semaine */}
      <View style={styles.weekNav}>
        <Pressable onPress={() => setOffset(o => o - 1)} hitSlop={12}>
          <Text style={styles.nav}>‹</Text>
        </Pressable>
        <View style={{ alignItems: 'center' }}>
          <Text style={styles.weekTitle}>
            {offset === 0 ? 'CETTE SEMAINE' : offset > 0 ? `+${offset} SEM.` : `${offset} SEM.`}
          </Text>
          {week && <Tag label={WEEK_LABEL[week.week_type]}
            color={week.week_type === 'big_work' ? colors.fitness : colors.signal} />}
        </View>
        <Pressable onPress={() => setOffset(o => o + 1)} hitSlop={12}>
          <Text style={styles.nav}>›</Text>
        </Pressable>
      </View>

      {/* Jours */}
      {week?.days.map(day => {
        const isToday = day.date === nowIso;
        const off = !day.is_work_day;
        const level: ReadinessLevel = day.done
          ? (day.done.status === 'done' ? 'green' : 'yellow')
          : off ? 'yellow' : 'orange';
        return (
          <Card key={day.date} style={{ flexDirection: 'row', marginBottom: spacing.s,
            ...(isToday ? { borderWidth: 1, borderColor: colors.signal } : {}) }}>
            <ReadinessBar level={level} />
            <View style={styles.dayBody}>
              <View style={styles.dayHead}>
                <Text style={[styles.dayName, isToday && { color: colors.signal }]}>
                  {DAY_LABELS[day.day_of_week as DayCode]} {day.date.slice(8)}/{day.date.slice(5, 7)}
                </Text>
                <Tag label={off ? 'OFF' : 'SERVICE'}
                  color={off ? colors.signal : colors.textSecondary} filled={off} />
              </View>
              <Text style={styles.intent}>{day.intent.label}</Text>
              {(day.done_all?.length ? day.done_all : day.done ? [day.done] : []).map((e, i) => (
                // TOUTES les séances du jour (ex. CAP matin + force soir) —
                // chacune comptée au suivi, supprimable individuellement (✕).
                <View key={e.id ?? i}>
                  <View style={styles.doneRow}>
                    <Text style={[e.status === 'done' ? styles.done : styles.planned, { flex: 1 }]}>
                      {e.status === 'done' ? '✓' : '○'} {disciplineLabel(e.discipline)}
                      {e.title ? ` · ${e.title}` : ''}
                      {' · '}{e.duration_min} min
                      {e.status === 'done' ? ' · fait' : ' · prévu'}
                      {e.score_label ? ` · 🏁 ${e.score_label}` : ''}
                    </Text>
                    {e.id ? (
                      <Pressable onPress={() => removeDone(e.id!)} hitSlop={8} style={styles.delBtn}>
                        <Text style={styles.delT}>✕</Text>
                      </Pressable>
                    ) : null}
                  </View>
                  {/* WOD : saisir ou corriger le score (temps/tours/reps/distance).
                      Disponible aussi sur une séance encore PRÉVUE — saisir le
                      score vaut réalisation, elle bascule alors en « fait ». */}
                  {e.discipline === 'crossfit' && e.id && (
                    <Pressable onPress={() => setEditing(e)} style={styles.scoreBtn}>
                      <Text style={styles.scoreT}>
                        {e.score_label ? '✎ MODIFIER LE SCORE' : '＋ SAISIR LE SCORE DU WOD'}
                      </Text>
                    </Pressable>
                  )}
                  {e.assessment ? (
                    <Text style={styles.assess}>💬 {e.assessment.comment}</Text>
                  ) : null}
                  {e.performed ? <PerformedView p={e.performed} /> : null}
                  {e.metrics ? <WatchMetricsView m={e.metrics} /> : null}
                </View>
              ))}
              {!day.done && !day.done_all?.length && <Text style={styles.pending}>—</Text>}
            </View>
          </Card>
        );
      })}
      </>)}

      {editing && (
        <WodScoreSheet
          visible
          title={editing.title ?? 'WOD'}
          initial={{
            mode: (editing.wod_result?.mode as 'for_time' | 'amrap')
              ?? modeForFormatKey(editing.wod_format_key),
            time_sec: editing.wod_result?.time_sec ?? 0,
            reps: editing.wod_result?.reps ?? 0,
            rounds: editing.wod_result?.rounds,
            distance_m: editing.wod_result?.distance_m,
            capped: !!editing.wod_result?.capped,
            cap_sec: editing.wod_result?.cap_sec ?? (editing.duration_min ?? 0) * 60,
          }}
          onSubmit={submitScore}
          onClose={() => setEditing(null)} />
      )}
    </ScrollView>
  );
}

function FormCard({ stats }: { stats: AnalyticsSnapshot }) {
  const meta = STATUS_META[stats.status] ?? { label: stats.status, color: colors.textSecondary };
  if (stats.status === 'warming_up') {
    return (
      <Card style={{ padding: spacing.m, marginBottom: spacing.m }}>
        <Text style={styles.formLabel}>ÉTAT DE FORME</Text>
        <Text style={styles.warming}>{stats.message}</Text>
      </Card>
    );
  }
  return (
    <Card style={{ padding: spacing.m, marginBottom: spacing.m }}>
      <View style={styles.formHead}>
        <Text style={styles.formLabel}>ÉTAT DE FORME</Text>
        <Tag label={meta.label} color={meta.color} />
      </View>
      <View style={styles.metricsRow}>
        <Metric value={`${stats.fitness ?? '—'}`} label="forme" />
        <Metric value={`${stats.readiness ?? '—'}`} label="readiness" />
        <Metric value={`${stats.acwr ?? '—'}`} label="ACWR"
          color={(stats.acwr ?? 0) > 1.3 ? colors.readyOrange : colors.signal} />
        <Metric value={(stats.risk ?? '—').toUpperCase()} label="risque"
          color={stats.risk === 'low' ? colors.signal : colors.readyOrange} />
      </View>
      {!!stats.intensity_distribution && (
        // Jauge 80/20 (Seiler) : part du volume course en basse intensité.
        <View style={styles.z2Box}>
          <View style={styles.z2Head}>
            <Text style={styles.z2Label}>COURSE FACILE / INTENSE (objectif 80/20)</Text>
            <Text style={[styles.z2Pct, {
              color: stats.intensity_distribution.low_pct >= 75 ? colors.signal : colors.readyOrange,
            }]}>{stats.intensity_distribution.low_pct}%</Text>
          </View>
          <View style={styles.z2Track}>
            <View style={[styles.z2Fill, { width: `${Math.min(100, stats.intensity_distribution.low_pct)}%` }]} />
            <View style={styles.z2Target} />
          </View>
          <Text style={styles.z2Msg}>{stats.intensity_distribution.message}</Text>
        </View>
      )}
    </Card>
  );
}

function Metric({ value, label, color = colors.textPrimary }:
  { value: string; label: string; color?: string }) {
  return (
    <View style={styles.metric}>
      <Text style={[styles.metricValue, { color }]}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  viewToggle: { flexDirection: 'row', backgroundColor: colors.bgCard, borderRadius: 8, padding: 3, marginBottom: spacing.m },
  viewBtn: { flex: 1, paddingVertical: spacing.s, borderRadius: 6, alignItems: 'center' },
  viewBtnOn: { backgroundColor: colors.signal },
  viewText: { color: colors.textSecondary, ...typography.label, fontSize: 10 },
  viewTextOn: { color: colors.bg },
  formHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  formLabel: { color: colors.textSecondary, ...typography.label },
  scoreBtn: { alignSelf: 'flex-start', paddingVertical: spacing.xs, paddingHorizontal: spacing.s,
    borderRadius: 6, borderWidth: 1, borderColor: colors.signal, marginTop: spacing.xs },
  scoreT: { color: colors.signal, ...typography.label, fontSize: 9 },
  assess: { color: colors.textSecondary, fontSize: typography.sizes.small, lineHeight: 18, marginTop: spacing.xs },
  z2Box: { marginTop: spacing.m },
  z2Head: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  z2Label: { color: colors.textSecondary, ...typography.label, fontSize: 9 },
  z2Pct: { fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2 },
  z2Track: { height: 6, backgroundColor: colors.hairline, borderRadius: 3, marginTop: 4, overflow: 'hidden' },
  z2Fill: { height: 6, backgroundColor: colors.signalDim, borderRadius: 3 },
  z2Target: { position: 'absolute', left: '80%', top: 0, width: 2, height: 6, backgroundColor: colors.textPrimary },
  z2Msg: { color: colors.textSecondary, fontSize: typography.sizes.micro, marginTop: 4, lineHeight: 14 },
  warming: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: spacing.s, lineHeight: 19 },
  metricsRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: spacing.m },
  metric: { alignItems: 'center', flex: 1 },
  metricValue: { fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h1 },
  metricLabel: { color: colors.textDisabled, ...typography.label, fontSize: 9, marginTop: 2 },
  weekNav: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    marginVertical: spacing.m,
  },
  nav: { color: colors.signal, fontSize: 34, paddingHorizontal: spacing.m },
  weekTitle: { color: colors.textPrimary, ...typography.label, marginBottom: spacing.xs },
  dayBody: { flex: 1, padding: spacing.m },
  dayHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  dayName: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2 },
  intent: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: spacing.xs },
  doneRow: { flexDirection: 'row', alignItems: 'center', marginTop: spacing.xs },
  done: { color: colors.signal, fontSize: typography.sizes.small },
  planned: { color: colors.readyYellow, fontSize: typography.sizes.small },
  delBtn: { width: 26, height: 26, borderRadius: 13, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: colors.hairlineStrong, marginLeft: spacing.s },
  delT: { color: colors.readyOrange, fontSize: 13 },
  pending: { color: colors.textDisabled, fontSize: typography.sizes.body, marginTop: spacing.xs },
});
