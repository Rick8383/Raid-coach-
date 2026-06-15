"""Base de connaissances nutrition (evidence-based, sources ISSN/méta-analyses).

3 niveaux de preuve : élevée / modérée / émergente. Aucune source commerciale.
Profil de référence : athlète hybride masculin 75 kg, recomp, sciatique L5-S1,
rythme police 3/2/2/3.
"""
from __future__ import annotations

# ---------------- COMPLÉMENTS ----------------
# when : quotidien | matin | pre | post | soir | test
# contexts : séances où c'est pertinent (force, cardio, wod, test, sommeil, toujours)
SUPPLEMENTS = [
    {
        "id": "creatine", "name": "Créatine monohydrate", "evidence": "élevée",
        "dose": "3–5 g/j (entretien). Charge optionnelle 0,3 g/kg/j (~24 g) 5–7 j.",
        "when": "quotidien", "with": "glucides + protéines (meilleure rétention)",
        "mechanism": "↑ phosphocréatine intramusculaire → resynthèse ATP, capacité haute intensité, masse maigre, tolérance au volume.",
        "relevance": "force (DC, squat) + endurance de force (tractions, dips, corde).",
        "source": "ISSN Position Stand, Kreider et al. 2017",
        "contexts": ["toujours", "force", "wod"],
    },
    {
        "id": "collagene", "name": "Collagène hydrolysé + vitamine C", "evidence": "émergente",
        "dose": "15 g collagène (jusqu'à 30 g) + ~50 mg vitamine C",
        "when": "pre", "with": "30–60 min AVANT l'effort de mise en charge tendineuse",
        "mechanism": "Vitamine C = cofacteur de la prolyl-hydroxylase → synthèse de collagène ; fenêtre pré-effort exploite le flux sanguin tendineux.",
        "relevance": "sciatique L5-S1, charges lourdes, corde/dips — le tendon s'adapte plus lentement que le muscle.",
        "source": "Shaw et al., Am J Clin Nutr 2017 (lab Baar)",
        "contexts": ["force", "wod", "toujours"],
    },
    {
        "id": "whey", "name": "Whey isolate", "evidence": "élevée",
        "dose": "25–32 g/prise (0,25–0,4 g/kg ; 700–3000 mg leucine)",
        "when": "post", "with": "pré OU post-effort ; répartir toutes les 3–4 h",
        "mechanism": "Riche en EAA/leucine → seuil leucinique, mTOR, maximise la synthèse protéique (MPS).",
        "relevance": "atteindre la cible protéique (~2,2 g/kg) en recomp.",
        "source": "ISSN Protein Position Stand, Jäger/Kerksick et al. 2017",
        "contexts": ["force", "wod", "cardio", "toujours"],
    },
    {
        "id": "caseine", "name": "Caséine (pré-sommeil)", "evidence": "modérée",
        "dose": "30–40 g", "when": "soir", "with": "30–60 min avant le coucher",
        "mechanism": "Digestion lente → MPS nocturne soutenue sans inhiber la lipolyse.",
        "relevance": "récupération nocturne, recomp, rythme 3/2/2/3.",
        "source": "ISSN Protein Position Stand 2017",
        "contexts": ["toujours"],
    },
    {
        "id": "cafeine", "name": "Caféine", "evidence": "élevée",
        "dose": "3–6 mg/kg (~225–450 mg pour 75 kg)",
        "when": "pre", "with": "60 min avant l'effort ; éviter dans les ~6 h avant le coucher",
        "mechanism": "Antagoniste de l'adénosine → endurance, force, sprint, vigilance.",
        "relevance": "VMA, Cooper, WOD, séances tardives (cycle police).",
        "source": "ISSN Position Stand, Guest et al. 2021",
        "contexts": ["cardio", "wod", "test"],
    },
    {
        "id": "beta_alanine", "name": "Bêta-alanine", "evidence": "élevée",
        "dose": "4–6 g/j (fractionné 0,8–1,6 g) en cure ≥2–4 semaines",
        "when": "quotidien", "with": "fractionner pour limiter les paresthésies",
        "mechanism": "Précurseur de la carnosine (tampon pH intracellulaire) → efforts 1–4 min.",
        "relevance": "WOD CrossFit, intervalles, Cooper.",
        "source": "ISSN Position Stand, Trexler et al. 2015",
        "contexts": ["wod", "cardio", "test"],
    },
    {
        "id": "omega3", "name": "Oméga-3 EPA/DHA", "evidence": "modérée",
        "dose": "2–3 g/j d'EPA+DHA", "when": "matin", "with": "un repas contenant des lipides (liposoluble)",
        "mechanism": "Membranes cellulaires, modulation de l'inflammation, soutien MPS ; carence quasi-généralisée chez l'athlète.",
        "relevance": "récupération, confort articulaire (cible Omega-3 Index >8%).",
        "source": "Revue 2025 (1452 athlètes) ; ISSN",
        "contexts": ["toujours"],
    },
    {
        "id": "vitd", "name": "Vitamine D3", "evidence": "modérée",
        "dose": "2000–4000 UI/j (cible 25(OH)D ≥40 ng/mL)",
        "when": "matin", "with": "un repas gras",
        "mechanism": "Hormone stéroïde (>900 gènes) : force, immunité, os, prédicteur de testostérone/cortisol.",
        "relevance": "hiver, performance, os ; test sanguin trimestriel.",
        "source": "Méta-analyses ; UL EFSA 4000 UI/j",
        "contexts": ["toujours"],
    },
    {
        "id": "magnesium", "name": "Magnésium bisglycinate", "evidence": "modérée",
        "dose": "200–400 mg élément", "when": "soir", "with": "30–60 min avant le coucher ; séparer du calcium de 2 h",
        "mechanism": "Tonus parasympathique, GABA, ↓ NMDA ; glycine calmante → sommeil/récupération.",
        "relevance": "gestion du cortisol, sommeil (RCT 2025 : insomnie ↓).",
        "source": "RCT 2025 ; revues sommeil",
        "contexts": ["sommeil", "toujours"],
    },
    {
        "id": "electrolytes", "name": "Électrolytes / sodium", "evidence": "modérée",
        "dose": "300–600 mg sodium/h (jusqu'à 1500+ selon sudation)",
        "when": "pre", "with": "efforts >60 min ou chaleur ; boisson 500–700 mg/L",
        "mechanism": "Volume plasmatique, prévention hyponatrémie/crampes.",
        "relevance": "longues courses, chaleur, jour de sélection.",
        "source": "ACSM / AND / DC",
        "contexts": ["cardio", "test"],
    },
]

