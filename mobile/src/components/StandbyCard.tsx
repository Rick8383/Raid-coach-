/**
 * Mode standby / vacances — configuré dans Profil, par athlète.
 *  - PAUSE   : pas de salle / pas le temps → plan gelé, puis semaine de reprise
 *              progressive et plan repris exactement là où il s'était arrêté.
 *  - VACANCES: plus de temps → bloc intensif (salle complète), 1 ou 2 séances/j.
 * La fenêtre est définie par « départ dans N jours » + « durée ». À l'échéance,
 * le plan normal reprend tout seul.
 */
import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { StandbyState, api } from '../api/client';
import { Card } from './ui';
import { colors, spacing, typography } from '../theme/tokens';
import { todayLocalAsUTC } from '../schedule';

const DAY_MS = 24 * 3600 * 1000;

function isoInDays(n: number): string {
  const t = todayLocalAsUTC();   // date CALENDRIER LOCAL (pas UTC)
  return new Date(Date.UTC(t.getUTCFullYear(), t.getUTCMonth(), t.getUTCDate()) + n * DAY_MS)
    .toISOString().slice(0, 10);
}
function frDate(iso: string): string {
  return `${iso.slice(8)}/${iso.slice(5, 7)}`;
}

type Mode = 'pause' | 'vacation';

export function StandbyCard() {
  const [state, setState] = useState<StandbyState | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const [mode, setMode] = useState<Mode>('pause');
  const [startIn, setStartIn] = useState(0);    // départ dans N jours
  const [duration, setDuration] = useState(7);  // durée en jours
  const [spd, setSpd] = useState(1);            // séances/jour (vacances)

  const load = () => api.getStandby().then(setState).catch(() => setState(null)).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);

  const activate = async () => {
    setBusy(true);
    try {
      const start = isoInDays(startIn);
      const end = isoInDays(startIn + Math.max(1, duration) - 1);
      const next = await api.setStandby({
        mode, start_date: start, end_date: end,
        sessions_per_day: mode === 'vacation' ? spd : 1, equipment: 'gym',
      });
      setState(next);
    } catch { /* hors connexion : réessaiera */ } finally { setBusy(false); }
  };

  const cancel = async () => {
    setBusy(true);
    try { setState(await api.clearStandby()); } catch { /* ignore */ } finally { setBusy(false); }
  };

  if (loading) {
    return (
      <>
        <Text style={styles.section}>MODE VACANCES / STANDBY</Text>
        <Card style={{ padding: spacing.m }}><ActivityIndicator color={colors.signal} /></Card>
      </>
    );
  }

  const active = state?.mode === 'pause' || state?.mode === 'vacation';

  return (
    <>
      <Text style={styles.section}>MODE VACANCES / STANDBY</Text>
      <Card style={{ padding: spacing.m }}>
        {active ? (
          <View>
            <Text style={[styles.activeTag, { color: state!.mode === 'pause' ? colors.readyYellow : colors.signal }]}>
              {state!.mode === 'pause' ? '⏸ PAUSE ACTIVE' : '🏝 MODE VACANCES ACTIF'}
            </Text>
            <Text style={styles.activeDates}>
              du {frDate(state!.start_date!)} au {frDate(state!.end_date!)}
              {state!.mode === 'vacation' && state!.params?.sessions_per_day
                ? ` · ${state!.params.sessions_per_day} séance(s)/jour` : ''}
            </Text>
            <Text style={styles.note}>
              {state!.mode === 'pause'
                ? "Le plan est en pause. À ton retour : une semaine de reprise progressive, puis le plan reprend là où il s'était arrêté (aucun cycle perdu)."
                : 'Bloc intensif salle complète sur la fenêtre. Le plan normal reprend à la fin.'}
            </Text>
            <Pressable onPress={cancel} disabled={busy} style={styles.cancelBtn}>
              <Text style={styles.cancelT}>ANNULER LE MODE</Text>
            </Pressable>
          </View>
        ) : (
          <View>
            {/* Choix du mode */}
            <View style={styles.modeRow}>
              {([['pause', 'PAUSE (pas de salle / temps)'], ['vacation', 'VACANCES (plus de temps)']] as const).map(([m, label]) => (
                <Pressable key={m} onPress={() => setMode(m)} style={[styles.modeBtn, mode === m && styles.modeBtnOn]}>
                  <Text style={[styles.modeT, mode === m && styles.modeTOn]}>{label}</Text>
                </Pressable>
              ))}
            </View>

            <Text style={styles.note}>
              {mode === 'pause'
                ? "Plan gelé pendant l'absence. Au retour : 1 semaine de reprise progressive (deload), puis reprise exactement là où tu t'étais arrêté."
                : 'Bloc intensif en salle complète, orienté RAID (course/force/WOD cohérents, anti-lombaire) sur toute la fenêtre.'}
            </Text>

            <Stepper label="DÉPART DANS" value={`${startIn} j`} onMinus={() => setStartIn(v => Math.max(0, v - 1))} onPlus={() => setStartIn(v => Math.min(120, v + 1))} hint={`(${frDate(isoInDays(startIn))})`} />
            <Stepper label="DURÉE" value={`${duration} j`} onMinus={() => setDuration(v => Math.max(1, v - 1))} onPlus={() => setDuration(v => Math.min(28, v + 1))} hint={`→ ${frDate(isoInDays(startIn + duration - 1))}`} />

            {mode === 'vacation' && (
              <View style={styles.spdRow}>
                <Text style={styles.stepLbl}>SÉANCES / JOUR</Text>
                <View style={styles.spdBtns}>
                  {[1, 2].map(n => (
                    <Pressable key={n} onPress={() => setSpd(n)} style={[styles.spdBtn, spd === n && styles.spdBtnOn]}>
                      <Text style={[styles.spdT, spd === n && styles.spdTOn]}>{n}</Text>
                    </Pressable>
                  ))}
                </View>
              </View>
            )}

            <Pressable onPress={activate} disabled={busy} style={styles.activateBtn}>
              <Text style={styles.activateT}>{busy ? '…' : 'ACTIVER'}</Text>
            </Pressable>
          </View>
        )}
      </Card>
    </>
  );
}

