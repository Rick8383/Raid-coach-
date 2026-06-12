/** Signature visuelle : liseré readiness vertical sur le bord gauche des cartes. */
import React from 'react';
import { View } from 'react-native';
import { ReadinessLevel, readinessColor, spacing } from '../theme/tokens';

export function ReadinessBar({ level }: { level: ReadinessLevel }) {
  return (
    <View style={{ width: spacing.readinessBar, backgroundColor: readinessColor(level) }} />
  );
}
