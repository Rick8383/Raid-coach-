/**
 * Force 5/3/1 (Mission 4) — Push/Pull/Legs, sélecteur jour + semaine.
 * Big 3 McGill, mouvement principal (charges du cycle), accessoires double
 * progression, GtG tractions (pull), finisher WOD. Marquer comme fait → agenda.
 */
import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { Strength531, api } from '../api/client';
import { Card, PrimaryButton, Tag } from './ui';
import { colors, spacing, typography } from '../theme/tokens';

const DAYS = [{ k: 'push', l: 'PUSH' }, { k: 'pull', l: 'PULL' }, { k: 'legs', l: 'LEGS' }];
const WEEKS = [1, 2, 3, 4];

export function StrengthProgram({ cycle = 0 }: { cycle?: number }) {
  const [day, setDay] = useState('push');
  const [week, setWeek] = useState(1);
  const [s, setS] = useState<Strength531 | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setLoading(true); setError(false); setSaved(false);
    api.strength531(day, week, cycle)
      .then(setS).catch(() => setError(true)).finally(() => setLoading(false));
  }, [day, week, cycle]);

  const save = async () => {
    if (!s) return;
    await api.saveSession({
      discipline: 'strength', session_date: new Date().toISOString().slice(0, 10),
      duration_min: 70, title: `Force ${day.toUpperCase()} S${week}`,
      status: 'done', detail: s,
    });
    setSaved(true);
  };

  return (
    <View>
      <View style={styles.selectors}>
        <View style={styles.row}>
          {DAYS.map(d => (
            <Pressable key={d.k} onPress={() => setDay(d.k)}
              style={[styles.chip, day === d.k && styles.chipOn]}>
              <Text style={[styles.chipT, day === d.k && styles.chipTOn]}>{d.l}</Text>
            </Pressable>
          ))}
        </View>
        <View style={[styles.row, { marginTop: spacing.s }]}>
          {WEEKS.map(w => (
            <Pressable key={w} onPress={() => setWeek(w)}
              style={[styles.weekChip, week === w && styles.chipOn]}>
              <Text style={[styles.chipT, week === w && styles.chipTOn]}>
                S{w}{w === 4 ? ' deload' : ''}
              </Text>
            </Pressable>
          ))}
        </View>
      </View>

      {loading && <ActivityIndicator color={colors.signal} style={{ marginTop: spacing.l }} />}
      {error && <Text style={styles.error}>API injoignable. Vérifie le déploiement backend.</Text>}

      {s && !loading && (
        <Card style={{ padding: spacing.m, marginTop: spacing.m }}>
          {/* Big 3 McGill */}
          <Text style={styles.section}>ÉCHAUFFEMENT — BIG 3 McGILL</Text>
          {s.warmup_mcgill.map((m, i) => (
            <Text key={i} style={styles.line}>• {m.name} — {m.prescription}</Text>
          ))}

          {/* Mouvement principal 5/3/1 */}
          <View style={styles.mainHead}>
            <Text style={styles.section}>PRINCIPAL — {s.main_lift.name}</Text>
            <Tag label={`TM ${s.main_lift.training_max}kg`} color={colors.fitness} />
          </View>
          {s.main_lift.sets.map((set, i) => (
            <View key={i} style={styles.set}>
              <Text style={styles.setLoad}>{set.load_kg} kg</Text>
              <Text style={styles.setReps}>× {set.reps}{set.amrap ? ' (max)' : ''}</Text>
              <Text style={styles.setPct}>{set.pct_tm}% · repos {set.rest_sec}s</Text>
            </View>
          ))}
          {!!s.main_lift.note && <Text style={styles.sciatic}>⚠ {s.main_lift.note}</Text>}

          {/* Accessoires */}
          <Text style={styles.section}>ACCESSOIRES (double progression)</Text>
          {s.accessories.map((a, i) => (
            <View key={i} style={styles.acc}>
              <Text style={styles.accName}>{a.name}</Text>
              <Text style={styles.accRx}>
                {a.sets}×{a.reps}{a.load_kg ? ` @${a.load_kg}kg` : ''} · tempo {a.tempo} · repos {a.rest_sec}s
              </Text>
            </View>
          ))}

          {/* GtG */}
          {!!s.grease_the_groove && (
            <Text style={styles.gtg}>💪 {s.grease_the_groove}</Text>
          )}

          {/* Finisher WOD */}
          <Text style={styles.section}>FINISHER — {s.finisher_wod.format}</Text>
          <Text style={styles.finisherName}>{s.finisher_wod.name}</Text>
          {s.finisher_wod.description.map((l, i) => (
            <Text key={i} style={styles.line}>• {l}</Text>
          ))}

          <View style={{ marginTop: spacing.l }}>
            {saved ? <Text style={styles.saved}>✓ Séance enregistrée comme faite</Text>
              : <PrimaryButton label="MARQUER COMME FAIT" onPress={save} />}
          </View>
        </Card>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  selectors: {},
  row: { flexDirection: 'row', gap: spacing.xs },
  chip: { flex: 1, paddingVertical: spacing.s, borderRadius: 6, alignItems: 'center', backgroundColor: colors.bgCard, borderWidth: 1, borderColor: colors.hairline },
  weekChip: { flex: 1, paddingVertical: spacing.s, borderRadius: 6, alignItems: 'center', backgroundColor: colors.bgCard, borderWidth: 1, borderColor: colors.hairline },
  chipOn: { backgroundColor: colors.signalSoft, borderColor: colors.signal },
  chipT: { color: colors.textSecondary, ...typography.label, fontSize: 10 },
  chipTOn: { color: colors.signal },
  section: { color: colors.textSecondary, ...typography.label, marginTop: spacing.m, marginBottom: spacing.xs },
  mainHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  line: { color: colors.textPrimary, fontSize: typography.sizes.small, lineHeight: 20 },
  set: { flexDirection: 'row', alignItems: 'baseline', paddingVertical: spacing.xs, gap: spacing.s },
  setLoad: { color: colors.signal, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2, minWidth: 70 },
  setReps: { color: colors.textPrimary, fontSize: typography.sizes.body, ...typography.bodyBold },
  setPct: { color: colors.textDisabled, fontSize: typography.sizes.small, marginLeft: 'auto' },
  sciatic: { color: colors.readyOrange, fontSize: typography.sizes.small, marginTop: spacing.s },
  acc: { paddingVertical: spacing.xs, borderTopWidth: 1, borderTopColor: colors.hairline },
  accName: { color: colors.textPrimary, fontSize: typography.sizes.body },
  accRx: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: 2 },
  gtg: { color: colors.fitness, fontSize: typography.sizes.small, marginTop: spacing.m, lineHeight: 19 },
  finisherName: { color: colors.signal, fontFamily: typography.bodyBold.fontFamily, fontSize: typography.sizes.body, marginBottom: spacing.xs },
  saved: { color: colors.signal, textAlign: 'center', fontSize: typography.sizes.small, paddingVertical: 14 },
  error: { color: colors.readyOrange, fontSize: typography.sizes.small, marginTop: spacing.l },
});
