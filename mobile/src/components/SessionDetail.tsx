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

function fmtDist(m?: number): string | null {
  if (!m) return null;
  return m >= 1000 ? `${(m / 1000).toFixed(1).replace('.', ',')} km` : `${m} m`;
}

function fmtRec(sec?: number): string | null {
  if (!sec) return null;
  if (sec >= 120 && sec % 60 === 0) return `${sec / 60} min`;
  if (sec >= 90) return `${(sec / 60).toFixed(1).replace('.', ',')} min`;
  return `${sec}s`;
}

function RunRow({ it }: { it: RunInterval }) {
  const zc = it.zone ? ZONE_COLOR[it.zone] ?? colors.hairlineStrong : colors.hairlineStrong;
  // Ligne « à faire » : durée + distance bien visibles (échauffement / retour au calme / corps).
  const stat = [
    it.duration_min ? `${it.duration_min} min` : null,
    fmtDist(it.distance_m),
    it.duration_min_each ? `${it.duration_min_each}′ par bloc` : null,
  ].filter(Boolean).join(' · ');
  const pace = [
    it.pace_kmh ? `${it.pace_kmh} km/h` : null,
    it.pace_min_km ? `${it.pace_min_km}/km` : null,
    it.pct_vma ? `${it.pct_vma}% VMA` : null,
  ].filter(Boolean).join(' · ');
  const fc = [
    it.fc_bpm ? `FC ${it.fc_bpm}${it.pct_fcmax ? ` (${it.pct_fcmax}%)` : ''}` : null,
    it.fc_attendue_fin,
  ].filter(Boolean).join(' · ');
  // Récupération isolée sur sa propre ligne colorée → « plus visible » (répétitions + séries).
  const rt = it.recovery_type ?? 'trot';
  const rec = [
    it.recovery_sec ? `${fmtRec(it.recovery_sec)} ${rt} entre répétitions` : null,
    it.recovery_min ? `${it.recovery_min} min ${rt} entre répétitions` : null,
    it.series_recovery_sec ? `${fmtRec(it.series_recovery_sec)} entre séries` : null,
  ].filter(Boolean).join(' · ');
  const extra = [it.structure, it.note, it.detail].filter(Boolean).join(' · ');
  return (
    <View style={styles.runRow}>
      <View style={[styles.zoneBar, { backgroundColor: zc }]} />
      <View style={{ flex: 1 }}>
        <View style={styles.runHead}>
          <Text style={styles.runLabel}>{it.label}</Text>
          {!!it.zone && <Text style={[styles.zoneTag, { color: zc }]}>{it.zone}</Text>}
        </View>
        {!!stat && <Text style={styles.runStat}>{stat}</Text>}
        {!!pace && <Text style={styles.runPace}>{pace}</Text>}
        {!!fc && <Text style={styles.runMeta}>{fc}</Text>}
        {!!rec && (
          <View style={styles.recBox}>
            <Text style={styles.recTag}>RÉCUP</Text>
            <Text style={styles.recText}>{rec}</Text>
          </View>
        )}
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
      {!!session.plyo_finisher && (
        <>
          <Text style={styles.phase}>⚡ {session.plyo_finisher.title.toUpperCase()}</Text>
          {session.plyo_finisher.blocks.map((b, i) => (
            <Text key={i} style={styles.line}>• {b}</Text>
          ))}
        </>
      )}
      {!!session.sciatic_note && <Text style={styles.sciatic}>⚠ {session.sciatic_note}</Text>}
    </View>
  );
}

// Ligne d'exercice ultra-lisible : n° · nom · (repos/charge) · grand « séries × reps ».
function ExerciseRow({ index, name, sets, reps, load, rest }: {
  index: number; name: string; sets: number | string; reps: string;
  load?: number | null; rest?: number;
}) {
  return (
    <View style={styles.exRow}>
      <Text style={styles.exNum}>{index}</Text>
      <View style={{ flex: 1 }}>
        <Text style={styles.exName}>{name}</Text>
        <Text style={styles.exMeta}>
          {load ? `charge ${load} kg · ` : ''}repos {rest ?? 60}s
        </Text>
      </View>
      <Text style={styles.exSets}>{sets} <Text style={styles.exX}>×</Text> {reps}</Text>
    </View>
  );
}

function MainLift({ lift, label }: { lift: NonNullable<Strength531['main_lift']>; label: string }) {
  return (
    <View>
      <View style={styles.mainHead}>
        <Text style={styles.phase}>{label} · {lift.name}</Text>
        <Text style={styles.tm}>TM {lift.training_max} kg</Text>
      </View>
      <Text style={styles.mainExplain}>
        {lift.sets.length} séries : la charge monte, les reps baissent, et la
        dernière se fait au MAXIMUM de reps possible.
      </Text>
      {lift.sets.map((s, i) => (
        <View key={i} style={styles.exRow}>
          <Text style={styles.exNum}>{i + 1}</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.exName}>{s.load_kg} kg</Text>
            <Text style={styles.exMeta}>
              {s.pct_tm}% du max{s.amrap ? ' · le plus de reps possible' : ''}
            </Text>
          </View>
          <Text style={styles.exSets}>
            <Text style={styles.exX}>× </Text>{s.amrap ? 'max' : s.reps}
          </Text>
        </View>
      ))}
      <Text style={styles.restLine}>Repos {lift.sets[0]?.rest_sec ?? 180}s entre chaque série.</Text>
      {!!lift.note && <Text style={styles.sciatic}>⚠ {lift.note}</Text>}
    </View>
  );
}

