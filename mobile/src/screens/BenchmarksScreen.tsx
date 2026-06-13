/** Benchmarks Sélection : progression vers les cibles élite (top 5%). */
import React, { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { AthleteProfile, api } from '../api/client';
import { ReadinessBar } from '../components/ReadinessBar';
import { colors, spacing, typography } from '../theme/tokens';

export function BenchmarksScreen({ profile }: { profile: AthleteProfile | null }) {
  const [report, setReport] = useState<any>(null);
  useEffect(() => {
    if (!profile) return;
    api.raidStrengthReport({
      current: profile.current, bodyweight_kg: profile.weight_kg ?? 75, tier: 'elite',
    }).then(setReport).catch(() => {});
  }, [profile]);

  return (
    <ScrollView style={styles.root} contentContainerStyle={{ padding: spacing.m }}>
      <Text style={styles.h1}>OBJECTIFS SÉLECTION</Text>
      {report && (
        <>
          <View style={styles.scoreCard}>
            <Text style={styles.scoreNumber}>{report.global_readiness_pct}%</Text>
            <Text style={styles.scoreLabel}>readiness élite (top 5%)</Text>
          </View>
          {report.targets.map((t: any) => {
            const pct = Math.min(100, (t.current / t.target) * 100);
            const level = pct >= 90 ? 'green' : pct >= 65 ? 'yellow'
              : pct >= 40 ? 'orange' : 'red';
            return (
              <View key={t.name} style={styles.card}>
                <ReadinessBar level={level} />
                <View style={styles.cardBody}>
                  <Text style={styles.targetName}>{t.name}</Text>
                  <Text style={styles.targetValue}>
                    {t.current} <Text style={styles.targetGoal}>/ {t.target} {t.unit === 'reps' ? '' : t.unit}</Text>
                  </Text>
                  <View style={styles.track}>
                    <View style={[styles.fill, { width: `${pct}%` }]} />
                  </View>
                </View>
              </View>
            );
          })}
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  h1: { color: colors.textPrimary, fontFamily: typography.display.fontFamily,
    fontSize: typography.sizes.h1, letterSpacing: 2, marginVertical: spacing.m },
  scoreCard: { alignItems: 'center', marginBottom: spacing.l },
  scoreNumber: { color: colors.signal, fontSize: 56,
    fontFamily: typography.display.fontFamily },
  scoreLabel: { color: colors.textSecondary, ...typography.label },
  card: { flexDirection: 'row', backgroundColor: colors.bgCard,
    borderRadius: spacing.cardRadius, overflow: 'hidden', marginBottom: spacing.s },
  cardBody: { flex: 1, padding: spacing.m },
  targetName: { color: colors.textSecondary, fontSize: typography.sizes.small },
  targetValue: { color: colors.textPrimary, fontFamily: typography.display.fontFamily,
    fontSize: typography.sizes.h1, marginVertical: spacing.xs },
  targetGoal: { color: colors.textDisabled, fontSize: typography.sizes.body },
  track: { height: 4, backgroundColor: colors.hairline, borderRadius: 2 },
  fill: { height: 4, backgroundColor: colors.signal, borderRadius: 2 },
});