# ---------------- ALIMENTS (pour 100 g, USDA sauf mention) ----------------
# cat : protein | carb | fat | mixed ; state : cuit/cru/poudre
FOODS = [
    {"id": "poulet", "name": "Poulet blanc (cuit)", "p": 31, "c": 0, "f": 3.6, "kcal": 165, "cat": "protein", "state": "cuit"},
    {"id": "boeuf5", "name": "Bœuf haché 5% (cuit)", "p": 26, "c": 0, "f": 6.7, "kcal": 164, "cat": "protein", "state": "cuit"},
    {"id": "steak", "name": "Steak maigre (cuit)", "p": 29, "c": 0, "f": 6, "kcal": 178, "cat": "protein", "state": "cuit"},
    {"id": "cabillaud", "name": "Cabillaud (cuit)", "p": 22.8, "c": 0, "f": 0.9, "kcal": 105, "cat": "protein", "state": "cuit"},
    {"id": "saumon", "name": "Saumon (cuit)", "p": 22.1, "c": 0, "f": 12.4, "kcal": 206, "cat": "protein", "state": "cuit"},
    {"id": "thon", "name": "Thon au naturel", "p": 19.4, "c": 0, "f": 1.0, "kcal": 86, "cat": "protein", "state": "conserve"},
    {"id": "oeuf", "name": "Œufs entiers", "p": 12.6, "c": 0.7, "f": 9.5, "kcal": 143, "cat": "mixed", "state": "cru"},
    {"id": "skyr", "name": "Skyr 0%", "p": 11, "c": 3.7, "f": 0.2, "kcal": 61, "cat": "protein", "state": "nature"},
    {"id": "fromageblanc", "name": "Fromage blanc 0%", "p": 11, "c": 3.9, "f": 0.3, "kcal": 62, "cat": "protein", "state": "nature"},
    {"id": "whey", "name": "Whey isolate (étiquette)", "p": 87, "c": 6, "f": 2, "kcal": 385, "cat": "protein", "state": "poudre"},
    {"id": "rizcuit", "name": "Riz blanc (cuit)", "p": 2.7, "c": 28.2, "f": 0.3, "kcal": 130, "cat": "carb", "state": "cuit"},
    {"id": "patescuites", "name": "Pâtes (cuites)", "p": 5.8, "c": 30.9, "f": 0.9, "kcal": 158, "cat": "carb", "state": "cuit"},
    {"id": "patatedouce", "name": "Patate douce (cuite)", "p": 1.6, "c": 20.7, "f": 0.15, "kcal": 90, "cat": "carb", "state": "cuit"},
    {"id": "pdt", "name": "Pomme de terre (cuite)", "p": 2.0, "c": 20, "f": 0.1, "kcal": 86, "cat": "carb", "state": "cuit"},
    {"id": "avoine", "name": "Flocons d'avoine (secs)", "p": 13.2, "c": 67.7, "f": 6.5, "kcal": 384, "cat": "carb", "state": "sec"},
    {"id": "paincomplet", "name": "Pain complet", "p": 12.5, "c": 42, "f": 3.4, "kcal": 250, "cat": "carb", "state": "—"},
    {"id": "lentilles", "name": "Lentilles (cuites)", "p": 9.0, "c": 20.1, "f": 0.4, "kcal": 116, "cat": "carb", "state": "cuit"},
    {"id": "banane", "name": "Banane", "p": 1.1, "c": 22.8, "f": 0.3, "kcal": 89, "cat": "carb", "state": "—"},
    {"id": "huileolive", "name": "Huile d'olive", "p": 0, "c": 0, "f": 100, "kcal": 884, "cat": "fat", "state": "—"},
    {"id": "amandes", "name": "Amandes", "p": 21.2, "c": 9, "f": 49.9, "kcal": 579, "cat": "fat", "state": "—"},
    {"id": "avocat", "name": "Avocat", "p": 2.0, "c": 8.5, "f": 14.7, "kcal": 160, "cat": "fat", "state": "—"},
    {"id": "beurrecacahuete", "name": "Beurre de cacahuète", "p": 24, "c": 19, "f": 50, "kcal": 588, "cat": "fat", "state": "—"},
]

