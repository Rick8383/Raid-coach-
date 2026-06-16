/**
 * Bips du chrono — qualité compétition, sans dépendance.
 * Web : Web Audio API (oscillateur). Natif : vibration (haptique de secours).
 * L'AudioContext est créé paresseusement, au premier bip déclenché par un
 * geste utilisateur (démarrage du chrono) → conforme aux règles d'autoplay.
 */
import { Platform, Vibration } from 'react-native';

type WebAudio = { ctx: AudioContext | null };
const w: WebAudio = { ctx: null };

function audioCtx(): AudioContext | null {
  if (Platform.OS !== 'web') return null;
  try {
    if (!w.ctx) {
      const Ctor = (globalThis as any).AudioContext || (globalThis as any).webkitAudioContext;
      if (!Ctor) return null;
      w.ctx = new Ctor();
    }
    if (w.ctx && w.ctx.state === 'suspended') w.ctx.resume().catch(() => {});
    return w.ctx;
  } catch {
    return null;
  }
}

/** Réveille l'audio sur un geste utilisateur (à appeler au lancement du chrono). */
export function primeSound(): void {
  audioCtx();
}

function tone(freq: number, durationMs: number, gain = 0.18): void {
  const ctx = audioCtx();
  if (!ctx) {
    if (Platform.OS !== 'web') Vibration.vibrate(Math.min(durationMs, 80));
    return;
  }
  const osc = ctx.createOscillator();
  const amp = ctx.createGain();
  osc.type = 'square';
  osc.frequency.value = freq;
  amp.gain.value = gain;
  osc.connect(amp);
  amp.connect(ctx.destination);
  const now = ctx.currentTime;
  // petite enveloppe pour éviter le clic
  amp.gain.setValueAtTime(gain, now);
  amp.gain.exponentialRampToValueAtTime(0.0001, now + durationMs / 1000);
  osc.start(now);
  osc.stop(now + durationMs / 1000);
}

/** Bip court grave — tic du décompte (3, 2, 1). */
export function beepTick(): void {
  tone(660, 140);
}

/** Bip long aigu — GO / fin de WOD. */
export function beepGo(): void {
  if (Platform.OS !== 'web') { Vibration.vibrate([0, 120, 60, 240]); return; }
  tone(990, 480, 0.22);
}

/** Bip de fin de round / repère (EMOM, fin de time cap). */
export function beepRound(): void {
  tone(820, 220, 0.2);
}
