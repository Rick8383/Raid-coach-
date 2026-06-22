/**
 * Coach local (hors-ligne) — miroir TypeScript de engines/coach_chat.
 *
 * Sert de cerveau de secours quand l'API est injoignable (Render free en veille,
 * pas de réseau) : le chatbot analyse quand même la question et donne une
 * réponse concrète, personnalisée avec le profil mis en cache et le planning
 * 3/2/2/3 calculé localement. Garantit qu'on n'a jamais « un seul et même
 * message » générique.
 */
import { AthleteProfile } from '../api/client';
import { RPE_SCALE } from '../components/RpeScale';
import { daySchedule, currentWeekIndex } from '../schedule';

export interface LocalAnswer { reply: string; topic: string; suggestions: string[]; }

const RPE_BY_VALUE = Object.fromEntries(RPE_SCALE.map(r => [r.value, r]));

/** minuscule + sans accents, pour un matching robuste (miroir de _norm). */
function norm(text: string): string {
  return (text || '')
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .toLowerCase();
}

const TOPIC_KEYWORDS: Record<string, string[]> = {
  today: ['aujourd hui', 'aujourdhui', 'auj', 'ce jour', 'ce matin', 'quoi faire',
    'je fais quoi', 'seance du jour', 'maintenant', 'ma seance', 'que faire'],
  schedule: ['planning', 'semaine', 'grande semaine', 'petite semaine', 'calendrier',
    'quand je travaille', 'service', 'off', 'repos', 'jour off', '3/2/2/3', 'rythme', 'agenda'],
  rpe: ['rpe', 'intensite', 'echelle', 'borg', 'rir', 'reps en reserve',
    'difficulte ressentie', 'c est quoi rpe'],
  nutrition: ['nutrition', 'manger', 'macro', 'macros', 'calorie', 'calories', 'proteine',
    'proteines', 'glucide', 'glucides', 'lipide', 'lipides', 'complement', 'complements',
    'creatine', 'whey', 'cafeine', 'collagene', 'omega', 'magnesium', 'electrolyte',
    'alimentation', 'poids', 'secher', 'seche', 'prise de masse', 'hydratation'],
  strength: ['force', 'musculation', 'muscu', '531', '5/3/1', 'developpe', 'developpe couche',
    'dc', 'squat', 'souleve', 'deadlift', 'ohp', 'rowing', 'row', 'charge', 'charges', '1rm',
    'training max', 'progression', 'tractions', 'gtg'],
  run: ['course', 'courir', 'run', 'allure', 'allures', 'vma', 'seuil', 'fractionne',
    'tempo', 'fartlek', 'z2', 'zone fc', 'zones fc', 'frequence cardiaque', 'fcmax',
    'footing', 'endurance', 'cardio', 'cote', 'cotes'],
  wod: ['wod', 'crossfit', 'amrap', 'for time', 'emom', 'metcon', 'hyrox', 'chrono',
    'timer', 'minuteur', 'death by', 'tabata', 'rft', 'chipper'],
  sciatica: ['sciatique', 'dos', 'lombaire', 'l5', 's1', 'douleur', 'mal de dos', 'hernie',
    'lumbago', 'nerf'],
  raid: ['raid', 'selection', 'epreuve', 'epreuves', '2029', 'rcos', 'test physique',
    'objectif', 'objectifs', 'but'],
  benchmarks: ['benchmark', 'benchmarks', 'test', 'tests', 'cooper', 'record', 'pr',
    'tractions max', 'montee de corde', 'corde', 'luc leger'],
  recovery: ['recuperation', 'recup', 'sommeil', 'dormir', 'fatigue', 'repos', 'hrv',
    'courbature', 'courbatures', 'deload', 'surentrainement'],
  help: ['aide', 'help', 'tu sais faire quoi', 'que sais tu', 'commandes', 'bonjour',
    'salut', 'hello', 'coucou', 'yo', 'hey'],
};

function detectTopic(message: string): string {
  const n = norm(message);
  let best = 'fallback';
  let bestScore = 0;
  for (const [topic, kws] of Object.entries(TOPIC_KEYWORDS)) {
    let score = 0;
    for (const kw of kws) if (n.includes(kw)) score += 1 + kw.length / 40;
    if (score > bestScore) { best = topic; bestScore = score; }
  }
  return best;
}

