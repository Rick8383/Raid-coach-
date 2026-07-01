/**
 * Séances — une page par discipline (Course / Force / WOD), chacune avec :
 *  - le focus du plan d'entraînement en cours (phase roadmap) ;
 *  - un bouton « Générer » spécifique qui produit une séance complète
 *    (indépendant de la décision du jour et des données montre).
 * L'onglet Course inclut aussi les zones FC & allures.
 */
import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { AthleteProfile, DetailedSession, PlanDay, Roadmap, api } from '../api/client';
import { SessionView } from '../components/SessionView';
import { PlannedSessions } from '../components/PlannedSessions';
import { RunZonesView } from './RunZonesScreen';
import { RunGenerator } from '../components/RunGenerator';
import { WodGenerator } from '../components/WodGenerator';
import { StrengthProgram } from '../components/StrengthProgram';
import { ManualSessionForm } from '../components/ManualSessionForm';
import { Card, PrimaryButton, Tag } from '../components/ui';
import { daySchedule, todayLocalAsUTC } from '../schedule';
import { colors, disciplineLabel, spacing, typography } from '../theme/tokens';

type Discipline = 'run' | 'strength' | 'crossfit' | 'manual';

const SEGMENTS: { key: Discipline; label: string }[] = [
  { key: 'run', label: 'COURSE' },
  { key: 'strength', label: 'FORCE' },
  { key: 'crossfit', label: 'WOD' },
  { key: 'manual', label: 'AUTRE' },
];

function weeksToGoal(goalDate?: string): number {
  const target = new Date(goalDate ?? '2029-03-01').getTime();
  return Math.max(8, Math.min(Math.round((target - Date.now()) / (7 * 24 * 3600 * 1000)), 220));
}

export function WorkoutsScreen({ profile }: { profile: AthleteProfile | null }) {
  const [disc, setDisc] = useState<Discipline>('run');
  const [phase, setPhase] = useState<Roadmap | null>(null);
  const [planToday, setPlanToday] = useState<PlanDay | null>(null);
  const todayIso = daySchedule(new Date()).date;

  useEffect(() => {
    api.roadmap(weeksToGoal(profile?.goal_date), 0).then(setPhase).catch(() => {});
  }, [profile]);

  useEffect(() => {
    api.planDay(todayIso, profile?.vma_kmh, profile?.fc_max)
      .then(setPlanToday).catch(() => setPlanToday(null));
  }, [todayIso, profile]);

  // Séance(s) du jour pour la discipline sélectionnée — MÊME source que l'Agenda
  // et l'écran Jour (séance identique pour un jour donné).
  const todaySessions = (planToday?.sessions ?? []).filter(s => s.type === disc);

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

      {/* Séance LIBRE (hors plan) — saisie manuelle comptée dans le suivi */}
      {disc === 'manual' && <ManualSessionForm />}

      {/* Séance du jour selon le plan — identique à l'écran Jour et à l'Agenda */}
      {disc !== 'manual' && (todaySessions.length > 0 || planToday?.standby) && (
        <Card style={{ padding: spacing.m, marginBottom: spacing.m }}>
          <Text style={styles.todayLbl}>SÉANCE DU JOUR · SELON TON PLAN</Text>
          <PlannedSessions sessions={todaySessions} dateIso={todayIso} completable
            standby={planToday?.standby} />
        </Card>
      )}

      {/* Générateurs : explorer / créer une variante (indépendant du plan). */}
      {disc !== 'manual' && <Text style={styles.exploreLbl}>EXPLORER / GÉNÉRER UNE VARIANTE</Text>}
      {disc === 'run' && (
        <>
          <RunGenerator profile={profile} />
          <View style={{ marginTop: spacing.xl }}>
            <RunZonesView profile={profile} />
          </View>
        </>
      )}
      {disc === 'crossfit' && <WodGenerator />}
      {disc === 'strength' && <StrengthProgram />}
    </ScrollView>
  );
}

const DAY_MS = 24 * 3600 * 1000;
const DAY_SHORT = ['DIM', 'LUN', 'MAR', 'MER', 'JEU', 'VEN', 'SAM'];

function nextDays(n: number): { iso: string; label: string }[] {
  const base = todayLocalAsUTC();   // date CALENDRIER LOCAL (pas UTC)
  return Array.from({ length: n }, (_, i) => {
    const d = new Date(Date.UTC(base.getUTCFullYear(), base.getUTCMonth(), base.getUTCDate()) + i * DAY_MS);
    return {
      iso: d.toISOString().slice(0, 10),
      label: i === 0 ? "AUJ." : `${DAY_SHORT[d.getUTCDay()]} ${d.getUTCDate()}`,
    };
  });
}

