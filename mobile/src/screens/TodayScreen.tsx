/**
 * Écran d'accueil — "Aujourd'hui".
 * Une seule question : quelle est la meilleure action aujourd'hui ?
 * Cap permanent (compte à rebours sélection) + planning 3/2/2/3 synchronisé
 * sur le calendrier réel + résumé de la séance, qui s'ouvre en détail.
 */
import React, { useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { api, AthleteProfile, PlanDay, SessionToday } from '../api/client';
import { ReadinessBar } from '../components/ReadinessBar';
import { WeekStrip } from '../components/WeekStrip';
import { MeterBar } from '../components/Chart';
import { PlannedSessions } from '../components/PlannedSessions';
import { Card, Tag } from '../components/ui';
import { configFrom, daySchedule, WEEK_LABEL } from '../schedule';
import {
  colors, disciplineLabel, DISCIPLINE, readinessLevelFor, spacing, typography,
} from '../theme/tokens';

const SELECTION_DATE = new Date('2029-03-01'); // sélection 2029 (cf. PROJECT_MASTER)

function weeksToSelection(): number {
  return Math.max(0, Math.round(
    (SELECTION_DATE.getTime() - Date.now()) / (7 * 24 * 3600 * 1000)));
}

type Checkin = { readiness: number; fatigue: number; sleep: number; sciatic: boolean; sleep_hours?: number };

export function TodayScreen({ checkin, profile, onRedoCheckin }: {
  checkin: Checkin;
  profile?: AthleteProfile | null;
  onRedoCheckin?: () => void;
}) {
  const [data, setData] = useState<SessionToday | null>(null);
  const [plan, setPlan] = useState<PlanDay | null>(null);
  const [error, setError] = useState<string | null>(null);

  const today = new Date();
  const cfg = configFrom(profile?.work_schedule);
  const sched = daySchedule(today, cfg);

  useEffect(() => {
    // Contexte adaptatif (budget/ACWR/conseil) — readiness du jour.
    api.sessionToday({
      date: sched.date,
      readiness: checkin.readiness,
      fatigue: checkin.fatigue,
      sleep_quality: checkin.sleep,
      sleep_hours: checkin.sleep_hours,   // < 6 h → intensité plafonnée (Fullagar 2015)
      sciatic_flare: checkin.sciatic,
      weeks_to_main_goal: weeksToSelection(),
    }).then(setData).catch(e => setError(String(e)));
  }, [checkin]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    // Séance(s) du jour = MÊME source que l'Agenda et l'onglet Séances.
    api.planDay(sched.date, profile?.vma_kmh, profile?.fc_max)
      .then(setPlan).catch(() => setPlan(null));
  }, [sched.date, profile]); // eslint-disable-line react-hooks/exhaustive-deps

  const level = readinessLevelFor(checkin.readiness, checkin.sciatic);
  const decision = data?.decision;
  const ctx = data?.context;
  const acwrAlarm = ctx?.acwr_label === 'elevated_injury_risk'
    || ctx?.acwr_label === 'high_injury_risk';

  return (
    <ScrollView style={styles.root} contentContainerStyle={{ padding: spacing.m }}>
      {/* Cap — compte à rebours sélection */}
      <View style={styles.countdown}>
        <Text style={styles.countdownNumber}>{weeksToSelection()}</Text>
        <Text style={styles.countdownLabel}>semaines avant la sélection</Text>
      </View>

      {/* Planning synchronisé sur le rythme de l'athlète */}
      <WeekStrip today={today} config={cfg} />

      {/* Statut du jour (selon le rythme de l'athlète) */}
      <View style={styles.todayRow}>
        {sched.weekType === 'weekly' ? (
          <Tag label={sched.trains ? 'JOUR D\'ENTRAÎNEMENT' : 'JOUR DE REPOS'}
            color={sched.trains ? colors.signal : colors.textSecondary} filled={sched.trains} />
        ) : (
          <Tag label={sched.isWorkDay ? 'JOUR DE SERVICE' : 'JOUR OFF · ENTRAÎNEMENT'}
            color={sched.isWorkDay ? colors.textSecondary : colors.signal}
            filled={!sched.isWorkDay} />
        )}
        <Tag label={WEEK_LABEL[sched.weekType]} color={colors.textDisabled} />
      </View>

      {/* Check-in du jour déjà rempli (persistant) — refaisable si besoin */}
      {!!onRedoCheckin && (
        <Pressable onPress={onRedoCheckin} style={styles.redoRow} hitSlop={6}>
          <Text style={styles.redoText}>
            ✓ Check-in du jour enregistré (forme {checkin.readiness}) · ↻ refaire
          </Text>
        </Pressable>
      )}

      {/* Charge de la semaine (boucle adaptative) — jauges visuelles */}
      {ctx && (
        <View style={styles.loadCard}>
          <View style={styles.loadHead}>
            <Text style={styles.loadLabel}>BUDGET FATIGUE HEBDO</Text>
            <Text style={[styles.loadPct, ctx.budget_consumed_pct >= 100 && { color: colors.readyOrange }]}>
              {ctx.budget_consumed_pct}%
            </Text>
          </View>
          <MeterBar value={ctx.budget_consumed_pct} max={100}
            color={ctx.budget_consumed_pct >= 100 ? colors.readyOrange
              : ctx.budget_consumed_pct >= 85 ? colors.readyYellow : colors.signal} />
          <Text style={styles.loadSub}>
            {ctx.consumed_su ?? 0} / {ctx.budget_su ?? 0} SU · {ctx.days_since_rest} j sans repos
          </Text>

          {ctx.acwr_label !== 'insufficient_history' && ctx.acwr != null && (
            <View style={{ marginTop: spacing.m }}>
              <View style={styles.loadHead}>
                <Text style={styles.loadLabel}>ACWR (zone optimale 0,8–1,3)</Text>
                <Text style={[styles.loadPct, acwrAlarm && { color: colors.readyOrange }]}>{ctx.acwr}</Text>
              </View>
              <MeterBar value={ctx.acwr} max={2} sweet={[0.8, 1.3]} marker={ctx.acwr}
                color={acwrAlarm ? colors.readyOrange : colors.signal} />
            </View>
          )}
        </View>
      )}

      {/* Conseil adaptatif du jour (selon la readiness) — n'altère pas la séance,
          il l'oriente : intensité, prudence sciatique, etc. */}
      {decision && (
        <Card style={{ flexDirection: 'row', marginTop: spacing.m }}>
          <ReadinessBar level={level} />
          <View style={styles.cardBody}>
            <Text style={styles.label}>Conseil du coach aujourd'hui</Text>
            <View style={styles.actionRow}>
              <Text style={styles.glyph}>{DISCIPLINE[decision.best_action]?.glyph ?? '▸'}</Text>
              <Text style={styles.action}>{disciplineLabel(decision.best_action)}</Text>
            </View>
            <Text style={styles.reason}>{decision.reason}</Text>
            {decision.safety_notes.length > 0 && (
              <View style={styles.safety}>
                {decision.safety_notes.map(n => (
                  <Text key={n} style={styles.safetyText}>⚠ {n}</Text>
                ))}
              </View>
            )}
          </View>
        </Card>
      )}

      {/* Séance(s) du jour — IDENTIQUE à l'Agenda et à l'onglet Séances */}
      <Text style={styles.sectionLabel}>SÉANCE(S) DU JOUR · SELON TON PLAN</Text>
      <Card style={{ padding: spacing.m }}>
        {plan ? (
          <PlannedSessions sessions={plan.sessions} dateIso={sched.date} completable
            standby={plan.standby} />
        ) : error ? (
          <Text style={styles.reason}>
            Pas de réseau et pas de plan en cache. Reconnecte-toi pour voir la
            séance du jour, ou pars sur 45' Z2 par défaut.
          </Text>
        ) : (
          <Text style={styles.loading}>Préparation de ta séance…</Text>
        )}
      </Card>
    </ScrollView>
  );
}

