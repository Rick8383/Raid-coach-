/**
 * Écran d'accueil — "Aujourd'hui".
 * Une seule question, une seule réponse : quelle est la meilleure action aujourd'hui ?
 * Le compte à rebours sélection est permanent en haut — c'est le cap.
 */
import React, { useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { api, DailyDecision } from '../api/client';
import { ReadinessBar } from '../components/ReadinessBar';
import { colors, spacing, typography } from '../theme/tokens';

const SELECTION_DATE = new Date('2029-03-01'); // ajustable dans Réglages

function weeksToSelection(): number {
  return Math.max(0, Math.round(
    (SELECTION_DATE.getTime() - Date.now()) / (7 * 24 * 3600 * 1000)));
}

const ACTION_LABELS: Record<string, string> = {
  run: 'COURSE', crossfit: 'CROSSFIT', strength: 'FORCE',
  swim: 'NATATION', recovery: 'RÉCUPÉRATION', rest: 'REPOS',
};

export function TodayScreen({ checkin }: { checkin: { readiness: number; fatigue: number; sleep: number; sciatic: boolean } }) {
  const [decision, setDecision] = useState<DailyDecision | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const today = new Date();
    const days = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];
    api.dailyDecision({
      day_of_week: days[today.getDay()],
      is_work_day: false, // TODO: dérivé du planning 3/2/2/3 stocké
      week_type: 'small_work',
      readiness: checkin.readiness,
      fatigue: checkin.fatigue,
      sleep_quality: checkin.sleep,
      sciatic_flare: checkin.sciatic,
      weeks_to_main_goal: weeksToSelection(),
    }).then(setDecision).catch(e => setError(String(e)));
  }, [checkin]);

  const readinessLevel =
    checkin.sciatic ? 'red'
    : checkin.readiness >= 70 ? 'green'
    : checkin.readiness >= 50 ? 'yellow'
    : checkin.readiness >= 30 ? 'orange' : 'red';

  return (
    <ScrollView style={styles.root} contentContainerStyle={{ padding: spacing.m }}>
      {/* Cap — compte à rebours sélection */}
      <View style={styles.countdown}>
        <Text style={styles.countdownNumber}>{weeksToSelection()}</Text>
        <Text style={styles.countdownLabel}>semaines avant la sélection</Text>
      </View>

      {/* Best Action Today */}
      {decision && (
        <View style={styles.card}>
          <ReadinessBar level={readinessLevel} />
          <View style={styles.cardBody}>
            <Text style={styles.label}>Meilleure action aujourd'hui</Text>
            <Text style={styles.action}>
              {ACTION_LABELS[decision.best_action] ?? decision.best_action}
              {decision.secondary_action
                ? ` + ${ACTION_LABELS[decision.secondary_action]}` : ''}
            </Text>
            <Text style={styles.meta}>
              {decision.duration_min} min · intensité max {decision.intensity_cap}/10
            </Text>
            <Text style={styles.reason}>{decision.reason}</Text>
            {decision.safety_notes.length > 0 && (
              <View style={styles.safety}>
                {decision.safety_notes.map((n: string) => (
                  <Text key={n} style={styles.safetyText}>⚠ {n}</Text>
                ))}
              </View>
            )}
            <Pressable style={styles.go} accessibilityRole="button">
              <Text style={styles.goText}>LANCER LA SÉANCE</Text>
            </Pressable>
            <Text style={styles.alt}>
              Alternatives : {decision.alternatives.join(' · ')}
            </Text>
          </View>
        </View>
      )}

      {error && (
        <View style={styles.card}>
          <ReadinessBar level="orange" />
          <View style={styles.cardBody}>
            <Text style={styles.label}>Hors connexion</Text>
            <Text style={styles.reason}>
              Pas de réseau et pas de décision en cache. Reconnecte-toi pour
              obtenir la décision du jour, ou pars sur 45' Z2 par défaut.
            </Text>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  countdown: { alignItems: 'center', marginVertical: spacing.l },
  countdownNumber: {
    color: colors.textPrimary,
    fontSize: typography.sizes.countdown,
    fontFamily: typography.display.fontFamily,
  },
  countdownLabel: {
    color: colors.textSecondary,
    ...typography.label,
  },
  card: {
    flexDirection: 'row',
    backgroundColor: colors.bgCard,
    borderRadius: spacing.cardRadius,
    overflow: 'hidden',
    marginBottom: spacing.m,
  },
  cardBody: { flex: 1, padding: spacing.m },
  label: { color: colors.textSecondary, ...typography.label, marginBottom: spacing.s },
  action: {
    color: colors.textPrimary,
    fontSize: typography.sizes.score,
    fontFamily: typography.display.fontFamily,
  },
  meta: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: spacing.xs },
  reason: { color: colors.textPrimary, fontSize: typography.sizes.body, marginTop: spacing.m, lineHeight: 22 },
  safety: { marginTop: spacing.m, gap: spacing.xs },
  safetyText: { color: colors.readyOrange, fontSize: typography.sizes.small },
  go: {
    backgroundColor: colors.signal,
    borderRadius: spacing.cardRadius,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: spacing.l,
  },
  goText: {
    color: colors.bg,
    fontFamily: typography.display.fontFamily,
    fontSize: typography.sizes.h2,
    letterSpacing: 1,
  },
  alt: { color: colors.textDisabled, fontSize: typography.sizes.small, marginTop: spacing.m },
});
