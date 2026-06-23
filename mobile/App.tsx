import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { useFonts, Inter_400Regular, Inter_500Medium, Inter_600SemiBold } from '@expo-google-fonts/inter';
import { BarlowCondensed_700Bold } from '@expo-google-fonts/barlow-condensed';
import {
  AthleteProfile, AuthUser, api, flushSyncQueue,
  loadToken, clearToken, setUnauthorizedHandler,
} from './src/api/client';
import { AuthScreen } from './src/screens/AuthScreen';
import { OnboardingScreen } from './src/screens/OnboardingScreen';
import { CheckinScreen } from './src/screens/CheckinScreen';
import { TodayScreen } from './src/screens/TodayScreen';
import { AgendaScreen } from './src/screens/AgendaScreen';
import { WorkoutsScreen } from './src/screens/WorkoutsScreen';
import { NutritionScreen } from './src/screens/NutritionScreen';
import { BenchmarksScreen } from './src/screens/BenchmarksScreen';
import { ProfileScreen } from './src/screens/ProfileScreen';
import { CoachChatScreen } from './src/screens/CoachChatScreen';
import { GarminConnectScreen } from './src/screens/GarminConnectScreen';
import { initReminders } from './src/notifications';
import { colors, typography } from './src/theme/tokens';

type Tab = 'today' | 'workouts' | 'agenda' | 'nutrition' | 'benchmarks' | 'coach' | 'profile';
type Checkin = { readiness: number; fatigue: number; sleep: number; sciatic: boolean };

const TABS: { key: Tab; label: string }[] = [
  { key: 'today', label: 'JOUR' },
  { key: 'workouts', label: 'SÉANCES' },
  { key: 'agenda', label: 'AGENDA' },
  { key: 'nutrition', label: 'NUTRITION' },
  { key: 'benchmarks', label: 'OBJECTIFS' },
  { key: 'coach', label: 'COACH' },
  { key: 'profile', label: 'PROFIL' },
];

export default function App() {
  const [fontsLoaded] = useFonts({
    Inter_400Regular, Inter_500Medium, Inter_600SemiBold, BarlowCondensed_700Bold,
  });
  const [checkin, setCheckin] = useState<Checkin | null>(null);
  const [tab, setTab] = useState<Tab>('today');
  const [showConnect, setShowConnect] = useState(false);
  const [profile, setProfile] = useState<AthleteProfile | null>(null);
  const [profileLoaded, setProfileLoaded] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);

  // Auth : restaure la session au lancement ; un 401 ailleurs → retour login.
  useEffect(() => {
    setUnauthorizedHandler(() => { clearToken().catch(() => {}); setUser(null); setCheckin(null); });
    (async () => {
      const tok = await loadToken().catch(() => null);
      if (tok) {
        try { setUser((await api.me()).user); } catch { await clearToken().catch(() => {}); }
      }
      setAuthChecked(true);
    })();
    return () => setUnauthorizedHandler(null);
  }, []);

  // Charge le profil de l'utilisateur connecté + programme les rappels.
  useEffect(() => {
    if (!user) { setProfileLoaded(false); return; }
    setProfileLoaded(false);
    api.profile().then(setProfile).catch(() => {}).finally(() => setProfileLoaded(true));
    initReminders().catch(() => {});
  }, [user]);

  // Vide la file d'écritures offline au lancement et après chaque check-in.
  useEffect(() => {
    flushSyncQueue().catch(() => {});
  }, [checkin]);

  const logout = async () => {
    await clearToken().catch(() => {});
    setUser(null); setCheckin(null); setProfile(null); setProfileLoaded(false); setTab('today');
  };

  // Onboarding requis tant que le rythme de travail n'est pas défini (nouveaux comptes).
  const needsOnboarding = !!user && profileLoaded && !profile?.work_schedule;

  if (!fontsLoaded || !authChecked || (user && !profileLoaded)) {
    return (
      <View style={styles.splash}>
        <Text style={styles.splashTitle}>RAID COACH</Text>
        <ActivityIndicator color={colors.signal} style={{ marginTop: 16 }} />
      </View>
    );
  }

  if (!user) {
    return (
      <SafeAreaProvider>
        <SafeAreaView style={styles.root}>
          <AuthScreen onAuth={setUser} />
        </SafeAreaView>
      </SafeAreaProvider>
    );
  }

  if (needsOnboarding) {
    return (
      <SafeAreaProvider>
        <SafeAreaView style={styles.root}>
          <OnboardingScreen onDone={(p) => { setProfile(p); }} />
        </SafeAreaView>
      </SafeAreaProvider>
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

  if (showConnect) {
    return (
      <SafeAreaProvider>
        <SafeAreaView style={styles.root}>
          <GarminConnectScreen onClose={() => setShowConnect(false)} />
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
          {tab === 'today' && <TodayScreen checkin={checkin} profile={profile} />}
          {tab === 'workouts' && <WorkoutsScreen profile={profile} />}
          {tab === 'agenda' && <AgendaScreen profile={profile} />}
          {tab === 'nutrition' && <NutritionScreen profile={profile} />}
          {tab === 'benchmarks' && <BenchmarksScreen profile={profile} />}
          {tab === 'coach' && <CoachChatScreen profile={profile} />}
          {tab === 'profile' && (
            <ProfileScreen profile={profile} onProfile={setProfile}
              onConnectWatch={() => setShowConnect(true)}
              user={user} onLogout={logout} />
          )}
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
  tabText: { color: colors.textDisabled, fontFamily: typography.label.fontFamily, fontSize: 9, letterSpacing: 0.3, textTransform: 'uppercase' },
  tabActive: { color: colors.signal },
});
