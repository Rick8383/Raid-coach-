/**
 * Connexion / Inscription. Inscription par code d'invitation ; le 1er inscrit
 * devient propriétaire et récupère le profil existant (côté serveur). Le jeton
 * est stocké localement par le client API.
 */
import React, { useState } from 'react';
import {
  ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView,
  StyleSheet, Text, TextInput, View,
} from 'react-native';
import { AuthUser, api, setToken } from '../api/client';
import { colors, spacing, typography } from '../theme/tokens';

function errMessage(e: unknown): string {
  const m = e instanceof Error ? e.message : String(e);
  const i = m.indexOf('{');
  if (i >= 0) {
    try { return JSON.parse(m.slice(i)).detail ?? m; } catch { /* noop */ }
  }
  if (m.includes('Network') || m.includes('Failed to fetch')) {
    return "Impossible de joindre le serveur. Vérifie ta connexion.";
  }
  return m;
}

export function AuthScreen({ onAuth }: { onAuth: (u: AuthUser) => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [invite, setInvite] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    if (busy) return;
    setError(null);
    if (!email.trim() || !password) { setError('Email et mot de passe requis.'); return; }
    if (mode === 'register' && password.length < 8) {
      setError('Mot de passe : 8 caractères minimum.'); return;
    }
    setBusy(true);
    try {
      const res = mode === 'login'
        ? await api.login(email.trim().toLowerCase(), password)
        : await api.register(email.trim().toLowerCase(), password, invite.trim() || undefined, name.trim() || undefined);
      await setToken(res.token);
      onAuth(res.user);
    } catch (e) {
      setError(errMessage(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.root}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Text style={styles.brand}>RAID<Text style={styles.accent}> COACH</Text></Text>
        <Text style={styles.sub}>SÉLECTION 2029</Text>

        <View style={styles.tabs}>
          {(['login', 'register'] as const).map(m => (
            <Pressable key={m} onPress={() => { setMode(m); setError(null); }}
              style={[styles.tab, mode === m && styles.tabOn]}>
              <Text style={[styles.tabT, mode === m && styles.tabTOn]}>
                {m === 'login' ? 'CONNEXION' : 'INSCRIPTION'}
              </Text>
            </Pressable>
          ))}
        </View>

        <Text style={styles.label}>EMAIL</Text>
        <TextInput style={styles.input} value={email} onChangeText={setEmail}
          autoCapitalize="none" keyboardType="email-address" autoComplete="email"
          placeholder="toi@exemple.com" placeholderTextColor={colors.textDisabled} />

        <Text style={styles.label}>MOT DE PASSE</Text>
        <TextInput style={styles.input} value={password} onChangeText={setPassword}
          secureTextEntry autoCapitalize="none"
          placeholder={mode === 'register' ? '8 caractères minimum' : '••••••••'}
          placeholderTextColor={colors.textDisabled} />

        {mode === 'register' && (
          <>
            <Text style={styles.label}>PRÉNOM (optionnel)</Text>
            <TextInput style={styles.input} value={name} onChangeText={setName}
              placeholder="Ton prénom" placeholderTextColor={colors.textDisabled} />

            <Text style={styles.label}>CODE D'INVITATION</Text>
            <TextInput style={styles.input} value={invite} onChangeText={setInvite}
              autoCapitalize="none" placeholder="fourni par le coach"
              placeholderTextColor={colors.textDisabled} />
            <Text style={styles.hint}>
              Laisse vide si tu es le premier inscrit (propriétaire) : tu récupères
              alors ton profil existant.
            </Text>
          </>
        )}

        {error && <Text style={styles.error}>{error}</Text>}

        <Pressable onPress={submit} disabled={busy} style={styles.submit}>
          {busy ? <ActivityIndicator color={colors.bg} />
            : <Text style={styles.submitT}>{mode === 'login' ? 'SE CONNECTER' : "S'INSCRIRE"}</Text>}
        </Pressable>

        <Pressable onPress={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(null); }}>
          <Text style={styles.switch}>
            {mode === 'login' ? "Pas encore de compte ? S'inscrire" : 'Déjà un compte ? Se connecter'}
          </Text>
        </Pressable>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.l, paddingTop: spacing.xl * 2 },
  brand: { color: colors.textPrimary, fontFamily: typography.display.fontFamily, fontSize: 34, letterSpacing: 2, textAlign: 'center' },
  accent: { color: colors.signal },
  sub: { color: colors.textDisabled, ...typography.label, fontSize: 10, textAlign: 'center', marginTop: 2, marginBottom: spacing.xl },
  tabs: { flexDirection: 'row', backgroundColor: colors.bgCard, borderRadius: 8, padding: 3, marginBottom: spacing.l },
  tab: { flex: 1, paddingVertical: spacing.s, borderRadius: 6, alignItems: 'center' },
  tabOn: { backgroundColor: colors.signal },
  tabT: { color: colors.textSecondary, ...typography.label, fontSize: 11 },
  tabTOn: { color: colors.bg },
  label: { color: colors.textSecondary, ...typography.label, fontSize: 10, marginTop: spacing.m, marginBottom: spacing.xs },
  input: {
    color: colors.textPrimary, backgroundColor: colors.bgInput, borderRadius: spacing.cardRadius,
    paddingHorizontal: spacing.m, paddingVertical: spacing.m, fontSize: typography.sizes.body,
    borderWidth: 1, borderColor: colors.hairline,
  },
  hint: { color: colors.textDisabled, fontSize: typography.sizes.micro, marginTop: spacing.xs, lineHeight: 16 },
  error: { color: colors.readyOrange, fontSize: typography.sizes.small, marginTop: spacing.m, lineHeight: 18 },
  submit: { backgroundColor: colors.signal, borderRadius: spacing.cardRadius, paddingVertical: 16, alignItems: 'center', marginTop: spacing.l },
  submitT: { color: colors.bg, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2, letterSpacing: 1 },
  switch: { color: colors.signal, fontSize: typography.sizes.small, textAlign: 'center', marginTop: spacing.l },
});
