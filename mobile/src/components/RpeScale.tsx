/**
 * Sélecteur RPE (1-10) avec fenêtre explicative au survol/à l'appui de chaque
 * chiffre — décrit le niveau et son intensité (Borg CR10 adaptée entraînement).
 * Le barème est aligné sur celui du backend (engines/coach_chat → RPE_SCALE).
 *
 * Web  : survol → fenêtre temporaire ; clic → sélection.
 * Natif: appui maintenu → fenêtre ; relâché → sélection.
 */
import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, spacing, typography } from '../theme/tokens';

export interface RpeLevel { value: number; label: string; zone: string; desc: string; }

export const RPE_SCALE: RpeLevel[] = [
  { value: 1, label: 'Très très facile', zone: 'Récupération', desc: 'Effort à peine perceptible, conversation sans aucune gêne.' },
  { value: 2, label: 'Très facile', zone: 'Récupération', desc: 'Footing de décrassage, tu pourrais tenir des heures.' },
  { value: 3, label: 'Facile', zone: 'Endurance Z1-Z2', desc: 'Confortable, respiration libre, phrases complètes.' },
  { value: 4, label: 'Modéré', zone: 'Endurance Z2', desc: 'Soutenu mais maîtrisé, conversation par phrases courtes.' },
  { value: 5, label: 'Modéré +', zone: 'Tempo / Z3 bas', desc: 'Ça pousse, respiration plus marquée.' },
  { value: 6, label: 'Difficile', zone: 'Tempo / Z3', desc: 'Inconfort net, quelques mots entre deux respirations.' },
  { value: 7, label: 'Très difficile', zone: 'Seuil / Z4', desc: 'Dur. En force : ~3-4 reps en réserve (RIR). Tu ne parles plus.' },
  { value: 8, label: 'Très très difficile', zone: 'Seuil haut / Z4-Z5', desc: 'Très exigeant. En force : ~2 reps en réserve. Halètement.' },
  { value: 9, label: 'Quasi maximal', zone: 'VO2max / Z5', desc: 'Proche de la limite. En force : 1 rep en réserve (RIR 1).' },
  { value: 10, label: 'Maximal', zone: 'Sprint / 1RM', desc: 'Effort total, rien en réserve. Réservé aux tests et finishers.' },
];

const RPE_BY_VALUE: Record<number, RpeLevel> = Object.fromEntries(
  RPE_SCALE.map(r => [r.value, r]),
);

export function RpeScale({ value, onChange, values = [4, 5, 6, 7, 8, 9, 10] }: {
  value: number;
  onChange: (v: number) => void;
  values?: number[];
}) {
  const [hover, setHover] = useState<number | null>(null);

  return (
    <View style={styles.row}>
      {values.map(n => {
        const r = RPE_BY_VALUE[n];
        const on = value === n;
        const showing = hover === n;
        return (
          <View key={n} style={styles.cell}>
            {showing && (
              <View style={styles.bubble} pointerEvents="none">
                <Text style={styles.bubbleTitle}>RPE {n} — {r.label}</Text>
                <Text style={styles.bubbleZone}>{r.zone}</Text>
                <Text style={styles.bubbleBody}>{r.desc}</Text>
                <View style={styles.arrow} />
              </View>
            )}
            <Pressable
              onPress={() => onChange(n)}
              onHoverIn={() => setHover(n)}
              onHoverOut={() => setHover(h => (h === n ? null : h))}
              onPressIn={() => setHover(n)}
              onPressOut={() => setHover(h => (h === n ? null : h))}
              accessibilityRole="button"
              accessibilityLabel={`RPE ${n}, ${r.label}. ${r.desc}`}
              style={[styles.chip, on && styles.chipOn]}>
              <Text style={[styles.text, on && styles.textOn]}>{n}</Text>
            </Pressable>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', justifyContent: 'space-between', gap: spacing.xs },
  cell: { flex: 1, position: 'relative' },
  chip: {
    paddingVertical: spacing.s, borderRadius: 6, backgroundColor: colors.bgElevated,
    alignItems: 'center', borderWidth: 1, borderColor: colors.hairline,
  },
  chipOn: { backgroundColor: colors.signalSoft, borderColor: colors.signal },
  text: { color: colors.textSecondary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.body },
  textOn: { color: colors.signal },
  bubble: {
    position: 'absolute', bottom: '100%', marginBottom: 10, width: 210,
    left: '50%', marginLeft: -105,
    backgroundColor: colors.bgElevated, borderRadius: 8, padding: spacing.s,
    borderWidth: 1, borderColor: colors.hairlineStrong, zIndex: 50,
    shadowColor: '#000', shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4, shadowRadius: 10, elevation: 8,
  },
  bubbleTitle: { color: colors.signal, ...typography.label, fontSize: 11, marginBottom: 2 },
  bubbleZone: { color: colors.readyYellow, fontSize: typography.sizes.micro, marginBottom: 3 },
  bubbleBody: { color: colors.textPrimary, fontSize: typography.sizes.small, lineHeight: 18 },
  arrow: {
    position: 'absolute', bottom: -6, left: '50%', marginLeft: -6,
    width: 0, height: 0, borderLeftWidth: 6, borderRightWidth: 6, borderTopWidth: 6,
    borderLeftColor: 'transparent', borderRightColor: 'transparent',
    borderTopColor: colors.hairlineStrong,
  },
});
