/**
 * Séance LIBRE (hors plan) : vélo, boxe, JJB, natation, rando… Saisie manuelle
 * des données (durée, RPE, et selon le sport : distance, FC, dénivelé, calories,
 * notes). Enregistrée comme faite → comptée dans le suivi (charge/agenda).
 */
import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { api } from '../api/client';
import { Card, PrimaryButton } from './ui';
import { NumberField } from './NumberField';
import { RpeScale } from './RpeScale';
import { colors, spacing, typography } from '../theme/tokens';

const DAY_MS = 24 * 3600 * 1000;
const DAY_SHORT = ['DIM', 'LUN', 'MAR', 'MER', 'JEU', 'VEN', 'SAM'];

function pastDays(n: number) {
  const base = new Date();
  return Array.from({ length: n }, (_, i) => {
    const d = new Date(Date.UTC(base.getUTCFullYear(), base.getUTCMonth(), base.getUTCDate()) - i * DAY_MS);
    return { iso: d.toISOString().slice(0, 10), label: i === 0 ? 'AUJ.' : `${DAY_SHORT[d.getUTCDay()]} ${d.getUTCDate()}` };
  });
}

const ACTIVITIES: { label: string; discipline: string }[] = [
  { label: 'Vélo', discipline: 'cycling' },
  { label: 'Boxe', discipline: 'combat' },
  { label: 'JJB', discipline: 'combat' },
  { label: 'Natation', discipline: 'swim' },
  { label: 'Rando', discipline: 'hiking' },
  { label: 'Mobilité', discipline: 'mobility' },
  { label: 'Autre', discipline: 'other' },
];

// Champ métrique optionnel : 0 = non renseigné (non envoyé).
function OptMetric({ label, value, onChange, step = 1, max = 100000, unit, decimals = 0 }: {
  label: string; value: number; onChange: (v: number) => void;
  step?: number; max?: number; unit?: string; decimals?: number;
}) {
  return (
    <View style={styles.metricRow}>
      <Text style={styles.metricLbl}>{label}</Text>
      <NumberField value={value} step={step} min={0} max={max} unit={unit}
        decimals={decimals} onChange={onChange} />
    </View>
  );
}

