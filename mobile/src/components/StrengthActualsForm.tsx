/**
 * Saisie des SÉRIES RÉELLEMENT RÉALISÉES sur une séance de force (reps × charge
 * par série), pré-remplie depuis les mouvements principaux 5/3/1 puis modifiable.
 * Calcule un 1RM estimé (Epley) par mouvement → le plan s'appuie ensuite sur ces
 * charges réelles. Rattaché au profil courant (isolation par utilisateur).
 *
 * Une séance peut porter DEUX mouvements principaux (« haut du corps » =
 * développé + rowing, en grande semaine) : chacun a son bloc de saisie.
 */
import React, { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Strength531 } from '../api/client';
import { NumberField } from './NumberField';
import { colors, spacing, typography } from '../theme/tokens';

export type PerformedSet = { reps: number; load_kg: number; top: boolean };
export type PerformedLift = { lift: string; sets: PerformedSet[]; est_1rm: number };
/** Un seul mouvement principal → forme simple ; séance combinée → { lifts }. */
export type Performed = PerformedLift | { lifts: PerformedLift[] };

/** Normalise les deux formes en une liste de mouvements. */
export function performedEntries(p: Performed | null | undefined): PerformedLift[] {
  if (!p) return [];
  if ('lifts' in p) return Array.isArray(p.lifts) ? p.lifts : [];
  return p.lift ? [p] : [];
}

function pack(lifts: PerformedLift[]): Performed {
  return lifts.length > 1 ? { lifts } : lifts[0];
}

// 1RM estimé (Epley) : charge × (1 + reps/30). On prend la meilleure série.
export function estimate1RM(sets: PerformedSet[]): number {
  const best = Math.max(0, ...sets.map(s => (s.load_kg > 0 && s.reps > 0 ? s.load_kg * (1 + s.reps / 30) : 0)));
  return Math.round(best * 2) / 2; // arrondi 0,5 kg
}

function toReps(s: string | undefined): number {
  const n = parseInt(String(s ?? '').replace(/\D/g, ''), 10);
  return Number.isFinite(n) && n > 0 ? n : 5;
}

function plannedLifts(detail: Strength531 | undefined): PerformedLift[] {
  const mains = detail?.main_lifts?.length
    ? detail.main_lifts
    : detail?.main_lift ? [detail.main_lift] : [];
  const out = mains
    .filter(l => l?.sets?.length)
    .map(l => {
      const sets = l.sets.map(st => ({ reps: toReps(st.reps), load_kg: st.load_kg, top: !!st.amrap }));
      return { lift: l.name, sets, est_1rm: estimate1RM(sets) };
    });
  if (out.length) return out;
  const sets = [{ reps: 5, load_kg: 0, top: false }, { reps: 3, load_kg: 0, top: false },
                { reps: 5, load_kg: 0, top: true }];
  return [{ lift: 'Mouvement principal', sets, est_1rm: 0 }];
}

function LiftBlock({ entry, showName, onChange }: {
  entry: PerformedLift; showName: boolean; onChange: (sets: PerformedSet[]) => void;
}) {
  const { sets } = entry;
  const setField = (i: number, k: keyof PerformedSet, v: number | boolean) =>
    onChange(sets.map((s, j) => (j === i ? { ...s, [k]: v } : s)));
  const addSet = () =>
    onChange([...sets, { reps: 5, load_kg: sets[sets.length - 1]?.load_kg ?? 0, top: false }]);
  const removeSet = (i: number) => onChange(sets.filter((_, j) => j !== i));
  const setTop = (i: number) => onChange(sets.map((s, j) => ({ ...s, top: j === i })));

  return (
    <View style={showName ? styles.liftBlock : undefined}>
      {showName && <Text style={styles.liftName}>{entry.lift}</Text>}
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
      {entry.est_1rm > 0 && (
        <View style={styles.estBox}>
          <Text style={styles.estT}>1RM estimé{showName ? ` · ${entry.lift}` : ''}</Text>
          <Text style={styles.estV}>≈ {entry.est_1rm.toFixed(1).replace('.', ',')} kg</Text>
        </View>
      )}
    </View>
  );
}

export function StrengthActualsForm({ detail, onChange }: {
  detail: Strength531 | undefined;
  onChange: (p: Performed) => void;
}) {
  const [lifts, setLifts] = useState<PerformedLift[]>(() => plannedLifts(detail));

  // Émet l'état pré-rempli dès l'ouverture : enregistrer SANS rien modifier
  // sauvegarde bien les séries affichées.
  useEffect(() => { onChange(pack(lifts)); }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  const update = (li: number, sets: PerformedSet[]) => {
    const next = lifts.map((l, j) =>
      j === li ? { ...l, sets, est_1rm: estimate1RM(sets) } : l);
    setLifts(next);
    onChange(pack(next));
  };

  return (
    <View style={styles.box}>
      <Text style={styles.intro}>
        Recopie ce que tu as vraiment fait (reps × charge par série). Marque la
        série « max ». Ces charges servent à calculer tes prochaines séances.
      </Text>
      {lifts.map((entry, i) => (
        <LiftBlock key={entry.lift + i} entry={entry} showName={lifts.length > 1}
          onChange={sets => update(i, sets)} />
      ))}
    </View>
  );
}

// Rendu compact des séries réalisées (suivi/historique).
export function PerformedView({ p }: { p: Performed }) {
  const entries = performedEntries(p).filter(e => e.sets?.length);
  if (!entries.length) return null;
  return (
    <View style={styles.viewBox}>
      {entries.map((e, k) => (
        <View key={k}>
          <Text style={styles.viewTag}>🏋 SÉRIES RÉALISÉES · {e.lift}</Text>
          <View style={styles.chips}>
            {e.sets.map((s, i) => (
              <Text key={i} style={[styles.chip, s.top && styles.chipTop]}>
                {s.reps}×{s.load_kg.toFixed(s.load_kg % 1 ? 1 : 0).replace('.', ',')}kg{s.top ? ' (max)' : ''}
              </Text>
            ))}
          </View>
          {e.est_1rm > 0 && (
            <Text style={styles.viewEst}>1RM estimé ≈ {e.est_1rm.toFixed(1).replace('.', ',')} kg</Text>
          )}
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  box: { marginTop: spacing.s },
  intro: { color: colors.textSecondary, fontSize: typography.sizes.small, lineHeight: 18, marginBottom: spacing.s },
  liftBlock: {
    borderLeftWidth: 2, borderLeftColor: colors.signal, paddingLeft: spacing.s,
    marginBottom: spacing.m,
  },
  liftName: { color: colors.signal, ...typography.label, fontSize: 11, marginBottom: spacing.xs },
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
