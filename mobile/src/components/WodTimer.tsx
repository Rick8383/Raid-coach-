/**
 * Chrono WOD qualité compétition.
 *  - Compte à rebours de départ (15 s par défaut) avec bips 3-2-1 puis GO.
 *  - Réglable en cliquant sur le chrono : durée du décompte, time cap, mode.
 *  - Mode FOR TIME : le chrono monte, on enregistre le temps de fin → score.
 *  - Mode AMRAP   : le chrono descend depuis le time cap, compteur de TOURS
 *    terminés (+1 par tour). Les reps du tour en cours se saisissent à la fin,
 *    dans la fenêtre de score (notation CrossFit « 2 tours + 22 reps »).
 * Le score (temps ou reps) remonte via onFinish pour être sauvegardé/suivi.
 */
import React, { useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Wod } from '../api/client';
import { beepGo, beepTick, beepRound, primeSound } from './sound';
import { WodScoreSheet, WodScoreInput, WodAssessment, modeForFormatKey } from './WodScoreSheet';
import { colors, spacing, typography } from '../theme/tokens';

export type ScoreMode = 'for_time' | 'amrap';
export interface WodResult {
  mode: ScoreMode; time_sec: number;
  rounds: number;   // tours COMPLÈTEMENT terminés (compteur du chrono)
  reps: number;     // reps du tour en cours — saisies à la fin, pas au chrono
  capped: boolean; cap_sec: number;
}

type Phase = 'idle' | 'countdown' | 'running' | 'done';

// For Time → le chrono monte ; sinon score en tours + reps → on descend du cap.
function modeForWod(wod?: Wod | null): ScoreMode {
  return modeForFormatKey(wod?.format_key);
}

