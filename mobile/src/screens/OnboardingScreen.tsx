/**
 * Onboarding (1er login d'un nouvel utilisateur) — niveau, objectif et RYTHME
 * de travail. Le plan s'adapte ensuite au rythme de chacun (3/2/2/3 ou hebdo).
 * Tout est modifiable plus tard dans Profil. Sauvegarde via PATCH /profile.
 */
import React, { useState } from 'react';
import {
  ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView,
  StyleSheet, Text, TextInput, View,
} from 'react-native';
import { AthleteProfile, api } from '../api/client';
import { NumberField } from '../components/NumberField';
import { DayCode, DAY_CODES, DAY_LABELS, todayLocalAsUTC } from '../schedule';
import { colors, spacing, typography } from '../theme/tokens';

const DAY_MS = 24 * 3600 * 1000;

function mondayThisWeekISO(offsetWeeks = 0): string {
  const t = todayLocalAsUTC();   // date CALENDRIER LOCAL (pas UTC)
  const utc = Date.UTC(t.getUTCFullYear(), t.getUTCMonth(), t.getUTCDate());
  const isoWd = (t.getUTCDay() + 6) % 7;
  return new Date(utc - isoWd * DAY_MS + offsetWeeks * 7 * DAY_MS).toISOString().slice(0, 10);
}

function goalDateIn(months: number): string {
  const t = todayLocalAsUTC();
  return new Date(Date.UTC(t.getUTCFullYear(), t.getUTCMonth() + months, t.getUTCDate()))
    .toISOString().slice(0, 10);
}

type Rythme = 'police_3223' | 'weekly';

