/**
 * Saisie des SÉRIES RÉELLEMENT RÉALISÉES sur une séance de force (reps × charge
 * par série), pré-remplie depuis le mouvement principal 5/3/1 puis modifiable.
 * Calcule un 1RM estimé (Epley) à partir de la meilleure série → utile pour la
 * progression. Rattaché au profil courant (isolation par utilisateur).
 */
import React, { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Strength531 } from '../api/client';
import { NumberField } from './NumberField';
import { colors, spacing, typography } from '../theme/tokens';

export type PerformedSet = { reps: number; load_kg: number; top: boolean };
export type Performed = { lift: string; sets: PerformedSet[]; est_1rm: number };

// 1RM estimé (Epley) : charge × (1 + reps/30). On prend la meilleure série.
export function estimate1RM(sets: PerformedSet[]): number {
  const best = Math.max(0, ...sets.map(s => (s.load_kg > 0 && s.reps > 0 ? s.load_kg * (1 + s.reps / 30) : 0)));
  return Math.round(best * 2) / 2; // arrondi 0,5 kg
}

function toReps(s: string | undefined): number {
  const n = parseInt(String(s ?? '').replace(/\D/g, ''), 10);
  return Number.isFinite(n) && n > 0 ? n : 5;
}

function plannedSets(detail: Strength531 | undefined): { name: string; sets: PerformedSet[] } {
  const lift = detail?.main_lift ?? detail?.main_lifts?.[0];
  if (lift?.sets?.length) {
    return {
      name: lift.name,
      sets: lift.sets.map(st => ({ reps: toReps(st.reps), load_kg: st.load_kg, top: !!st.amrap })),
    };
  }
  return { name: 'Mouvement principal', sets: [
    { reps: 5, load_kg: 0, top: false }, { reps: 3, load_kg: 0, top: false },
    { reps: 5, load_kg: 0, top: true },
  ] };
}

