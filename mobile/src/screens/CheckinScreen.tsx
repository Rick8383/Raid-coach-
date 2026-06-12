/** Check-in du matin : 30 secondes, 4 curseurs, 1 interrupteur sciatique.
 * C'est la porte d'entrée quotidienne — sans check-in, pas de décision. */
import React, { useState } from 'react';
import { Pressable, StyleSheet, Switch, Text, View } from 'react-native';
import Slider from '@react-native-community/slider';
import { api } from '../api/client';
import { colors, spacing, typography } from '../theme/tokens';

export function CheckinScreen({ onDone }: { onDone: (c: any) => void }) {
  const [readiness, setReadiness] = useState(70);
  const [fatigue, setFatigue] = useState(40);
  const [sleep, setSleep] = useState(70);
  const [sciatic, setSciatic] = useState(false);

  const submit = async () => {
    const checkin = { readiness, fatigue, sleep, sciatic };
    await api.recordMetrics({
      date: new Date().toISOString().slice(0, 10),
      readiness, fatigue,
      sleep_quality: sleep,
      sciatic_flare: sciatic,
    });
    onDone(checkin);
  };

  const Row = ({ label, value, set }: any) => (
    <View style={styles.row}>
      <View style={styles.rowHeader}>
        <Text style={styles.label}>{label}</Text>
        <Text style={styles.value}>{value}</Text>
      </View>
      <Slider minimumValue={0} maximumValue={100} step={5} value={value}
        onValueChange={set} minimumTrackTintColor={colors.signal}
        maximumTrackTintColor={colors.hairline} thumbTintColor={colors.textPrimary} />
    </View>
  );

  return (
    <View style={styles.root}>
      <Text style={styles.title}>CHECK-IN</Text>
      <Row label="Forme ressentie" value={readiness} set={setReadiness} />
      <Row label="Fatigue" value={fatigue} set={setFatigue} />
      <Row label="Sommeil" value={sleep} set={setSleep} />
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

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg, padding: spacing.l, justifyContent: 'center' },
  title: { color: colors.textPrimary, fontFamily: typography.display.fontFamily,
    fontSize: typography.sizes.h1, textAlign: 'center', marginBottom: spacing.xl,
    letterSpacing: 2 },
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