/** Extrait un nombre de minutes d'une chaîne (« AMRAP 12 min », « cap 15' »). */
function minutesFrom(text?: string, fallback = 12): number {
  if (!text) return fallback;
  const m = text.match(/(\d{1,2})\s*(?:min|')/i) ?? text.match(/(\d{1,2})/);
  const v = m ? parseInt(m[1], 10) : fallback;
  return Math.max(1, Math.min(60, v));
}

function fmt(sec: number): string {
  const s = Math.max(0, Math.floor(sec));
  const m = Math.floor(s / 60);
  return `${String(m).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
}

const COUNTDOWN_CHOICES = [0, 5, 10, 15, 20, 30];

export function WodTimer({ wod, durationMin, onFinish }: {
  wod?: Wod | null;
  durationMin?: number;
  /** Score confirmé/corrigé dans la fenêtre → renvoie le verdict de perf. */
  onFinish?: (s: WodScoreInput) => Promise<WodAssessment | null>;
}) {
  const [mode, setMode] = useState<ScoreMode>(modeForWod(wod));
  const [countdownSec, setCountdownSec] = useState(15);
  const [capSec, setCapSec] = useState(minutesFrom(wod?.duration_or_cap, durationMin ?? 12) * 60);
  const [phase, setPhase] = useState<Phase>('idle');
  const [showSettings, setShowSettings] = useState(false);
  const [rounds, setRounds] = useState(0);   // tours terminés
  const [now, setNow] = useState(Date.now());
  const [result, setResult] = useState<WodResult | null>(null);
  const [sheet, setSheet] = useState(false);   // fenêtre de saisie du score

  // Réinitialise quand le WOD change.
  useEffect(() => {
    setMode(modeForWod(wod));
    setCapSec(minutesFrom(wod?.duration_or_cap, durationMin ?? 12) * 60);
    reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wod?.seed, wod?.format_key]);

  const cdEndRef = useRef(0);
  const runStartRef = useRef(0);
  const amrapEndRef = useRef(0);
  const prevWholeRef = useRef(-1);

  const reset = () => {
    setPhase('idle'); setRounds(0); setResult(null); prevWholeRef.current = -1;
  };

  const start = () => {
    primeSound();
    setRounds(0); setResult(null); prevWholeRef.current = -1;
    if (countdownSec > 0) {
      cdEndRef.current = Date.now() + countdownSec * 1000;
      setPhase('countdown');
    } else {
      beginRunning();
    }
    setNow(Date.now());
  };

  const beginRunning = () => {
    const t = Date.now();
    runStartRef.current = t;
    amrapEndRef.current = t + capSec * 1000;
    prevWholeRef.current = -1;
    setPhase('running');
  };

  const finish = (capped: boolean) => {
    // Temps réel écoulé dans les deux modes : un AMRAP stoppé à la main (■)
    // enregistre le temps effectif, pas le cap complet.
    const timeSec = Math.min(capSec, Math.round((Date.now() - runStartRef.current) / 1000));
    const r: WodResult = { mode, time_sec: timeSec, rounds, reps: 0, capped, cap_sec: capSec };
    setResult(r);
    setPhase('done');
    beepGo();
    if (onFinish) setSheet(true);   // fenêtre de score dès l'arrêt du chrono
  };

  // Boucle de tick (200 ms) pendant décompte / course, pilotée par timestamps.
  useEffect(() => {
    if (phase !== 'countdown' && phase !== 'running') return;
    const id = setInterval(() => setNow(Date.now()), 200);
    return () => clearInterval(id);
  }, [phase]);

  // Réagit aux passages de seconde (bips + transitions).
  useEffect(() => {
    if (phase === 'countdown') {
      const remaining = Math.ceil((cdEndRef.current - now) / 1000);
      if (remaining !== prevWholeRef.current) {
        prevWholeRef.current = remaining;
        if (remaining <= 3 && remaining >= 1) beepTick();   // décompte 3-2-1
      }
      if (now >= cdEndRef.current) { beepGo(); beginRunning(); }
      return;
    }
    if (phase === 'running') {
      // Temps restant avant la fin (AMRAP) ou avant le time cap (For Time).
      const remaining = mode === 'amrap'
        ? Math.ceil((amrapEndRef.current - now) / 1000)
        : Math.ceil((runStartRef.current + capSec * 1000 - now) / 1000);
      if (remaining !== prevWholeRef.current) {
        prevWholeRef.current = remaining;
        // Bips sur les 10 dernières secondes ; les 3 derniers plus marqués.
        if (remaining <= 3 && remaining >= 1) beepTick();
        else if (remaining <= 10 && remaining > 3) beepRound();
      }
      if (remaining <= 0) finish(mode === 'for_time');  // For Time auto = capé
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [now, phase]);

  // Valeur affichée du chrono selon la phase / le mode.
  let big = '00:00';
  let sub = '';
  if (phase === 'countdown') {
    big = String(Math.max(0, Math.ceil((cdEndRef.current - now) / 1000)));
    sub = 'DÉPART';
  } else if (phase === 'running') {
    if (mode === 'for_time') {
      big = fmt((now - runStartRef.current) / 1000);
      sub = `TIME CAP ${fmt(capSec)}`;
    } else {
      big = fmt((amrapEndRef.current - now) / 1000);
      sub = 'TEMPS RESTANT';
    }
  } else if (phase === 'done' && result) {
    big = result.mode === 'for_time' ? fmt(result.time_sec) : `${result.rounds}`;
    sub = result.mode === 'for_time'
      ? (result.capped ? 'TIME CAP ATTEINT' : 'TEMPS FINAL')
      : 'TOURS TERMINÉS';
  } else {
    big = mode === 'for_time' ? '00:00' : fmt(capSec);
    sub = mode === 'for_time' ? `TIME CAP ${fmt(capSec)}` : 'AMRAP — TEMPS';
  }

  const running = phase === 'running';
  const countingDown = phase === 'countdown';

  return (
    <View style={styles.root}>
      {/* Affichage chrono — cliquable pour régler (hors course) */}
      <Pressable
        onPress={() => { if (phase === 'idle' || phase === 'done') setShowSettings(s => !s); }}
        style={[styles.display, countingDown && styles.displayCd]}>
        <Text style={[styles.mode, { color: mode === 'for_time' ? colors.signal : colors.readyYellow }]}>
          {mode === 'for_time' ? 'FOR TIME' : 'AMRAP'}
        </Text>
        <Text style={[styles.big, countingDown && styles.bigCd]}>{big}</Text>
        <Text style={styles.sub}>{sub}</Text>
        {(phase === 'idle' || phase === 'done') && (
          <Text style={styles.gear}>⚙ régler (décompte {countdownSec}s · cap {fmt(capSec)})</Text>
        )}
      </Pressable>

      {/* Panneau de réglages */}
      {showSettings && (phase === 'idle' || phase === 'done') && (
        <View style={styles.settings}>
          <Text style={styles.setLabel}>MODE DE SCORE</Text>
          <View style={styles.segRow}>
            {(['for_time', 'amrap'] as const).map(m => (
              <Pressable key={m} onPress={() => setMode(m)}
                style={[styles.seg, mode === m && styles.segOn]}>
                <Text style={[styles.segT, mode === m && styles.segTOn]}>
                  {m === 'for_time' ? 'FOR TIME (temps)' : 'AMRAP (reps)'}
                </Text>
              </Pressable>
            ))}
          </View>

          <Text style={styles.setLabel}>COMPTE À REBOURS DE DÉPART</Text>
          <View style={styles.segRow}>
            {COUNTDOWN_CHOICES.map(c => (
              <Pressable key={c} onPress={() => setCountdownSec(c)}
                style={[styles.pill, countdownSec === c && styles.pillOn]}>
                <Text style={[styles.pillT, countdownSec === c && styles.pillTOn]}>{c}s</Text>
              </Pressable>
            ))}
          </View>

          <Text style={styles.setLabel}>TIME CAP</Text>
          <View style={styles.capRow}>
            <Pressable onPress={() => setCapSec(s => Math.max(60, s - 60))} style={styles.capBtn}>
              <Text style={styles.capBtnT}>–</Text>
            </Pressable>
            <Text style={styles.capVal}>{fmt(capSec)}</Text>
            <Pressable onPress={() => setCapSec(s => Math.min(60 * 60, s + 60))} style={styles.capBtn}>
              <Text style={styles.capBtnT}>+</Text>
            </Pressable>
          </View>
        </View>
      )}

      {/* Compteur de reps (AMRAP) pendant la course */}
      {running && mode === 'amrap' && (
        <View style={styles.repBox}>
          <Text style={styles.repLabel}>TOURS TERMINÉS (+1 par tour fini)</Text>
          <View style={styles.repRow}>
            <Pressable onPress={() => setRounds(r => Math.max(0, r - 1))} style={styles.repBtnMinus}>
              <Text style={styles.repBtnT}>–</Text>
            </Pressable>
            <Text style={styles.repCount}>{rounds}</Text>
            <Pressable onPress={() => { setRounds(r => r + 1); beepRound(); }} style={styles.repBtnPlus}>
              <Text style={styles.repBtnPlusT}>+1</Text>
            </Pressable>
          </View>
        </View>
      )}

      {/* Commandes */}
      <View style={styles.controls}>
        {(phase === 'idle' || phase === 'done') && (
          <Pressable onPress={start} style={styles.startBtn}>
            <Text style={styles.startT}>{phase === 'done' ? '↻ REFAIRE' : '▶ DÉMARRER'}</Text>
          </Pressable>
        )}
        {countingDown && (
          <Pressable onPress={reset} style={styles.stopBtn}>
            <Text style={styles.stopT}>ANNULER</Text>
          </Pressable>
        )}
        {running && (
          <Pressable onPress={() => finish(false)} style={styles.finishBtn}>
            <Text style={styles.finishT}>■ TERMINER</Text>
          </Pressable>
        )}
      </View>

      {/* Résultat + fenêtre de saisie du score (ouverte dès l'arrêt du chrono) */}
      {phase === 'done' && result && (
        <View style={styles.resultBox}>
          <Text style={styles.resultText}>
            {result.mode === 'for_time'
              ? `Score : ${fmt(result.time_sec)}${result.capped ? ' (cap atteint)' : ''}`
              : `${result.rounds} tour${result.rounds > 1 ? 's' : ''} terminé${result.rounds > 1 ? 's' : ''} — ajoute les reps du tour en cours`}
          </Text>
          {onFinish && (
            <Pressable onPress={() => setSheet(true)} style={styles.saveScoreBtn}>
              <Text style={styles.saveScoreT}>✓ SAISIR / VALIDER LE SCORE</Text>
            </Pressable>
          )}
        </View>
      )}
      {onFinish && result && (
        <WodScoreSheet
          visible={sheet}
          title={wod?.name ?? 'WOD'}
          initial={{
            mode: result.mode, time_sec: result.time_sec,
            rounds: result.rounds, reps: result.reps,
            capped: result.capped, cap_sec: result.cap_sec,
          }}
          onSubmit={onFinish}
          onClose={() => setSheet(false)} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { marginTop: spacing.m },
  display: {
    backgroundColor: colors.bgInput, borderRadius: spacing.cardRadius, paddingVertical: spacing.l,
    alignItems: 'center', borderWidth: 1, borderColor: colors.hairlineStrong,
  },
  displayCd: { borderColor: colors.readyOrange },
  mode: { ...typography.label, fontSize: 11, marginBottom: 2 },
  big: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: 64, lineHeight: 68 },
  bigCd: { color: colors.readyOrange, fontSize: 80, lineHeight: 84 },
  sub: { color: colors.textSecondary, ...typography.label, fontSize: 10, marginTop: 2 },
  gear: { color: colors.textDisabled, fontSize: typography.sizes.micro, marginTop: spacing.s },
  settings: {
    marginTop: spacing.s, padding: spacing.m, backgroundColor: colors.bgElevated,
    borderRadius: spacing.cardRadius, borderWidth: 1, borderColor: colors.hairline,
  },
  setLabel: { color: colors.textSecondary, ...typography.label, marginTop: spacing.s, marginBottom: spacing.xs },
  segRow: { flexDirection: 'row', gap: spacing.xs, flexWrap: 'wrap' },
  seg: { flex: 1, paddingVertical: spacing.s, borderRadius: 6, alignItems: 'center', borderWidth: 1, borderColor: colors.hairlineStrong },
  segOn: { backgroundColor: colors.signalSoft, borderColor: colors.signal },
  segT: { color: colors.textSecondary, ...typography.label, fontSize: 9 },
  segTOn: { color: colors.signal },
  pill: { paddingVertical: spacing.s, paddingHorizontal: spacing.m, borderRadius: 6, backgroundColor: colors.bgCard, borderWidth: 1, borderColor: colors.hairline },
  pillOn: { backgroundColor: colors.signalSoft, borderColor: colors.signal },
  pillT: { color: colors.textSecondary, ...typography.label, fontSize: 10 },
  pillTOn: { color: colors.signal },
  capRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.l },
  capBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: colors.bgCard, borderWidth: 1, borderColor: colors.hairlineStrong, alignItems: 'center', justifyContent: 'center' },
  capBtnT: { color: colors.signal, fontSize: 24, fontFamily: typography.display.fontFamily },
  capVal: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h1, minWidth: 80, textAlign: 'center' },
  repBox: { marginTop: spacing.m, alignItems: 'center' },
  repLabel: { color: colors.textSecondary, ...typography.label, marginBottom: spacing.s },
  repRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.l },
  repCount: { color: colors.signal, fontFamily: typography.display.fontFamily, fontSize: 56, minWidth: 90, textAlign: 'center' },
  repBtnMinus: { width: 56, height: 56, borderRadius: 28, backgroundColor: colors.bgElevated, borderWidth: 1, borderColor: colors.hairlineStrong, alignItems: 'center', justifyContent: 'center' },
  repBtnPlus: { width: 72, height: 72, borderRadius: 36, backgroundColor: colors.signal, alignItems: 'center', justifyContent: 'center' },
  repBtnT: { color: colors.textPrimary, fontSize: 28, fontFamily: typography.display.fontFamily },
  repBtnPlusT: { color: colors.bg, fontSize: 26, fontFamily: typography.display.fontFamily },
  controls: { flexDirection: 'row', gap: spacing.s, marginTop: spacing.m },
  startBtn: { flex: 1, paddingVertical: 16, borderRadius: spacing.cardRadius, backgroundColor: colors.signal, alignItems: 'center' },
  startT: { color: colors.bg, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2, letterSpacing: 1 },
  stopBtn: { flex: 1, paddingVertical: 16, borderRadius: spacing.cardRadius, borderWidth: 1, borderColor: colors.readyOrange, alignItems: 'center' },
  stopT: { color: colors.readyOrange, ...typography.label, fontSize: 12 },
  finishBtn: { flex: 1, paddingVertical: 16, borderRadius: spacing.cardRadius, backgroundColor: colors.readyOrange, alignItems: 'center' },
  finishT: { color: colors.bg, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2, letterSpacing: 1 },
  resultBox: { marginTop: spacing.m, alignItems: 'center' },
  resultText: { color: colors.textPrimary, fontSize: typography.sizes.body, marginBottom: spacing.s },
  saveScoreBtn: { paddingVertical: 12, paddingHorizontal: spacing.l, borderRadius: spacing.cardRadius, backgroundColor: colors.signalSoft, borderWidth: 1, borderColor: colors.signal },
  saveScoreT: { color: colors.signal, ...typography.label, fontSize: 11 },
});