function DisciplinePanel({ discipline, profile }:
  { discipline: Discipline; profile: AthleteProfile | null }) {
  const [session, setSession] = useState<DetailedSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [wodKind, setWodKind] = useState<'death_by' | 'time_cap'>('death_by');
  const [error, setError] = useState(false);
  const [planDate, setPlanDate] = useState(nextDays(1)[0].iso);
  const [saved, setSaved] = useState<string | null>(null);
  const days = nextDays(7);

  const save = async (status: 'planned' | 'done') => {
    if (!session) return;
    const date = status === 'done' ? nextDays(1)[0].iso : planDate;
    const res = await api.saveSession({
      discipline, session_date: date, duration_min: session.duration_min,
      intensity_rpe: Math.min(10, session.intensity_cap),
      title: session.title, status, detail: session,
    });
    setSaved(status === 'done'
      ? 'Séance enregistrée comme faite'
      : `Planifiée le ${date}${res.queued ? ' (sera synchronisée)' : ''}`);
  };

  const generate = async () => {
    setLoading(true);
    setError(false);
    setSaved(null);
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

          {/* Enregistrer dans l'historique / l'agenda */}
          <Text style={styles.saveLabel}>PLANIFIER LE</Text>
          <View style={styles.dayPicker}>
            {days.map(d => (
              <Pressable key={d.iso} onPress={() => setPlanDate(d.iso)}
                style={[styles.dayChip, planDate === d.iso && styles.dayChipOn]}>
                <Text style={[styles.dayChipText, planDate === d.iso && styles.dayChipTextOn]}>{d.label}</Text>
              </Pressable>
            ))}
          </View>
          <View style={styles.saveRow}>
            <Pressable onPress={() => save('planned')} style={[styles.saveBtn, styles.savePlan]}>
              <Text style={styles.savePlanText}>AJOUTER À L'AGENDA</Text>
            </Pressable>
            <Pressable onPress={() => save('done')} style={[styles.saveBtn, styles.saveDone]}>
              <Text style={styles.saveDoneText}>✓ FAIT</Text>
            </Pressable>
          </View>
          {saved && <Text style={styles.savedMsg}>✓ {saved}</Text>}
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
  todayLbl: { color: colors.signal, ...typography.label, marginBottom: spacing.s },
  exploreLbl: { color: colors.textSecondary, ...typography.label, marginBottom: spacing.s },
  wodKinds: { flexDirection: 'row', gap: spacing.s, marginBottom: spacing.m },
  kindChip: { flex: 1, paddingVertical: spacing.s, borderRadius: 6, alignItems: 'center', borderWidth: 1, borderColor: colors.hairlineStrong },
  kindChipOn: { backgroundColor: colors.signalSoft, borderColor: colors.signal },
  kindText: { color: colors.textSecondary, ...typography.label, fontSize: 9 },
  kindTextOn: { color: colors.signal },
  sessionTitle: { color: colors.signal, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h1, letterSpacing: 0.5 },
  error: { color: colors.readyOrange, fontSize: typography.sizes.small, marginTop: spacing.l, lineHeight: 19 },
  saveLabel: { color: colors.textSecondary, ...typography.label, marginTop: spacing.l, marginBottom: spacing.s },
  dayPicker: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginBottom: spacing.m },
  dayChip: { paddingVertical: spacing.s, paddingHorizontal: spacing.m, borderRadius: 6, backgroundColor: colors.bgCard },
  dayChipOn: { backgroundColor: colors.signalSoft, borderWidth: 1, borderColor: colors.signal },
  dayChipText: { color: colors.textSecondary, ...typography.label, fontSize: 10 },
  dayChipTextOn: { color: colors.signal },
  saveRow: { flexDirection: 'row', gap: spacing.s },
  saveBtn: { flex: 1, paddingVertical: 14, borderRadius: spacing.cardRadius, alignItems: 'center' },
  savePlan: { backgroundColor: colors.bgElevated, borderWidth: 1, borderColor: colors.signal },
  savePlanText: { color: colors.signal, ...typography.label, fontSize: 11 },
  saveDone: { backgroundColor: colors.signal, maxWidth: 110 },
  saveDoneText: { color: colors.bg, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2 },
  savedMsg: { color: colors.signal, fontSize: typography.sizes.small, marginTop: spacing.m, textAlign: 'center' },
});
