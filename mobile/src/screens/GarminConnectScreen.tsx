/**
 * Connexion montre (Garmin) — alimente le suivi et la mise à niveau du plan
 * d'entraînement (boucle adaptative). N'a AUCUNE incidence sur les boutons
 * « Générer » de chaque page (course/force/wod), qui restent manuels.
 *
 * Deux usages immédiats :
 *  - Synchroniser : lit le snapshot santé (Apple/Garmin en build natif, sinon
 *    simulation) et enregistre les métriques du jour.
 *  - Saisie manuelle : reporter à la main HRV / FC repos / sommeil de la montre.
 *
 * La synchro Garmin 100% automatique nécessite des clés API Garmin Connect
 * (OAuth, côté serveur) — voir DEPLOY.md. La saisie manuelle rend l'app
 * exploitable dès maintenant.
 */
import React, { useEffect, useState } from 'react';
import { Linking, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { api } from '../api/client';
import { Card, PrimaryButton, Tag } from '../components/ui';
import { HealthSnapshot, readHealthSnapshot, sleepQualityFromHours } from '../wearable/health';
import { colors, spacing, typography } from '../theme/tokens';

export function GarminConnectScreen({ onClose }: { onClose: () => void }) {
  const [snap, setSnap] = useState<HealthSnapshot | null>(null);
  const [hrv, setHrv] = useState(65);
  const [rhr, setRhr] = useState(48);
  const [sleepH, setSleepH] = useState(75);
  const [status, setStatus] = useState<string | null>(null);
  const [garmin, setGarmin] = useState<{ configured: boolean; connected: boolean } | null>(null);

  useEffect(() => {
    readHealthSnapshot().then(s => {
      setSnap(s);
      if (s.hrv_ms) setHrv(s.hrv_ms);
      if (s.resting_hr) setRhr(s.resting_hr);
      if (s.sleep_hours) setSleepH(Math.round(s.sleep_hours * 10));
    }).catch(() => {});
    api.garminStatus().then(setGarmin).catch(() => setGarmin({ configured: false, connected: false }));
  }, []);

  const today = () => new Date().toISOString().slice(0, 10);

  const connectGarmin = async () => {
    try {
      const { authorize_url } = await api.garminConnect();
      await Linking.openURL(authorize_url); // autorisation sur connect.garmin.com
      setStatus('Autorise l\'accès dans la fenêtre Garmin, puis reviens et synchronise.');
    } catch {
      setStatus('Connexion Garmin indisponible (clés API non configurées côté serveur).');
    }
  };

  const syncGarmin = async () => {
    try {
      const r = await api.garminSync();
      const m = r.metrics || {};
      setStatus(`Garmin synchronisé : HRV ${m.hrv ?? '—'} · FC ${m.resting_hr ?? '—'} · sommeil ${m.sleep_hours ?? '—'} h`);
      api.garminStatus().then(setGarmin).catch(() => {});
    } catch {
      setStatus('Synchronisation Garmin échouée. Vérifie la connexion.');
    }
  };

  const disconnectGarmin = async () => {
    await api.garminDisconnect().catch(() => {});
    setGarmin(g => g ? { ...g, connected: false } : g);
    setStatus('Compte Garmin déconnecté.');
  };

  const syncNow = async () => {
    const s = await readHealthSnapshot();
    await api.recordMetrics({
      date: today(),
      hrv: s.hrv_ms ?? undefined,
      resting_hr: s.resting_hr ?? undefined,
      sleep_hours: s.sleep_hours ?? undefined,
      sleep_quality: s.sleep_quality ?? undefined,
    });
    setStatus(`Synchronisé (${s.source_label})`);
  };

  const saveManual = async () => {
    const hours = sleepH / 10;
    await api.recordMetrics({
      date: today(),
      hrv, resting_hr: rhr, sleep_hours: hours,
      sleep_quality: sleepQualityFromHours(hours),
    });
    setStatus('Données montre enregistrées (saisie manuelle)');
  };

  return (
    <View style={styles.root}>
      <View style={styles.header}>
        <Pressable onPress={onClose} hitSlop={12}><Text style={styles.back}>‹ RETOUR</Text></Pressable>
        <Tag label="MONTRE" color={colors.signal} />
      </View>

      <ScrollView contentContainerStyle={{ padding: spacing.m }}>
        <Text style={styles.h1}>CONNEXION MONTRE</Text>
        <Text style={styles.sub}>
          HRV, FC de repos et sommeil alimentent le suivi et adaptent les séances de
          ton plan. Sans incidence sur les boutons « Générer ».
        </Text>

        {/* Compte Garmin (OAuth serveur) */}
        <Card style={{ padding: spacing.m, marginTop: spacing.m }}>
          <View style={styles.srcRow}>
            <Text style={styles.srcLabel}>COMPTE GARMIN</Text>
            <Tag
              label={garmin?.connected ? 'CONNECTÉ' : garmin?.configured ? 'NON CONNECTÉ' : 'NON CONFIGURÉ'}
              color={garmin?.connected ? colors.signal : garmin?.configured ? colors.readyYellow : colors.textDisabled} />
          </View>
          {garmin?.configured ? (
            garmin.connected ? (
              <>
                <PrimaryButton label="SYNCHRONISER DEPUIS GARMIN" onPress={syncGarmin} />
                <Pressable onPress={disconnectGarmin} style={{ paddingVertical: spacing.m, alignItems: 'center' }}>
                  <Text style={styles.disconnect}>Déconnecter</Text>
                </Pressable>
              </>
            ) : (
              <PrimaryButton label="CONNECTER MON COMPTE GARMIN" onPress={connectGarmin} />
            )
          ) : (
            <Text style={styles.note}>
              La connexion Garmin automatique nécessite des clés API Garmin Connect
              côté serveur (voir DEPLOY.md). En attendant, utilise la synchro montre
              ci-dessous ou la saisie manuelle.
            </Text>
          )}
        </Card>

        {/* Source détectée */}
        <Card style={{ padding: spacing.m, marginTop: spacing.m }}>
          <View style={styles.srcRow}>
            <Text style={styles.srcLabel}>SOURCE DÉTECTÉE</Text>
            <Tag label={(snap?.source_label ?? '—').toUpperCase()}
              color={snap?.source === 'apple_health' || snap?.source === 'garmin' ? colors.signal : colors.textSecondary} />
          </View>
          <View style={styles.metrics}>
            <Metric value={snap?.hrv_ms ? `${snap.hrv_ms}` : '—'} unit="ms" label="HRV" />
            <Metric value={snap?.resting_hr ? `${snap.resting_hr}` : '—'} unit="bpm" label="FC repos" />
            <Metric value={snap?.sleep_hours ? `${snap.sleep_hours}` : '—'} unit="h" label="Sommeil" />
          </View>
          <View style={{ marginTop: spacing.m }}>
            <PrimaryButton label="SYNCHRONISER MAINTENANT" onPress={syncNow} />
          </View>
        </Card>

        {/* Saisie manuelle */}
        <Text style={styles.section}>SAISIE MANUELLE</Text>
        <Card style={{ padding: spacing.m }}>
          <Stepper label="HRV (SDNN, ms)" value={hrv} step={1} min={15} max={150} onChange={setHrv} />
          <Stepper label="FC de repos (bpm)" value={rhr} step={1} min={30} max={90} onChange={setRhr} />
          <Stepper label="Sommeil (h)" value={sleepH} step={5} min={0} max={120}
            onChange={setSleepH} display={(v) => (v / 10).toFixed(1)} />
          <View style={{ marginTop: spacing.s }}>
            <PrimaryButton label="ENREGISTRER" onPress={saveManual} />
          </View>
        </Card>

        {status && <Text style={styles.status}>✓ {status}</Text>}

        <Text style={styles.note}>
          Synchro Garmin 100% automatique : nécessite des clés API Garmin Connect
          (OAuth). En attendant, la saisie manuelle (ou Apple Santé en build natif)
          fait remonter les données dans le suivi et le plan.
        </Text>
      </ScrollView>
    </View>
  );
}

function Metric({ value, unit, label }: { value: string; unit: string; label: string }) {
  return (
    <View style={styles.metric}>
      <Text style={styles.metricValue}>{value}<Text style={styles.metricUnit}> {unit}</Text></Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

function Stepper({ label, value, onChange, step, min, max, display }: {
  label: string; value: number; onChange: (v: number) => void;
  step: number; min: number; max: number; display?: (v: number) => string;
}) {
  const set = (v: number) => onChange(Math.max(min, Math.min(max, v)));
  return (
    <View style={styles.stepRow}>
      <Text style={styles.stepLabel}>{label}</Text>
      <View style={styles.stepCtrl}>
        <Pressable onPress={() => set(value - step)} style={styles.stepBtn}><Text style={styles.stepBtnText}>–</Text></Pressable>
        <Text style={styles.stepValue}>{display ? display(value) : value}</Text>
        <Pressable onPress={() => set(value + step)} style={styles.stepBtn}><Text style={styles.stepBtnText}>+</Text></Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: spacing.m, paddingVertical: spacing.m, borderBottomWidth: 1, borderBottomColor: colors.hairline },
  back: { color: colors.textSecondary, ...typography.label, letterSpacing: 1.5 },
  h1: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h1, letterSpacing: 2 },
  sub: { color: colors.textSecondary, fontSize: typography.sizes.small, marginTop: spacing.xs, lineHeight: 19 },
  srcRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.m },
  srcLabel: { color: colors.textSecondary, ...typography.label },
  metrics: { flexDirection: 'row', justifyContent: 'space-between' },
  metric: { alignItems: 'center', flex: 1 },
  metricValue: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h1 },
  metricUnit: { color: colors.textSecondary, fontSize: typography.sizes.small },
  metricLabel: { color: colors.textDisabled, ...typography.label, fontSize: 9, marginTop: 2 },
  section: { color: colors.textSecondary, ...typography.label, marginTop: spacing.l, marginBottom: spacing.s },
  stepRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: spacing.s },
  stepLabel: { color: colors.textSecondary, fontSize: typography.sizes.body },
  stepCtrl: { flexDirection: 'row', alignItems: 'center', gap: spacing.m },
  stepBtn: { width: 36, height: 36, borderRadius: 18, backgroundColor: colors.bgElevated, borderWidth: 1, borderColor: colors.hairlineStrong, alignItems: 'center', justifyContent: 'center' },
  stepBtnText: { color: colors.signal, fontSize: 20, fontFamily: typography.display.fontFamily },
  stepValue: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2, minWidth: 44, textAlign: 'center' },
  status: { color: colors.signal, fontSize: typography.sizes.small, marginTop: spacing.l, textAlign: 'center' },
  disconnect: { color: colors.textSecondary, ...typography.label, fontSize: 10 },
  note: { color: colors.textDisabled, fontSize: typography.sizes.micro, marginTop: spacing.l, lineHeight: 16 },
});
