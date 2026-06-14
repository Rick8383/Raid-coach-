/**
 * Rappels locaux (sans serveur push) :
 *  - check-in du matin (quotidien, heure configurable) ;
 *  - re-test des benchmarks (~toutes les 10 semaines, ré-armé à chaque ouverture).
 *
 * Tout est encapsulé dans des try/catch : sur le web ou sans permission,
 * les fonctions ne font rien plutôt que de planter.
 */
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Notifications from 'expo-notifications';

const PREFS_KEY = 'raid_coach:reminders';
const BENCHMARK_DAYS = 70; // ~10 semaines

export interface ReminderPrefs {
  enabled: boolean;
  hour: number;   // heure du check-in (0-23)
  minute: number;
}

const DEFAULT_PREFS: ReminderPrefs = { enabled: true, hour: 7, minute: 0 };

export async function loadPrefs(): Promise<ReminderPrefs> {
  try {
    const raw = await AsyncStorage.getItem(PREFS_KEY);
    return raw ? { ...DEFAULT_PREFS, ...JSON.parse(raw) } : DEFAULT_PREFS;
  } catch {
    return DEFAULT_PREFS;
  }
}

async function savePrefs(prefs: ReminderPrefs): Promise<void> {
  try {
    await AsyncStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
  } catch {
    /* ignore */
  }
}

// Gardé hors web et protégé : un échec ici ne doit jamais empêcher l'app de rendre.
if (Platform.OS !== 'web') {
  try {
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: false,
        shouldSetBadge: false,
      }),
    });
  } catch {
    /* module non disponible / non supporté */
  }
}

async function ensurePermission(): Promise<boolean> {
  if (Platform.OS === 'web') return false;
  try {
    const current = await Notifications.getPermissionsAsync();
    if (current.granted) return true;
    const req = await Notifications.requestPermissionsAsync();
    return req.granted;
  } catch {
    return false;
  }
}

/** (Re)programme les deux rappels selon les préférences. */
export async function applyReminders(prefs: ReminderPrefs): Promise<void> {
  await savePrefs(prefs);
  if (Platform.OS === 'web') return;
  try {
    await Notifications.cancelAllScheduledNotificationsAsync();
    if (!prefs.enabled) return;
    if (!(await ensurePermission())) return;

    // Check-in quotidien
    await Notifications.scheduleNotificationAsync({
      content: {
        title: 'Check-in du matin',
        body: 'Renseigne ta forme du jour pour obtenir ta séance.',
      },
      trigger: { hour: prefs.hour, minute: prefs.minute, repeats: true },
    });

    // Re-test benchmarks (~10 semaines)
    await Notifications.scheduleNotificationAsync({
      content: {
        title: 'Re-test benchmarks',
        body: 'Il est temps de re-tester tes maxes (tractions, Cooper, WODs sélection).',
      },
      trigger: { seconds: BENCHMARK_DAYS * 24 * 3600, repeats: false },
    });
  } catch {
    /* ignore (permissions, plateforme) */
  }
}

/** À appeler au lancement : applique les préférences enregistrées. */
export async function initReminders(): Promise<ReminderPrefs> {
  const prefs = await loadPrefs();
  await applyReminders(prefs);
  return prefs;
}
