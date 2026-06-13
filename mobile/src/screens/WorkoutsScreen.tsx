/**
 * Séances — une page par discipline (Course / Force / WOD), chacune avec :
 *  - le focus du plan d'entraînement en cours (phase roadmap) ;
 *  - un bouton « Générer » spécifique qui produit une séance complète
 *    (indépendant de la décision du jour et des données montre).
 * L'onglet Course inclut aussi les zones FC & allures.
 */
import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { AthleteProfile, DetailedSession, Roadmap, api } from '../api/client';
import { SessionView } from '../components/SessionView';
import { RunZonesView } from './RunZonesScreen';
import { PrimaryButton, Tag } from '../components/ui';
import { colors, disciplineLabel, spacing, typography } from '../theme/tokens';

type Discipline = 'run' | 'strength' | 'crossfit';

const SEGMENTS: { key: Discipline; label: string }[] = [
  { key: 'run', label: 'COURSE' },
  { key: 'strength', label: 'FORCE' },
  { key: 'crossfit', label: 'WOD' },
];

function weeksToGoal(goalDate?: string): number {
  const target = new Date(goalDate ?? '2029-03-01').getTime();
  return Math.max(8, Math.min(Math.round((target - Date.now()) / (7 * 24 * 3600 * 1000)), 220));
}

export function WorkoutsScreen({ profile }: { profile: AthleteProfile | null }) {
  const [disc, setDisc] = useState<Discipline>('run');
  const [phase, setPhase] = useState<Roadmap | null>(null);

  useEffect(() => {
    api.roadmap(weeksToGoal(profile?.goal_date), 0).then(setPhase).catch(() => {});
  }, [profile]);

  return (
    <ScrollView style={styles.root} contentContainerStyle={{ padding: spacing.m }}>
      {/* Sélecteur de discipline */}
      <View style={styles.segmented}>
        {SEGMENTS.map(s => (
          <Pressable key={s.key} onPress={() => setDisc(s.key)}
            style={[styles.segment, disc === s.key && styles.segmentOn]}>
            <Text style={[styles.segmentText, disc === s.key && styles.segmentTextOn]}>{s.label}</Text>
          </Pressable>
        ))}
      </View>

      {/* Plan en cours */}
      {phase && (
        <View style={styles.planCard}>
          <View style={styles.planHead}>
            <Text style={styles.planLabel}>PLAN EN COURS</Text>
            <Tag label={phase.current_phase.toUpperCase()} color={colors.fitness} filled />
          </View>
          <Text style={styles.planFocus}>{phase.current_focus}</Text>
          <Text style={styles.planMeta}>Semaine {phase.current_week} / {phase.selection_week} · cap sélection 2029</Text>
        </View>
      )}

      <DisciplinePanel key={disc} discipline={disc} profile={profile} />

      {disc === 'run' && (
        <View style={{ marginTop: spacing.xl }}>
          <RunZonesView profile={profile} />
        </View>
      )}
    </ScrollView>
  );
}

function DisciplinePanel({ discipline, profile }:
  { discipline: Discipline; profile: AthleteProfile | null }) {
  const [session, setSession] = useState<DetailedSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [wodKind, setWodKind] = useState<'death_by' | 'time_cap'>('death_by');
  const [error, setError] = useState(false);

  const generate = async () => {
    setLoading(true);
    setError(false);
    try {
      const s = await api.generate({
        discipline,
        seed: `${Date.now()}`,            // change à chaque clic → séance différente
        wod_kind: wodKind,
        athlete_level: 'intermediate',
      });
      setSession(s);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View>
      {discipline === 'crossfit' && (
        <View style={styles.wodKinds}>
          {(['death_by', 'time_cap'] as const).map(k => (
            <Pressable key={k} onPress={() => setWodKind(k)}
              style={[styles.kindChip, wodKind === k && styles.kindChipOn]}>
              <Text style={[styles.kindText, wodKind === k && styles.kindTextOn]}>
                {k === 'death_by' ? 'DEATH BY EMOM' : 'TIME CAP LESTÉ'}
              </Text>
            </Pressable>
          ))}
        </View>
      )}

      <PrimaryButton
        label={session ? `↻ NOUVELLE SÉANCE ${disciplineLabel(discipline)}` : `GÉNÉRER UNE SÉANCE ${disciplineLabel(discipline)}`}
        onPress={generate} />

      {loading && <ActivityIndicator color={colors.signal} style={{ marginTop: spacing.l }} />}

      {error && (
        <Text style={styles.error}>
          Pas de réseau / API injoignable. Vérifie que le backend est déployé et que
          l'URL de l'API est configurée.
        </Text>
      )}

      {session && !loading && (
        <View style={{ marginTop: spacing.m }}>
          <Text style={styles.sessionTitle}>{session.title}</Text>
          <SessionView session={session} />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  segmented: { flexDirection: 'row', backgroundColor: colors.bgCard, borderRadius: 8, padding: 3, marginBottom: spacing.m },
  segment: { flex: 1, paddingVertical: spacing.s, borderRadius: 6, alignItems: 'center' },
  segmentOn: { backgroundColor: colors.signal },
  segmentText: { color: colors.textSecondary, ...typography.label, fontSize: 11 },
  segmentTextOn: { color: colors.bg },
  planCard: { backgroundColor: colors.bgElevated, borderRadius: spacing.cardRadius, padding: spacing.m, marginBottom: spacing.m },
  planHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  planLabel: { color: colors.textSecondary, ...typography.label },
  planFocus: { color: colors.textPrimary, fontSize: typography.sizes.body, marginTop: spacing.s, lineHeight: 21 },
  planMeta: { color: colors.textDisabled, fontSize: typography.sizes.small, marginTop: spacing.xs },
  wodKinds: { flexDirection: 'row', gap: spacing.s, marginBottom: spacing.m },
  kindChip: { flex: 1, paddingVertical: spacing.s, borderRadius: 6, alignItems: 'center', borderWidth: 1, borderColor: colors.hairlineStrong },
  kindChipOn: { backgroundColor: colors.signalSoft, borderColor: colors.signal },
  kindText: { color: colors.textSecondary, ...typography.label, fontSize: 9 },
  kindTextOn: { color: colors.signal },
  sessionTitle: { color: colors.signal, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h1, letterSpacing: 0.5 },
  error: { color: colors.readyOrange, fontSize: typography.sizes.small, marginTop: spacing.l, lineHeight: 19 },
});