FOODS_BY_ID = {f["id"]: f for f in FOODS}

# ---------------- SYNERGIES (assimilation / hormones) ----------------
SYNERGIES = [
    {"combo": "Collagène + vitamine C", "evidence": "émergente",
     "why": "Vitamine C = cofacteur de la synthèse de collagène (tendons/ligaments).",
     "example": "15 g collagène + 1 kiwi ou jus d'orange, 30–60 min avant la séance."},
    {"combo": "Fer + vitamine C", "evidence": "élevée",
     "why": "La vitamine C réduit le fer Fe³⁺→Fe²⁺ et améliore l'absorption du fer non héminique.",
     "example": "Lentilles + poivron/citron, ou steak + jus d'orange."},
    {"combo": "Protéines + glucides post-effort", "evidence": "élevée",
     "why": "Restaure le glycogène et la MPS ; ↓ ratio cortisol/testostérone.",
     "example": "Whey 25–32 g + riz/banane (0,8–1,2 g/kg de glucides) juste après."},
    {"combo": "Vitamine D / oméga-3 + lipides", "evidence": "élevée",
     "why": "Vitamines liposolubles → bien mieux absorbées avec un repas gras.",
     "example": "D3 + oméga-3 au petit-déjeuner avec œufs/avocat."},
    {"combo": "Lipides suffisants → testostérone", "evidence": "modérée",
     "why": "Régimes <0,8 g/kg de lipides → testostérone ~10–15% plus basse (cholestérol = substrat).",
     "example": "Ne jamais descendre sous 0,8 g/kg/j de lipides (œufs, huile d'olive, saumon)."},
    {"combo": "Curcuma + poivre noir", "evidence": "émergente",
     "why": "La pipérine ralentit l'élimination de la curcumine (biodisponibilité ×20).",
     "example": "Curcuma + poivre (ratio ~100:1), cuit avec un corps gras."},
]

ANTI_SYNERGIES = [
    {"pair": "Fer + café/thé", "mechanism": "Polyphénols/tanins chélatent le fer", "magnitude": "−39% à −90%", "delay": "≥1–2 h"},
    {"pair": "Fer + calcium", "mechanism": "Compétition d'absorption", "magnitude": "−18 à −27%", "delay": "1–2 h"},
    {"pair": "Magnésium + calcium (haute dose)", "mechanism": "Compétition", "magnitude": "—", "delay": "2 h"},
    {"pair": "Calcium + zinc (haute dose)", "mechanism": "Compétition", "magnitude": "—", "delay": "espacer"},
    {"pair": "Caféine + sommeil", "mechanism": "Demi-vie ~5 h, blocage adénosine", "magnitude": "—", "delay": "éviter ~6 h avant le coucher"},
    {"pair": "Phytates/fibres + fer", "mechanism": "Chélation", "magnitude": "−18 à −82%", "delay": "espacer des repas riches en fer"},
]
