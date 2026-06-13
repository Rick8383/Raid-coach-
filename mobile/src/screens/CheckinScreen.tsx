/** Check-in du matin : pré-rempli depuis le wearable (HRV, FC repos, sommeil),
 * complété par 3 curseurs ressentis + interrupteur sciatique. ~30 secondes.
 * Sans check-in, pas de décision. */
import React, { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Switch, Text, View } from 'react-native';
import { api } from '../api/client';
import { GaugeInput } from '../components/GaugeInput';
import { HealthSnapshot, readHealthSnapshot } from '../wearable/health';
import { colors, spacing, typography } from '../theme/tokens';

export function CheckinScreen({ onDone }: { onDone: (c: any) => void }) {
  const [readiness, setReadiness] = useState(70);
  const [fatigue, setFatigue] = useState(40);
  const [sleep, setSleep] = useState(70);
  const [sciatic, setSciatic] = useState(false);
  const [health, setHealth] = useState<HealthSnapshot | null>(null);

  // Lecture wearable au montage : pré-remplit la qualité de sommeil.
  useEffect(() => {
    readHealthSnapshot().then(h => {
      setHealth(h);
      if (h.sleep_quality != null) setSleep(h.sleep_quality);
    }).catch(() => {});
  }, []);

  const submit = async () => {
    const checkin = { readiness, fatigue, sleep, sciatic };
    await api.recordMetrics({
      date: new Date().toISOString().slice(0, 10),
      readiness, fatigue,
      sleep_quality: sleep,
      sleep_hours: health?.sleep_hours ?? undefined,
      hrv: health?.hrv_ms ?? undefined,
      resting_hr: health?.resting_hr ?? undefined,
      sciatic_flare: sciatic,
    });
    onDone(checkin);
  };

  return (
    <View style={styles.root}>
      <Text style={styles.title}>CHECK-IN</Text>

      {/* Données wearable */}
      {health && (
        <View style={styles.wearable}>
          <View style={styles.wearableHead}>
            <Text style={styles.wearableLabel}>DONNÉES MONTRE</Text>
            <Text style={styles.source}>{health.source_label}</Text>
          </View>
          <View style={styles.metrics}>
            <Metric value={health.hrv_ms != null ? `${health.hrv_ms}` : '—'} unit="ms" label="HRV" />
            <Metric value={health.resting_hr != null ? `${health.resting_hr}` : '—'} unit="bpm" label="FC repos" />
            <Metric value={health.sleep_hours != null ? `${health.sleep_hours}` : '—'} unit="h" label="Sommeil" />
          </View>
        </View>
      )}

      <GaugeInput label="Forme ressentie" value={readiness} onChange={setReadiness} />
      <GaugeInput label="Fatigue" value={fatigue} onChange={setFatigue} color={colors.readyOrange} />
      <GaugeInput label="Sommeil" value={sleep} onChange={setSleep} color={colors.fitness} />
      <View style={[styles.row, styles.switchRow]}>
        <Text style={styles.label}>Gêne sciatique aujourd'hui</Text>
        <Switch value={sciatic} onValueChange={setSciatic}
          trackColor={{ true: colors.readyRed, false: colors.hairline }} />
      </View>
      <Pressable style={styles.go} onPress={submit}>
        <Text style={styles.goText}>OBTENIR MA SÉANCE</Text>
      </Pressable>
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

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg, padding: spacing.l, justifyContent: 'center' },
  title: { color: colors.textPrimary, fontFamily: typography.display.fontFamily,
    fontSize: typography.sizes.h1, textAlign: 'center', marginBottom: spacing.l,
    letterSpacing: 2 },
  wearable: {
    backgroundColor: colors.bgCard, borderRadius: spacing.cardRadius,
    padding: spacing.m, marginBottom: spacing.l,
  },
  wearableHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.m },
  wearableLabel: { color: colors.textSecondary, ...typography.label },
  source: { color: colors.signal, ...typography.label, fontSize: 10 },
  metrics: { flexDirection: 'row', justifyContent: 'space-between' },
  metric: { alignItems: 'center', flex: 1 },
  metricValue: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h1 },
  metricUnit: { color: colors.textSecondary, fontSize: typography.sizes.small },
  metricLabel: { color: colors.textDisabled, ...typography.label, fontSize: 9, marginTop: 2 },
  row: { marginBottom: spacing.l },
  rowHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: spacing.xs },
  switchRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  label: { color: colors.textSecondary, ...typography.label },
  value: { color: colors.textPrimary, fontFamily: typography.display.fontFamily,
    fontSize: typography.sizes.h2 },
  go: { backgroundColor: colors.signal, borderRadius: spacing.cardRadius,
    paddingVertical: 16, alignItems: 'center', marginTop: spacing.l },
  goText: { color: colors.bg, fontFamily: typography.display.fontFamily,
    fontSize: typography.sizes.h2, letterSpacing: 1 },
});
