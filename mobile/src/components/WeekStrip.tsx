/**
 * Bande planning 3/2/2/3 — rend visible la synchronisation service / OFF.
 * Chaque jour : pastille avec son code, marquée "service" (police) ou "OFF"
 * (jour d'entraînement). Le jour courant est mis en avant.
 */
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { DAY_LABELS, DaySchedule, ScheduleConfig, WEEK_LABEL, weekSchedule } from '../schedule';
import { colors, spacing, typography } from '../theme/tokens';
import { Tag } from './ui';

export function WeekStrip({ today = new Date(), config }:
  { today?: Date; config?: ScheduleConfig }) {
  const { weekType, days } = weekSchedule(today, config);
  const weekly = weekType === 'weekly';
  const todayIso = new Date(Date.UTC(
    today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate())).toISOString().slice(0, 10);

  return (
    <View>
      <View style={styles.header}>
        <Text style={styles.title}>SEMAINE EN COURS</Text>
        <Tag label={WEEK_LABEL[weekType]}
          color={weekType === 'big_work' ? colors.fitness : colors.signal} />
      </View>
      <View style={styles.row}>
        {days.map((d: DaySchedule) => {
          const isToday = d.date === todayIso;
          // « actif » = jour d'entraînement mis en avant (OFF police / jour choisi weekly)
          const active = weekly ? d.trains : !d.isWorkDay;
          return (
            <View key={d.date} style={[styles.dayCol, isToday && styles.todayCol]}>
              <Text style={[styles.dayCode, isToday && styles.todayText]}>
                {DAY_LABELS[d.dayCode]}
              </Text>
              <View style={[
                styles.dot,
                active ? styles.dotOff : styles.dotWork,
                isToday && styles.dotToday,
              ]} />
              <Text style={[styles.slot, active ? styles.slotOff : styles.slotWork]}>
                {weekly ? (d.trains ? 'ENTR.' : 'REPOS') : (d.isWorkDay ? 'SERV.' : 'OFF')}
              </Text>
            </View>
          );
        })}
      </View>
      <Text style={styles.legend}>
        {weekly
          ? 'ENTR. = jour d\'entraînement choisi · REPOS = jour off'
          : 'OFF = entraînement · SERV. = service police (séance courte)'}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', marginBottom: spacing.s,
  },
  title: { color: colors.textSecondary, ...typography.label },
  row: {
    flexDirection: 'row', justifyContent: 'space-between',
    backgroundColor: colors.bgCard, borderRadius: spacing.cardRadius,
    paddingVertical: spacing.m, paddingHorizontal: spacing.xs,
  },
  dayCol: { flex: 1, alignItems: 'center', paddingVertical: spacing.xs, borderRadius: 8 },
  todayCol: { backgroundColor: colors.signalSoft },
  dayCode: { color: colors.textDisabled, ...typography.label, fontSize: 10, marginBottom: spacing.s },
  todayText: { color: colors.signal },
  dot: { width: 10, height: 10, borderRadius: 5, marginBottom: spacing.s },
  dotOff: { backgroundColor: colors.signal },
  dotWork: { backgroundColor: colors.hairlineStrong },
  dotToday: { borderWidth: 2, borderColor: colors.signal },
  slot: { ...typography.label, fontSize: 9, letterSpacing: 0.5 },
  slotOff: { color: colors.signal },
  slotWork: { color: colors.textDisabled },
  legend: {
    color: colors.textDisabled, fontSize: typography.sizes.micro,
    marginTop: spacing.s, textAlign: 'center',
  },
});
