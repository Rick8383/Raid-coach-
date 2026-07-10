/**
 * Plan d'entraînement détaillé (Mission 1B) — calendrier glissant.
 * Navigation semaine par semaine, Y COMPRIS vers les semaines PASSÉES
 * (jusqu'au début du plan) ; chaque jour liste ses séances (couleur par type) ;
 * on déplie une séance pour voir le détail (allures run, séries 5/3/1, lignes
 * WOD). Les jours passés et aujourd'hui sont « marquables faits » →
 * enregistrement RÉTROACTIF possible (séance faite mais oubliée sur le moment).
 * Données du backend /plan/weekly (1 semaine par requête, mise en cache).
 */
import React, { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { AthleteProfile, WeeklyPlan, api } from '../api/client';
import { Card, Tag } from './ui';
import { PlannedSessions } from './PlannedSessions';
import { currentWeekIndex, DAY_LABELS, DayCode, localISODate, WEEK_LABEL } from '../schedule';
import { colors, spacing, typography } from '../theme/tokens';

const MAX_AHEAD = 12;   // semaines visibles vers l'avant

export function PlanView({ profile }: { profile: AthleteProfile | null }) {
  const base = currentWeekIndex();
  const minOffset = -base;                       // semaine 0 = début du plan
  const [offset, setOffset] = useState(0);       // négatif = semaines passées
  const [plan, setPlan] = useState<WeeklyPlan | null>(null);
  const today = localISODate();

  useEffect(() => {
    setPlan(null);
    api.weeklyPlan(base + offset, 1, profile?.vma_kmh, profile?.fc_max)
      .then(setPlan).catch(() => {});
  }, [profile, offset]); // eslint-disable-line react-hooks/exhaustive-deps

  const week = plan?.weeks[0];
  const monday = week?.days[0]?.date;
  const title = offset === 0 ? 'CETTE SEMAINE'
    : monday ? `SEMAINE DU ${monday.slice(8)}/${monday.slice(5, 7)}`
    : offset > 0 ? `SEMAINE +${offset}` : `SEMAINE ${offset}`;

  return (
    <View>
      <View style={styles.nav}>
        <Pressable onPress={() => setOffset(o => Math.max(minOffset, o - 1))} hitSlop={12}
          disabled={offset <= minOffset}>
          <Text style={[styles.navArrow, offset <= minOffset && styles.navOff]}>‹</Text>
        </Pressable>
        <View style={{ alignItems: 'center' }}>
          <Text style={styles.navTitle}>{title}</Text>
          <View style={styles.tagRow}>
            {offset < 0 && <Tag label="PASSÉ" color={colors.textSecondary} />}
            {week && <Tag label={WEEK_LABEL[week.week_type as 'big_work' | 'small_work']}
              color={week.week_type === 'big_work' ? colors.fitness : colors.signal} />}
          </View>
        </View>
        <Pressable onPress={() => setOffset(o => Math.min(MAX_AHEAD, o + 1))} hitSlop={12}
          disabled={offset >= MAX_AHEAD}>
          <Text style={[styles.navArrow, offset >= MAX_AHEAD && styles.navOff]}>›</Text>
        </Pressable>
      </View>
      {offset !== 0 && (
        <Pressable onPress={() => setOffset(0)} style={styles.todayLink} hitSlop={6}>
          <Text style={styles.todayLinkT}>↩ Revenir à cette semaine</Text>
        </Pressable>
      )}

      {!plan && <Text style={styles.loading}>Chargement du plan…</Text>}

      {week?.days.map(day => (
        <Card key={day.date} style={{ padding: spacing.m, marginBottom: spacing.s }}>
          <View style={styles.dayHead}>
            <Text style={[styles.dayName, day.date === today && { color: colors.signal }]}>
              {DAY_LABELS[day.day_of_week as DayCode]} {day.date.slice(8)}/{day.date.slice(5, 7)}
            </Text>
            <Tag label={day.is_work_day ? 'SERVICE' : 'OFF'}
              color={day.is_work_day ? colors.textSecondary : colors.signal} filled={!day.is_work_day} />
          </View>
          {/* Jours passés + aujourd'hui : marquables faits (rétroactif OK —
              séance faite mais oubliée sur le moment). Jours futurs : lecture. */}
          <PlannedSessions sessions={day.sessions} standby={day.standby}
            dateIso={day.date} completable={day.date <= today} />
        </Card>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  nav: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginVertical: spacing.m },
  navArrow: { color: colors.signal, fontSize: 32, paddingHorizontal: spacing.m },
  navOff: { color: colors.hairlineStrong },
  navTitle: { color: colors.textPrimary, ...typography.label, marginBottom: spacing.xs },
  tagRow: { flexDirection: 'row', gap: spacing.xs },
  todayLink: { alignItems: 'center', marginBottom: spacing.s },
  todayLinkT: { color: colors.textSecondary, fontSize: typography.sizes.small, textDecorationLine: 'underline' },
  loading: { color: colors.textDisabled, textAlign: 'center', marginTop: spacing.l },
  dayHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.s },
  dayName: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2 },
});