const SUGGESTIONS: Record<string, string[]> = {
  today: ["Quelle allure pour mon footing ?", "C'est quoi une grande semaine ?", "Que manger après la séance ?"],
  schedule: ["Qu'est-ce que je fais aujourd'hui ?", "C'est quoi un jour OFF ?"],
  rpe: ["Explique-moi le RPE 8", "Comment coter une séance de force ?"],
  nutrition: ["Combien de protéines par jour ?", "Quels compléments prendre ?", "Créatine : comment ?"],
  strength: ["Mon objectif au développé couché ?", "C'est quoi le 5/3/1 ?", "Comment progresser aux tractions ?"],
  run: ["Mes zones de fréquence cardiaque ?", "C'est quoi une séance de seuil ?"],
  wod: ["Comment marche le chrono ?", "Différence AMRAP / For Time ?"],
  sciatica: ["Quels mouvements éviter ?", "Alternative au soulevé de terre ?"],
  raid: ["Combien de semaines avant la sélection ?", "Mes objectifs de force ?"],
  benchmarks: ["Quand re-tester ?", "Mes objectifs élite ?"],
  recovery: ["C'est quoi une semaine deload ?", "Comment lire ma readiness ?"],
  help: ["Qu'est-ce que je fais aujourd'hui ?", "Explique-moi le RPE", "Combien de protéines par jour ?"],
  fallback: ["Qu'est-ce que je fais aujourd'hui ?", "Explique-moi le RPE", "Mon planning de la semaine"],
};

function weeksToGoal(p?: AthleteProfile | null): number | null {
  if (!p?.goal_date) return null;
  const days = (new Date(p.goal_date).getTime() - Date.now()) / (24 * 3600 * 1000);
  return days > 0 ? Math.floor(days / 7) : 0;
}

// --- Handlers (miroir des _h_* du backend, personnalisés côté client) ---
function hHelp(p: AthleteProfile | null): string {
  const hello = p?.name ? `Salut ${p.name} ! ` : 'Salut ! ';
  return hello + "Je suis ton coach RAID. Pose-moi une question sur :\n"
    + "• **Ta séance du jour**\n• **Le planning 3/2/2/3** (grande/petite semaine)\n"
    + "• **La force 5/3/1** (charges, objectifs 1RM)\n• **La course** (allures, zones FC)\n"
    + "• **Les WOD** (chrono, score)\n• **La nutrition** (macros, compléments)\n"
    + "• **Le RPE**\n• **La sciatique L5-S1**\n• **La sélection RAID 2029**";
}

function hToday(p: AthleteProfile | null): string {
  const d = daySchedule(new Date());
  const wt = d.weekType === 'big_work' ? 'grande semaine' : 'petite semaine';
  const work = d.isWorkDay ? 'service' : 'OFF';
  const lines = [`On est en **${wt}**, jour **${work}**.`, `Intention du jour : *${d.intent.label}*.`];
  if (d.isWorkDay) lines.push("Jour de service → **séance courte de qualité**, intensité plafonnée.");
  else lines.push("Jour OFF → **double séance** possible (course + force).");
  lines.push("Détail complet dans l'onglet JOUR (échauffement → corps → retour au calme).");
  return lines.join('\n');
}

function hSchedule(): string {
  const d = daySchedule(new Date());
  const wt = d.weekType === 'big_work' ? 'grande' : 'petite';
  const work = d.isWorkDay ? 'service' : 'OFF';
  return "Ton rythme police **3/2/2/3** (ancre : semaine du 15/06/2026 = grande semaine) :\n"
    + "• **Grande semaine** — service lun/mar/ven/sam/dim, **OFF mer + jeu**.\n"
    + "• **Petite semaine** — service mer/jeu, le reste OFF.\n\n"
    + "Entraînement : **jour OFF = double séance**, **service = séance courte**, "
    + "**dimanche de petite semaine = natation récup**.\n\n"
    + `Aujourd'hui : **${wt} semaine**, jour **${work}**.`;
}

