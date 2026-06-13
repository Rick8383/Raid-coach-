import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { useFonts, Inter_400Regular, Inter_500Medium, Inter_600SemiBold } from '@expo-google-fonts/inter';
import { BarlowCondensed_700Bold } from '@expo-google-fonts/barlow-condensed';
import { AthleteProfile, api, flushSyncQueue, SessionToday } from './src/api/client';
import { CheckinScreen } from './src/screens/CheckinScreen';
import { TodayScreen } from './src/screens/TodayScreen';
import { AgendaScreen } from './src/screens/AgendaScreen';
import { NutritionScreen } from './src/screens/NutritionScreen';
import { BenchmarksScreen } from './src/screens/BenchmarksScreen';
import { ProfileScreen } from './src/screens/ProfileScreen';
import { SessionDetailScreen } from './src/screens/SessionDetailScreen';
import { readinessLevelFor, colors, typography } from './src/theme/tokens';

type Tab = 'today' | 'agenda' | 'nutrition' | 'benchmarks' | 'profile';
type Checkin = { readiness: number; fatigue: number; sleep: number; sciatic: boolean };
type OpenSession = { data: SessionToday; dateIso: string };

const TABS: { key: Tab; label: string }[] = [
  { key: 'today', label: 'JOUR' },
  { key: 'agenda', label: 'AGENDA' },
  { key: 'nutrition', label: 'NUTRITION' },
  { key: 'benchmarks', label: 'OBJECTIFS' },
  { key: 'profile', label: 'PROFIL' },
];

export default function App() {
  const [fontsLoaded] = useFonts({
    Inter_400Regular, Inter_500Medium, Inter_600SemiBold, BarlowCondensed_700Bold,
  });
  const [checkin, setCheckin] = useState<Checkin | null>(null);
  const [tab, setTab] = useState<Tab>('today');
  const [openSession, setOpenSession] = useState<OpenSession | null>(null);
  const [profile, setProfile] = useState<AthleteProfile | null>(null);

  // Charge le profil réel (avec cache offline) au lancement.
  useEffect(() => {
    api.profile().then(setProfile).catch(() => {});
  }, []);

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

  if (!checkin) {
    return (
      <SafeAreaProvider>
        <SafeAreaView style={styles.root}>
          <CheckinScreen onDone={setCheckin} />
        </SafeAreaView>
      </SafeAreaProvider>
    );
  }

  if (openSession) {
    return (
      <SafeAreaProvider>
        <SafeAreaView style={styles.root}>
          <SessionDetailScreen
            session={openSession.data.session}
            level={readinessLevelFor(checkin.readiness, checkin.sciatic)}
            dateIso={openSession.dateIso}
            onClose={() => setOpenSession(null)}
          />
        </SafeAreaView>
      </SafeAreaProvider>
    );
  }

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.root}>
        <View style={styles.appbar}>
          <Text style={styles.brand}>RAID<Text style={styles.brandAccent}> COACH</Text></Text>
          <Text style={styles.brandSub}>SÉLECTION 2029</Text>
        </View>
        <View style={{ flex: 1 }}>
          {tab === 'today' && (
            <TodayScreen
              checkin={checkin}
              onOpenSession={(data, dateIso) => setOpenSession({ data, dateIso })} />
          )}
          {tab === 'agenda' && <AgendaScreen />}
          {tab === 'nutrition' && <NutritionScreen profile={profile} />}
          {tab === 'benchmarks' && <BenchmarksScreen profile={profile} />}
          {tab === 'profile' && <ProfileScreen profile={profile} onProfile={setProfile} />}
        </View>
        <View style={styles.tabbar}>
          {TABS.map(t => (
            <Pressable key={t.key} style={styles.tab} onPress={() => setTab(t.key)}>
              <Text style={[styles.tabText, tab === t.key && styles.tabActive]}>{t.label}</Text>
            </Pressable>
          ))}
        </View>
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
  tabText: { color: colors.textDisabled, fontFamily: typography.label.fontFamily, fontSize: 10, letterSpacing: 0.5, textTransform: 'uppercase' },
  tabActive: { color: colors.signal },
});
