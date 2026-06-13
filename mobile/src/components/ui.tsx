/** Primitives UI partagées — cohérence et finition "tableau de bord opérationnel". */
import React from 'react';
import { Pressable, StyleSheet, Text, View, ViewStyle } from 'react-native';
import { colors, elevation, spacing, typography } from '../theme/tokens';

export function Tag({ label, color = colors.textSecondary, filled = false }:
  { label: string; color?: string; filled?: boolean }) {
  return (
    <View style={[
      styles.tag,
      filled ? { backgroundColor: color } : { borderColor: color, borderWidth: 1 },
    ]}>
      <Text style={[styles.tagText, { color: filled ? colors.bg : color }]}>{label}</Text>
    </View>
  );
}

export function Card({ children, style }: { children: React.ReactNode; style?: ViewStyle }) {
  return <View style={[styles.card, elevation.card, style]}>{children}</View>;
}

export function SectionTitle({ children }: { children: React.ReactNode }) {
  return <Text style={styles.sectionTitle}>{children}</Text>;
}

export function PrimaryButton({ label, onPress, disabled }:
  { label: string; onPress: () => void; disabled?: boolean }) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      accessibilityRole="button"
      style={({ pressed }) => [
        styles.primary,
        pressed && styles.primaryPressed,
        disabled && styles.primaryDisabled,
      ]}>
      <Text style={styles.primaryText}>{label}</Text>
    </Pressable>
  );
}

export function GhostButton({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} accessibilityRole="button"
      style={({ pressed }) => [styles.ghost, pressed && { opacity: 0.6 }]}>
      <Text style={styles.ghostText}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  tag: {
    paddingHorizontal: spacing.s, paddingVertical: 3, borderRadius: 4,
    alignSelf: 'flex-start',
  },
  tagText: { ...typography.label, fontSize: 10, letterSpacing: 1 },
  card: {
    backgroundColor: colors.bgCard, borderRadius: spacing.cardRadius,
    overflow: 'hidden',
  },
  sectionTitle: {
    color: colors.textSecondary, ...typography.label,
    marginBottom: spacing.s, marginTop: spacing.l,
  },
  primary: {
    backgroundColor: colors.signal, borderRadius: spacing.cardRadius,
    paddingVertical: 16, alignItems: 'center',
  },
  primaryPressed: { backgroundColor: colors.signalDim },
  primaryDisabled: { backgroundColor: colors.hairlineStrong },
  primaryText: {
    color: colors.bg, fontFamily: typography.display.fontFamily,
    fontSize: typography.sizes.h2, letterSpacing: 1,
  },
  ghost: { paddingVertical: 14, alignItems: 'center' },
  ghostText: {
    color: colors.textSecondary, ...typography.label, letterSpacing: 1.5,
  },
});
