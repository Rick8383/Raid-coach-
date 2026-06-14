/**
 * Générateur Run (Mission 2) — 7 types, séance unique jamais répétée à chaque clic.
 * Affiche les allures (km/h + min/km + %VMA) et la FC (bpm + %FCmax) de chaque
 * fraction. Sauvegarde dans l'agenda.
 */
import React, { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { AthleteProfile, RunInterval, RunSession, api } from '../api/client';
import { Card, PrimaryButton, Tag } from './ui';
import { colors, spacing, typography } from '../theme/tokens';

const TYPES: { key: string; label: string }[] = [
  { key: 'vma_courte', label: 'VMA COURTE' },
  { key: 'vma_longue', label: 'VMA LONGUE' },
  { key: 'seuil', label: 'SEUIL' },
  { key: 'fartlek', label: 'FARTLEK' },
  { key: 'tempo', label: 'TEMPO' },
  { key: 'z2', label: 'Z2' },
  { key: 'cotes', label: 'CÔTES' },
];

function Stars({ n }: { n: number }) {
  return <Text style={styles.stars}>{'◆'.repeat(n)}{'◇'.repeat(5 - n)}</Text>;
}

function IntervalRow({ it }: { it: RunInterval }) {
  const paceParts = [
    it.pace_kmh ? `${it.pace_kmh} km/h` : null,
    it.pace_min_km ? `${it.pace_min_km}/km` : null,
    it.pct_vma ? `${it.pct_vma}% VMA` : null,
  ].filter(Boolean).join(' · ');
  const fc = it.fc_bpm ? `FC ${it.fc_bpm} bpm${it.pct_fcmax ? ` (${it.pct_fcmax}%)` : ''}` : '';
  const rec = it.recovery_sec ? `récup ${it.recovery_sec}s ${it.recovery_type ?? ''}`
    : it.recovery_min ? `récup ${it.recovery_min} min ${it.recovery_type ?? ''}` : '';
  return (
    <View style={styles.interval}>
      <Text style={styles.intLabel}>{it.label}</Text>
      {!!paceParts && <Text style={styles.intPace}>{paceParts}</Text>}
      {!!it.structure && <Text style={styles.intMeta}>{it.structure}</Text>}
      <Text style={styles.intMeta}>
        {[fc, rec, it.note, it.fc_attendue_fin, it.detail].filter(Boolean).join(' · ')}
      </Text>
    </View>
  );
}

export function RunGenerator({ profile }: { profile: AthleteProfile | null }) {
  const [type, setType] = useState('vma_courte');
  const [seeds, setSeeds] = useState<Record<string, number>>({});
  const [session, setSession] = useState<RunSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [saved, setSaved] = useState(false);

  const generate = async (t: string) => {
    const next = (seeds[t] ?? 0) + 1;
    setSeeds(s => ({ ...s, [t]: next }));
    setType(t); setLoading(true); setError(false); setSaved(false);
    try {
      const s = await api.generateRun(t, next, profile?.vma_kmh, profile?.fc_max);
      setSession(s);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const save = async () => {
    if (!session) return;
    await api.saveSession({
      discipline: 'run', session_date: new Date().toISOString().slice(0, 10),
      duration_min: session.duration_min, title: session.title,
      status: 'planned', detail: session,
    });
    setSaved(true);
  };

  return (
    <View>
      <View style={styles.grid}>
        {TYPES.map(t => (
          <Pressable key={t.key} onPress={() => generate(t.key)}
            style={[styles.typeBtn, type === t.key && styles.typeBtnOn]}>
            <Text style={[styles.typeText, type === t.key && styles.typeTextOn]}>{t.label}</Text>
          </Pressable>
        ))}
      </View>

      {loading && <ActivityIndicator color={colors.signal} style={{ marginTop: spacing.l }} />}
      {error && <Text style={styles.error}>API injoignable. Vérifie que le backend est déployé.</Text>}

      {session && !loading && (
        <Card style={{ padding: spacing.m, marginTop: spacing.m }}>
          <View style={styles.head}>
            <Tag label={session.type.replace('_', ' ').toUpperCase()} color={colors.signal} />
            <Stars n={session.difficulty} />
          </View>
          <Text style={styles.title}>{session.title}</Text>
          <Text style={styles.meta}>
            {session.duration_min} min · {session.distance_km} km · {session.calories} kcal
          </Text>

          <Text style={styles.section}>ÉCHAUFFEMENT</Text>
          <IntervalRow it={session.warmup} />
          <Text style={styles.section}>CORPS DE SÉANCE</Text>
          {session.body.map((it, i) => <IntervalRow key={i} it={it} />)}
          <Text style={styles.section}>RETOUR AU CALME</Text>
          <IntervalRow it={session.cooldown} />

          {!!session.sciatic_note && <Text style={styles.sciatic}>⚠ {session.sciatic_note}</Text>}

          <View style={styles.actions}>
            <Pressable onPress={() => generate(type)} style={styles.again}>
              <Text style={styles.againText}>↻ GÉNÉRER UNE AUTRE</Text>
            </Pressable>
          </View>
          <View style={{ marginTop: spacing.s }}>
            {saved ? <Text style={styles.saved}>✓ Ajoutée à l'agenda</Text>
              : <PrimaryButton label="SAUVEGARDER CETTE SÉANCE" onPress={save} />}
          </View>
        </Card>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs },
  typeBtn: { paddingVertical: spacing.s, paddingHorizontal: spacing.m, borderRadius: 6,
    backgroundColor: colors.bgCard, borderWidth: 1, borderColor: colors.hairline },
  typeBtnOn: { backgroundColor: colors.signalSoft, borderColor: colors.signal },
  typeText: { color: colors.textSecondary, ...typography.label, fontSize: 10 },
  typeTextOn: { color: colors.signal },
  head: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  stars: { color: colors.readyYellow, fontSize: 12, letterSpacing: 2 },
  title: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h1, marginTop: spacing.s },
  meta: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: 2 },
  section: { color: colors.textSecondary, ...typography.label, marginTop: spacing.m, marginBottom: spacing.xs },
  interval: { paddingVertical: spacing.s, borderTopWidth: 1, borderTopColor: colors.hairline },
  intLabel: { color: colors.textPrimary, fontSize: typography.sizes.body, ...typography.bodyBold },
  intPace: { color: colors.signal, fontSize: typography.sizes.small, marginTop: 2 },
  intMeta: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: 2 },
  sciatic: { color: colors.readyOrange, fontSize: typography.sizes.small, marginTop: spacing.m },
  actions: { marginTop: spacing.l },
  again: { paddingVertical: 12, alignItems: 'center', borderRadius: spacing.cardRadius,
    borderWidth: 1, borderColor: colors.signal },
  againText: { color: colors.signal, ...typography.label, fontSize: 11 },
  saved: { color: colors.signal, textAlign: 'center', fontSize: typography.sizes.small, paddingVertical: 14 },
  error: { color: colors.readyOrange, fontSize: typography.sizes.small, marginTop: spacing.l },
});