function LoadStat({ value, label, color }: { value: string; label: string; color: string }) {
  return (
    <View style={styles.loadStat}>
      <Text style={[styles.loadValue, { color }]}>{value}</Text>
      <Text style={styles.loadLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  countdown: { alignItems: 'center', marginVertical: spacing.l },
  loadRow: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-around',
    backgroundColor: colors.bgCard, borderRadius: spacing.cardRadius,
    paddingVertical: spacing.m, marginTop: spacing.m,
  },
  loadStat: { alignItems: 'center', flex: 1 },
  loadValue: { fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h1 },
  loadLabel: { color: colors.textSecondary, ...typography.label, fontSize: 10 },
  loadDivider: { width: 1, height: 28, backgroundColor: colors.hairline },
  loadCard: { backgroundColor: colors.bgCard, borderRadius: spacing.cardRadius, padding: spacing.m, marginTop: spacing.m },
  loadHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: spacing.s },
  loadPct: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2 },
  loadSub: { color: colors.textDisabled, fontSize: typography.sizes.small, marginTop: spacing.s },
  countdownNumber: {
    color: colors.textPrimary, fontSize: typography.sizes.countdown,
    fontFamily: typography.display.fontFamily,
  },
  countdownLabel: { color: colors.textSecondary, ...typography.label },
  todayRow: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', marginTop: spacing.m,
  },
  redoRow: { marginTop: spacing.s, alignItems: 'center' },
  redoText: { color: colors.textSecondary, fontSize: typography.sizes.small },
  cardBody: { flex: 1, padding: spacing.m },
  label: { color: colors.textSecondary, ...typography.label, marginBottom: spacing.s },
  sectionLabel: { color: colors.textSecondary, ...typography.label, marginTop: spacing.l, marginBottom: spacing.s },
  actionRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.s },
  glyph: { color: colors.signal, fontSize: 22 },
  action: {
    color: colors.textPrimary, fontSize: typography.sizes.score,
    fontFamily: typography.display.fontFamily,
  },
  sessionTitle: {
    color: colors.signal, fontFamily: typography.bodyBold.fontFamily,
    fontSize: typography.sizes.body, marginTop: spacing.xs,
  },
  meta: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: spacing.xs },
  reason: { color: colors.textPrimary, fontSize: typography.sizes.body, marginTop: spacing.m, lineHeight: 22 },
  safety: { marginTop: spacing.m, gap: spacing.xs },
  safetyText: { color: colors.readyOrange, fontSize: typography.sizes.small },
  loading: { color: colors.textDisabled, textAlign: 'center', marginTop: spacing.xl },
});
