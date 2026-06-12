/**
 * RAID Coach — Design System
 *
 * Direction : "tableau de bord opérationnel nocturne".
 * Ni fitness pastel, ni template sombre générique : l'univers visuel vient du
 * terrain RAID — vision nocturne, marquages d'équipement, signalétique
 * d'intervention. Fond bleu-noir profond (pas un #000 neutre), un seul accent
 * signal (vert lumière de casque), statuts readiness en code couleur opérationnel.
 *
 * Signature : la "ligne de readiness" — un liseré vertical coloré GREEN/YELLOW/
 * ORANGE/RED sur le bord gauche de chaque carte séance, comme un marquage
 * d'équipement. C'est l'élément mémorable, tout le reste est discipliné.
 */

export const colors = {
  // Fond — bleu nuit profond, pas noir pur
  bg: '#0B1120',
  bgElevated: '#111A2E',
  bgCard: '#16213B',
  hairline: '#1F2C49',

  // Accent unique — vert "lampe de casque" (réservé aux actions et au GO)
  signal: '#3DDC84',
  signalDim: '#1F6B44',

  // Statuts readiness (code opérationnel, jamais utilisés en décoration)
  readyGreen: '#3DDC84',
  readyYellow: '#E8C547',
  readyOrange: '#E8853D',
  readyRed: '#E5484D',

  // Texte
  textPrimary: '#EDF1F7',
  textSecondary: '#8B98B8',
  textDisabled: '#4A5670',

  // Données / graphiques
  fitness: '#5B8DEF',
  fatigue: '#E8853D',
  form: '#3DDC84',
} as const;

export const typography = {
  // Display : condensé industriel — chiffres de chrono, scores, compte à rebours
  display: {
    fontFamily: 'BarlowCondensed_700Bold',
    letterSpacing: 0.5,
  },
  // Corps : lisible terrain, écran de téléphone en salle/extérieur
  body: {
    fontFamily: 'Inter_400Regular',
  },
  bodyBold: {
    fontFamily: 'Inter_600SemiBold',
  },
  // Utilitaire : étiquettes, unités, méta — petites capitales espacées
  label: {
    fontFamily: 'Inter_500Medium',
    letterSpacing: 1.2,
    textTransform: 'uppercase' as const,
    fontSize: 11,
  },
  sizes: {
    countdown: 44,
    score: 32,
    h1: 24,
    h2: 18,
    body: 15,
    small: 13,
    micro: 11,
  },
} as const;

export const spacing = {
  xs: 4, s: 8, m: 16, l: 24, xl: 32,
  cardRadius: 10,
  readinessBar: 4, // largeur du liseré signature
} as const;

export type ReadinessLevel = 'green' | 'yellow' | 'orange' | 'red';

export const readinessColor = (level: ReadinessLevel): string =>
  ({
    green: colors.readyGreen,
    yellow: colors.readyYellow,
    orange: colors.readyOrange,
    red: colors.readyRed,
  }[level]);
