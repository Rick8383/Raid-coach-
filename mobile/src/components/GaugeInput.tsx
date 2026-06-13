/**
 * Saisie 0-100 compatible web ET natif (remplace @react-native-community/slider,
 * qui ne rend pas de façon fiable sur navigateur). Barre tactile + boutons ±.
 */
import React from 'react';
import { LayoutChangeEvent, Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, spacing, typography } from '../theme/tokens';

export function GaugeInput({ label, value, onChange, step = 5, color = colors.signal }: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  step?: number;
  color?: string;
}) {
  const [width, setWidth] = React.useState(0);
  const clamp = (v: number) => Math.max(0, Math.min(100, Math.round(v / step) * step));

  const onLayout = (e: LayoutChangeEvent) => setWidth(e.nativeEvent.layout.width);
  const onPressBar = (x: number) => {
    if (width > 0) onChange(clamp((x / width) * 100));
  };

  return (
    <View style={styles.root}>
      <View style={styles.header}>
        <Text style={styles.label}>{label}</Text>
        <Text style={styles.value}>{value}</Text>
      </View>
      <View style={styles.row}>
        <Pressable onPress={() => onChange(clamp(value - step))} hitSlop={8} style={styles.btn}>
          <Text style={styles.btnText}>–</Text>
        </Pressable>
        <Pressable
          style={styles.track}
          onLayout={onLayout}
          onPress={(e) => onPressBar(e.nativeEvent.locationX)}>
          <View style={[styles.fill, { width: `${value}%`, backgroundColor: color }]} />
          <View style={[styles.thumb, { left: `${value}%`, borderColor: color }]} />
        </Pressable>
        <Pressable onPress={() => onChange(clamp(value + step))} hitSlop={8} style={styles.btn}>
          <Text style={styles.btnText}>+</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { marginBottom: spacing.l },
  header: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: spacing.s },
  label: { color: colors.textSecondary, ...typography.label },
  value: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2 },
  row: { flexDirection: 'row', alignItems: 'center', gap: spacing.m },
  btn: {
    width: 38, height: 38, borderRadius: 19, backgroundColor: colors.bgElevated,
    borderWidth: 1, borderColor: colors.hairlineStrong, alignItems: 'center', justifyContent: 'center',
  },
  btnText: { color: colors.signal, fontSize: 22, fontFamily: typography.display.fontFamily },
  track: { flex: 1, height: 10, borderRadius: 5, backgroundColor: colors.hairline, justifyContent: 'center' },
  fill: { height: 10, borderRadius: 5 },
  thumb: {
    position: 'absolute', width: 18, height: 18, borderRadius: 9, marginLeft: -9,
    backgroundColor: colors.textPrimary, borderWidth: 2,
  },
});
