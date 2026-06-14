/**
 * Plan d'entraînement détaillé (Mission 1B) — calendrier glissant.
 * Navigation semaine par semaine ; chaque jour liste ses séances (couleur par
 * type) ; on déplie une séance pour voir le détail (allures run, séries 5/3/1,
 * lignes WOD). Données du backend /plan/weekly, assemblées via les générateurs.
 */
import React, { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { AthleteProfile, PlanSession, WeeklyPlan, api } from '../api/client';
import { Card, Tag } from './ui';
import { RunDetail, StrengthDetail, WodDetail } from './SessionDetail';
import { currentWeekIndex, DAY_LABELS, DayCode, WEEK_LABEL } from '../schedule';
import { colors, spacing, typography } from '../theme/tokens';

const TYPE_COLOR: Record<string, string> = {
  run: colors.fitness, strength: colors.readyRed, crossfit: colors.readyOrange,
  swim: colors.signal, recovery: colors.signal, rest: colors.textDisabled,
};
const TYPE_LABEL: Record<string, string> = {
  run: 'COURSE', strength: 'FORCE', crossfit: 'WOD', swim: 'NATATION',
  recovery: 'RÉCUP', rest: 'REPOS',
};

function SessionExpanded({ s }: { s: PlanSession }) {
  const d = s.detail || {};
  if (s.type === 'run' && Array.isArray(d.body)) return <RunDetail session={d} />;
  if (s.type === 'strength' && d.main_lift) return <StrengthDetail session={d} />;
  if (s.type === 'crossfit' && Array.isArray(d.description)) return <WodDetail wod={d} />;
  if (s.type === 'swim' && Array.isArray(d.blocks)) {
    return <View>{d.blocks.map((b: string, i: number) => (
      <Text key={i} style={styles.detailLine}>• {b}</Text>))}</View>;
  }
  return null;
}

export function PlanView({ profile }: { profile: AthleteProfile | null }) {
  const base = currentWeekIndex();
  const [offset, setOffset] = useState(0);
  const [plan, setPlan] = useState<WeeklyPlan | null>(null);
  const [open, setOpen] = useState<string | null>(null);

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
          {day.sessions.map((s, i) => {
            const id = `${day.date}-${i}`;
            const opened = open === id;
            return (
              <View key={id}>
                <Pressable onPress={() => setOpen(opened ? null : id)} style={styles.sessRow}>
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
                  </View>
                )}
              </View>
            );
          })}
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
  sessRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.s, borderTopWidth: 1, borderTopColor: colors.hairline, gap: spacing.s },
  dot: { width: 8, height: 8, borderRadius: 4 },
  sessTitle: { color: colors.textPrimary, fontSize: typography.sizes.body },
  sessMeta: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: 2 },
  chevron: { color: colors.signal, fontSize: 20, width: 20, textAlign: 'center' },
  detail: { paddingLeft: spacing.l, paddingBottom: spacing.s, gap: 2 },
  detailLine: { color: colors.textSecondary, fontSize: typography.sizes.small, lineHeight: 19 },
});
