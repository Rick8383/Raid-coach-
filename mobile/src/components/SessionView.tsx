/** Rendu présentational d'une séance détaillée (phases + prescriptions). */
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { DetailedSession } from '../api/client';
import { ReadinessBar } from './ReadinessBar';
import { Card } from './ui';
import { colors, ReadinessLevel, spacing, typography } from '../theme/tokens';

const PHASE_LABEL: Record<string, string> = {
  warmup: 'ÉCHAUFFEMENT', main: 'CORPS DE SÉANCE',
  cooldown: 'RETOUR AU CALME', finisher: 'SÉANCE 2',
};

export function SessionView({ session, level = 'green' }:
  { session: DetailedSession; level?: ReadinessLevel }) {
  return (
    <View>
      <View style={styles.metaRow}>
        <Stat value={`${session.duration_min}'`} label="durée" />
        <View style={styles.divider} />
        <Stat value={`${session.intensity_cap}/10`} label="intensité max" />
      </View>

      {session.safety_notes.length > 0 && (
        <View style={styles.safety}>
          {session.safety_notes.map(n => <Text key={n} style={styles.safetyText}>⚠ {n}</Text>)}
        </View>
      )}
      {session.targets.length > 0 && (
        <View style={styles.targets}>
          {session.targets.map(t => <Text key={t} style={styles.targetText}>◎ {t}</Text>)}
        </View>
      )}

      {session.phases.map((phase, i) => (
        <View key={`${phase.kind}-${i}`} style={styles.phase}>
          <Text style={styles.phaseLabel}>{PHASE_LABEL[phase.kind] ?? phase.label}</Text>
          <Text style={styles.phaseSub}>{phase.label}</Text>
          <Card style={{ flexDirection: 'row' }}>
            <ReadinessBar level={phase.kind === 'finisher' ? 'yellow' : level} />
            <View style={styles.phaseBody}>
              {phase.items.map((it, j) => (
                <View key={j} style={[styles.item, j > 0 && styles.itemBorder]}>
                  <View style={styles.itemHead}>
                    <Text style={styles.itemName}>{it.name}</Text>
                    {!!it.prescription && <Text style={styles.itemRx}>{it.prescription}</Text>}
                  </View>
                  {!!it.meta && <Text style={styles.itemMeta}>{it.meta}</Text>}
                  {!!it.notes && <Text style={styles.itemNotes}>{it.notes}</Text>}
                </View>
              ))}
            </View>
          </Card>
        </View>
      ))}
    </View>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <View>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  metaRow: { flexDirection: 'row', alignItems: 'center', marginVertical: spacing.m },
  divider: { width: 1, height: 28, backgroundColor: colors.hairline, marginHorizontal: spacing.l },
  statValue: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.score },
  statLabel: { color: colors.textSecondary, ...typography.label, marginTop: 2 },
  safety: { padding: spacing.m, borderRadius: 8, backgroundColor: 'rgba(229,72,77,0.10)',
    borderLeftWidth: 3, borderLeftColor: colors.readyRed, gap: spacing.xs, marginBottom: spacing.s },
  safetyText: { color: colors.readyOrange, fontSize: typography.sizes.small, lineHeight: 19 },
  targets: { gap: spacing.xs, marginBottom: spacing.s },
  targetText: { color: colors.signal, fontSize: typography.sizes.small },
  phase: { marginTop: spacing.l },
  phaseLabel: { color: colors.textSecondary, ...typography.label },
  phaseSub: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2, marginBottom: spacing.s },
  phaseBody: { flex: 1, padding: spacing.m },
  item: { paddingVertical: spacing.s },
  itemBorder: { borderTopWidth: 1, borderTopColor: colors.hairline },
  itemHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  itemName: { color: colors.textPrimary, fontSize: typography.sizes.body, ...typography.bodyBold, flex: 1, paddingRight: spacing.s },
  itemRx: { color: colors.signal, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2 },
  itemMeta: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: 2 },
  itemNotes: { color: colors.readyYellow, fontSize: typography.sizes.small, marginTop: spacing.xs, fontStyle: 'italic' },
});
