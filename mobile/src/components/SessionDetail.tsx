/**
 * Rendus de séance riches et réutilisés partout (générateurs + plan détaillé).
 * Course : fractions avec zone FC colorée + allures multiples. Force : séries
 * 5/3/1 avec barre de charge. WOD : description structurée + note lombaire.
 */
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { RunInterval, RunSession, Strength531, Wod } from '../api/client';
import { colors, spacing, typography } from '../theme/tokens';

const ZONE_COLOR: Record<string, string> = {
  Z1: colors.fitness, Z2: colors.signal, Z3: colors.readyYellow,
  Z4: colors.readyOrange, Z5: colors.readyRed,
};

function RunRow({ it }: { it: RunInterval }) {
  const zc = it.zone ? ZONE_COLOR[it.zone] ?? colors.hairlineStrong : colors.hairlineStrong;
  const pace = [
    it.pace_kmh ? `${it.pace_kmh} km/h` : null,
    it.pace_min_km ? `${it.pace_min_km}/km` : null,
    it.pct_vma ? `${it.pct_vma}% VMA` : null,
  ].filter(Boolean).join(' · ');
  const extra = [
    it.fc_bpm ? `FC ${it.fc_bpm}${it.pct_fcmax ? ` (${it.pct_fcmax}%)` : ''}` : null,
    it.recovery_sec ? `récup ${it.recovery_sec}s ${it.recovery_type ?? ''}` : null,
    it.recovery_min ? `récup ${it.recovery_min}min ${it.recovery_type ?? ''}` : null,
    it.structure, it.note, it.fc_attendue_fin, it.detail,
  ].filter(Boolean).join(' · ');
  return (
    <View style={styles.runRow}>
      <View style={[styles.zoneBar, { backgroundColor: zc }]} />
      <View style={{ flex: 1 }}>
        <View style={styles.runHead}>
          <Text style={styles.runLabel}>{it.label}</Text>
          {!!it.zone && <Text style={[styles.zoneTag, { color: zc }]}>{it.zone}</Text>}
        </View>
        {!!pace && <Text style={styles.runPace}>{pace}</Text>}
        {!!extra && <Text style={styles.runMeta}>{extra}</Text>}
      </View>
    </View>
  );
}

export function RunDetail({ session }: { session: RunSession }) {
  return (
    <View>
      <Text style={styles.metaTop}>{session.duration_min} min · {session.distance_km} km · {session.calories} kcal</Text>
      <Text style={styles.phase}>ÉCHAUFFEMENT</Text>
      <RunRow it={session.warmup} />
      <Text style={styles.phase}>CORPS DE SÉANCE</Text>
      {session.body.map((it, i) => <RunRow key={i} it={it} />)}
      <Text style={styles.phase}>RETOUR AU CALME</Text>
      <RunRow it={session.cooldown} />
      {!!session.sciatic_note && <Text style={styles.sciatic}>⚠ {session.sciatic_note}</Text>}
    </View>
  );
}

function MainLift({ lift, label }: { lift: Strength531['main_lift']; label: string }) {
  const maxLoad = Math.max(...lift.sets.map(s => s.load_kg), lift.training_max);
  return (
    <View>
      <View style={styles.mainHead}>
        <Text style={styles.phase}>{label} · {lift.name}</Text>
        <Text style={styles.tm}>TM {lift.training_max} kg</Text>
      </View>
      {lift.sets.map((s, i) => (
        <View key={i} style={styles.setRow}>
          <Text style={styles.setLoad}>{s.load_kg} kg</Text>
          <Text style={styles.setReps}>×{s.reps}{s.amrap ? ' max' : ''}</Text>
          <View style={styles.setTrack}>
            <View style={[styles.setFill, { width: `${(s.load_kg / maxLoad) * 100}%` }]} />
          </View>
          <Text style={styles.setPct}>{s.pct_tm}%</Text>
        </View>
      ))}
      {!!lift.note && <Text style={styles.sciatic}>⚠ {lift.note}</Text>}
    </View>
  );
}

