/**
 * Graphique à barres sans dépendance (fonctionne web + natif via flexbox).
 * Échelle non nulle pour amplifier la progression ; barre courante mise en avant.
 */
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, spacing, typography } from '../theme/tokens';

export interface BarDatum {
  label: string;
  value: number;
  display?: string;
  highlight?: boolean;
}

export function BarChart({ data, color = colors.signal, height = 130, unit = '' }:
  { data: BarDatum[]; color?: string; height?: number; unit?: string }) {
  if (!data.length) return null;
  const values = data.map(d => d.value);
  const max = Math.max(...values);
  const min = Math.min(...values);
  const floor = min - (max - min) * 0.6 - (max === min ? max * 0.1 || 1 : 0);
  const usable = height - 34;
  const barH = (v: number) => Math.max(6, ((v - floor) / (max - floor || 1)) * usable);

  return (
    <View style={[styles.root, { height }]}>
      {data.map((d, i) => (
        <View key={i} style={styles.col}>
          <Text style={[styles.val, d.highlight && { color }]}>{d.display ?? d.value}{unit}</Text>
          <View style={[styles.bar, {
            height: barH(d.value),
            backgroundColor: d.highlight ? color : colors.hairlineStrong,
          }]} />
          <Text style={[styles.lbl, d.highlight && { color: colors.textPrimary }]}>{d.label}</Text>
        </View>
      ))}
    </View>
  );
}

/** Jauge horizontale : remplissage + zone "sweet spot" optionnelle + marqueur. */
export function MeterBar({ value, max, color = colors.signal, sweet, marker }:
  { value: number; max: number; color?: string; sweet?: [number, number]; marker?: number }) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <View style={styles.meter}>
      {sweet && (
        <View style={[styles.sweet, {
          left: `${(sweet[0] / max) * 100}%`,
          width: `${((sweet[1] - sweet[0]) / max) * 100}%`,
        }]} />
      )}
      <View style={[styles.meterFill, { width: `${pct}%`, backgroundColor: color }]} />
      {marker != null && (
        <View style={[styles.marker, { left: `${Math.min(100, (marker / max) * 100)}%` }]} />
      )}
    </View>
  );
}

/** Barre de répartition (proportions empilées), ex. macros. */
export function StackBar({ segments }: { segments: { value: number; color: string }[] }) {
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;
  return (
    <View style={styles.stack}>
      {segments.map((s, i) => (
        <View key={i} style={{ flex: s.value / total, backgroundColor: s.color }} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', gap: 6 },
  meter: { height: 10, borderRadius: 5, backgroundColor: colors.hairline, overflow: 'hidden', justifyContent: 'center' },
  sweet: { position: 'absolute', top: 0, bottom: 0, backgroundColor: colors.signalSoft },
  meterFill: { height: 10, borderRadius: 5 },
  marker: { position: 'absolute', width: 3, top: -2, bottom: -2, marginLeft: -1, backgroundColor: colors.textPrimary },
  stack: { flexDirection: 'row', height: 10, borderRadius: 5, overflow: 'hidden' },
  col: { flex: 1, alignItems: 'center', justifyContent: 'flex-end', height: '100%' },
  bar: { width: '70%', borderTopLeftRadius: 3, borderTopRightRadius: 3, marginTop: 4 },
  val: { color: colors.textSecondary, fontFamily: typography.display.fontFamily, fontSize: 12 },
  lbl: { color: colors.textDisabled, ...typography.label, fontSize: 8, marginTop: spacing.xs },
});
