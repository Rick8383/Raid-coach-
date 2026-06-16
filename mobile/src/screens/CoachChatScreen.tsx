/**
 * Coach Chat — assistant à qui poser des questions (entraînement, nutrition,
 * RPE, planning, sélection RAID). Réponses du backend déterministe, branchées
 * sur le profil réel. Suggestions de relance cliquables, rendu markdown léger.
 */
import React, { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView,
  StyleSheet, Text, TextInput, View,
} from 'react-native';
import { api } from '../api/client';
import { colors, spacing, typography } from '../theme/tokens';

interface Msg { role: 'user' | 'coach'; text: string; suggestions?: string[]; }

const WELCOME: Msg = {
  role: 'coach',
  text: 'Salut ! Je suis ton coach RAID. Pose-moi une question sur ta séance du '
    + 'jour, ton **planning 3/2/2/3**, la **force**, la **course**, les **WOD**, '
    + 'la **nutrition**, le **RPE** ou la **sélection 2029**.',
  suggestions: ["Qu'est-ce que je fais aujourd'hui ?", 'Explique-moi le RPE',
    'Combien de protéines par jour ?'],
};

/** Rendu markdown minimal : **gras** et lignes. */
function RichText({ text, style }: { text: string; style: any }) {
  return (
    <View>
      {text.split('\n').map((line, i) => (
        <Text key={i} style={style}>
          {line.split(/(\*\*[^*]+\*\*)/g).map((seg, j) =>
            seg.startsWith('**') && seg.endsWith('**')
              ? <Text key={j} style={styles.bold}>{seg.slice(2, -2)}</Text>
              : <Text key={j}>{seg}</Text>)}
        </Text>
      ))}
    </View>
  );
}

export function CoachChatScreen() {
  const [messages, setMessages] = useState<Msg[]>([WELCOME]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<ScrollView>(null);

  useEffect(() => {
    const t = setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 50);
    return () => clearTimeout(t);
  }, [messages]);

  const send = async (text: string) => {
    const q = text.trim();
    if (!q || busy) return;
    setInput('');
    setMessages(m => [...m, { role: 'user', text: q }]);
    setBusy(true);
    try {
      const res = await api.chat(q, new Date().toISOString().slice(0, 10));
      setMessages(m => [...m, { role: 'coach', text: res.reply, suggestions: res.suggestions }]);
    } catch {
      setMessages(m => [...m, {
        role: 'coach',
        text: "Je n'arrive pas à joindre le coach (réseau / API). Réessaie quand "
          + 'tu es en ligne — je réponds avec tes données réelles.',
      }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.root}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView ref={scrollRef} style={{ flex: 1 }}
        contentContainerStyle={{ padding: spacing.m, paddingBottom: spacing.l }}>
        {messages.map((m, i) => (
          <View key={i} style={[styles.bubbleWrap, m.role === 'user' ? styles.right : styles.left]}>
            <View style={[styles.bubble, m.role === 'user' ? styles.userBubble : styles.coachBubble]}>
              {m.role === 'coach' && <Text style={styles.coachTag}>COACH</Text>}
              <RichText text={m.text}
                style={m.role === 'user' ? styles.userText : styles.coachText} />
            </View>
            {m.suggestions && m.suggestions.length > 0 && (
              <View style={styles.suggRow}>
                {m.suggestions.map(s => (
                  <Pressable key={s} onPress={() => send(s)} style={styles.sugg}>
                    <Text style={styles.suggT}>{s}</Text>
                  </Pressable>
                ))}
              </View>
            )}
          </View>
        ))}
        {busy && <ActivityIndicator color={colors.signal} style={{ marginTop: spacing.m }} />}
      </ScrollView>

      <View style={styles.inputBar}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Pose ta question au coach…"
          placeholderTextColor={colors.textDisabled}
          onSubmitEditing={() => send(input)}
          returnKeyType="send"
          multiline
        />
        <Pressable onPress={() => send(input)} style={styles.sendBtn} disabled={busy}>
          <Text style={styles.sendT}>▸</Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  bubbleWrap: { marginBottom: spacing.m, maxWidth: '92%' },
  left: { alignSelf: 'flex-start', alignItems: 'flex-start' },
  right: { alignSelf: 'flex-end', alignItems: 'flex-end' },
  bubble: { borderRadius: spacing.cardRadius, padding: spacing.m },
  coachBubble: { backgroundColor: colors.bgCard, borderWidth: 1, borderColor: colors.hairline },
  userBubble: { backgroundColor: colors.signalSoft, borderWidth: 1, borderColor: colors.signalDim },
  coachTag: { color: colors.signal, ...typography.label, fontSize: 9, marginBottom: spacing.xs },
  coachText: { color: colors.textPrimary, fontSize: typography.sizes.body, lineHeight: 22 },
  userText: { color: colors.textPrimary, fontSize: typography.sizes.body, lineHeight: 21 },
  bold: { fontFamily: typography.bodyBold.fontFamily, color: colors.textPrimary },
  suggRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginTop: spacing.s },
  sugg: {
    paddingVertical: spacing.xs, paddingHorizontal: spacing.s, borderRadius: 16,
    backgroundColor: colors.bgElevated, borderWidth: 1, borderColor: colors.hairlineStrong,
  },
  suggT: { color: colors.signal, fontSize: typography.sizes.small },
  inputBar: {
    flexDirection: 'row', alignItems: 'flex-end', gap: spacing.s, padding: spacing.s,
    borderTopWidth: 1, borderTopColor: colors.hairline, backgroundColor: colors.bgElevated,
  },
  input: {
    flex: 1, color: colors.textPrimary, backgroundColor: colors.bgInput,
    borderRadius: spacing.cardRadius, paddingHorizontal: spacing.m, paddingVertical: spacing.s,
    fontSize: typography.sizes.body, maxHeight: 120, borderWidth: 1, borderColor: colors.hairline,
  },
  sendBtn: {
    width: 46, height: 46, borderRadius: 23, backgroundColor: colors.signal,
    alignItems: 'center', justifyContent: 'center',
  },
  sendT: { color: colors.bg, fontSize: 24, fontFamily: typography.display.fontFamily },
});
