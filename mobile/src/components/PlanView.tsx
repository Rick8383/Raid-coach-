/**
 * Plan d'entraînement détaillé (Mission 1B) — calendrier glissant.
 * Navigation semaine par semaine ; chaque jour liste ses séances (couleur par
 * type) ; on déplie une séance pour voir le détail (allures run, séries 5/3/1,
 * lignes WOD). Données du backend /plan/weekly, assemblées via les générateurs.
 */
import React, { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { AthleteProfile, WeeklyPlan, api } from '../api/client';
import { Card, Tag } from './ui';
import { PlannedSessions } from './PlannedSessions';
import { currentWeekIndex, DAY_LABELS, DayCode, WEEK_LABEL } from '../schedule';
import { colors, spacing, typography } from '../theme/tokens';

export function PlanView({ profile }: { profile: AthleteProfile | null }) {
  const base = currentWeekIndex();
  const [offset, setOffset] = useState(0);
  const [plan, setPlan] = useState<WeeklyPlan | null>(null);

  useEffect(() => {
    api.weeklyPlan(base, 6, profile?.vma_kmh, profile?.fc_max).then(setPlan).catch(() => {});
  }, [profile]); // eslint-disable-line react-hooks/exhaustive-deps

  const week = plan?.weeks[offset];

  return (
    <View>
      <View style={styles.nav}>
        <Pressable onPress={() => setOffset(o => Math.max(0, o - 1))} hitSlop={12}>
          <Text style={styles.navArrow}>‹</Text>
        </Pressable>
        <View style={{ alignItems: 'center' }}>
          <Text style={styles.navTitle}>{offset === 0 ? 'CETTE SEMAINE' : `SEMAINE +${offset}`}</Text>
          {week && <Tag label={WEEK_LABEL[week.week_type as 'big_work' | 'small_work']}
            color={week.week_type === 'big_work' ? colors.fitness : colors.signal} />}
        </View>
        <Pressable onPress={() => setOffset(o => Math.min((plan?.weeks.length ?? 1) - 1, o + 1))} hitSlop={12}>
          <Text style={styles.navArrow}>›</Text>
        </Pressable>
      </View>

      {!plan && <Text style={styles.loading}>Chargement du plan…</Text>}

      {week?.days.map(day => (
        <Card key={day.date} style={{ padding: spacing.m, marginBottom: spacing.s }}>
          <View style={styles.dayHead}>
            <Text style={styles.dayName}>
              {DAY_LABELS[day.day_of_week as DayCode]} {day.date.slice(8)}/{day.date.slice(5, 7)}
            </Text>
            <Tag label={day.is_work_day ? 'SERVICE' : 'OFF'}
              color={day.is_work_day ? colors.textSecondary : colors.signal} filled={!day.is_work_day} />
          </View>
          <PlannedSessions sessions={day.sessions} standby={day.standby} />
        </Card>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  nav: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginVertical: spacing.m },
  navArrow: { color: colors.signal, fontSize: 32, paddingHorizontal: spacing.m },
  navTitle: { color: colors.textPrimary, ...typography.label, marginBottom: spacing.xs },
  loading: { color: colors.textDisabled, textAlign: 'center', marginTop: spacing.l },
  dayHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.s },
  dayName: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2 },
});
