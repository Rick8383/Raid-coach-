/**
 * Feuille de route — plan annuel rétro-planifié jusqu'à la sélection 2029.
 * Cycles Base / Build / Peak / Taper, bloc courant mis en avant, jalons benchmarks.
 */
import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { api, Roadmap as RoadmapData } from '../api/client';
import { Card, Tag } from '../components/ui';
import { colors, spacing, typography } from '../theme/tokens';

const PHASE_META: Record<string, { label: string; color: string }> = {
  base: { label: 'BASE', color: colors.fitness },
  build: { label: 'BUILD', color: colors.signal },
  peak: { label: 'PEAK', color: colors.readyYellow },
  taper: { label: 'TAPER', color: colors.readyOrange },
  transition: { label: 'TRANSITION', color: colors.textSecondary },
  selection: { label: 'SÉLECTION', color: colors.readyRed },
};

export function Roadmap({ weeksToSelection }: { weeksToSelection: number }) {
  const [plan, setPlan] = useState<RoadmapData | null>(null);

  useEffect(() => {
    api.roadmap(weeksToSelection, 0).then(setPlan).catch(() => {});
  }, [weeksToSelection]);

  if (!plan) return null;

  return (
    <View>
      <Text style={styles.section}>FEUILLE DE ROUTE → SÉLECTION 2029</Text>
      <Card style={{ padding: spacing.m, marginBottom: spacing.m }}>
        <View style={styles.head}>
          <Tag label={PHASE_META[plan.current_phase]?.label ?? plan.current_phase}
            color={PHASE_META[plan.current_phase]?.color ?? colors.signal} filled />
          <Text style={styles.phaseWeeks}>Phase actuelle</Text>
        </View>
        <Text style={styles.currentFocus}>{plan.current_focus}</Text>
      </Card>

      {/* Frise des blocs (compacte) */}
      <View style={styles.timeline}>
        {plan.blocks.map((b, i) => {
          const meta = PHASE_META[b.phase] ?? { label: b.phase, color: colors.hairlineStrong };
          const span = b.week_end - b.week_start + 1;
          return (
            <View key={i}
              style={[styles.segment, {
                flex: span,
                backgroundColor: b.is_current ? meta.color : colors.bgCard,
                borderColor: meta.color,
              }]} />
          );
        })}
      </View>
      <Text style={styles.legend}>
        {plan.weeks_total} semaines · {plan.blocks.length} blocs · cap : semaine {plan.selection_week}
      </Text>

      {/* Jalons clés */}
      <Text style={styles.section}>JALONS</Text>
      <Card style={{ padding: spacing.s }}>
        {plan.milestones.slice(0, 8).map((m, i) => (
          <View key={i} style={[styles.milestone, i > 0 && styles.mBorder]}>
            <Text style={styles.mDot}>◆</Text>
            <Text style={styles.mText}>{m}</Text>
          </View>
        ))}
      </Card>
    </View>
  );
}

const styles = StyleSheet.create({
  section: { color: colors.textSecondary, ...typography.label, marginTop: spacing.l, marginBottom: spacing.s },
  head: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  phaseWeeks: { color: colors.textDisabled, ...typography.label, fontSize: 10 },
  currentFocus: { color: colors.textPrimary, fontSize: typography.sizes.body, marginTop: spacing.s, lineHeight: 21 },
  timeline: { flexDirection: 'row', height: 14, gap: 2, borderRadius: 4, overflow: 'hidden' },
  segment: { height: 14, borderRadius: 2, borderWidth: 1 },
  legend: { color: colors.textDisabled, fontSize: typography.sizes.micro, marginTop: spacing.s, textAlign: 'center' },
  milestone: { flexDirection: 'row', alignItems: 'flex-start', paddingVertical: spacing.s, paddingHorizontal: spacing.s, gap: spacing.s },
  mBorder: { borderTopWidth: 1, borderTopColor: colors.hairline },
  mDot: { color: colors.signal, fontSize: 10, marginTop: 2 },
  mText: { color: colors.textSecondary, fontSize: typography.sizes.small, flex: 1, lineHeight: 19 },
});
