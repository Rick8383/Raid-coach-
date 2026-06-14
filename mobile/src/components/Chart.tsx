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

const styles = StyleSheet.create({
  root: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', gap: 6 },
  col: { flex: 1, alignItems: 'center', justifyContent: 'flex-end', height: '100%' },
  bar: { width: '70%', borderTopLeftRadius: 3, borderTopRightRadius: 3, marginTop: 4 },
  val: { color: colors.textSecondary, fontFamily: typography.display.fontFamily, fontSize: 12 },
  lbl: { color: colors.textDisabled, ...typography.label, fontSize: 8, marginTop: spacing.xs },
});
