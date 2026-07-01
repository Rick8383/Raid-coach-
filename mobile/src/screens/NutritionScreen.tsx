/**
 * Nutrition Elite+ — 4 onglets :
 *  MACROS (cyclage 3/2/2/3 + garde-fous hormonaux/RED-S),
 *  ALIMENTS (convertisseur macro→grammes + table),
 *  COMPLÉMENTS (créatine, collagène… doses/timing par type de séance),
 *  SYNERGIES (combinaisons d'assimilation + anti-synergies).
 * Tout est evidence-based (sources ISSN / méta-analyses).
 */
import React, { useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import {
  AthleteProfile, FoodItem, Guardrail, MacroTarget, Portions,
  SupplementSchedule, Synergy, AntiSynergy, api,
} from '../api/client';
import { StackBar } from '../components/Chart';
import { Card, Tag } from '../components/ui';
import { daySchedule } from '../schedule';
import { colors, spacing, typography } from '../theme/tokens';

function ageFrom(birth?: string): number {
  if (!birth) return 31;
  return Math.max(14, Math.floor((Date.now() - new Date(birth).getTime()) / (365.25 * 24 * 3600 * 1000)));
}

const DAY_TYPE_LABEL: Record<string, string> = {
  high_carb: 'JOUR GLUCIDES HAUT', medium_carb: 'JOUR GLUCIDES MODÉRÉ', low_carb: 'JOUR GLUCIDES BAS',
};
const EVIDENCE_COLOR: Record<string, string> = {
  'élevée': colors.signal, 'modérée': colors.readyYellow, 'émergente': colors.readyOrange,
};
const LEVEL_COLOR: Record<string, string> = { ok: colors.signal, warn: colors.readyYellow, alert: colors.readyRed };

type Tab = 'macros' | 'aliments' | 'supps' | 'synergies';
const TABS: { k: Tab; l: string }[] = [
  { k: 'macros', l: 'MACROS' }, { k: 'aliments', l: 'ALIMENTS' },
  { k: 'supps', l: 'COMPLÉMENTS' }, { k: 'synergies', l: 'SYNERGIES' },
];

export function NutritionScreen({ profile }: { profile: AthleteProfile | null }) {
  const [tab, setTab] = useState<Tab>('macros');
  const [macros, setMacros] = useState<MacroTarget | null>(null);
  const sched = daySchedule(new Date());
  const activity = sched.intent?.focus === 'double' ? 'high' : sched.intent?.focus === 'swim' ? 'light' : 'moderate';

  useEffect(() => {
    if (!profile) return;
    api.dailyMacros({
      weight_kg: profile.weight_kg ?? 75, height_cm: profile.height_cm ?? 172,
      age: ageFrom(profile.birth_date), body_fat_pct: profile.body_fat_pct,
      target_weight_kg: profile.target_weight_kg, activity,
    }).then(setMacros).catch(() => {});
  }, [profile, activity]);

  return (
    <ScrollView style={styles.root} contentContainerStyle={{ padding: spacing.m }}>
      <Text style={styles.h1}>NUTRITION ELITE+</Text>
      <View style={styles.tabbar}>
        {TABS.map(t => (
          <Pressable key={t.k} onPress={() => setTab(t.k)} style={[styles.tab, tab === t.k && styles.tabOn]}>
            <Text style={[styles.tabT, tab === t.k && styles.tabTOn]}>{t.l}</Text>
          </Pressable>
        ))}
      </View>

      {tab === 'macros' && <MacrosTab macros={macros} profile={profile} sched={sched} activity={activity} />}
      {tab === 'aliments' && <AlimentsTab macros={macros} />}
      {tab === 'supps' && <SupplementsTab />}
      {tab === 'synergies' && <SynergiesTab />}
    </ScrollView>
  );
}

function MacrosTab({ macros, profile, sched, activity }:
  { macros: MacroTarget | null; profile: AthleteProfile | null; sched: any; activity: string }) {
  const [guards, setGuards] = useState<Guardrail[]>([]);
  useEffect(() => {
    if (!macros || !profile) return;
    const ex = activity === 'high' ? 700 : activity === 'light' ? 300 : 450;
    api.nutritionGuardrails({
      weight_kg: profile.weight_kg ?? 75, calories: macros.calories,
      protein_g: macros.protein_g, fat_g: macros.fat_g,
      body_fat_pct: profile.body_fat_pct, exercise_kcal: ex,
    }).then(r => setGuards(r.guardrails)).catch(() => {});
  }, [macros, profile, activity]);

  if (!macros) return <Text style={styles.empty}>Calcul des macros…</Text>;
  return (
    <View>
      <View style={styles.contextRow}>
        <Tag label={sched.isWorkDay ? 'JOUR DE SERVICE' : 'JOUR OFF'}
          color={sched.isWorkDay ? colors.textSecondary : colors.signal} filled={!sched.isWorkDay} />
        <Tag label="PHASE RECOMP" color={colors.fitness} />
      </View>
      <Card style={{ padding: spacing.l, marginTop: spacing.m, alignItems: 'center' }}>
        <Text style={styles.dayType}>{DAY_TYPE_LABEL[macros.day_type] ?? macros.day_type}</Text>
        <Text style={styles.calories}>{macros.calories}</Text>
        <Text style={styles.cLabel}>kcal cible</Text>
      </Card>
      <View style={{ marginTop: spacing.m }}>
        <StackBar segments={[
          { value: macros.protein_g * 4, color: colors.fitness },
          { value: macros.carbs_g * 4, color: colors.signal },
          { value: macros.fat_g * 9, color: colors.readyYellow }]} />
        <View style={styles.legend}>
          <Text style={[styles.leg, { color: colors.fitness }]}>● P {macros.protein_g}g</Text>
          <Text style={[styles.leg, { color: colors.signal }]}>● G {macros.carbs_g}g</Text>
          <Text style={[styles.leg, { color: colors.readyYellow }]}>● L {macros.fat_g}g</Text>
        </View>
      </View>
      {/* Garde-fous */}
      {guards.length > 0 && (
        <View style={{ marginTop: spacing.l }}>
          <Text style={styles.section}>GARDE-FOUS SANTÉ</Text>
          {guards.map(g => (
            <View key={g.code} style={[styles.guard, { borderLeftColor: LEVEL_COLOR[g.level] }]}>
              <Text style={[styles.guardDot, { color: LEVEL_COLOR[g.level] }]}>
                {g.level === 'ok' ? '✓' : '⚠'}
              </Text>
              <Text style={styles.guardMsg}>{g.message}</Text>
            </View>
          ))}
        </View>
      )}
      {/* Répartition protéique + timing péri-entraînement (ISSN / Schoenfeld) */}
      {!!macros.meal_distribution && (
        <View style={{ marginTop: spacing.l }}>
          <Text style={styles.section}>RÉPARTITION & TIMING</Text>
          <Text style={styles.note}>🍽 {macros.meal_distribution.note}</Text>
          {!!macros.peri_workout && (
            <>
              <Text style={styles.note}>⏱ Avant : {macros.peri_workout.avant}</Text>
              <Text style={styles.note}>⏱ Après : {macros.peri_workout.apres}</Text>
              <Text style={styles.note}>⚡ {macros.peri_workout.double_seance}</Text>
            </>
          )}
        </View>
      )}
      {macros.notes.length > 0 && (
        <View style={styles.notes}>{macros.notes.map(n => <Text key={n} style={styles.note}>• {n}</Text>)}</View>
      )}
    </View>
  );
}

function AlimentsTab({ macros }: { macros: MacroTarget | null }) {
  const [foods, setFoods] = useState<FoodItem[]>([]);
  const [protein, setProtein] = useState('poulet');
  const [carb, setCarb] = useState('rizcuit');
  const [fat, setFat] = useState('huileolive');
  const [res, setRes] = useState<Portions | null>(null);

  useEffect(() => { api.nutritionFoods().then(r => setFoods(r.foods)).catch(() => {}); }, []);
  useEffect(() => {
    if (!macros) return;
    api.nutritionPortions({
      target_p: macros.protein_g, target_c: macros.carbs_g, target_f: macros.fat_g,
      protein_id: protein, carb_id: carb, fat_id: fat,
    }).then(setRes).catch(() => {});
  }, [macros, protein, carb, fat]);

  const opt = (cat: string) => foods.filter(f => f.cat === cat || (cat === 'protein' && f.cat === 'mixed'));
  const Picker = ({ cat, val, set }: { cat: string; val: string; set: (s: string) => void }) => (
    <View style={styles.pickRow}>
      {opt(cat).slice(0, 6).map(f => (
        <Pressable key={f.id} onPress={() => set(f.id)} style={[styles.fChip, val === f.id && styles.fChipOn]}>
          <Text style={[styles.fChipT, val === f.id && styles.fChipTOn]}>{f.name.split(' (')[0]}</Text>
        </Pressable>
      ))}
    </View>
  );

  return (
    <View>
      <Text style={styles.section}>CONVERTISSEUR MACRO → GRAMMES</Text>
      <Text style={styles.hint}>Atteins ta cible du jour avec tes aliments. Pèse dans l'état indiqué (cuit/cru).</Text>
      <Text style={styles.pickLabel}>PROTÉINES</Text><Picker cat="protein" val={protein} set={setProtein} />
      <Text style={styles.pickLabel}>GLUCIDES</Text><Picker cat="carb" val={carb} set={setCarb} />
      <Text style={styles.pickLabel}>LIPIDES</Text><Picker cat="fat" val={fat} set={setFat} />

      {res && (
        <Card style={{ padding: spacing.m, marginTop: spacing.m }}>
          {res.items.map(it => (
            <View key={it.id} style={styles.portionRow}>
              <Text style={styles.portionGrams}>{it.grams} g</Text>
              <Text style={styles.portionName}>{it.name}</Text>
              <Text style={styles.portionMacro}>{it.p}P {it.c}G {it.f}L</Text>
            </View>
          ))}
          <Text style={styles.portionTotal}>
            Total ≈ {res.totals.kcal} kcal · {res.totals.p}P / {res.totals.c}G / {res.totals.f}L
          </Text>
        </Card>
      )}
    </View>
  );
}

function SupplementsTab() {
  const [type, setType] = useState('strength');
  const [sch, setSch] = useState<SupplementSchedule | null>(null);
  useEffect(() => { api.nutritionSupplements(type).then(setSch).catch(() => {}); }, [type]);
  const TYPES = [{ k: 'strength', l: 'FORCE' }, { k: 'run', l: 'COURSE' }, { k: 'crossfit', l: 'WOD' }, { k: 'rest', l: 'REPOS' }];
  return (
    <View>
      <View style={styles.pickRow}>
        {TYPES.map(t => (
          <Pressable key={t.k} onPress={() => setType(t.k)} style={[styles.fChip, type === t.k && styles.fChipOn]}>
            <Text style={[styles.fChipT, type === t.k && styles.fChipTOn]}>{t.l}</Text>
          </Pressable>
        ))}
      </View>
      {sch?.groups.map(g => (
        <View key={g.when} style={{ marginTop: spacing.m }}>
          <Text style={styles.section}>{g.label.toUpperCase()}</Text>
          {g.items.map(it => (
            <Card key={it.name} style={{ padding: spacing.m, marginBottom: spacing.s }}>
              <View style={styles.suppHead}>
                <Text style={styles.suppName}>{it.name}</Text>
                <Tag label={it.evidence} color={EVIDENCE_COLOR[it.evidence] ?? colors.textSecondary} />
              </View>
              <Text style={styles.suppDose}>{it.dose}</Text>
              <Text style={styles.suppWith}>⏱ {it.with}</Text>
              <Text style={styles.suppWhy}>{it.why}</Text>
            </Card>
          ))}
        </View>
      ))}
    </View>
  );
}

function SynergiesTab() {
  const [data, setData] = useState<{ synergies: Synergy[]; anti_synergies: AntiSynergy[] } | null>(null);
  useEffect(() => { api.nutritionSynergies().then(setData).catch(() => {}); }, []);
  if (!data) return <Text style={styles.empty}>Chargement…</Text>;
  return (
    <View>
      <Text style={styles.section}>COMBINAISONS QUI BOOSTENT L'ASSIMILATION / LES HORMONES</Text>
      {data.synergies.map(s => (
        <Card key={s.combo} style={{ padding: spacing.m, marginBottom: spacing.s }}>
          <View style={styles.suppHead}>
            <Text style={styles.synCombo}>{s.combo}</Text>
            <Tag label={s.evidence} color={EVIDENCE_COLOR[s.evidence] ?? colors.textSecondary} />
          </View>
          <Text style={styles.suppWhy}>{s.why}</Text>
          <Text style={styles.synEx}>→ {s.example}</Text>
        </Card>
      ))}
      <Text style={styles.section}>À ÉVITER / ESPACER</Text>
      {data.anti_synergies.map(a => (
        <View key={a.pair} style={styles.antiRow}>
          <Text style={styles.antiPair}>✕ {a.pair}</Text>
          <Text style={styles.antiMeta}>{a.mechanism} · {a.magnitude} · {a.delay}</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  h1: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h1, letterSpacing: 2, marginBottom: spacing.m },
  tabbar: { flexDirection: 'row', backgroundColor: colors.bgCard, borderRadius: 8, padding: 3, marginBottom: spacing.m },
  tab: { flex: 1, paddingVertical: spacing.s, borderRadius: 6, alignItems: 'center' },
  tabOn: { backgroundColor: colors.signal },
  tabT: { color: colors.textSecondary, ...typography.label, fontSize: 9 },
  tabTOn: { color: colors.bg },
  empty: { color: colors.textDisabled, textAlign: 'center', marginTop: spacing.xl },
  contextRow: { flexDirection: 'row', gap: spacing.s },
  dayType: { color: colors.textSecondary, ...typography.label },
  calories: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: 52 },
  cLabel: { color: colors.textSecondary, ...typography.label },
  legend: { flexDirection: 'row', justifyContent: 'space-between', marginTop: spacing.s },
  leg: { ...typography.label, fontSize: typography.sizes.micro },
  section: { color: colors.textSecondary, ...typography.label, marginTop: spacing.l, marginBottom: spacing.s },
  guard: { flexDirection: 'row', gap: spacing.s, paddingVertical: spacing.s, paddingHorizontal: spacing.m, borderLeftWidth: 3, backgroundColor: colors.bgCard, borderRadius: 6, marginBottom: spacing.xs },
  guardDot: { fontSize: 14 },
  guardMsg: { color: colors.textPrimary, fontSize: typography.sizes.small, flex: 1, lineHeight: 19 },
  notes: { marginTop: spacing.m, gap: spacing.xs },
  note: { color: colors.textSecondary, fontSize: typography.sizes.small, lineHeight: 20 },
  hint: { color: colors.textDisabled, fontSize: typography.sizes.small, marginBottom: spacing.m },
  pickLabel: { color: colors.textSecondary, ...typography.label, fontSize: 9, marginTop: spacing.s, marginBottom: spacing.xs },
  pickRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs },
  fChip: { paddingVertical: spacing.xs, paddingHorizontal: spacing.s, borderRadius: 6, backgroundColor: colors.bgCard, borderWidth: 1, borderColor: colors.hairline },
  fChipOn: { backgroundColor: colors.signalSoft, borderColor: colors.signal },
  fChipT: { color: colors.textSecondary, ...typography.label, fontSize: 9 },
  fChipTOn: { color: colors.signal },
  portionRow: { flexDirection: 'row', alignItems: 'baseline', paddingVertical: spacing.s, borderTopWidth: 1, borderTopColor: colors.hairline, gap: spacing.s },
  portionGrams: { color: colors.signal, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2, minWidth: 60 },
  portionName: { color: colors.textPrimary, fontSize: typography.sizes.small, flex: 1 },
  portionMacro: { color: colors.textDisabled, fontSize: typography.sizes.micro },
  portionTotal: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: spacing.m, textAlign: 'center' },
  suppHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  suppName: { color: colors.textPrimary, fontFamily: typography.bodyBold.fontFamily, fontSize: typography.sizes.body, flex: 1, paddingRight: spacing.s },
  suppDose: { color: colors.signal, fontSize: typography.sizes.small, marginTop: spacing.xs },
  suppWith: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: 2 },
  suppWhy: { color: colors.textDisabled, fontSize: typography.sizes.small, marginTop: spacing.xs, lineHeight: 18 },
  synCombo: { color: colors.textPrimary, fontFamily: typography.bodyBold.fontFamily, fontSize: typography.sizes.body, flex: 1, paddingRight: spacing.s },
  synEx: { color: colors.signal, fontSize: typography.sizes.small, marginTop: spacing.xs },
  antiRow: { paddingVertical: spacing.s, borderTopWidth: 1, borderTopColor: colors.hairline },
  antiPair: { color: colors.readyOrange, fontSize: typography.sizes.small, ...typography.bodyBold },
  antiMeta: { color: colors.textDisabled, fontSize: typography.sizes.micro, marginTop: 2 },
});
