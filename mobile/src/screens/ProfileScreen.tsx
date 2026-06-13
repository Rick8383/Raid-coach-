/**
 * Profil athlète — données réelles chargées depuis l'API, poids ajustable.
 * Affiche l'objectif, les mensurations, la contrainte sciatique et les maxes.
 */
import React, { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { AthleteProfile, api } from '../api/client';
import { Card } from '../components/ui';
import { Roadmap } from '../components/Roadmap';
import { colors, spacing, typography } from '../theme/tokens';

function weeksToGoal(goalDate?: string): number {
  const target = new Date(goalDate ?? '2029-03-01').getTime();
  const weeks = Math.round((target - Date.now()) / (7 * 24 * 3600 * 1000));
  return Math.max(8, Math.min(weeks, 220));
}

const MAX_LABELS: Record<string, string> = {
  pullups_max: 'Tractions', pushups_max: 'Pompes', dips_max: 'Dips',
  leg_raises_max: 'Toes to bar', rope_climb_5m: 'Corde 5 m',
  cooper_m: 'Cooper (m)', bench_ratio: 'Dév. couché (kg)', squat_ratio: 'Squat (kg)',
};

export function ProfileScreen({ profile, onProfile }: {
  profile: AthleteProfile | null;
  onProfile: (p: AthleteProfile) => void;
}) {
  const [saving, setSaving] = useState(false);

  if (!profile) {
    return <View style={styles.root}><Text style={styles.empty}>Profil indisponible.</Text></View>;
  }

  const adjustWeight = async (delta: number) => {
    const next = Math.round(((profile.weight_kg ?? 75) + delta) * 10) / 10;
    setSaving(true);
    try {
      const updated = await api.updateProfile({ weight_kg: next });
      onProfile(updated);
    } catch {
      /* hors connexion : on ignore, la valeur reste celle du cache */
    } finally {
      setSaving(false);
    }
  };

  const maxes = Object.entries(profile.current ?? {});

  return (
    <ScrollView style={styles.root} contentContainerStyle={{ padding: spacing.m }}>
      <Text style={styles.name}>{profile.name ?? 'Athlète RAID'}</Text>
      <Text style={styles.goal}>{profile.main_goal ?? 'Sélection RAID'}</Text>

      {/* Poids ajustable */}
      <Card style={{ padding: spacing.l, marginTop: spacing.m, alignItems: 'center' }}>
        <Text style={styles.fieldLabel}>POIDS ACTUEL</Text>
        <View style={styles.weightRow}>
          <Stepper label="–" onPress={() => adjustWeight(-0.5)} disabled={saving} />
          <Text style={styles.weight}>{(profile.weight_kg ?? 75).toFixed(1)}<Text style={styles.unit}> kg</Text></Text>
          <Stepper label="+" onPress={() => adjustWeight(0.5)} disabled={saving} />
        </View>
        <Text style={styles.target}>Objectif : {profile.target_weight_kg ?? 79} kg sec</Text>
      </Card>

      {/* Mensurations */}
      <View style={styles.statsRow}>
        <Stat value={`${profile.height_cm ?? '—'}`} label="taille (cm)" />
        <Stat value={`${profile.body_fat_pct ?? '—'}`} label="% gras" />
        <Stat value={`${profile.fc_max ?? '—'}`} label="FC max" />
        <Stat value={`${profile.vma_kmh ?? '—'}`} label="VMA" />
      </View>

      {/* Contrainte */}
      {profile.injuries?.map(inj => (
        <View key={inj.zone} style={styles.injury}>
          <Text style={styles.injuryText}>⚠ {inj.type} {inj.zone}{inj.note ? ` — ${inj.note}` : ''}</Text>
        </View>
      ))}

      {/* Maxes actuels */}
      <Text style={styles.section}>MAXES ACTUELS</Text>
      <Card style={{ padding: spacing.s }}>
        {maxes.map(([k, v], i) => (
          <View key={k} style={[styles.maxRow, i > 0 && styles.maxBorder]}>
            <Text style={styles.maxLabel}>{MAX_LABELS[k] ?? k}</Text>
            <Text style={styles.maxValue}>{v}</Text>
          </View>
        ))}
      </Card>
      <Text style={styles.hint}>
        Les maxes se mettent à jour via les re-tests benchmarks (toutes les 8-12 sem.).
      </Text>

      {/* Feuille de route → 2029 */}
      <Roadmap weeksToSelection={weeksToGoal(profile.goal_date)} />
    </ScrollView>
  );
}

function Stepper({ label, onPress, disabled }: { label: string; onPress: () => void; disabled?: boolean }) {
  return (
    <Pressable onPress={onPress} disabled={disabled}
      style={({ pressed }) => [styles.stepper, pressed && { opacity: 0.6 }]}>
      <Text style={styles.stepperText}>{label}</Text>
    </Pressable>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  empty: { color: colors.textDisabled, textAlign: 'center', marginTop: spacing.xl },
  name: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h1, letterSpacing: 1 },
  goal: { color: colors.signal, ...typography.label, marginTop: spacing.xs },
  fieldLabel: { color: colors.textSecondary, ...typography.label },
  weightRow: { flexDirection: 'row', alignItems: 'center', marginVertical: spacing.m, gap: spacing.l },
  weight: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: 48 },
  unit: { color: colors.textSecondary, fontSize: typography.sizes.h2 },
  target: { color: colors.textSecondary, fontSize: typography.sizes.small },
  stepper: {
    width: 48, height: 48, borderRadius: 24, backgroundColor: colors.bgElevated,
    borderWidth: 1, borderColor: colors.hairlineStrong, alignItems: 'center', justifyContent: 'center',
  },
  stepperText: { color: colors.signal, fontSize: 26, fontFamily: typography.display.fontFamily },
  statsRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: spacing.l },
  stat: { alignItems: 'center', flex: 1 },
  statValue: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h1 },
  statLabel: { color: colors.textDisabled, ...typography.label, fontSize: 9, marginTop: 2 },
  injury: {
    marginTop: spacing.l, padding: spacing.m, borderRadius: 8,
    backgroundColor: 'rgba(229,72,77,0.10)', borderLeftWidth: 3, borderLeftColor: colors.readyRed,
  },
  injuryText: { color: colors.readyOrange, fontSize: typography.sizes.small, lineHeight: 19 },
  section: { color: colors.textSecondary, ...typography.label, marginTop: spacing.l, marginBottom: spacing.s },
  maxRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: spacing.s, paddingHorizontal: spacing.s },
  maxBorder: { borderTopWidth: 1, borderTopColor: colors.hairline },
  maxLabel: { color: colors.textSecondary, fontSize: typography.sizes.body },
  maxValue: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2 },
  hint: { color: colors.textDisabled, fontSize: typography.sizes.micro, marginTop: spacing.s, lineHeight: 16 },
});