export function StrengthDetail({ session }: { session: Strength531 }) {
  return (
    <View>
      <Text style={styles.phase}>ÉCHAUFFEMENT — BIG 3 McGILL</Text>
      {session.warmup_mcgill.map((m, i) => (
        <Text key={i} style={styles.line}>• {m.name} — {m.prescription}</Text>
      ))}

      {session.movements ? (
        // FULL BODY : liste d'exercices variés, ultra détaillée.
        <>
          <Text style={styles.phase}>EXERCICES · {session.movements.length}</Text>
          {session.movements.map((m, i) => (
            <ExerciseRow key={i} index={i + 1} name={m.name} sets={m.sets}
              reps={m.reps} load={m.load_kg} rest={m.rest_sec} />
          ))}
        </>
      ) : (
        <>
          {(session.main_lifts?.length ? session.main_lifts : [session.main_lift!]).map((l, i, arr) => (
            <MainLift key={i} lift={l} label={arr.length > 1 ? `PRINCIPAL ${i + 1}/${arr.length}` : 'PRINCIPAL'} />
          ))}
          <Text style={styles.phase}>ACCESSOIRES</Text>
          {session.accessories.map((a, i) => (
            <ExerciseRow key={i} index={i + 1} name={a.name} sets={a.sets}
              reps={a.reps} load={a.load_kg} rest={a.rest_sec} />
          ))}
        </>
      )}

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
  runStat: { color: colors.textPrimary, fontSize: typography.sizes.body, ...typography.bodyBold, marginTop: 3 },
  runPace: { color: colors.signal, fontSize: typography.sizes.small, marginTop: 2 },
  runMeta: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: 2 },
  recBox: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.s, marginTop: spacing.xs,
    backgroundColor: colors.signalSoft, borderRadius: 8, paddingVertical: 6, paddingHorizontal: spacing.s,
  },
  recTag: {
    color: colors.signal, fontFamily: typography.display.fontFamily, fontSize: 10,
    letterSpacing: 1, backgroundColor: colors.signalSoft,
  },
  recText: { color: colors.textPrimary, fontSize: typography.sizes.small, flex: 1, lineHeight: 17 },
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
  restLine: { color: colors.textDisabled, fontSize: typography.sizes.micro, marginTop: 2, marginBottom: spacing.s },
  mainExplain: { color: colors.textSecondary, fontSize: typography.sizes.small, lineHeight: 18, marginBottom: spacing.xs },
  exRow: {
    flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.s, gap: spacing.s,
    borderTopWidth: 1, borderTopColor: colors.hairline,
  },
  exNum: {
    width: 22, height: 22, borderRadius: 11, textAlign: 'center', lineHeight: 22,
    backgroundColor: colors.signalSoft, color: colors.signal,
    fontFamily: typography.display.fontFamily, fontSize: 12, overflow: 'hidden',
  },
  exName: { color: colors.textPrimary, fontSize: typography.sizes.body, ...typography.bodyBold },
  exMeta: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: 1 },
  exSets: { color: colors.signal, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h1 },
  exX: { color: colors.textDisabled, fontSize: typography.sizes.body },
  gtg: { color: colors.fitness, fontSize: typography.sizes.small, marginTop: spacing.s, lineHeight: 19 },
  wodName: { color: colors.signal, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h1, letterSpacing: 1 },
  wodCap: { color: colors.signal, ...typography.label, marginTop: 2, marginBottom: spacing.xs },
  wodLine: { color: colors.textPrimary, fontSize: typography.sizes.body, lineHeight: 21, ...typography.bodyBold },
  wodScore: { color: colors.textPrimary, fontSize: typography.sizes.small, marginTop: spacing.xs },
  lumbar: { fontSize: typography.sizes.small, marginTop: spacing.xs },
});

/** Contenu d'une séance selon sa discipline : allures de course, séries 5/3/1,
 * lignes du WOD, blocs natation/mobilité. Partagé par le plan (PlannedSessions)
 * et le suivi (Agenda) — le réalisé doit montrer exactement ce qui a été fait. */
export function SessionContent({ type, detail }: { type: string; detail: any }) {
  const d = detail || {};
  if (type === 'run' && Array.isArray(d.body)) return <RunDetail session={d} />;
  if (type === 'strength' && (d.main_lift || d.main_lifts?.length || d.movements)) {
    return <StrengthDetail session={d} />;
  }
  if (type === 'crossfit' && Array.isArray(d.description)) return <WodDetail wod={d} />;
  if (Array.isArray(d.blocks)) {
    return (
      <View>
        {d.blocks.map((b: string, i: number) => (
          <Text key={i} style={styles.line}>• {b}</Text>))}
        {!!d.note && <Text style={styles.sciatic}>💡 {d.note}</Text>}
      </View>
    );
  }
  return null;
}
