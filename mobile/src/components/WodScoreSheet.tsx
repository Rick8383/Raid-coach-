/**
 * Fenêtre de saisie du score d'un WOD (fin de chrono, ou correction depuis
 * l'agenda). Temps, reps/rounds, distance, time cap, note — puis retour
 * HONNÊTE du serveur sur la performance (comparaison aux tentatives passées).
 */
import React, { useState } from 'react';
import { Modal, Pressable, ScrollView, StyleSheet, Switch, Text, TextInput, View } from 'react-native';
import { NumberField } from './NumberField';
import { colors, spacing, typography } from '../theme/tokens';

export type ScoreMode = 'for_time' | 'amrap';

// Formats dont le score est un TEMPS ; tout le reste se score en reps/rounds.
export const TIME_FORMATS = new Set([
  'for_time', 'rft', 'chipper', 'pyramid_asc', 'pyramid_desc', 'pyramid_full',
]);

/** Mode de score attendu pour un format de WOD donné. */
export function modeForFormatKey(key?: string | null): ScoreMode {
  return key && TIME_FORMATS.has(key) ? 'for_time' : 'amrap';
}

export interface WodScoreInput {
  mode: ScoreMode;
  time_sec: number;
  reps: number;
  rounds?: number;
  distance_m?: number;
  capped: boolean;
  cap_sec: number;
  notes?: string;
}

export interface WodAssessment {
  verdict: string;
  comment: string;
  reference: string | null;
  delta_pct: number | null;
}

const VERDICT_COLOR: Record<string, string> = {
  record: colors.signal,
  'référence posée': colors.fitness,
  stable: colors.readyYellow,
  'en retrait': colors.readyOrange,
  'non terminé': colors.readyOrange,
  'score manquant': colors.readyRed,
};

