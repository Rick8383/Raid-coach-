# Déploiement — backend en ligne + app iOS (TestFlight) + web

L'app a besoin d'un backend **joignable publiquement** pour générer les séances.
En local sur `http://localhost:8000`, une page web hébergée ou un téléphone ne
peut pas l'atteindre : il faut déployer l'API, puis pointer l'app dessus.

## 1. Déployer le backend (Render, gratuit, ~5 min)

1. Pousser ce dépôt sur GitHub (déjà fait si tu lis ceci depuis GitHub).
2. Aller sur [render.com](https://render.com) → **New** → **Blueprint** → choisir ce dépôt.
3. Render détecte `render.yaml`, build l'image Docker et déploie. Tu obtiens une URL
   du type `https://raid-coach-api.onrender.com`.
4. Vérifier : ouvrir `https://<ton-url>/health` → `{"status":"ok",...}` et `.../docs`
   pour la doc interactive (tester les endpoints à la main).

> Alternative Railway : **New Project → Deploy from repo**, racine `backend/`,
> Railway lit le `Dockerfile` automatiquement. Ajouter un volume sur `/app/data`.

CORS est ouvert par défaut (`CORS_ORIGINS=*`) pour la beta ; en production, mettre
l'URL exacte du front.

## 2. Pointer l'app sur l'API en ligne

- **Web / Expo** : définir la variable d'environnement avant de lancer
  `EXPO_PUBLIC_API_URL=https://<ton-url>` (ou éditer `mobile/.env`).
- **Build natif** : `mobile/app.json` → `expo.extra.apiUrl` est lu en repli ;
  y mettre l'URL de prod avant le build EAS.

## 3. App iOS sur TestFlight (build EAS)

Expo Go ne suffit pas (modules natifs : notifications, HealthKit/Garmin). Il faut
un **build EAS** soumis à TestFlight. Prérequis : compte **Apple Developer** (99 $/an)
et compte **Expo** (gratuit).

```bash
cd mobile
npm install -g eas-cli
eas login                       # compte Expo
eas build:configure            # crée/complète eas.json (déjà fourni)
# 1er build iOS (Expo gère la signature, ou fournir tes certs)
eas build --platform ios --profile production
# soumettre à TestFlight
eas submit --platform ios --latest
```

Puis dans **App Store Connect → TestFlight**, ajouter ton e-mail comme testeur ;
tu reçois l'invitation et installes l'app via **TestFlight** sur l'iPhone.

Renseigner `mobile/app.json` avant le build :
- `expo.extra.eas.projectId` (donné par `eas build:configure`),
- `expo.ios.buildNumber` (incrémenter à chaque soumission),
- `expo.extra.apiUrl` = URL Render de l'étape 1.

## 4. Web (déploiement statique, optionnel)

```bash
cd mobile
npx expo export --platform web      # génère dist/
```
Héberger `dist/` sur Netlify / Vercel / GitHub Pages, avec
`EXPO_PUBLIC_API_URL` pointant sur l'API Render.

## Récapitulatif des variables

| Variable | Où | Rôle |
|---|---|---|
| `EXPO_PUBLIC_API_URL` | app (web/dev) | URL de l'API |
| `expo.extra.apiUrl` | `app.json` | URL de l'API (repli build natif) |
| `CORS_ORIGINS` | backend (Render) | origines autorisées |
| `RAID_COACH_DB` | backend | chemin SQLite (volume persistant) |
