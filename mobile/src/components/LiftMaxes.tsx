/**
 * Éditeur des 1RM par mouvement → pilote les charges du 5/3/1 de CHAQUE
 * utilisateur (TM = 90% du 1RM). Saisie clavier (NumberField). À l'enregistrement,
 * le plan d'entraînement se recalcule avec ces valeurs.
 */
import React, { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { api } from '../api/client';
import { Card } from './ui';
import { NumberField } from './NumberField';
import { colors, spacing, typography } from '../theme/tokens';

const LIFTS: { key: string; label: string; def: number }[] = [
  { key: 'bench', label: 'Développé couché', def: 100 },
  { key: 'squat', label: 'Squat', def: 117 },
  { key: 'ohp', label: 'Presse militaire', def: 64 },
  { key: 'row', label: 'Rowing barre', def: 103 },
];

export function LiftMaxes() {
  const [maxes, setMaxes] = useState<Record<string, number>>(
    Object.fromEntries(LIFTS.map(l => [l.key, l.def])));
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    LIFTS.forEach(l => {
      api.lift1RM(l.key)
        .then(p => {
          const last = p.results?.slice(-1)[0]?.result_value;
          if (last) setMaxes(m => ({ ...m, [l.key]: last }));
        })
        .catch(() => {});
    });
  }, []);

  const save = async () => {
    setBusy(true);
    try {
      for (const l of LIFTS) await api.setLift1RM(l.key, maxes[l.key]);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch { /* hors connexion : réessaiera */ } finally { setBusy(false); }
  };

  return (
    <>
      <Text style={styles.section}>MES 1RM (CHARGES PERSONNALISÉES)</Text>
      <Card style={{ padding: spacing.m }}>
        <Text style={styles.hint}>
          Le plan force (5/3/1) calcule tes charges à partir de ces 1RM (Training
          Max = 90%). Appuie sur une valeur pour la taper au clavier.
        </Text>
        {LIFTS.map(l => (
          <View key={l.key} style={styles.row}>
            <Text style={styles.lbl}>{l.label}</Text>
            <NumberField value={maxes[l.key]} step={2.5} min={20} max={400} decimals={1}
              unit="kg" onChange={(v) => { setSaved(false); setMaxes(m => ({ ...m, [l.key]: v })); }} />
          </View>
        ))}
        {saved
          ? <Text style={styles.saved}>✓ 1RM enregistrés — ton plan est recalculé</Text>
          : (
            <Pressable onPress={save} disabled={busy} style={styles.saveBtn}>
              <Text style={styles.saveT}>{busy ? '…' : 'ENREGISTRER MES 1RM'}</Text>
            </Pressable>
          )}
      </Card>
    </>
  );
}

const styles = StyleSheet.create({
  section: { color: colors.textSecondary, ...typography.label, marginTop: spacing.l, marginBottom: spacing.s },
  hint: { color: colors.textDisabled, fontSize: typography.sizes.micro, lineHeight: 16, marginBottom: spacing.s },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: spacing.s, borderTopWidth: 1, borderTopColor: colors.hairline },
  lbl: { color: colors.textPrimary, fontSize: typography.sizes.small, flex: 1, paddingRight: spacing.s },
  saveBtn: { marginTop: spacing.m, paddingVertical: 14, borderRadius: spacing.cardRadius, backgroundColor: colors.signal, alignItems: 'center' },
  saveT: { color: colors.bg, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2, letterSpacing: 1 },
  saved: { color: colors.signal, textAlign: 'center', fontSize: typography.sizes.small, paddingVertical: 14 },
});
