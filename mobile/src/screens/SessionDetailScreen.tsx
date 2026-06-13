/**
 * Écran séance détaillée — la séance du jour, prête à exécuter.
 * Structure par phases (échauffement / corps / retour au calme / 2e séance),
 * chaque bloc avec sa prescription. En-tête collant, bandeau sécurité,
 * bouton de fin qui enregistre la séance (offline-first).
 */
import React, { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { api, DetailedSession, flushSyncQueue } from '../api/client';
import { ReadinessBar } from '../components/ReadinessBar';
import { Card, PrimaryButton, Tag } from '../components/ui';
import {
  colors, disciplineLabel, DISCIPLINE, ReadinessLevel, spacing, typography,
} from '../theme/tokens';

const PHASE_LABEL: Record<string, string> = {
  warmup: 'ÉCHAUFFEMENT', main: 'CORPS DE SÉANCE',
  cooldown: 'RETOUR AU CALME', finisher: 'SÉANCE 2',
};

export function SessionDetailScreen({ session, level, dateIso, onClose }: {
  session: DetailedSession;
  level: ReadinessLevel;
  dateIso: string;
  onClose: () => void;
}) {
  const [done, setDone] = useState(false);
  // RPE ressenti par défaut = plafond d'intensité prescrit, ajustable après l'effort
  const [rpe, setRpe] = useState(Math.round(Math.min(10, session.intensity_cap)));

  const complete = async () => {
    await api.completeSession({
      discipline: session.discipline,
      session_date: dateIso,
      duration_min: session.duration_min,
      intensity_rpe: rpe,
      family_id: session.title,
    });
    flushSyncQueue().catch(() => {}); // tente la synchro immédiate si en ligne
    setDone(true);
  };

  const isRest = session.discipline === 'rest';

  const glyph = DISCIPLINE[session.discipline]?.glyph ?? '▸';

  return (
    <View style={styles.root}>
      {/* En-tête */}
      <View style={styles.header}>
        <Pressable onPress={onClose} hitSlop={12} accessibilityRole="button">
          <Text style={styles.back}>‹ RETOUR</Text>
        </Pressable>
        <Tag label={disciplineLabel(session.discipline)} color={colors.signal} />
      </View>

      <ScrollView contentContainerStyle={{ padding: spacing.m, paddingBottom: spacing.xl }}>
        {/* Bloc titre */}
        <Text style={styles.glyph}>{glyph}</Text>
        <Text style={styles.title}>{session.title}</Text>
        <View style={styles.metaRow}>
          <Stat value={`${session.duration_min}'`} label="durée" />
          <View style={styles.metaDivider} />
          <Stat value={`${session.intensity_cap}/10`} label="intensité max" />
        </View>
        <Text style={styles.reason}>{session.coach_reason}</Text>

        {/* Bandeau sécurité */}
        {session.safety_notes.length > 0 && (
          <View style={styles.safety}>
            {session.safety_notes.map(n => (
              <Text key={n} style={styles.safetyText}>⚠ {n}</Text>
            ))}
          </View>
        )}

        {/* Objectifs */}
        {session.targets.length > 0 && (
          <View style={styles.targets}>
            {session.targets.map(t => <Text key={t} style={styles.targetText}>◎ {t}</Text>)}
          </View>
        )}

        {/* Phases */}
        {session.phases.map((phase, i) => (
          <View key={`${phase.kind}-${i}`} style={styles.phase}>
            <Text style={styles.phaseLabel}>{PHASE_LABEL[phase.kind] ?? phase.label}</Text>
            <Text style={styles.phaseSub}>{phase.label}</Text>
            <Card style={{ flexDirection: 'row' }}>
              <ReadinessBar level={phase.kind === 'finisher' ? 'yellow' : level} />
              <View style={styles.phaseBody}>
                {phase.items.map((it, j) => (
                  <View key={j} style={[styles.item, j > 0 && styles.itemBorder]}>
                    <View style={styles.itemHead}>
                      <Text style={styles.itemName}>{it.name}</Text>
                      {!!it.prescription && (
                        <Text style={styles.itemRx}>{it.prescription}</Text>
                      )}
                    </View>
                    {!!it.meta && <Text style={styles.itemMeta}>{it.meta}</Text>}
                    {!!it.notes && <Text style={styles.itemNotes}>{it.notes}</Text>}
                  </View>
                ))}
              </View>
            </Card>
          </View>
        ))}

        {/* Alternatives */}
        {session.alternatives.length > 0 && (
          <View style={styles.alt}>
            <Text style={styles.altLabel}>SI BESOIN</Text>
            {session.alternatives.map(a => <Text key={a} style={styles.altText}>• {a}</Text>)}
          </View>
        )}

        <View style={{ marginTop: spacing.l }}>
          {isRest ? (
            <View style={styles.doneBox}>
              <Text style={styles.doneText}>JOUR DE REPOS · RIEN À FORCER</Text>
            </View>
          ) : done ? (
            <View style={styles.doneBox}>
              <Text style={styles.doneText}>✓ SÉANCE ENREGISTRÉE</Text>
            </View>
          ) : (
            <>
              {/* RPE ressenti → alimente la charge (SU) et la boucle adaptative */}
              <Text style={styles.rpeLabel}>DIFFICULTÉ RESSENTIE (RPE)</Text>
              <View style={styles.rpeRow}>
                {[4, 5, 6, 7, 8, 9, 10].map(n => (
                  <Pressable key={n} onPress={() => setRpe(n)}
                    style={[styles.rpeChip, rpe === n && styles.rpeChipOn]}>
                    <Text style={[styles.rpeText, rpe === n && styles.rpeTextOn]}>{n}</Text>
                  </Pressable>
                ))}
              </View>
              <PrimaryButton label="TERMINER LA SÉANCE" onPress={complete} />
            </>
          )}
        </View>
      </ScrollView>
    </View>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: spacing.m, paddingVertical: spacing.m,
    borderBottomWidth: 1, borderBottomColor: colors.hairline,
  },
  back: { color: colors.textSecondary, ...typography.label, letterSpacing: 1.5 },
  glyph: { color: colors.signal, fontSize: 28, marginBottom: spacing.xs },
  title: {
    color: colors.textPrimary, fontFamily: typography.display.fontFamily,
    fontSize: 30, letterSpacing: 0.5,
  },
  metaRow: { flexDirection: 'row', alignItems: 'center', marginTop: spacing.m },
  metaDivider: { width: 1, height: 28, backgroundColor: colors.hairline, marginHorizontal: spacing.l },
  stat: { alignItems: 'flex-start' },
  statValue: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.score },
  statLabel: { color: colors.textSecondary, ...typography.label, marginTop: 2 },
  reason: { color: colors.textPrimary, fontSize: typography.sizes.body, lineHeight: 22, marginTop: spacing.m },
  safety: {
    marginTop: spacing.m, padding: spacing.m, borderRadius: 8,
    backgroundColor: 'rgba(229,72,77,0.10)', borderLeftWidth: 3, borderLeftColor: colors.readyRed,
    gap: spacing.xs,
  },
  safetyText: { color: colors.readyOrange, fontSize: typography.sizes.small, lineHeight: 19 },
  targets: { marginTop: spacing.m, gap: spacing.xs },
  targetText: { color: colors.signal, fontSize: typography.sizes.small },
  phase: { marginTop: spacing.l },
  phaseLabel: { color: colors.textSecondary, ...typography.label },
  phaseSub: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2, marginBottom: spacing.s },
  phaseBody: { flex: 1, padding: spacing.m },
  item: { paddingVertical: spacing.s },
  itemBorder: { borderTopWidth: 1, borderTopColor: colors.hairline },
  itemHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  itemName: { color: colors.textPrimary, fontSize: typography.sizes.body, ...typography.bodyBold, flex: 1, paddingRight: spacing.s },
  itemRx: { color: colors.signal, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2 },
  itemMeta: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: 2 },
  itemNotes: { color: colors.readyYellow, fontSize: typography.sizes.small, marginTop: spacing.xs, fontStyle: 'italic' },
  alt: { marginTop: spacing.l, padding: spacing.m, backgroundColor: colors.bgElevated, borderRadius: 8 },
  altLabel: { color: colors.textSecondary, ...typography.label, marginBottom: spacing.s },
  altText: { color: colors.textSecondary, fontSize: typography.sizes.small, lineHeight: 20 },
  rpeLabel: { color: colors.textSecondary, ...typography.label, marginBottom: spacing.s, textAlign: 'center' },
  rpeRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: spacing.m, gap: spacing.xs },
  rpeChip: { flex: 1, paddingVertical: spacing.s, borderRadius: 6, backgroundColor: colors.bgElevated, alignItems: 'center', borderWidth: 1, borderColor: colors.hairline },
  rpeChipOn: { backgroundColor: colors.signalSoft, borderColor: colors.signal },
  rpeText: { color: colors.textSecondary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.body },
  rpeTextOn: { color: colors.signal },
  doneBox: {
    paddingVertical: 16, alignItems: 'center', borderRadius: spacing.cardRadius,
    backgroundColor: colors.signalSoft, borderWidth: 1, borderColor: colors.signalDim,
  },
  doneText: { color: colors.signal, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2, letterSpacing: 1 },
});
