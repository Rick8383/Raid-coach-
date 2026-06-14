/**
 * Nutrition — macros du jour adaptées au profil et au planning 3/2/2/3.
 * Cyclage glucidique : haut les jours OFF (double séance), modéré en service.
 */
import React, { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { AthleteProfile, MacroTarget, api } from '../api/client';
import { StackBar } from '../components/Chart';
import { Card, Tag } from '../components/ui';
import { daySchedule } from '../schedule';
import { colors, spacing, typography } from '../theme/tokens';

function ageFrom(birth?: string): number {
  if (!birth) return 31;
  const b = new Date(birth);
  const diff = Date.now() - b.getTime();
  return Math.max(14, Math.floor(diff / (365.25 * 24 * 3600 * 1000)));
}

const DAY_TYPE_LABEL: Record<string, string> = {
  high_carb: 'JOUR GLUCIDES HAUT',
  medium_carb: 'JOUR GLUCIDES MODÉRÉ',
  low_carb: 'JOUR GLUCIDES BAS',
};

export function NutritionScreen({ profile }: { profile: AthleteProfile | null }) {
  const [macros, setMacros] = useState<MacroTarget | null>(null);
  const [error, setError] = useState(false);

  const sched = daySchedule(new Date());
  const activity = sched.intent?.focus === 'double' ? 'high'
    : sched.intent?.focus === 'swim' ? 'light' : 'moderate';

  useEffect(() => {
    if (!profile) return;
    api.dailyMacros({
      weight_kg: profile.weight_kg ?? 75,
      height_cm: profile.height_cm ?? 172,
      age: ageFrom(profile.birth_date),
      body_fat_pct: profile.body_fat_pct,
      target_weight_kg: profile.target_weight_kg,
      activity,
    }).then(setMacros).catch(() => setError(true));
  }, [profile, activity]);

  return (
    <ScrollView style={styles.root} contentContainerStyle={{ padding: spacing.m }}>
      <Text style={styles.h1}>NUTRITION DU JOUR</Text>
      <View style={styles.contextRow}>
        <Tag label={sched.isWorkDay ? 'JOUR DE SERVICE' : 'JOUR OFF'}
          color={sched.isWorkDay ? colors.textSecondary : colors.signal}
          filled={!sched.isWorkDay} />
        <Tag label="PHASE RECOMP" color={colors.fitness} />
      </View>

      {macros && (
        <>
          <Card style={{ padding: spacing.l, marginTop: spacing.m, alignItems: 'center' }}>
            <Text style={styles.dayType}>{DAY_TYPE_LABEL[macros.day_type] ?? macros.day_type}</Text>
            <Text style={styles.calories}>{macros.calories}</Text>
            <Text style={styles.caloriesLabel}>kcal cible</Text>
          </Card>

          {/* Répartition visuelle des macros (calories : P×4, G×4, L×9) */}
          <View style={{ marginTop: spacing.m }}>
            <StackBar segments={[
              { value: macros.protein_g * 4, color: colors.fitness },
              { value: macros.carbs_g * 4, color: colors.signal },
              { value: macros.fat_g * 9, color: colors.readyYellow },
            ]} />
            <View style={styles.legend}>
              <Text style={[styles.legendItem, { color: colors.fitness }]}>● Protéines</Text>
              <Text style={[styles.legendItem, { color: colors.signal }]}>● Glucides</Text>
              <Text style={[styles.legendItem, { color: colors.readyYellow }]}>● Lipides</Text>
            </View>
          </View>

          <View style={styles.macroGrid}>
            <MacroCard label="Protéines" value={macros.protein_g} color={colors.fitness} />
            <MacroCard label="Glucides" value={macros.carbs_g} color={colors.signal} />
            <MacroCard label="Lipides" value={macros.fat_g} color={colors.readyYellow} />
          </View>

          <Card style={{ padding: spacing.m, marginTop: spacing.s, flexDirection: 'row',
            justifyContent: 'space-between', alignItems: 'center' }}>
            <Text style={styles.waterLabel}>HYDRATATION</Text>
            <Text style={styles.water}>{macros.water_l} L</Text>
          </Card>

          {macros.notes.length > 0 && (
            <View style={styles.notes}>
              {macros.notes.map(n => <Text key={n} style={styles.note}>• {n}</Text>)}
            </View>
          )}
        </>
      )}

      {error && <Text style={styles.error}>Impossible de calculer les macros hors connexion.</Text>}
      {!profile && <Text style={styles.error}>Profil indisponible.</Text>}
    </ScrollView>
  );
}

function MacroCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <Card style={{ flex: 1, padding: spacing.m, alignItems: 'center' }}>
      <Text style={[styles.macroValue, { color }]}>{value}</Text>
      <Text style={styles.macroUnit}>g</Text>
      <Text style={styles.macroLabel}>{label}</Text>
    </Card>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  h1: { color: colors.textPrimary, fontFamily: typography.display.fontFamily,
    fontSize: typography.sizes.h1, letterSpacing: 2, marginBottom: spacing.m },
  contextRow: { flexDirection: 'row', gap: spacing.s },
  dayType: { color: colors.textSecondary, ...typography.label, marginBottom: spacing.s },
  calories: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: 52 },
  caloriesLabel: { color: colors.textSecondary, ...typography.label },
  legend: { flexDirection: 'row', justifyContent: 'space-between', marginTop: spacing.s },
  legendItem: { ...typography.label, fontSize: typography.sizes.micro },
  macroGrid: { flexDirection: 'row', gap: spacing.s, marginTop: spacing.s },
  macroValue: { fontFamily: typography.display.fontFamily, fontSize: typography.sizes.score },
  macroUnit: { color: colors.textDisabled, fontSize: typography.sizes.micro },
  macroLabel: { color: colors.textSecondary, ...typography.label, fontSize: 10, marginTop: spacing.xs },
  waterLabel: { color: colors.textSecondary, ...typography.label },
  water: { color: colors.fitness, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h1 },
  notes: { marginTop: spacing.m, gap: spacing.xs },
  note: { color: colors.textSecondary, fontSize: typography.sizes.small, lineHeight: 20 },
  error: { color: colors.textDisabled, textAlign: 'center', marginTop: spacing.xl },
});