function hRpe(message: string): string {
  const m = norm(message).match(/\b(10|[1-9])\b/);
  if (m) {
    const r = RPE_BY_VALUE[parseInt(m[1], 10)];
    if (r) return `**RPE ${r.value} — ${r.label}** (${r.zone})\n${r.desc}`;
  }
  const lines = ["Le **RPE** (échelle 1-10) cote la difficulté *ressentie*. En force, on le relie aux **reps en réserve (RIR)**. Repères :"];
  for (const v of [4, 6, 7, 8, 9, 10]) {
    const r = RPE_BY_VALUE[v];
    lines.push(`• **${v}** — ${r.label} : ${r.desc}`);
  }
  lines.push("\nDans l'app, survole (ou appuie sur) chaque chiffre RPE pour son explication.");
  return lines.join('\n');
}

function hNutrition(p: AthleteProfile | null, message: string): string {
  const n = norm(message);
  if (n.includes('creatine')) {
    return "**Créatine monohydrate** : 3-5 g/jour, tous les jours (timing indifférent). "
      + "Preuve A+ pour la force et la puissance répétée. Pas de phase de charge nécessaire.";
  }
  if (['complement', 'complements', 'whey', 'cafeine', 'omega', 'magnesium'].some(k => n.includes(k))) {
    return "Compléments à preuve solide : **créatine** (3-5 g/j), **whey** (autour des séances), "
      + "**caféine** (3-6 mg/kg avant un effort clé), **oméga-3**, **vit D3**, **magnésium** le soir, "
      + "**électrolytes** sur les grosses séances. Détail (dose/timing/preuve) dans l'onglet NUTRITION.";
  }
  const w = p?.weight_kg;
  const lines = ["Cadre nutrition (recomposition + performance) :"];
  if (w) {
    lines.push(`• **Protéines** ~${Math.round(2 * w)} g/j (2 g/kg) — plancher 1,8 g/kg.`);
    lines.push(`• **Lipides** ≥ ${Math.round(0.8 * w)} g/j (0,8 g/kg mini).`);
    lines.push("• **Glucides** : le reste des calories, concentrés autour des séances dures.");
  } else {
    lines.push("• Protéines ~2 g/kg, lipides ≥ 0,8 g/kg, glucides autour des séances.");
  }
  lines.push("• **Hydratation** : ~35 ml/kg + pertes à l'effort.");
  lines.push("\nL'onglet NUTRITION calcule tes macros exactes et les convertit en grammes d'aliments.");
  return lines.join('\n');
}

function hStrength(p: AthleteProfile | null, message: string): string {
  const cur = p?.current || {};
  const n = norm(message);
  const lines = ["Ta force suit un **5/3/1** (cycle 4 sem. : 5/5/5+, 3/3/3+, 5/3/1+, deload). "
    + "+2,5 kg haut du corps / +5 kg bas par cycle, via le **Training Max** (~90 % du 1RM)."];
  const bench = cur.bench_ratio ?? cur.bench_1rm;
  const squat = cur.squat_ratio ?? cur.squat_1rm;
  if (bench) lines.push(`• **Développé couché** : 1RM ~${bench} kg → objectif **140 kg**.`);
  if (squat) lines.push(`• **Squat** : 1RM ~${squat} kg → objectif **160 kg**.`);
  if (n.includes('traction') || n.includes('gtg')) {
    lines.push("• **Tractions** : Grease the Groove (séries fréquentes loin de l'échec) le jour PULL.");
  }
  lines.push("⚠ Sciatique L5-S1 : pas de soulevé de terre lourd → **hip thrust**, **Big 3 McGill** à l'échauffement.");
  lines.push("\nL'onglet SÉANCES → FORCE génère ta séance et trace la progression des charges.");
  return lines.join('\n');
}

function hRun(p: AthleteProfile | null): string {
  const vma = p?.vma_kmh;
  const fc = p?.fc_max;
  const lines = ["Course : 7 types — VMA courte/longue, seuil, fartlek, tempo, Z2, côtes."];
  if (vma) {
    lines.push(`À partir de ta **VMA ${vma} km/h** : endurance Z2 ~${(vma * 0.65).toFixed(1)} km/h `
      + `(65 %), seuil ~${(vma * 0.85).toFixed(1)} km/h (85 %), VO2max 95-105 %.`);
  }
  if (fc) {
    lines.push(`Zones FC sur **FCmax ${fc} bpm** : Z2 ~${Math.round(fc * 0.7)}-${Math.round(fc * 0.8)} bpm, `
      + `seuil ~${Math.round(fc * 0.85)}-${Math.round(fc * 0.9)} bpm.`);
  }
  lines.push("L'onglet SÉANCES → COURSE génère une séance chiffrée (allures + % VMA, FC cible).");
  return lines.join('\n');
}

