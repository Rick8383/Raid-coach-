/**
 * Écran d'accueil — "Aujourd'hui".
 * Une seule question : quelle est la meilleure action aujourd'hui ?
 * Cap permanent (compte à rebours sélection) + planning 3/2/2/3 synchronisé
 * sur le calendrier réel + résumé de la séance, qui s'ouvre en détail.
 */
import React, { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { api, SessionToday } from '../api/client';
import { ReadinessBar } from '../components/ReadinessBar';
import { WeekStrip } from '../components/WeekStrip';
import { Card, PrimaryButton, Tag } from '../components/ui';
import { daySchedule, WEEK_LABEL } from '../schedule';
import {
  colors, disciplineLabel, DISCIPLINE, readinessLevelFor, spacing, typography,
} from '../theme/tokens';

const SELECTION_DATE = new Date('2029-03-01'); // sélection 2029 (cf. PROJECT_MASTER)

function weeksToSelection(): number {
  return Math.max(0, Math.round(
    (SELECTION_DATE.getTime() - Date.now()) / (7 * 24 * 3600 * 1000)));
}

type Checkin = { readiness: number; fatigue: number; sleep: number; sciatic: boolean };

export function TodayScreen({ checkin, onOpenSession }: {
  checkin: Checkin;
  onOpenSession: (s: SessionToday, dateIso: string) => void;
}) {
  const [data, setData] = useState<SessionToday | null>(null);
  const [error, setError] = useState<string | null>(null);

  const today = new Date();
  const sched = daySchedule(today);

  useEffect(() => {
    api.sessionToday({
      date: sched.date,
      readiness: checkin.readiness,
      fatigue: checkin.fatigue,
      sleep_quality: checkin.sleep,
      sciatic_flare: checkin.sciatic,
      weeks_to_main_goal: weeksToSelection(),
    }).then(setData).catch(e => setError(String(e)));
  }, [checkin]); // eslint-disable-line react-hooks/exhaustive-deps

  const level = readinessLevelFor(checkin.readiness, checkin.sciatic);
  const decision = data?.decision;
  const session = data?.session;

  return (
    <ScrollView style={styles.root} contentContainerStyle={{ padding: spacing.m }}>
      {/* Cap — compte à rebours sélection */}
      <View style={styles.countdown}>
        <Text style={styles.countdownNumber}>{weeksToSelection()}</Text>
        <Text style={styles.countdownLabel}>semaines avant la sélection</Text>
      </View>

      {/* Planning 3/2/2/3 synchronisé */}
      <WeekStrip today={today} />

      {/* Statut du jour */}
      <View style={styles.todayRow}>
        <Tag label={sched.isWorkDay ? 'JOUR DE SERVICE' : 'JOUR OFF · ENTRAÎNEMENT'}
          color={sched.isWorkDay ? colors.textSecondary : colors.signal}
          filled={!sched.isWorkDay} />
        <Tag label={WEEK_LABEL[sched.weekType]} color={colors.textDisabled} />
      </View>

      {/* Best Action Today */}
      {session && decision && (
        <Card style={{ flexDirection: 'row', marginTop: spacing.m }}>
          <ReadinessBar level={level} />
          <View style={styles.cardBody}>
            <Text style={styles.label}>Meilleure action aujourd'hui</Text>
            <View style={styles.actionRow}>
              <Text style={styles.glyph}>{DISCIPLINE[decision.best_action]?.glyph ?? '▸'}</Text>
              <Text style={styles.action}>
                {disciplineLabel(decision.best_action)}
                {decision.secondary_action
                  ? ` + ${disciplineLabel(decision.secondary_action)}` : ''}
              </Text>
            </View>
            <Text style={styles.sessionTitle}>{session.title}</Text>
            <Text style={styles.meta}>
              {session.duration_min} min · intensité max {session.intensity_cap}/10
            </Text>
            <Text style={styles.reason}>{decision.reason}</Text>

            {decision.safety_notes.length > 0 && (
              <View style={styles.safety}>
                {decision.safety_notes.map(n => (
                  <Text key={n} style={styles.safetyText}>⚠ {n}</Text>
                ))}
              </View>
            )}

            <View style={{ marginTop: spacing.l }}>
              <PrimaryButton label="VOIR LA SÉANCE DÉTAILLÉE"
                onPress={() => onOpenSession(data!, sched.date)} />
            </View>
          </View>
        </Card>
      )}

      {!data && !error && (
        <Text style={styles.loading}>Préparation de ta séance…</Text>
      )}

      {error && (
        <Card style={{ flexDirection: 'row', marginTop: spacing.m }}>
          <ReadinessBar level="orange" />
          <View style={styles.cardBody}>
            <Text style={styles.label}>Hors connexion</Text>
            <Text style={styles.reason}>
              Pas de réseau et pas de séance en cache. Reconnecte-toi pour obtenir
              la séance du jour, ou pars sur 45' Z2 par défaut.
            </Text>
          </View>
        </Card>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  countdown: { alignItems: 'center', marginVertical: spacing.l },
  countdownNumber: {
    color: colors.textPrimary, fontSize: typography.sizes.countdown,
    fontFamily: typography.display.fontFamily,
  },
  countdownLabel: { color: colors.textSecondary, ...typography.label },
  todayRow: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', marginTop: spacing.m,
  },
  cardBody: { flex: 1, padding: spacing.m },
  label: { color: colors.textSecondary, ...typography.label, marginBottom: spacing.s },
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