function Stepper({ label, value, hint, onMinus, onPlus }: {
  label: string; value: string; hint?: string; onMinus: () => void; onPlus: () => void;
}) {
  return (
    <View style={styles.stepRow}>
      <View style={{ flex: 1 }}>
        <Text style={styles.stepLbl}>{label}</Text>
        {!!hint && <Text style={styles.stepHint}>{hint}</Text>}
      </View>
      <View style={styles.stepCtrl}>
        <Pressable onPress={onMinus} style={styles.stepBtn}><Text style={styles.stepBtnT}>–</Text></Pressable>
        <Text style={styles.stepVal}>{value}</Text>
        <Pressable onPress={onPlus} style={styles.stepBtn}><Text style={styles.stepBtnT}>+</Text></Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  section: { color: colors.textSecondary, ...typography.label, marginTop: spacing.l, marginBottom: spacing.s },
  activeTag: { ...typography.label, fontSize: 12 },
  activeDates: { color: colors.textPrimary, fontSize: typography.sizes.body, marginTop: spacing.xs },
  note: { color: colors.textSecondary, fontSize: typography.sizes.small, lineHeight: 19, marginTop: spacing.s },
  cancelBtn: { marginTop: spacing.m, paddingVertical: 12, borderRadius: spacing.cardRadius, borderWidth: 1, borderColor: colors.readyOrange, alignItems: 'center' },
  cancelT: { color: colors.readyOrange, ...typography.label, fontSize: 11 },
  modeRow: { flexDirection: 'row', gap: spacing.s },
  modeBtn: { flex: 1, paddingVertical: spacing.s, borderRadius: 6, alignItems: 'center', borderWidth: 1, borderColor: colors.hairlineStrong },
  modeBtnOn: { backgroundColor: colors.signalSoft, borderColor: colors.signal },
  modeT: { color: colors.textSecondary, ...typography.label, fontSize: 9, textAlign: 'center' },
  modeTOn: { color: colors.signal },
  stepRow: { flexDirection: 'row', alignItems: 'center', marginTop: spacing.m },
  stepLbl: { color: colors.textSecondary, ...typography.label, fontSize: 10 },
  stepHint: { color: colors.textDisabled, fontSize: typography.sizes.micro, marginTop: 2 },
  stepCtrl: { flexDirection: 'row', alignItems: 'center', gap: spacing.m },
  stepBtn: { width: 36, height: 36, borderRadius: 18, backgroundColor: colors.bgElevated, borderWidth: 1, borderColor: colors.hairlineStrong, alignItems: 'center', justifyContent: 'center' },
  stepBtnT: { color: colors.signal, fontSize: 20, fontFamily: typography.display.fontFamily },
  stepVal: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2, minWidth: 48, textAlign: 'center' },
  spdRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: spacing.m },
  spdBtns: { flexDirection: 'row', gap: spacing.s },
  spdBtn: { width: 44, height: 36, borderRadius: 6, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: colors.hairlineStrong },
  spdBtnOn: { backgroundColor: colors.signalSoft, borderColor: colors.signal },
  spdT: { color: colors.textSecondary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2 },
  spdTOn: { color: colors.signal },
  activateBtn: { marginTop: spacing.l, paddingVertical: 14, borderRadius: spacing.cardRadius, backgroundColor: colors.signal, alignItems: 'center' },
  activateT: { color: colors.bg, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2, letterSpacing: 1 },
});
