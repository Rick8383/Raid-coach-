/** Benchmarks Sélection : progression vers les cibles élite (top 5%) + suivi chiffré. */
import React, { useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { AthleteProfile, BenchmarkProgression, SessionRow, api } from '../api/client';
import { ReadinessBar } from '../components/ReadinessBar';
import { BarChart } from '../components/Chart';
import { Card, PrimaryButton } from '../components/ui';
import { colors, spacing, typography } from '../theme/tokens';

const TRACKED: { id: string; label: string; unit: string; step: number }[] = [
  { id: 'pullups_max', label: 'TRACTIONS', unit: 'reps', step: 1 },
  { id: 'pushups_max', label: 'POMPES', unit: 'reps', step: 1 },
  { id: 'dips_max', label: 'DIPS', unit: 'reps', step: 1 },
  { id: 'leg_raises_max', label: 'TOES-TO-BAR', unit: 'reps', step: 1 },
  { id: 'cooper_m', label: 'COOPER', unit: 'm', step: 50 },
];

function BenchmarkTracker() {
  const [sel, setSel] = useState(TRACKED[0]);
  const [prog, setProg] = useState<BenchmarkProgression | null>(null);
  const [val, setVal] = useState(16);
  const [saved, setSaved] = useState(false);

  const load = (id: string) => api.benchmarkProgression(id).then(setProg).catch(() => setProg(null));
  useEffect(() => { load(sel.id); setSaved(false); }, [sel]);
  useEffect(() => {
    const last = prog?.results?.slice(-1)[0]?.result_value;
    if (last) setVal(last);
  }, [prog]);

  const logTest = async () => {
    await api.recordBenchmark({
      benchmark_id: sel.id, result_value: val, result_unit: sel.unit,
      test_date: new Date().toISOString().slice(0, 10),
    });
    setSaved(true);
    setTimeout(() => load(sel.id), 400); // laisse la file de sync passer
  };

  const points = (prog?.results ?? []).map(r => ({
    label: r.test_date.slice(5), value: r.result_value, display: `${r.result_value}`,
    highlight: false,
  }));
  if (points.length) points[points.length - 1].highlight = true;

  return (
    <Card style={{ padding: spacing.m, marginTop: spacing.l }}>
      <Text style={styles.trackTitle}>SUIVI CHIFFRÉ</Text>
      <View style={styles.chips}>
        {TRACKED.map(t => (
          <Pressable key={t.id} onPress={() => setSel(t)} style={[styles.chip, sel.id === t.id && styles.chipOn]}>
            <Text style={[styles.chipT, sel.id === t.id && styles.chipTOn]}>{t.label}</Text>
          </Pressable>
        ))}
      </View>
      {points.length > 0
        ? <BarChart data={points} unit={sel.unit === 'm' ? '' : ''} />
        : <Text style={styles.empty}>Aucun test enregistré pour le moment.</Text>}
      <View style={styles.logRow}>
        <Pressable onPress={() => setVal(v => Math.max(0, v - sel.step))} style={styles.stepBtn}><Text style={styles.stepT}>–</Text></Pressable>
        <Text style={styles.logVal}>{val} {sel.unit}</Text>
        <Pressable onPress={() => setVal(v => v + sel.step)} style={styles.stepBtn}><Text style={styles.stepT}>+</Text></Pressable>
      </View>
      {saved ? <Text style={styles.saved}>✓ Test enregistré</Text>
        : <PrimaryButton label="ENREGISTRER LE TEST DU JOUR" onPress={logTest} />}
    </Card>
  );
}

function WodPerfHistory() {
  const [wods, setWods] = useState<SessionRow[]>([]);
  useEffect(() => {
    api.recentSessions(60)
      .then(r => setWods((r.sessions ?? []).filter(s =>
        s.discipline === 'crossfit' && s.status === 'done' && !!s.score)))
      .catch(() => setWods([]));
  }, []);

  return (
    <Card style={{ padding: spacing.m, marginTop: spacing.l }}>
      <Text style={styles.trackTitle}>DERNIERS WODS — PERFORMANCE</Text>
      {wods.length === 0 ? (
        <Text style={styles.empty}>
          Aucun WOD chronométré pour l'instant. Lance le chrono sur un WOD et
          enregistre ton score : il apparaîtra ici et alimentera ton analyse de forme.
        </Text>
      ) : (
        wods.slice(0, 12).map((s, i) => (
          <View key={i} style={styles.wodRow}>
            <Text style={styles.wodDate}>{s.session_date.slice(5)}</Text>
            <Text style={styles.wodName} numberOfLines={1}>
              {(s.family_id ?? 'WOD').replace(/ — .*/, '')}
            </Text>
            <Text style={styles.wodScore}>
              {s.score?.type === 'time' ? '🏁 ' : '🔁 '}{s.score?.label}
            </Text>
          </View>
        ))
      )}
      <Text style={styles.wodNote}>
        Le temps (For Time) et les reps (AMRAP) comptent dans ta charge et dans
        la dimension « performance » de l'analyse de forme.
      </Text>
    </Card>
  );
}

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

      <WodPerfHistory />
      <BenchmarkTracker />
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
  trackTitle: { color: colors.textSecondary, ...typography.label, marginBottom: spacing.m },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginBottom: spacing.m },
  chip: { paddingVertical: spacing.xs, paddingHorizontal: spacing.s, borderRadius: 6, backgroundColor: colors.bgElevated, borderWidth: 1, borderColor: colors.hairline },
  chipOn: { backgroundColor: colors.signalSoft, borderColor: colors.signal },
  chipT: { color: colors.textSecondary, ...typography.label, fontSize: 9 },
  chipTOn: { color: colors.signal },
  empty: { color: colors.textDisabled, fontSize: typography.sizes.small, textAlign: 'center', paddingVertical: spacing.l },
  logRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.l, marginVertical: spacing.m },
  stepBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: colors.bgElevated, borderWidth: 1, borderColor: colors.hairlineStrong, alignItems: 'center', justifyContent: 'center' },
  stepT: { color: colors.signal, fontSize: 22, fontFamily: typography.display.fontFamily },
  logVal: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h1, minWidth: 90, textAlign: 'center' },
  saved: { color: colors.signal, textAlign: 'center', fontSize: typography.sizes.small, paddingVertical: 14 },
  wodRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.s,
    borderTopWidth: 1, borderTopColor: colors.hairline, gap: spacing.s },
  wodDate: { color: colors.textDisabled, fontSize: typography.sizes.micro, width: 44 },
  wodName: { color: colors.textPrimary, fontSize: typography.sizes.small, flex: 1 },
  wodScore: { color: colors.signal, fontFamily: typography.display.fontFamily,
    fontSize: typography.sizes.body },
  wodNote: { color: colors.textDisabled, fontSize: typography.sizes.micro,
    marginTop: spacing.m, lineHeight: 16 },
});