export function StrengthDetail({ session }: { session: Strength531 }) {
  const lifts = session.main_lifts && session.main_lifts.length ? session.main_lifts : [session.main_lift];
  const fullBody = lifts.length > 1;
  return (
    <View>
      <Text style={styles.phase}>ÉCHAUFFEMENT — BIG 3 McGILL</Text>
      {session.warmup_mcgill.map((m, i) => (
        <Text key={i} style={styles.line}>• {m.name} — {m.prescription}</Text>
      ))}
      {lifts.map((l, i) => (
        <MainLift key={i} lift={l}
          label={fullBody ? `PRINCIPAL ${i + 1}/${lifts.length}` : 'PRINCIPAL'} />
      ))}
      <Text style={styles.phase}>ACCESSOIRES</Text>
      {session.accessories.map((a, i) => (
        <Text key={i} style={styles.line}>
          • {a.name} — {a.sets}×{a.reps}{a.load_kg ? ` @${a.load_kg}kg` : ''} · repos {a.rest_sec}s
        </Text>
      ))}
      {!!session.grease_the_groove && <Text style={styles.gtg}>💪 {session.grease_the_groove}</Text>}
      {!!session.finisher_wod && (
        <>
          <Text style={styles.phase}>FINISHER · {session.finisher_wod.format}</Text>
          <WodDetail wod={session.finisher_wod} compact />
        </>
      )}
    </View>
  );
}

export function WodDetail({ wod, compact = false }: { wod: Wod; compact?: boolean }) {
  return (
    <View>
      {!compact && <Text style={styles.wodName}>{wod.name}</Text>}
      <Text style={styles.wodCap}>{wod.format} · {wod.duration_or_cap}</Text>
      {wod.description.map((l, i) => <Text key={i} style={styles.wodLine}>• {l}</Text>)}
      <Text style={styles.wodScore}>🎯 {wod.target_score}</Text>
      {!compact && <Text style={styles.line}>Muscles : {wod.muscles}</Text>}
      <Text style={[styles.lumbar, { color: wod.lumbar_safe ? colors.signal : colors.readyOrange }]}>
        {wod.lumbar_note}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  metaTop: { color: colors.textSecondary, fontSize: typography.sizes.small, marginBottom: spacing.s },
  phase: { color: colors.textSecondary, ...typography.label, marginTop: spacing.m, marginBottom: spacing.xs },
  runRow: { flexDirection: 'row', paddingVertical: spacing.s, gap: spacing.s, borderTopWidth: 1, borderTopColor: colors.hairline },
  zoneBar: { width: 3, borderRadius: 2 },
  runHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  runLabel: { color: colors.textPrimary, fontSize: typography.sizes.body, ...typography.bodyBold, flex: 1 },
  zoneTag: { fontFamily: typography.display.fontFamily, fontSize: 13 },
  runPace: { color: colors.signal, fontSize: typography.sizes.small, marginTop: 2 },
  runMeta: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: 2 },
  sciatic: { color: colors.readyOrange, fontSize: typography.sizes.small, marginTop: spacing.s },
  line: { color: colors.textSecondary, fontSize: typography.sizes.small, lineHeight: 20 },
  mainHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  tm: { color: colors.fitness, ...typography.label },
  setRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.xs, gap: spacing.s },
  setLoad: { color: colors.signal, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2, minWidth: 64 },
  setReps: { color: colors.textPrimary, fontSize: typography.sizes.small, minWidth: 48 },
  setTrack: { flex: 1, height: 6, backgroundColor: colors.hairline, borderRadius: 3, overflow: 'hidden' },
  setFill: { height: 6, backgroundColor: colors.signalDim, borderRadius: 3 },
  setPct: { color: colors.textDisabled, fontSize: typography.sizes.small, width: 36, textAlign: 'right' },
  gtg: { color: colors.fitness, fontSize: typography.sizes.small, marginTop: spacing.s, lineHeight: 19 },
  wodName: { color: colors.signal, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h1, letterSpacing: 1 },
  wodCap: { color: colors.signal, ...typography.label, marginTop: 2, marginBottom: spacing.xs },
  wodLine: { color: colors.textPrimary, fontSize: typography.sizes.body, lineHeight: 21, ...typography.bodyBold },
  wodScore: { color: colors.textPrimary, fontSize: typography.sizes.small, marginTop: spacing.xs },
  lumbar: { fontSize: typography.sizes.small, marginTop: spacing.xs },
});