function hWod(): string {
  return "WOD/CrossFit : 15 formats (AMRAP, For Time, EMOM, Death By, Chipper, RFT, Tabata, "
    + "Ladder, Pyramide…), garde-fou anti-lombaire activé par défaut (sciatique).\n\n"
    + "Sur la page WOD, le **chrono de compétition** démarre par un compte à rebours de 15 s "
    + "(réglable en cliquant dessus : countdown, time cap, mode) avec des bips. Il **compte le "
    + "temps** sur les For Time et **les reps/rounds** sur les AMRAP → ton **score** est enregistré "
    + "dans l'agenda.";
}

function hSciatica(): string {
  return "Protocole **sciatique L5-S1** appliqué partout :\n"
    + "• WOD : exclusion des mouvements lombaires (deadlift, GHD, good morning, snatch lourd) — "
    + "ON par défaut, jamais en finisseur.\n"
    + "• Force : soulevé de terre lourd → **hip thrust**, **Big 3 McGill** à chaque échauffement.\n"
    + "• Douleur signalée au check-in → intensité plafonnée, bascule mobilité / Z2.\n\n"
    + "Si la douleur irradie dans la jambe ou s'aggrave : repos et avis médical.";
}

function hRaid(p: AthleteProfile | null): string {
  let base = "Cap : **sélection RAID 2029**. L'app rétro-planifie (BASE → BUILD → PEAK → TRANSITION). "
    + "Objectifs élite : DC 140 kg, Squat 160 kg, VMA en hausse, tractions/corde, endurance lestée — "
    + "suivis dans l'onglet OBJECTIFS.";
  const wk = weeksToGoal(p);
  if (wk != null) base += `\n\nIl reste ~**${wk} semaines** avant l'échéance visée.`;
  return base;
}

function hBenchmarks(): string {
  return "Tes **benchmarks** (Cooper, tractions max, montée de corde, WOD de référence, 1RM) se "
    + "saisissent et se tracent dans l'onglet OBJECTIFS. Re-teste toutes les 4-6 semaines (fin de "
    + "bloc) pour recaler allures et charges.";
}

function hRecovery(): string {
  return "Récupération : sommeil et HRV pilotent ta readiness, donc la charge autorisée "
    + "(ACWR + budget fatigue). Une semaine **deload** est planifiée toutes les 4 semaines. "
    + "Vise 7-9 h de sommeil ; si la fatigue grimpe plusieurs jours, lève le pied avant que "
    + "l'ACWR ne dépasse 1,3.";
}

export function localCoachAnswer(message: string, profile: AthleteProfile | null): LocalAnswer {
  const topic = detectTopic(message);
  let reply: string;
  switch (topic) {
    case 'today': reply = hToday(profile); break;
    case 'schedule': reply = hSchedule(); break;
    case 'rpe': reply = hRpe(message); break;
    case 'nutrition': reply = hNutrition(profile, message); break;
    case 'strength': reply = hStrength(profile, message); break;
    case 'run': reply = hRun(profile); break;
    case 'wod': reply = hWod(); break;
    case 'sciatica': reply = hSciatica(); break;
    case 'raid': reply = hRaid(profile); break;
    case 'benchmarks': reply = hBenchmarks(); break;
    case 'recovery': reply = hRecovery(); break;
    case 'help': reply = hHelp(profile); break;
    default:
      reply = "Je n'ai pas bien saisi 🤔. Je suis affûté sur l'entraînement (course, force, WOD), "
        + "la nutrition, le RPE, ton planning et la sélection RAID. Essaie une suggestion ci-dessous.";
  }
  return { reply, topic, suggestions: SUGGESTIONS[topic] || SUGGESTIONS.fallback };
}
