/**
 * Force 5/3/1 (Mission 4) — sélecteur jour/semaine, graphe de progression des
 * charges (sur 6 cycles), détail riche de la séance, « Marquer comme fait ».
 */
import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { Strength531, StrengthProgression, api } from '../api/client';
import { BarChart } from './Chart';
import { StrengthDetail } from './SessionDetail';
import { Card, PrimaryButton, Tag } from './ui';
import { colors, spacing, typography } from '../theme/tokens';
import { localISODate } from '../schedule';

const DAYS = [{ k: 'push', l: 'PUSH' }, { k: 'pull', l: 'PULL' }, { k: 'legs', l: 'LEGS' }];
const WEEKS = [1, 2, 3, 4];
const LIFT_BY_DAY: Record<string, string> = { push: 'bench', pull: 'row', legs: 'squat' };

export function StrengthProgram({ cycle = 0 }: { cycle?: number }) {
  const [day, setDay] = useState('push');
  const [week, setWeek] = useState(1);
  const [s, setS] = useState<Strength531 | null>(null);
  const [prog, setProg] = useState<StrengthProgression | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setLoading(true); setError(false); setSaved(false);
    api.strength531(day, week, cycle)
      .then(setS).catch(() => setError(true)).finally(() => setLoading(false));
  }, [day, week, cycle]);

  useEffect(() => {
    api.strengthProgression(LIFT_BY_DAY[day], 6).then(setProg).catch(() => setProg(null));
  }, [day]);

  const save = async () => {
    if (!s) return;
    await api.saveSession({
      discipline: 'strength', session_date: localISODate(),
      duration_min: 70, title: `Force ${day.toUpperCase()} S${week}`, status: 'done', detail: s,
    });
    setSaved(true);
  };

  return (
    <View>
      <View style={styles.row}>
        {DAYS.map(d => (
          <Pressable key={d.k} onPress={() => setDay(d.k)} style={[styles.chip, day === d.k && styles.chipOn]}>
            <Text style={[styles.chipT, day === d.k && styles.chipTOn]}>{d.l}</Text>
          </Pressable>
        ))}
      </View>
      <View style={[styles.row, { marginTop: spacing.s }]}>
        {WEEKS.map(w => (
          <Pressable key={w} onPress={() => setWeek(w)} style={[styles.chip, week === w && styles.chipOn]}>
            <Text style={[styles.chipT, week === w && styles.chipTOn]}>S{w}{w === 4 ? ' DL' : ''}</Text>
          </Pressable>
        ))}
      </View>

      {/* Graphe progression des charges */}
      {prog && (
        <Card style={{ padding: spacing.m, marginTop: spacing.m }}>
          <View style={styles.progHead}>
            <Text style={styles.progLabel}>PROGRESSION — {prog.name}</Text>
            <Tag label={`+${prog.increment}kg/cycle`} color={colors.signal} />
          </View>
          <BarChart unit="kg" data={prog.points.map((p, i) => ({
            label: `C${p.cycle}`, value: p.top_set_kg, display: `${p.top_set_kg}`,
            highlight: i === cycle,
          }))} />
          <Text style={styles.progNote}>
            Série lourde (S3) · 1RM estimé ~{prog.points[cycle]?.est_1rm ?? prog.points[0].est_1rm} kg
            {prog.goal_1rm ? ` · objectif ${prog.goal_1rm} kg` : ''}
          </Text>
        </Card>
      )}

      {loading && <ActivityIndicator color={colors.signal} style={{ marginTop: spacing.l }} />}
      {error && <Text style={styles.error}>API injoignable. Vérifie le déploiement backend.</Text>}

      {s && !loading && (
        <Card style={{ padding: spacing.m, marginTop: spacing.m }}>
          {s.is_deload && <Tag label="SEMAINE DELOAD" color={colors.readyYellow} />}
          <StrengthDetail session={s} />
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
  row: { flexDirection: 'row', gap: spacing.xs },
  chip: { flex: 1, paddingVertical: spacing.s, borderRadius: 6, alignItems: 'center', backgroundColor: colors.bgCard, borderWidth: 1, borderColor: colors.hairline },
  chipOn: { backgroundColor: colors.signalSoft, borderColor: colors.signal },
  chipT: { color: colors.textSecondary, ...typography.label, fontSize: 10 },
  chipTOn: { color: colors.signal },
  progHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.m },
  progLabel: { color: colors.textSecondary, ...typography.label },
  progNote: { color: colors.textDisabled, fontSize: typography.sizes.micro, marginTop: spacing.s, textAlign: 'center' },
  saved: { color: colors.signal, textAlign: 'center', fontSize: typography.sizes.small, paddingVertical: 14 },
  error: { color: colors.readyOrange, fontSize: typography.sizes.small, marginTop: spacing.l },
});
