/**
 * Rendu partagé des séances planifiées d'un jour — source unique d'affichage
 * pour l'Agenda (plan détaillé), l'écran Jour et l'onglet Séances. Comme les
 * trois consomment les MÊMES données (/plan/day ou /plan/weekly, mêmes seeds),
 * une séance donnée est identique partout.
 *
 * Chaque séance se déplie (détail course/force/WOD/natation). En option
 * (`completable`), on peut la marquer « faite » avec son RPE → enregistrée
 * comme séance done (charge + suivi), avec invalidation du cache agenda.
 */
import React, { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { PlanSession, StandbyInfo, api } from '../api/client';
import { RunDetail, StrengthDetail, WodDetail } from './SessionDetail';
import { RpeScale } from './RpeScale';
import { WatchMetricsForm, WatchMetricsView, WatchMetrics } from './WatchMetricsForm';
import { StrengthActualsForm, PerformedView, Performed, performedEntries } from './StrengthActualsForm';
import { colors, spacing, typography } from '../theme/tokens';

const TYPE_COLOR: Record<string, string> = {
  run: colors.fitness, strength: colors.readyRed, crossfit: colors.readyOrange,
  swim: colors.signal, recovery: colors.signal, rest: colors.textDisabled,
};
const TYPE_LABEL: Record<string, string> = {
  run: 'COURSE', strength: 'FORCE', crossfit: 'WOD', swim: 'NATATION',
  recovery: 'RÉCUP', rest: 'REPOS',
};
const COMPLETABLE = new Set(['run', 'strength', 'crossfit', 'swim', 'recovery']);

function SessionExpanded({ s }: { s: PlanSession }) {
  const d = s.detail || {};
  if (s.type === 'run' && Array.isArray(d.body)) return <RunDetail session={d} />;
  if (s.type === 'strength' && (d.main_lift || d.movements)) return <StrengthDetail session={d} />;
  if (s.type === 'crossfit' && Array.isArray(d.description)) return <WodDetail wod={d} />;
  if ((s.type === 'swim' || s.type === 'recovery') && Array.isArray(d.blocks)) {
    // Natation ou mobilité (GOWOD) : liste de blocs minutés + consigne.
    return (
      <View>
        {d.blocks.map((b: string, i: number) => (
          <Text key={i} style={styles.detailLine}>• {b}</Text>))}
        {!!d.note && <Text style={styles.detailNote}>💡 {d.note}</Text>}
      </View>
    );
  }
  return null;
}

const METRIC_KEYS: (keyof WatchMetrics)[] = [
  'distance_km', 'hr_avg', 'hr_max', 'elevation_m', 'calories', 'cadence_spm',
  'te_aerobic', 'te_anaerobic',
];

function CompleteRow({ s, dateIso, alreadyDone, onSaved }: {
  s: PlanSession; dateIso: string; alreadyDone: boolean; onSaved: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [rpe, setRpe] = useState(7);
  const [watchOpen, setWatchOpen] = useState(false);
  const [metrics, setMetrics] = useState<WatchMetrics>({ duration_min: s.duration_min });
  const [liftsOpen, setLiftsOpen] = useState(false);
  const [performed, setPerformed] = useState<Performed | null>(null);
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);
  const [rmSug, setRmSug] = useState<{ lift_key: string; lift_name: string;
    current_1rm: number | null; estimated_1rm: number } | null>(null);
  const [rmUpdated, setRmUpdated] = useState(false);
  const isStrength = s.type === 'strength';

  const applyRm = async () => {
    if (!rmSug) return;
    try {
      await api.setLift1RM(rmSug.lift_key, rmSug.estimated_1rm);
      setRmUpdated(true);
    } catch { /* réessayable */ }
  };

  const save = async () => {
    if (busy) return;                 // anti double-clic pendant l'envoi
    setBusy(true);
    const dur = metrics.duration_min && metrics.duration_min > 0 ? metrics.duration_min : s.duration_min;
    const body: Record<string, unknown> = {
      discipline: s.type, session_date: dateIso, duration_min: dur,
      intensity_rpe: rpe, title: s.title, status: 'done', detail: s.detail ?? {},
    };
    for (const k of METRIC_KEYS) {
      const v = metrics[k];
      if (typeof v === 'number' && v > 0) body[k] = v;
    }
    // Une séance « haut du corps » porte deux mouvements principaux → on
    // enregistre dès qu'un mouvement a des séries renseignées.
    if (performed && performedEntries(performed)
        .some(e => e.sets.some(x => x.load_kg > 0 || x.reps > 0))) {
      body.performed = performed;
    }
    try {
      const res = await api.saveSession(body);
      if (res.rm_suggestion) setRmSug(res.rm_suggestion);
      setDone(true);
      onSaved();   // le parent marque la séance faite → l'état survit au repli/dépli
    } finally { setBusy(false); }
  };

  if (done) {
    return (
      <View>
        <Text style={styles.doneMsg}>✓ Séance enregistrée comme faite (RPE {rpe})</Text>
        {performed ? <PerformedView p={performed} /> : null}
        <WatchMetricsView m={metrics} />
        {rmSug && (rmUpdated ? (
          <Text style={styles.doneMsg}>
            ✓ 1RM {rmSug.lift_name} mis à jour à {rmSug.estimated_1rm} kg — plan recalculé
          </Text>
        ) : (
          // Autorégulation : la série max dépasse le 1RM enregistré → 1 clic
          // pour recaler les charges 5/3/1 sur le vrai niveau.
          <Pressable onPress={applyRm} style={styles.rmBtn}>
            <Text style={styles.rmBtnT}>
              ⬆ Ta série max vaut ≈ {rmSug.estimated_1rm} kg au {rmSug.lift_name}
              {rmSug.current_1rm ? ` (1RM actuel : ${rmSug.current_1rm} kg)` : ''}
              {'\n'}METTRE À JOUR MON 1RM
            </Text>
          </Pressable>
        ))}
      </View>
    );
  }
  if (!COMPLETABLE.has(s.type)) return null;
  // Déjà enregistrée (retour sur l'onglet, autre appareil…) : état persistant,
  // pas de re-clic nécessaire. Le détail est visible dans l'Agenda (Suivi).
  if (alreadyDone && !open) {
    return (
      <View>
        <Text style={styles.doneMsg}>✓ Déjà enregistrée comme faite — comptée dans le suivi</Text>
        <Pressable onPress={() => setOpen(true)} style={styles.editBtn}>
          <Text style={styles.editBtnT}>Modifier (RPE / données)</Text>
        </Pressable>
      </View>
    );
  }
  return (
    <View style={styles.completeBox}>
      {open ? (
        <>
          <Text style={styles.rpeLbl}>DIFFICULTÉ RESSENTIE (RPE)</Text>
          <RpeScale value={rpe} onChange={setRpe} />

          {isStrength && (
            <>
              <Pressable
                onPress={() => setLiftsOpen(o => {
                  if (o) setPerformed(null);   // replié = saisie annulée (pas de valeurs cachées)
                  return !o;
                })}
                style={styles.watchToggle}>
                <Text style={styles.watchToggleT}>
                  {liftsOpen ? '−' : '＋'} Séries réalisées (reps × charge)
                </Text>
              </Pressable>
              {liftsOpen && <StrengthActualsForm detail={s.detail} onChange={setPerformed} />}
            </>
          )}

          <Pressable
            onPress={() => setWatchOpen(o => {
              if (o) setMetrics({ duration_min: s.duration_min });   // replié = saisie annulée
              return !o;
            })}
            style={styles.watchToggle}>
            <Text style={styles.watchToggleT}>
              {watchOpen ? '−' : '＋'} Données réelles de la montre (Garmin)
            </Text>
          </Pressable>
          {watchOpen && <WatchMetricsForm defaultDuration={s.duration_min} onChange={setMetrics} />}

          <Pressable onPress={save} style={[styles.doneBtn, busy && { opacity: 0.5 }]} disabled={busy}>
            <Text style={styles.doneBtnT}>{busy ? '…' : '✓ ENREGISTRER COMME FAIT'}</Text>
          </Pressable>
        </>
      ) : (
        <Pressable onPress={() => setOpen(true)} style={styles.markBtn}>
          <Text style={styles.markBtnT}>✓ MARQUER FAIT</Text>
        </Pressable>
      )}
    </View>
  );
}

const STANDBY_COLOR: Record<string, string> = {
  pause: colors.readyYellow, reboot: colors.signal, vacation: colors.signal,
};

export function PlannedSessions({ sessions, dateIso, completable = false, standby = null }: {
  sessions: PlanSession[];
  dateIso?: string;
  completable?: boolean;
  standby?: StandbyInfo | null;
}) {
  const [open, setOpen] = useState<number | null>(completable && sessions.length === 1 ? 0 : null);
  // État « fait » PERSISTANT : on relit l'historique du jour au montage
  // (le cache est invalidé à chaque enregistrement) → revenir sur l'onglet
  // montre ✓ au lieu de redemander « marquer fait ».
  const [doneKeys, setDoneKeys] = useState<Set<string>>(new Set());
  useEffect(() => {
    if (!completable || !dateIso) return;
    let alive = true;
    api.recentSessions(150).then(res => {   // large → couvre les semaines passées (rétroactif)
      if (!alive) return;
      const keys = new Set<string>();
      for (const r of res.sessions ?? []) {
        if (r.session_date === dateIso && r.status === 'done') {
          keys.add(`${r.discipline}|${r.family_id ?? ''}`);
        }
      }
      setDoneKeys(keys);
    }).catch(() => {});
    return () => { alive = false; };
  }, [completable, dateIso]);

  const banner = standby ? (
    <View style={[styles.standby, { borderLeftColor: STANDBY_COLOR[standby.mode] ?? colors.signal }]}>
      <Text style={[styles.standbyTag, { color: STANDBY_COLOR[standby.mode] ?? colors.signal }]}>
        {standby.mode === 'pause' ? '⏸ STANDBY' : standby.mode === 'reboot' ? '↩ REPRISE' : '🏝 VACANCES'}
      </Text>
      <Text style={styles.standbyMsg}>{standby.message}</Text>
    </View>
  ) : null;

  if (!sessions.length) {
    return (
      <View>
        {banner}
        {!standby && <Text style={styles.rest}>Repos — rien de prescrit aujourd'hui.</Text>}
      </View>
    );
  }
  return (
    <View>
      {banner}
      {sessions.map((s, i) => {
        const opened = open === i;
        return (
          <View key={i}>
            <Pressable onPress={() => setOpen(opened ? null : i)} style={styles.sessRow}>
              <View style={[styles.dot, { backgroundColor: TYPE_COLOR[s.type] ?? colors.textDisabled }]} />
              <View style={{ flex: 1 }}>
                <Text style={styles.sessTitle}>{s.title}</Text>
                <Text style={styles.sessMeta}>
                  {s.moment} · {TYPE_LABEL[s.type] ?? s.type} · {s.duration_min} min
                </Text>
              </View>
              <Text style={styles.chevron}>{opened ? '−' : '+'}</Text>
            </Pressable>
            {opened && (
              <View style={styles.detail}>
                <SessionExpanded s={s} />
                {completable && dateIso && (
                  <CompleteRow s={s} dateIso={dateIso}
                    alreadyDone={doneKeys.has(`${s.type}|${s.title ?? ''}`)}
                    onSaved={() => setDoneKeys(prev =>
                      new Set(prev).add(`${s.type}|${s.title ?? ''}`))} />
                )}
              </View>
            )}
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  sessRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.s, borderTopWidth: 1, borderTopColor: colors.hairline, gap: spacing.s },
  dot: { width: 8, height: 8, borderRadius: 4 },
  sessTitle: { color: colors.textPrimary, fontSize: typography.sizes.body },
  sessMeta: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: 2 },
  chevron: { color: colors.signal, fontSize: 20, width: 20, textAlign: 'center' },
  detail: { paddingLeft: spacing.m, paddingBottom: spacing.s, gap: 2 },
  detailLine: { color: colors.textSecondary, fontSize: typography.sizes.small, lineHeight: 19 },
  detailNote: { color: colors.fitness, fontSize: typography.sizes.small, lineHeight: 18, marginTop: spacing.s },
  rest: { color: colors.textDisabled, fontSize: typography.sizes.small, paddingVertical: spacing.m },
  standby: { borderLeftWidth: 3, paddingLeft: spacing.s, paddingVertical: spacing.xs, marginBottom: spacing.s, backgroundColor: colors.bgElevated, borderRadius: 6 },
  standbyTag: { ...typography.label, fontSize: 10 },
  standbyMsg: { color: colors.textSecondary, fontSize: typography.sizes.small, lineHeight: 18, marginTop: 2 },
  completeBox: { marginTop: spacing.m },
  markBtn: { paddingVertical: 12, borderRadius: spacing.cardRadius, borderWidth: 1, borderColor: colors.signal, alignItems: 'center' },
  markBtnT: { color: colors.signal, ...typography.label, fontSize: 11 },
  rpeLbl: { color: colors.textSecondary, ...typography.label, marginBottom: spacing.s, textAlign: 'center' },
  watchToggle: { marginTop: spacing.m, paddingVertical: spacing.s, alignItems: 'center' },
  watchToggleT: { color: colors.signal, fontSize: typography.sizes.small, ...typography.bodyBold },
  editBtn: { alignItems: 'center', paddingVertical: spacing.s },
  editBtnT: { color: colors.textSecondary, fontSize: typography.sizes.small, textDecorationLine: 'underline' },
  rmBtn: {
    marginTop: spacing.s, backgroundColor: colors.signalSoft, borderWidth: 1,
    borderColor: colors.signal, borderRadius: spacing.cardRadius, padding: spacing.m,
  },
  rmBtnT: { color: colors.signal, fontSize: typography.sizes.small, lineHeight: 19, textAlign: 'center', ...typography.bodyBold },
  doneBtn: { backgroundColor: colors.signal, paddingVertical: 14, borderRadius: spacing.cardRadius, alignItems: 'center', marginTop: spacing.s },
  doneBtnT: { color: colors.bg, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2, letterSpacing: 1 },
  doneMsg: { color: colors.signal, fontSize: typography.sizes.small, paddingVertical: spacing.m, textAlign: 'center' },
});
