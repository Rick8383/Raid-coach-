import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { useFonts, Inter_400Regular, Inter_500Medium, Inter_600SemiBold } from '@expo-google-fonts/inter';
import { BarlowCondensed_700Bold } from '@expo-google-fonts/barlow-condensed';
import { flushSyncQueue, SessionToday } from './src/api/client';
import { CheckinScreen } from './src/screens/CheckinScreen';
import { TodayScreen } from './src/screens/TodayScreen';
import { BenchmarksScreen } from './src/screens/BenchmarksScreen';
import { SessionDetailScreen } from './src/screens/SessionDetailScreen';
import { readinessLevelFor, colors, typography } from './src/theme/tokens';

// Profil athlète — sera chargé depuis l'API/profil en v2
const PROFILE = {
  weight: 75,
  current: {
    pullups_max: 16, pushups_max: 60, dips_max: 40, leg_raises_max: 18,
    rope_climb_5m: 1, bench_ratio: 95, squat_ratio: 110, cooper_m: 2850,
  },
};

type Tab = 'today' | 'benchmarks';
type Checkin = { readiness: number; fatigue: number; sleep: number; sciatic: boolean };
type OpenSession = { data: SessionToday; dateIso: string };

export default function App() {
  const [fontsLoaded] = useFonts({
    Inter_400Regular, Inter_500Medium, Inter_600SemiBold, BarlowCondensed_700Bold,
  });
  const [checkin, setCheckin] = useState<Checkin | null>(null);
  const [tab, setTab] = useState<Tab>('today');
  const [openSession, setOpenSession] = useState<OpenSession | null>(null);

  // Vide la file d'écritures offline au lancement et après chaque check-in.
  useEffect(() => {
    flushSyncQueue().catch(() => {});
  }, [checkin]);

  if (!fontsLoaded) {
    return (
      <View style={styles.splash}>
        <Text style={styles.splashTitle}>RAID COACH</Text>
        <ActivityIndicator color={colors.signal} style={{ marginTop: 16 }} />
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.root}>
        {!checkin ? (
          <CheckinScreen onDone={setCheckin} />
        ) : openSession ? (
          <SessionDetailScreen
            session={openSession.data.session}
            level={readinessLevelFor(checkin.readiness, checkin.sciatic)}
            dateIso={openSession.dateIso}
            onClose={() => setOpenSession(null)}
          />
        ) : (
          <>
            <View style={styles.appbar}>
              <Text style={styles.brand}>RAID<Text style={styles.brandAccent}> COACH</Text></Text>
              <Text style={styles.brandSub}>SÉLECTION 2029</Text>
            </View>
            <View style={{ flex: 1 }}>
              {tab === 'today'
                ? <TodayScreen
                    checkin={checkin}
                    onOpenSession={(data, dateIso) => setOpenSession({ data, dateIso })} />
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
  splash: { flex: 1, backgroundColor: colors.bg, alignItems: 'center', justifyContent: 'center' },
  splashTitle: { color: colors.textPrimary, fontSize: 32, letterSpacing: 4, fontWeight: '700' },
  appbar: {
    flexDirection: 'row', alignItems: 'baseline', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 12,
    borderBottomWidth: 1, borderBottomColor: colors.hairline,
  },
  brand: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: 22, letterSpacing: 2 },
  brandAccent: { color: colors.signal },
  brandSub: { color: colors.textDisabled, ...typography.label, fontSize: 10 },
  tabbar: {
    flexDirection: 'row', borderTopWidth: 1, borderTopColor: colors.hairline,
    backgroundColor: colors.bgElevated,
  },
  tab: { flex: 1, paddingVertical: 14, alignItems: 'center' },
  tabText: { color: colors.textDisabled, ...typography.label },
  tabActive: { color: colors.signal },
});