export function WodScoreSheet({ visible, title, initial, onSubmit, onClose }: {
  visible: boolean;
  title: string;
  initial: WodScoreInput;
  /** Enregistre et renvoie le commentaire de performance (null si échec). */
  onSubmit: (s: WodScoreInput) => Promise<WodAssessment | null>;
  onClose: () => void;
}) {
  const [mode, setMode] = useState<ScoreMode>(initial.mode);
  const [min, setMin] = useState(Math.floor((initial.time_sec || 0) / 60));
  const [sec, setSec] = useState((initial.time_sec || 0) % 60);
  const [reps, setReps] = useState(initial.reps || 0);
  const [rounds, setRounds] = useState(initial.rounds ?? 0);
  const [distance, setDistance] = useState(initial.distance_m ?? 0);
  const [capped, setCapped] = useState(!!initial.capped);
  const [notes, setNotes] = useState(initial.notes ?? '');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<WodAssessment | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setBusy(true); setError(null);
    try {
      const a = await onSubmit({
        mode,
        time_sec: Math.max(0, min * 60 + sec),
        reps,
        rounds: rounds > 0 ? rounds : undefined,
        distance_m: distance > 0 ? distance : undefined,
        capped,
        cap_sec: initial.cap_sec,
        notes: notes.trim() || undefined,
      });
      if (a) setResult(a); else onClose();
    } catch {
      setError('Enregistrement impossible — réessaie une fois en ligne.');
    } finally { setBusy(false); }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <ScrollView contentContainerStyle={{ padding: spacing.l }}>
            <Text style={styles.title}>SCORE — {title}</Text>

            {result ? (
              <View>
                <Text style={[styles.verdict, { color: VERDICT_COLOR[result.verdict] ?? colors.textPrimary }]}>
                  {result.verdict.toUpperCase()}
                </Text>
                <Text style={styles.comment}>{result.comment}</Text>
                {!!result.reference && (
                  <Text style={styles.ref}>Référence précédente : {result.reference}</Text>
                )}
                <Pressable onPress={onClose} style={styles.primaryBtn}>
                  <Text style={styles.primaryT}>FERMER</Text>
                </Pressable>
              </View>
            ) : (
              <View>
                <Text style={styles.lbl}>TYPE DE SCORE</Text>
                <View style={styles.row}>
                  {(['for_time', 'amrap'] as const).map(m => (
                    <Pressable key={m} onPress={() => setMode(m)}
                      style={[styles.modeBtn, mode === m && styles.modeBtnOn]}>
                      <Text style={[styles.modeT, mode === m && styles.modeTOn]}>
                        {m === 'for_time' ? 'FOR TIME (chrono)' : 'AMRAP (reps/rounds)'}
                      </Text>
                    </Pressable>
                  ))}
                </View>

                <Text style={styles.lbl}>TEMPS RÉALISÉ</Text>
                <View style={styles.row}>
                  <View style={styles.half}>
                    <NumberField value={min} step={1} min={0} max={240} unit="min" onChange={setMin} />
                  </View>
                  <View style={styles.half}>
                    <NumberField value={sec} step={5} min={0} max={59} unit="s" onChange={setSec} />
                  </View>
                </View>

                <Text style={styles.lbl}>REPS / ROUNDS (0 si non concerné)</Text>
                <View style={styles.row}>
                  <View style={styles.half}>
                    <NumberField value={reps} step={1} min={0} max={100000} unit="reps" onChange={setReps} />
                  </View>
                  <View style={styles.half}>
                    <NumberField value={rounds} step={1} min={0} max={1000} unit="tours" onChange={setRounds} />
                  </View>
                </View>

                <Text style={styles.lbl}>DISTANCE (0 si non concerné)</Text>
                <NumberField value={distance} step={100} min={0} max={200000} unit="m" onChange={setDistance} />

                <View style={styles.switchRow}>
                  <Text style={styles.switchLbl}>Time cap atteint (WOD non terminé)</Text>
                  <Switch value={capped} onValueChange={setCapped}
                    trackColor={{ true: colors.readyOrange, false: colors.hairline }} />
                </View>

                <Text style={styles.lbl}>NOTE (optionnel)</Text>
                <TextInput style={styles.input} value={notes} onChangeText={setNotes}
                  placeholder="Ressenti, scaling, matériel…"
                  placeholderTextColor={colors.textDisabled} multiline />

                {!!error && <Text style={styles.err}>{error}</Text>}
                <Pressable onPress={submit} disabled={busy}
                  style={[styles.primaryBtn, busy && { opacity: 0.5 }]}>
                  <Text style={styles.primaryT}>{busy ? '…' : 'ENREGISTRER LE SCORE'}</Text>
                </Pressable>
                <Pressable onPress={onClose} style={styles.cancelBtn}>
                  <Text style={styles.cancelT}>Annuler</Text>
                </Pressable>
              </View>
            )}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.75)', justifyContent: 'flex-end' },
  sheet: {
    backgroundColor: colors.bgElevated, borderTopLeftRadius: 18, borderTopRightRadius: 18,
    maxHeight: '90%', borderTopWidth: 1, borderColor: colors.hairline,
  },
  title: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2, marginBottom: spacing.m },
  lbl: { color: colors.textSecondary, ...typography.label, fontSize: 10, marginTop: spacing.m, marginBottom: spacing.xs },
  row: { flexDirection: 'row', gap: spacing.s },
  half: { flex: 1 },
  modeBtn: { flex: 1, paddingVertical: spacing.s, borderRadius: 6, borderWidth: 1, borderColor: colors.hairlineStrong, alignItems: 'center' },
  modeBtnOn: { backgroundColor: colors.signalSoft, borderColor: colors.signal },
  modeT: { color: colors.textSecondary, ...typography.label, fontSize: 9, textAlign: 'center' },
  modeTOn: { color: colors.signal },
  switchRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: spacing.l },
  switchLbl: { color: colors.textPrimary, fontSize: typography.sizes.small, flex: 1, paddingRight: spacing.s },
  input: {
    color: colors.textPrimary, backgroundColor: colors.bgInput, borderRadius: spacing.cardRadius,
    paddingHorizontal: spacing.m, paddingVertical: spacing.s, fontSize: typography.sizes.body,
    borderWidth: 1, borderColor: colors.hairline, minHeight: 44,
  },
  primaryBtn: {
    marginTop: spacing.l, paddingVertical: 14, borderRadius: spacing.cardRadius,
    backgroundColor: colors.signalSoft, borderWidth: 1, borderColor: colors.signal, alignItems: 'center',
  },
  primaryT: { color: colors.signal, ...typography.label, fontSize: 11 },
  cancelBtn: { paddingVertical: spacing.m, alignItems: 'center' },
  cancelT: { color: colors.textSecondary, fontSize: typography.sizes.small },
  verdict: { fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h1, marginBottom: spacing.s },
  comment: { color: colors.textPrimary, fontSize: typography.sizes.body, lineHeight: 22 },
  ref: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: spacing.s },
  err: { color: colors.readyRed, fontSize: typography.sizes.small, marginTop: spacing.s },
});
