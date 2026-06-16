/**
 * Générateur WOD (Mission 3) — 15 formats, durée réglable, toggle anti-lombaire
 * (sciatique L5-S1, ON par défaut). Affiche le WOD complet et l'ajoute à la séance.
 */
import React, { useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { Wod, api } from '../api/client';
import { WodDetail } from './SessionDetail';
import { WodTimer, WodResult } from './WodTimer';
import { Card, PrimaryButton, Tag } from './ui';
import { colors, spacing, typography } from '../theme/tokens';

function fmtTime(sec: number): string {
  const m = Math.floor(sec / 60);
  return `${String(m).padStart(2, '0')}:${String(sec % 60).padStart(2, '0')}`;
}

const FORMATS: { key: string; label: string }[] = [
  { key: 'auto', label: 'SURPRISE' },
  { key: 'amrap', label: 'AMRAP' },
  { key: 'for_time', label: 'FOR TIME' },
  { key: 'emom', label: 'EMOM' },
  { key: 'death_by', label: 'DEATH BY' },
  { key: 'death_by_emom', label: 'DEATH BY EMOM' },
  { key: 'chipper', label: 'CHIPPER' },
  { key: 'rft', label: 'RFT' },
  { key: 'tabata', label: 'TABATA' },
  { key: 'ladder', label: 'LADDER' },
  { key: 'pyramid_full', label: 'PYRAMIDE' },
  { key: 'buy_in_amrap_buy_out', label: 'BUY-IN/OUT' },
];

function Stars({ n }: { n: number }) {
  return <Text style={styles.stars}>{'◆'.repeat(n)}{'◇'.repeat(5 - n)}</Text>;
}

export function WodGenerator() {
  const [format, setFormat] = useState('auto');
  const [duration, setDuration] = useState(12);
  const [excludeLumbar, setExcludeLumbar] = useState(true);
  const [seed, setSeed] = useState(0);
  const [wod, setWod] = useState<Wod | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [saved, setSaved] = useState(false);
  const [scoreSaved, setScoreSaved] = useState<string | null>(null);

  const generate = async () => {
    const next = seed + 1;
    setSeed(next); setLoading(true); setError(false); setSaved(false); setScoreSaved(null);
    try {
      const w = await api.generateWod({
        format, duration_min: duration, seed: `w${next}`, exclude_lumbar: excludeLumbar,
      });
      setWod(w);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const save = async () => {
    if (!wod) return;
    await api.saveSession({
      discipline: 'crossfit', session_date: new Date().toISOString().slice(0, 10),
      duration_min: duration, title: wod.name, status: 'planned', detail: wod,
    });
    setSaved(true);
  };

  // Le chrono a livré un score → on enregistre la séance comme FAITE avec le
  // score (temps ou reps) dans le détail → suivi dans l'agenda/l'historique.
  const saveScore = async (r: WodResult) => {
    if (!wod) return;
    const scoreLabel = r.mode === 'for_time'
      ? `${fmtTime(r.time_sec)}${r.capped ? ' (cap)' : ''}`
      : `${r.reps} reps/rounds`;
    await api.saveSession({
      discipline: 'crossfit', session_date: new Date().toISOString().slice(0, 10),
      duration_min: Math.max(1, Math.round(r.time_sec / 60)) || duration,
      intensity_rpe: 9, title: `${wod.name} — ${scoreLabel}`, status: 'done',
      detail: { ...wod, result: r, score_label: scoreLabel },
    });
    setScoreSaved(scoreLabel);
  };

  return (
    <View>
      <Text style={styles.lbl}>FORMAT</Text>
      <View style={styles.grid}>
        {FORMATS.map(f => (
          <Pressable key={f.key} onPress={() => setFormat(f.key)}
            style={[styles.fmt, format === f.key && styles.fmtOn]}>
            <Text style={[styles.fmtText, format === f.key && styles.fmtTextOn]}>{f.label}</Text>
          </Pressable>
        ))}
      </View>

      <View style={styles.controls}>
        <Text style={styles.lbl}>DURÉE</Text>
        <View style={styles.durRow}>
          <Pressable onPress={() => setDuration(d => Math.max(5, d - 1))} style={styles.durBtn}><Text style={styles.durBtnT}>–</Text></Pressable>
          <Text style={styles.durVal}>{duration} min</Text>
          <Pressable onPress={() => setDuration(d => Math.min(25, d + 1))} style={styles.durBtn}><Text style={styles.durBtnT}>+</Text></Pressable>
        </View>
      </View>

      <View style={styles.lumbarRow}>
        <Text style={styles.lumbarLbl}>Éviter mouvements lombaires (sciatique)</Text>
        <Switch value={excludeLumbar} onValueChange={setExcludeLumbar}
          trackColor={{ true: colors.signalDim, false: colors.hairline }} />
      </View>

      <PrimaryButton label={wod ? '↻ GÉNÉRER ENCORE' : 'GÉNÉRER UN WOD'} onPress={generate} />

      {loading && <ActivityIndicator color={colors.signal} style={{ marginTop: spacing.l }} />}
      {error && <Text style={styles.error}>API injoignable. Vérifie le déploiement backend.</Text>}

      {wod && !loading && (
        <Card style={{ padding: spacing.m, marginTop: spacing.m }}>
          <View style={styles.head}>
            <Tag label={wod.format} color={colors.signal} />
            <Stars n={wod.difficulty} />
          </View>
          <Text style={styles.name}>{wod.name}</Text>
          <WodDetail wod={wod} />

          {/* Chrono compétition : compte à rebours + bips, temps (For Time) ou
              reps (AMRAP) → score enregistré pour le suivi. */}
          <Text style={styles.timerLbl}>CHRONO COMPÉTITION</Text>
          <WodTimer wod={wod} durationMin={duration} onFinish={saveScore} />
          {scoreSaved && <Text style={styles.saved}>✓ Score enregistré : {scoreSaved}</Text>}

          <View style={{ marginTop: spacing.m }}>
            {saved ? <Text style={styles.saved}>✓ Ajouté à ta séance CrossFit (agenda)</Text>
              : <PrimaryButton label="AJOUTER À MA SÉANCE CROSSFIT" onPress={save} />}
          </View>
        </Card>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  lbl: { color: colors.textSecondary, ...typography.label, marginBottom: spacing.s, marginTop: spacing.s },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs },
  fmt: { paddingVertical: spacing.s, paddingHorizontal: spacing.s, borderRadius: 6, backgroundColor: colors.bgCard, borderWidth: 1, borderColor: colors.hairline },
  fmtOn: { backgroundColor: colors.signalSoft, borderColor: colors.signal },
  fmtText: { color: colors.textSecondary, ...typography.label, fontSize: 9 },
  fmtTextOn: { color: colors.signal },
  controls: { marginTop: spacing.m },
  durRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.l },
  durBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: colors.bgElevated, borderWidth: 1, borderColor: colors.hairlineStrong, alignItems: 'center', justifyContent: 'center' },
  durBtnT: { color: colors.signal, fontSize: 22, fontFamily: typography.display.fontFamily },
  durVal: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2, minWidth: 70, textAlign: 'center' },
  lumbarRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginVertical: spacing.m },
  lumbarLbl: { color: colors.textSecondary, fontSize: typography.sizes.small, flex: 1, paddingRight: spacing.s },
  head: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  stars: { color: colors.readyYellow, fontSize: 12, letterSpacing: 2 },
  name: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h1, letterSpacing: 1, marginTop: spacing.s },
  cap: { color: colors.signal, ...typography.label, marginTop: 2 },
  desc: { marginTop: spacing.m, gap: spacing.xs },
  descLine: { color: colors.textPrimary, fontSize: typography.sizes.body, lineHeight: 22, ...typography.bodyBold },
  score: { color: colors.textPrimary, fontSize: typography.sizes.body, marginTop: spacing.m },
  muscles: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: spacing.xs },
  lumbarNote: { fontSize: typography.sizes.small, marginTop: spacing.s },
  saved: { color: colors.signal, textAlign: 'center', fontSize: typography.sizes.small, paddingVertical: 14 },
  timerLbl: { color: colors.textSecondary, ...typography.label, marginTop: spacing.l },
  error: { color: colors.readyOrange, fontSize: typography.sizes.small, marginTop: spacing.l },
});
