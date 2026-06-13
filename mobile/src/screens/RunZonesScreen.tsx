/**
 * Course — zones de fréquence cardiaque + table d'allures.
 * Les deux sont alignées par zone (Z1→Z5). Sélecteur terrain et gilet lesté :
 * l'allure cible s'adapte (le moteur tient compte du D+ et de la charge portée).
 */
import React, { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { AthleteProfile, HRProfile, PaceTable, api } from '../api/client';
import { Card } from '../components/ui';
import { colors, spacing, typography } from '../theme/tokens';

const ZONE_META: Record<string, { label: string; color: string }> = {
  z1_recovery: { label: 'Z1 · Récup', color: colors.fitness },
  z2_endurance: { label: 'Z2 · Endurance', color: colors.signal },
  z3_tempo: { label: 'Z3 · Tempo', color: colors.readyYellow },
  z4_threshold: { label: 'Z4 · Seuil', color: colors.readyOrange },
  z5_vo2max: { label: 'Z5 · VO2max', color: colors.readyRed },
};

const TERRAINS = [
  { key: 'road', label: 'ROUTE' },
  { key: 'trail', label: 'TRAIL' },
  { key: 'hilly', label: 'VALLONNÉ' },
  { key: 'mountain', label: 'MONTAGNE' },
];

function ageFrom(birth?: string): number {
  if (!birth) return 31;
  return Math.max(14, Math.floor((Date.now() - new Date(birth).getTime()) / (365.25 * 24 * 3600 * 1000)));
}

export function RunZonesView({ profile }: { profile: AthleteProfile | null }) {
  const [hr, setHr] = useState<HRProfile | null>(null);
  const [paces, setPaces] = useState<PaceTable | null>(null);
  const [terrain, setTerrain] = useState('trail');
  const [loaded, setLoaded] = useState(false); // gilet 10 kg

  const vma = profile?.vma_kmh ?? 13.6;

  useEffect(() => {
    if (!profile) return;
    api.hrProfile({ age: ageFrom(profile.birth_date), fc_max: profile.fc_max })
      .then(setHr).catch(() => {});
  }, [profile]);

  useEffect(() => {
    api.paceTable({
      vma_kmh: vma, terrain,
      elevation_gain_m_per_km: terrain === 'mountain' ? 60 : terrain === 'hilly' ? 30 : terrain === 'trail' ? 15 : 0,
      load_kg: loaded ? 10 : 0,
    }).then(setPaces).catch(() => {});
  }, [vma, terrain, loaded]);

  const paceByZone = (z: string) => paces?.targets.find(t => t.zone === z);

  return (
    <View>
      <Text style={styles.h1}>ZONES FC & ALLURES</Text>
      <Text style={styles.sub}>
        VMA {vma} km/h · FC max {hr?.fc_max ?? profile?.fc_max ?? '—'} bpm
        {hr ? ` · méthode ${hr.method}` : ''}
      </Text>

      {/* Sélecteur terrain */}
      <View style={styles.selector}>
        {TERRAINS.map(t => (
          <Pressable key={t.key} onPress={() => setTerrain(t.key)}
            style={[styles.chip, terrain === t.key && styles.chipActive]}>
            <Text style={[styles.chipText, terrain === t.key && styles.chipTextActive]}>{t.label}</Text>
          </Pressable>
        ))}
      </View>

      {/* Gilet lesté */}
      <Pressable onPress={() => setLoaded(v => !v)}
        style={[styles.loadToggle, loaded && styles.loadToggleOn]}>
        <Text style={[styles.loadText, loaded && { color: colors.bg }]}>
          {loaded ? '✓ ' : ''}GILET LESTÉ 10 KG
        </Text>
      </Pressable>

      {/* Tableau zones */}
      {hr?.zones.map(z => {
        const meta = ZONE_META[z.zone] ?? { label: z.zone, color: colors.textSecondary };
        const pace = paceByZone(z.zone);
        return (
          <Card key={z.zone} style={{ flexDirection: 'row', marginBottom: spacing.s }}>
            <View style={[styles.zoneBar, { backgroundColor: meta.color }]} />
            <View style={styles.zoneBody}>
              <View style={styles.zoneHead}>
                <Text style={[styles.zoneLabel, { color: meta.color }]}>{meta.label}</Text>
                <Text style={styles.bpm}>{z.min_bpm}–{z.max_bpm} bpm</Text>
              </View>
              <Text style={styles.desc}>{z.description}</Text>
              {pace && (
                <View style={styles.paceRow}>
                  <Text style={styles.paceLabel}>ALLURE</Text>
                  <Text style={styles.pace}>{pace.pace_fast} — {pace.pace_slow}</Text>
                </View>
              )}
            </View>
          </Card>
        );
      })}

      {!hr && <Text style={styles.empty}>Chargement des zones…</Text>}
      <Text style={styles.hint}>
        Allures ajustées au terrain (D+) et à la charge portée. Re-teste ta VMA
        en semaine 1 de chaque bloc pour les recalibrer.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  h1: { color: colors.textPrimary, fontFamily: typography.display.fontFamily,
    fontSize: typography.sizes.h1, letterSpacing: 2 },
  sub: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: spacing.xs, marginBottom: spacing.m },
  selector: { flexDirection: 'row', gap: spacing.xs, marginBottom: spacing.s },
  chip: { flex: 1, paddingVertical: spacing.s, borderRadius: 6, backgroundColor: colors.bgCard, alignItems: 'center' },
  chipActive: { backgroundColor: colors.signalSoft, borderWidth: 1, borderColor: colors.signal },
  chipText: { color: colors.textSecondary, ...typography.label, fontSize: 9 },
  chipTextActive: { color: colors.signal },
  loadToggle: { paddingVertical: spacing.s, borderRadius: 6, alignItems: 'center',
    borderWidth: 1, borderColor: colors.hairlineStrong, marginBottom: spacing.m },
  loadToggleOn: { backgroundColor: colors.signal, borderColor: colors.signal },
  loadText: { color: colors.textSecondary, ...typography.label, fontSize: 10 },
  zoneBar: { width: spacing.readinessBar },
  zoneBody: { flex: 1, padding: spacing.m },
  zoneHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  zoneLabel: { fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2 },
  bpm: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2 },
  desc: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: spacing.xs },
  paceRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    marginTop: spacing.s, paddingTop: spacing.s, borderTopWidth: 1, borderTopColor: colors.hairline },
  paceLabel: { color: colors.textDisabled, ...typography.label, fontSize: 9 },
  pace: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.body },
  empty: { color: colors.textDisabled, textAlign: 'center', marginTop: spacing.xl },
  hint: { color: colors.textDisabled, fontSize: typography.sizes.micro, marginTop: spacing.m, lineHeight: 16 },
});
