/**
 * Saisie manuelle des VRAIES données de la montre (Garmin) pour une séance
 * faite : distance, durée réelle, FC moy/max, dénivelé, calories, cadence,
 * Training Effect. Toutes optionnelles (0 = non renseigné). Ces données sont
 * rattachées au profil courant (isolation par utilisateur) — elles servent au
 * suivi et n'affectent pas les autres utilisateurs.
 */
import React, { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { NumberField } from './NumberField';
import { colors, spacing, typography } from '../theme/tokens';

export type WatchMetrics = {
  duration_min?: number; distance_km?: number; hr_avg?: number; hr_max?: number;
  elevation_m?: number; calories?: number; cadence_spm?: number;
  te_aerobic?: number; te_anaerobic?: number;
};

function Metric({ label, value, onChange, step = 1, max = 100000, unit, decimals = 0 }: {
  label: string; value: number; onChange: (v: number) => void;
  step?: number; max?: number; unit?: string; decimals?: number;
}) {
  return (
    <View style={styles.row}>
      <Text style={styles.lbl}>{label}</Text>
      <NumberField value={value} step={step} min={0} max={max} unit={unit}
        decimals={decimals} onChange={onChange} />
    </View>
  );
}

export function WatchMetricsForm({ defaultDuration, onChange }: {
  defaultDuration: number;
  onChange: (m: WatchMetrics) => void;
}) {
  const [m, setM] = useState<WatchMetrics>({ duration_min: defaultDuration });
  const set = (k: keyof WatchMetrics, v: number) => {
    const next = { ...m, [k]: v };
    setM(next);
    onChange(next);
  };
  return (
    <View style={styles.box}>
      <Text style={styles.intro}>
        Recopie les chiffres de ta montre. Laisse 0 pour ce que tu ne veux pas
        renseigner. Ces données restent sur ton profil.
      </Text>
      <Metric label="Distance" value={m.distance_km ?? 0} onChange={v => set('distance_km', v)}
        step={0.1} max={1000} decimals={2} unit="km" />
      <Metric label="Durée réelle" value={m.duration_min ?? 0} onChange={v => set('duration_min', v)}
        step={1} max={600} unit="min" />
      <Metric label="FC moyenne" value={m.hr_avg ?? 0} onChange={v => set('hr_avg', v)}
        max={230} unit="bpm" />
      <Metric label="FC max" value={m.hr_max ?? 0} onChange={v => set('hr_max', v)}
        max={230} unit="bpm" />
      <Metric label="Dénivelé" value={m.elevation_m ?? 0} onChange={v => set('elevation_m', v)}
        step={5} max={12000} unit="m" />
      <Metric label="Calories" value={m.calories ?? 0} onChange={v => set('calories', v)}
        step={10} max={20000} unit="kcal" />
      <Metric label="Cadence" value={m.cadence_spm ?? 0} onChange={v => set('cadence_spm', v)}
        max={260} unit="ppm" />
      <Metric label="Training Effect aérobie" value={m.te_aerobic ?? 0} onChange={v => set('te_aerobic', v)}
        step={0.1} max={5} decimals={1} />
      <Metric label="Training Effect anaérobie" value={m.te_anaerobic ?? 0} onChange={v => set('te_anaerobic', v)}
        step={0.1} max={5} decimals={1} />
    </View>
  );
}

// Rendu compact et lisible des données montre enregistrées (suivi/historique).
export function WatchMetricsView({ m }: { m: WatchMetrics }) {
  const pace = m.distance_km && m.duration_min && m.distance_km > 0
    ? (() => {
        const secPerKm = (m.duration_min! * 60) / m.distance_km!;
        return `${Math.floor(secPerKm / 60)}:${String(Math.round(secPerKm % 60)).padStart(2, '0')}/km`;
      })()
    : null;
  const chips = [
    m.distance_km ? `${m.distance_km.toFixed(2).replace('.', ',')} km` : null,
    m.duration_min ? `${m.duration_min} min` : null,
    pace,
    m.hr_avg ? `FC moy ${m.hr_avg}` : null,
    m.hr_max ? `FC max ${m.hr_max}` : null,
    m.elevation_m ? `D+ ${m.elevation_m} m` : null,
    m.calories ? `${m.calories} kcal` : null,
    m.cadence_spm ? `${m.cadence_spm} ppm` : null,
    m.te_aerobic ? `TE aéro ${m.te_aerobic.toFixed(1).replace('.', ',')}` : null,
    m.te_anaerobic ? `TE anaéro ${m.te_anaerobic.toFixed(1).replace('.', ',')}` : null,
  ].filter(Boolean) as string[];
  if (!chips.length) return null;
  return (
    <View style={styles.viewBox}>
      <Text style={styles.viewTag}>⌚ DONNÉES MONTRE</Text>
      <View style={styles.chips}>
        {chips.map((c, i) => <Text key={i} style={styles.chip}>{c}</Text>)}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  box: { marginTop: spacing.s, gap: 2 },
  intro: { color: colors.textSecondary, fontSize: typography.sizes.small, lineHeight: 18, marginBottom: spacing.s },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: spacing.xs },
  lbl: { color: colors.textPrimary, fontSize: typography.sizes.small, flex: 1 },
  viewBox: {
    marginTop: spacing.s, backgroundColor: colors.signalSoft, borderRadius: 10,
    padding: spacing.s, gap: spacing.xs,
  },
  viewTag: { color: colors.signal, ...typography.label, fontSize: 10 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs },
  chip: {
    color: colors.textPrimary, fontSize: typography.sizes.small,
    backgroundColor: colors.bgCard, borderRadius: 6, paddingHorizontal: spacing.s, paddingVertical: 3,
    overflow: 'hidden',
  },
});