export function StrengthActualsForm({ detail, onChange }: {
  detail: Strength531 | undefined;
  onChange: (p: Performed) => void;
}) {
  const init = plannedSets(detail);
  const [lift] = useState(init.name);
  const [sets, setSets] = useState<PerformedSet[]>(init.sets);

  // Émet l'état pré-rempli dès l'ouverture : enregistrer SANS rien modifier
  // sauvegarde bien les séries affichées (sinon performed restait null).
  useEffect(() => {
    onChange({ lift, sets, est_1rm: estimate1RM(sets) });
  }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  const emit = (next: PerformedSet[]) => {
    setSets(next);
    onChange({ lift, sets: next, est_1rm: estimate1RM(next) });
  };
  const setField = (i: number, k: keyof PerformedSet, v: number | boolean) =>
    emit(sets.map((s, j) => (j === i ? { ...s, [k]: v } : s)));
  const addSet = () => emit([...sets, { reps: 5, load_kg: sets[sets.length - 1]?.load_kg ?? 0, top: false }]);
  const removeSet = (i: number) => emit(sets.filter((_, j) => j !== i));
  const setTop = (i: number) => emit(sets.map((s, j) => ({ ...s, top: j === i })));

  const est = estimate1RM(sets);
  return (
    <View style={styles.box}>
      <Text style={styles.intro}>
        {lift} — recopie ce que tu as vraiment fait (reps × charge par série).
        Marque la série « max » (dernière au maximum de reps).
      </Text>
      {sets.map((s, i) => (
        <View key={i} style={styles.setRow}>
          <Text style={styles.setNum}>{i + 1}</Text>
          <View style={styles.field}>
            <NumberField value={s.reps} step={1} min={0} max={50} unit="reps"
              onChange={v => setField(i, 'reps', v)} />
          </View>
          <View style={styles.field}>
            <NumberField value={s.load_kg} step={2.5} min={0} max={400} decimals={1} unit="kg"
              onChange={v => setField(i, 'load_kg', v)} />
          </View>
          <Pressable onPress={() => setTop(i)} hitSlop={6}
            style={[styles.topBtn, s.top && styles.topBtnOn]}>
            <Text style={[styles.topT, s.top && styles.topTOn]}>max</Text>
          </Pressable>
          {sets.length > 1 && (
            <Pressable onPress={() => removeSet(i)} hitSlop={6} style={styles.del}>
              <Text style={styles.delT}>✕</Text>
            </Pressable>
          )}
        </View>
      ))}
      <Pressable onPress={addSet} style={styles.addBtn}>
        <Text style={styles.addT}>＋ Ajouter une série</Text>
      </Pressable>
      {est > 0 && (
        <View style={styles.estBox}>
          <Text style={styles.estT}>1RM estimé</Text>
          <Text style={styles.estV}>≈ {est.toFixed(1).replace('.', ',')} kg</Text>
        </View>
      )}
    </View>
  );
}

// Rendu compact des séries réalisées (suivi/historique).
export function PerformedView({ p }: { p: Performed }) {
  if (!p?.sets?.length) return null;
  return (
    <View style={styles.viewBox}>
      <Text style={styles.viewTag}>🏋 SÉRIES RÉALISÉES · {p.lift}</Text>
      <View style={styles.chips}>
        {p.sets.map((s, i) => (
          <Text key={i} style={[styles.chip, s.top && styles.chipTop]}>
            {s.reps}×{s.load_kg.toFixed(s.load_kg % 1 ? 1 : 0).replace('.', ',')}kg{s.top ? ' (max)' : ''}
          </Text>
        ))}
      </View>
      {p.est_1rm > 0 && <Text style={styles.viewEst}>1RM estimé ≈ {p.est_1rm.toFixed(1).replace('.', ',')} kg</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  box: { marginTop: spacing.s },
  intro: { color: colors.textSecondary, fontSize: typography.sizes.small, lineHeight: 18, marginBottom: spacing.s },
  setRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs, paddingVertical: 3 },
  setNum: {
    width: 20, height: 20, borderRadius: 10, textAlign: 'center', lineHeight: 20,
    backgroundColor: colors.signalSoft, color: colors.signal,
    fontFamily: typography.display.fontFamily, fontSize: 11, overflow: 'hidden',
  },
  field: { flex: 1 },
  topBtn: { paddingHorizontal: spacing.s, paddingVertical: 4, borderRadius: 6, borderWidth: 1, borderColor: colors.hairline },
  topBtnOn: { backgroundColor: colors.signalSoft, borderColor: colors.signal },
  topT: { color: colors.textSecondary, ...typography.label, fontSize: 9 },
  topTOn: { color: colors.signal },
  del: { paddingHorizontal: 4 },
  delT: { color: colors.textDisabled, fontSize: 14 },
  addBtn: { paddingVertical: spacing.s, alignItems: 'center' },
  addT: { color: colors.signal, fontSize: typography.sizes.small, ...typography.bodyBold },
  estBox: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    marginTop: spacing.s, backgroundColor: colors.signalSoft, borderRadius: 8, padding: spacing.s,
  },
  estT: { color: colors.textSecondary, ...typography.label, fontSize: 10 },
  estV: { color: colors.signal, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2 },
  viewBox: { marginTop: spacing.s, backgroundColor: colors.signalSoft, borderRadius: 10, padding: spacing.s, gap: spacing.xs },
  viewTag: { color: colors.signal, ...typography.label, fontSize: 10 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs },
  chip: {
    color: colors.textPrimary, fontSize: typography.sizes.small,
    backgroundColor: colors.bgCard, borderRadius: 6, paddingHorizontal: spacing.s, paddingVertical: 3, overflow: 'hidden',
  },
  chipTop: { color: colors.signal, borderWidth: 1, borderColor: colors.signal },
  viewEst: { color: colors.signal, fontSize: typography.sizes.small, ...typography.bodyBold },
});