export function ManualSessionForm() {
  const days = pastDays(8);
  const [act, setAct] = useState(ACTIVITIES[0]);
  const [custom, setCustom] = useState('');
  const [date, setDate] = useState(days[0].iso);
  const [duration, setDuration] = useState(60);
  const [rpe, setRpe] = useState(6);
  const [distance, setDistance] = useState(0);
  const [hrAvg, setHrAvg] = useState(0);
  const [hrMax, setHrMax] = useState(0);
  const [elevation, setElevation] = useState(0);
  const [calories, setCalories] = useState(0);
  const [notes, setNotes] = useState('');
  const [saved, setSaved] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const label = act.discipline === 'other' && custom.trim() ? custom.trim() : act.label;

  const save = async () => {
    setBusy(true); setSaved(null);
    const body: Record<string, unknown> = {
      activity: label, discipline: act.discipline, session_date: date,
      duration_min: duration, intensity_rpe: rpe,
    };
    if (distance > 0) body.distance_km = distance;
    if (hrAvg > 0) body.hr_avg = hrAvg;
    if (hrMax > 0) body.hr_max = hrMax;
    if (elevation > 0) body.elevation_m = elevation;
    if (calories > 0) body.calories = calories;
    if (notes.trim()) body.notes = notes.trim();
    try {
      await api.logManualSession(body);
      setSaved(`${label} · ${duration} min enregistrée — visible dans l'Agenda (Suivi)`);
    } catch {
      setSaved('Erreur réseau — réessaie une fois en ligne.');
    } finally { setBusy(false); }
  };

  return (
    <View>
      <Text style={styles.intro}>
        Enregistre une séance qui n'est pas dans ton plan. Elle compte dans ton
        suivi (charge, agenda, historique).
      </Text>

      <Text style={styles.lbl}>TYPE DE SÉANCE</Text>
      <View style={styles.chips}>
        {ACTIVITIES.map(a => (
          <Pressable key={a.label} onPress={() => setAct(a)}
            style={[styles.chip, act.label === a.label && styles.chipOn]}>
            <Text style={[styles.chipT, act.label === a.label && styles.chipTOn]}>{a.label}</Text>
          </Pressable>
        ))}
      </View>
      {act.discipline === 'other' && (
        <TextInput style={styles.input} value={custom} onChangeText={setCustom}
          placeholder="Nom de l'activité (ex. escalade, padel…)" placeholderTextColor={colors.textDisabled} />
      )}

      <Text style={styles.lbl}>QUAND</Text>
      <View style={styles.chips}>
        {days.map(d => (
          <Pressable key={d.iso} onPress={() => setDate(d.iso)}
            style={[styles.dayChip, date === d.iso && styles.chipOn]}>
            <Text style={[styles.chipT, date === d.iso && styles.chipTOn]}>{d.label}</Text>
          </Pressable>
        ))}
      </View>

      <Card style={{ padding: spacing.m, marginTop: spacing.m }}>
        <View style={styles.metricRow}>
          <Text style={styles.metricLbl}>Durée</Text>
          <NumberField value={duration} step={5} min={1} max={600} unit="min" onChange={setDuration} />
        </View>
        <Text style={[styles.metricLbl, { marginTop: spacing.m }]}>Intensité ressentie (RPE)</Text>
        <View style={{ marginTop: spacing.s }}>
          <RpeScale value={rpe} onChange={setRpe} />
        </View>

        <Text style={styles.optTitle}>DONNÉES (optionnelles — laisse 0 si non concerné)</Text>
        <OptMetric label="Distance" value={distance} onChange={setDistance} step={0.5} max={1000} decimals={1} unit="km" />
        <OptMetric label="FC moyenne" value={hrAvg} onChange={setHrAvg} max={230} unit="bpm" />
        <OptMetric label="FC max" value={hrMax} onChange={setHrMax} max={230} unit="bpm" />
        <OptMetric label="Dénivelé" value={elevation} onChange={setElevation} step={10} max={12000} unit="m" />
        <OptMetric label="Calories" value={calories} onChange={setCalories} step={10} max={20000} unit="kcal" />
        <Text style={[styles.metricLbl, { marginTop: spacing.m }]}>Notes</Text>
        <TextInput style={[styles.input, { marginTop: spacing.s }]} value={notes} onChangeText={setNotes}
          placeholder="Ressenti, technique travaillée…" placeholderTextColor={colors.textDisabled} multiline />
      </Card>

      <View style={{ marginTop: spacing.m }}>
        <PrimaryButton label={busy ? '…' : 'ENREGISTRER LA SÉANCE'} onPress={save} disabled={busy} />
      </View>
      {saved && <Text style={styles.saved}>✓ {saved}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  intro: { color: colors.textSecondary, fontSize: typography.sizes.small, lineHeight: 19, marginBottom: spacing.m },
  lbl: { color: colors.textSecondary, ...typography.label, marginTop: spacing.m, marginBottom: spacing.s },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs },
  chip: { paddingVertical: spacing.s, paddingHorizontal: spacing.m, borderRadius: 6, backgroundColor: colors.bgCard, borderWidth: 1, borderColor: colors.hairline },
  dayChip: { paddingVertical: spacing.s, paddingHorizontal: spacing.s, borderRadius: 6, backgroundColor: colors.bgCard, borderWidth: 1, borderColor: colors.hairline },
  chipOn: { backgroundColor: colors.signalSoft, borderColor: colors.signal },
  chipT: { color: colors.textSecondary, ...typography.label, fontSize: 10 },
  chipTOn: { color: colors.signal },
  input: {
    color: colors.textPrimary, backgroundColor: colors.bgInput, borderRadius: spacing.cardRadius,
    paddingHorizontal: spacing.m, paddingVertical: spacing.s, fontSize: typography.sizes.body,
    borderWidth: 1, borderColor: colors.hairline, marginTop: spacing.s,
  },
  metricRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: spacing.xs },
  metricLbl: { color: colors.textPrimary, fontSize: typography.sizes.small },
  optTitle: { color: colors.textSecondary, ...typography.label, fontSize: 10, marginTop: spacing.l, marginBottom: spacing.xs },
  saved: { color: colors.signal, fontSize: typography.sizes.small, marginTop: spacing.m, textAlign: 'center', lineHeight: 18 },
});
