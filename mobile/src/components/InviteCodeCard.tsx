/**
 * Gestion du code d'invitation par le propriétaire (in-app, sans Render).
 * Le code est stocké côté serveur (privé). Le proprio le donne à ses amis pour
 * qu'ils s'inscrivent.
 */
import React, { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { api } from '../api/client';
import { Card } from './ui';
import { colors, spacing, typography } from '../theme/tokens';

export function InviteCodeCard() {
  const [code, setCode] = useState('');
  const [loaded, setLoaded] = useState(false);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.getInviteCode()
      .then(r => setCode(r.invite_code || ''))
      .catch(() => {})
      .finally(() => setLoaded(true));
  }, []);

  const save = async () => {
    setBusy(true);
    try {
      const r = await api.setInviteCode(code.trim());
      setCode(r.invite_code || '');
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch { /* ignore */ } finally { setBusy(false); }
  };

  if (!loaded) return null;

  return (
    <>
      <Text style={styles.section}>CODE D'INVITATION (AMIS)</Text>
      <Card style={{ padding: spacing.m }}>
        <Text style={styles.hint}>
          Définis un code et donne-le à tes amis : ils le saisissent à l'inscription
          pour créer leur compte. Laisse vide pour fermer les inscriptions.
        </Text>
        <View style={styles.row}>
          <TextInput style={styles.input} value={code} onChangeText={(t) => { setCode(t); setSaved(false); }}
            autoCapitalize="characters" placeholder="ex. 1995" placeholderTextColor={colors.textDisabled} />
          <Pressable onPress={save} disabled={busy} style={styles.btn}>
            <Text style={styles.btnT}>{busy ? '…' : 'OK'}</Text>
          </Pressable>
        </View>
        {saved && <Text style={styles.saved}>✓ Code enregistré{code ? ` : ${code}` : ' (inscriptions fermées)'}</Text>}
      </Card>
    </>
  );
}

const styles = StyleSheet.create({
  section: { color: colors.textSecondary, ...typography.label, marginTop: spacing.l, marginBottom: spacing.s },
  hint: { color: colors.textDisabled, fontSize: typography.sizes.micro, lineHeight: 16, marginBottom: spacing.s },
  row: { flexDirection: 'row', alignItems: 'center', gap: spacing.s },
  input: {
    flex: 1, color: colors.textPrimary, backgroundColor: colors.bgInput, borderRadius: spacing.cardRadius,
    paddingHorizontal: spacing.m, paddingVertical: spacing.s, fontSize: typography.sizes.body,
    borderWidth: 1, borderColor: colors.hairline, letterSpacing: 2,
  },
  btn: { paddingHorizontal: spacing.l, paddingVertical: spacing.m, borderRadius: spacing.cardRadius, backgroundColor: colors.signal },
  btnT: { color: colors.bg, fontFamily: typography.display.fontFamily, fontSize: typography.sizes.h2 },
  saved: { color: colors.signal, fontSize: typography.sizes.small, marginTop: spacing.s },
});
