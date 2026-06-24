/**
 * Champ numérique : boutons +/− ET saisie clavier (on appuie sur la valeur, on
 * tape au clavier du téléphone). Compatible web et natif.
 */
import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View, ViewStyle } from 'react-native';
import { colors, spacing, typography } from '../theme/tokens';

export function NumberField({ value, onChange, step = 1, min = 0, max = 9999,
  decimals = 0, unit, style }: {
  value: number;
  onChange: (v: number) => void;
  step?: number;
  min?: number;
  max?: number;
  decimals?: number;
  unit?: string;
  style?: ViewStyle;
}) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState('');

  const clamp = (v: number) => Math.max(min, Math.min(max, v));
  const fmt = (v: number) => (decimals > 0 ? v.toFixed(decimals) : String(Math.round(v)));

  const commit = () => {
    const v = parseFloat(text.replace(',', '.'));
    if (!isNaN(v)) onChange(clamp(decimals > 0 ? +v.toFixed(decimals) : Math.round(v)));
    setEditing(false);
  };

  return (
    <View style={[styles.row, style]}>
      <Pressable onPress={() => onChange(clamp(+(value - step).toFixed(decimals)))}
        hitSlop={8} style={styles.btn}>
        <Text style={styles.btnT}>–</Text>
      </Pressable>
      {editing ? (
        <TextInput
          style={styles.input}
          value={text}
          onChangeText={setText}
          onBlur={commit}
          onSubmitEditing={commit}
          keyboardType="decimal-pad"
          autoFocus
          selectTextOnFocus
          returnKeyType="done"
        />
      ) : (
        <Pressable onPress={() => { setText(fmt(value)); setEditing(true); }} style={styles.valueBox}>
          <Text style={styles.value}>{fmt(value)}{unit ? <Text style={styles.unit}> {unit}</Text> : null}</Text>
        </Pressable>
      )}
      <Pressable onPress={() => onChange(clamp(+(value + step).toFixed(decimals)))}
        hitSlop={8} style={styles.btn}>
        <Text style={styles.btnT}>+</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: spacing.m },
  btn: {
    width: 38, height: 38, borderRadius: 19, backgroundColor: colors.bgElevated,
    borderWidth: 1, borderColor: colors.hairlineStrong, alignItems: 'center', justifyContent: 'center',
  },
  btnT: { color: colors.signal, fontSize: 22, fontFamily: typography.display.fontFamily },
  valueBox: { minWidth: 80, alignItems: 'center', paddingVertical: 4 },
  value: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2 },
  unit: { color: colors.textSecondary, fontSize: typography.sizes.small },
  input: {
    minWidth: 80, textAlign: 'center', color: colors.textPrimary,
    fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2,
    borderBottomWidth: 2, borderBottomColor: colors.signal, paddingVertical: 2,
  },
});