export function OnboardingScreen({ onDone }: { onDone: (p: AthleteProfile) => void }) {
  const [vma, setVma] = useState(14);
  const [fcmax, setFcmax] = useState(186);
  const [goal, setGoal] = useState('');
  const [horizon, setHorizon] = useState(12); // mois
  const [rythme, setRythme] = useState<Rythme>('police_3223');
  const [bigThisWeek, setBigThisWeek] = useState(true);
  const [days, setDays] = useState<DayCode[]>(['mon', 'wed', 'fri', 'sun']);
  const [style, setStyle] = useState<'split' | 'fullbody'>('split');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleDay = (d: DayCode) =>
    setDays(cur => cur.includes(d) ? cur.filter(x => x !== d) : [...cur, d]);

  const submit = async () => {
    setError(null);
    const work_schedule = rythme === 'police_3223'
      ? { type: 'police_3223', anchor_big_week_monday: mondayThisWeekISO(bigThisWeek ? 0 : -1), training_style: style }
      : { type: 'weekly', training_days: days, training_style: style };
    if (rythme === 'weekly' && days.length === 0) {
      setError('Choisis au moins un jour d\'entraînement.'); return;
    }
    setBusy(true);
    try {
      const updated = await api.updateProfile({
        vma_kmh: vma, fc_max: fcmax,
        main_goal: goal.trim() || 'Objectif perso',
        goal_date: goalDateIn(horizon),
        work_schedule,
      });
      onDone(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.root}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Text style={styles.h1}>BIENVENUE</Text>
        <Text style={styles.sub}>Configure ton profil — le plan s'adaptera à toi.</Text>

        <Text style={styles.section}>TON NIVEAU</Text>
        <FieldRow label="VMA (km/h)">
          <NumberField value={vma} step={0.5} min={8} max={22} decimals={1} onChange={setVma} />
        </FieldRow>
        <FieldRow label="FC max (bpm)">
          <NumberField value={fcmax} step={1} min={150} max={210} onChange={setFcmax} />
        </FieldRow>

        <Text style={styles.section}>TON OBJECTIF</Text>
        <TextInput style={styles.input} value={goal} onChangeText={setGoal}
          placeholder="ex. Hyrox, trail 50 km, sélection…" placeholderTextColor={colors.textDisabled} />
        <FieldRow label="Échéance (mois)">
          <NumberField value={horizon} step={1} min={3} max={48} onChange={setHorizon} />
        </FieldRow>

        <Text style={styles.section}>TON RYTHME DE TRAVAIL</Text>
        <View style={styles.modeRow}>
          {([['police_3223', '3/2/2/3 (police)'], ['weekly', 'Hebdomadaire']] as const).map(([m, l]) => (
            <Pressable key={m} onPress={() => setRythme(m)} style={[styles.modeBtn, rythme === m && styles.modeBtnOn]}>
              <Text style={[styles.modeT, rythme === m && styles.modeTOn]}>{l}</Text>
            </Pressable>
          ))}
        </View>

        {rythme === 'police_3223' ? (
          <>
            <Text style={styles.q}>Cette semaine, tu es en :</Text>
            <View style={styles.modeRow}>
              {([[true, 'GRANDE semaine'], [false, 'PETITE semaine']] as const).map(([b, l]) => (
                <Pressable key={l} onPress={() => setBigThisWeek(b)} style={[styles.modeBtn, bigThisWeek === b && styles.modeBtnOn]}>
                  <Text style={[styles.modeT, bigThisWeek === b && styles.modeTOn]}>{l}</Text>
                </Pressable>
              ))}
            </View>
            <Text style={styles.hint}>Grande = service lun/mar/ven/sam/dim · Petite = service mer/jeu.</Text>
          </>
        ) : (
          <>
            <Text style={styles.q}>Tes jours d'entraînement :</Text>
            <View style={styles.daysRow}>
              {DAY_CODES.map(d => (
                <Pressable key={d} onPress={() => toggleDay(d)}
                  style={[styles.dayChip, days.includes(d) && styles.dayChipOn]}>
                  <Text style={[styles.dayT, days.includes(d) && styles.dayTOn]}>{DAY_LABELS[d]}</Text>
                </Pressable>
              ))}
            </View>
            <Text style={styles.hint}>{days.length} séance(s)/semaine. Les autres jours = repos.</Text>
          </>
        )}

        <Text style={styles.section}>STYLE D'ENTRAÎNEMENT (FORCE)</Text>
        <View style={styles.modeRow}>
          {([['split', 'SPLIT (push/pull/legs)'], ['fullbody', 'FULL BODY (1h-1h15)']] as const).map(([m, l]) => (
            <Pressable key={m} onPress={() => setStyle(m)} style={[styles.modeBtn, style === m && styles.modeBtnOn]}>
              <Text style={[styles.modeT, style === m && styles.modeTOn]}>{l}</Text>
            </Pressable>
          ))}
        </View>
        <Text style={styles.hint}>
          Full body = chaque séance force travaille tout le corps (squat + DC + rowing),
          1h-1h15 max. Split = un groupe par séance.
        </Text>

        {error && <Text style={styles.error}>{error}</Text>}

        <Pressable onPress={submit} disabled={busy} style={styles.submit}>
          {busy ? <ActivityIndicator color={colors.bg} />
            : <Text style={styles.submitT}>C'EST PARTI</Text>}
        </Pressable>
        <Text style={styles.hint}>Tout est modifiable plus tard dans Profil.</Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function FieldRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <View style={styles.stepRow}>
      <Text style={styles.stepLbl}>{label}</Text>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.l, paddingTop: spacing.xl },
  h1: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: 30, letterSpacing: 1 },
  sub: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: spacing.xs, marginBottom: spacing.m },
  section: { color: colors.signal, ...typography.label, marginTop: spacing.l, marginBottom: spacing.s },
  q: { color: colors.textPrimary, fontSize: typography.sizes.body, marginTop: spacing.m, marginBottom: spacing.s },
  input: {
    color: colors.textPrimary, backgroundColor: colors.bgInput, borderRadius: spacing.cardRadius,
    paddingHorizontal: spacing.m, paddingVertical: spacing.m, fontSize: typography.sizes.body,
    borderWidth: 1, borderColor: colors.hairline,
  },
  stepRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: spacing.s },
  stepLbl: { color: colors.textSecondary, fontSize: typography.sizes.body },
  stepCtrl: { flexDirection: 'row', alignItems: 'center', gap: spacing.m },
  stepBtn: { width: 38, height: 38, borderRadius: 19, backgroundColor: colors.bgElevated, borderWidth: 1, borderColor: colors.hairlineStrong, alignItems: 'center', justifyContent: 'center' },
  stepBtnT: { color: colors.signal, fontSize: 22, fontFamily: typography.display.fontFamily },
  stepVal: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2, minWidth: 56, textAlign: 'center' },
  modeRow: { flexDirection: 'row', gap: spacing.s, marginTop: spacing.s },
  modeBtn: { flex: 1, paddingVertical: spacing.m, borderRadius: 6, alignItems: 'center', borderWidth: 1, borderColor: colors.hairlineStrong },
  modeBtnOn: { backgroundColor: colors.signalSoft, borderColor: colors.signal },
  modeT: { color: colors.textSecondary, ...typography.label, fontSize: 10, textAlign: 'center' },
  modeTOn: { color: colors.signal },
  daysRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs },
  dayChip: { width: 42, paddingVertical: spacing.s, borderRadius: 6, alignItems: 'center', backgroundColor: colors.bgCard, borderWidth: 1, borderColor: colors.hairline },
  dayChipOn: { backgroundColor: colors.signalSoft, borderColor: colors.signal },
  dayT: { color: colors.textSecondary, ...typography.label, fontSize: 9 },
  dayTOn: { color: colors.signal },
  hint: { color: colors.textDisabled, fontSize: typography.sizes.micro, marginTop: spacing.s, lineHeight: 16 },
  error: { color: colors.readyOrange, fontSize: typography.sizes.small, marginTop: spacing.m },
  submit: { backgroundColor: colors.signal, borderRadius: spacing.cardRadius, paddingVertical: 16, alignItems: 'center', marginTop: spacing.l },
  submitT: { color: colors.bg, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2, letterSpacing: 1 },
});
