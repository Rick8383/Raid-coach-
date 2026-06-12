import React, { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { flushSyncQueue } from './src/api/client';
import { CheckinScreen } from './src/screens/CheckinScreen';
import { TodayScreen } from './src/screens/TodayScreen';
import { BenchmarksScreen } from './src/screens/BenchmarksScreen';
import { colors, typography } from './src/theme/tokens';

// Profil athlète — sera chargé depuis l'API/profil en v2
const PROFILE = {
  weight: 75,
  current: {
    pullups_max: 16, pushups_max: 60, dips_max: 40, leg_raises_max: 18,
    rope_climb_5m: 1, bench_ratio: 95, squat_ratio: 110, cooper_m: 2850,
  },
};

type Tab = 'today' | 'benchmarks';

export default function App() {
  const [checkin, setCheckin] = useState<any>(null);
  const [tab, setTab] = useState<Tab>('today');

  // Vide la file d'écritures offline au lancement et après chaque check-in.
  useEffect(() => {
    flushSyncQueue().catch(() => {});
  }, [checkin]);

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.root}>
        {!checkin ? (
          <CheckinScreen onDone={setCheckin} />
        ) : (
          <>
            <View style={{ flex: 1 }}>
              {tab === 'today'
                ? <TodayScreen checkin={checkin} />
                : <BenchmarksScreen profile={PROFILE} />}
            </View>
            <View style={styles.tabbar}>
              {(['today', 'benchmarks'] as Tab[]).map(t => (
                <Pressable key={t} style={styles.tab} onPress={() => setTab(t)}>
                  <Text style={[styles.tabText, tab === t && styles.tabActive]}>
                    {t === 'today' ? "AUJOURD'HUI" : 'OBJECTIFS'}
                  </Text>
                </Pressable>
              ))}
            </View>
          </>
        )}
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  tabbar: { flexDirection: 'row', borderTopWidth: 1, borderTopColor: colors.hairline,
    backgroundColor: colors.bgElevated },
  tab: { flex: 1, paddingVertical: 14, alignItems: 'center' },
  tabText: { color: colors.textDisabled, ...typography.label },
  tabActive: { color: colors.signal },
});
