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

### Données persistantes (PostgreSQL)

Le `render.yaml` provisionne une base **PostgreSQL** et injecte `DATABASE_URL` :
le backend bascule automatiquement dessus (sinon SQLite local), et tes données
**survivent aux redéploiements** (plus besoin de disque, non supporté en free tier).
Le schéma est créé au démarrage, aucune migration manuelle.

Si le PostgreSQL managé Render ne convient pas (quota, expiration de l'offre
gratuite) : supprimer le bloc `databases:` du `render.yaml`, créer une base
**externe gratuite** (Neon, Supabase…) et coller son URL dans la variable
`DATABASE_URL` (Render → service → Environment). Format attendu :
`postgresql://user:pass@host:5432/dbname?sslmode=require`.

#### ⚠️ Activer PostgreSQL sur un service DÉJÀ déployé (prérequis multi-utilisateurs)

Si le backend a été déployé **avant** que le bloc `databases:` ne soit actif, il
tourne encore sur **SQLite éphémère** (les données — et donc tout compte
utilisateur — sont perdues à chaque redéploiement/réveil).

> **Durabilité** : la base **PostgreSQL *free* de Render est supprimée au bout de
> ~30 jours**. Pour un usage **multi-utilisateurs durable**, préférer une base
> **Neon** (gratuite, sans expiration) — c'est l'**option A** ci-dessous, recommandée.
> L'option B (Blueprint Render) est plus rapide mais sa base free expire.

**Option A — Neon (gratuit, durable) → recommandé pour le multi-comptes**
1. Créer un compte sur [neon.tech](https://neon.tech) → **New Project** (région proche, ex. EU).
2. Copier la *connection string* (Dashboard → **Connection Details** →
   « Connection string », format `postgresql://user:pass@ep-xxx.eu.aws.neon.tech/neondb?sslmode=require`).
3. Render → ton service `raid-coach-api` → **Environment** → **Add Environment Variable** :
   - Key = `DATABASE_URL`  ·  Value = la connection string Neon.
   - **Save Changes** → Render redéploie automatiquement.
4. (Conseillé) Retirer le bloc `databases:` du `render.yaml` pour ne pas
   provisionner en double la base Render éphémère.

**Option B — Re-synchroniser le Blueprint Render (rapide, base free ~30 j)**
1. Render → ton service → onglet **Blueprint** → **Sync** (Render relit
   `render.yaml`, **provisionne `raid-coach-db`** et injecte `DATABASE_URL`).
   Si l'option n'apparaît pas : **New → Blueprint** sur le dépôt (recrée le
   groupe service + base liés).
2. Attendre le redéploiement.

**Vérifier que c'est bien actif** — ouvrir `https://raid-coach-api.onrender.com/health` :
```json
{ "status": "ok", "db_backend": "postgres", "persistent": true }
```
`"persistent": true` ⇒ les données (comptes, profils, séances, mode standby…)
survivent désormais aux redéploiements. Si tu vois `"db_backend": "sqlite"`,
`DATABASE_URL` n'est pas injecté → reprendre l'option A ou B. Le schéma (toutes
les tables, dont `users` et `standby_state`) se crée **tout seul au démarrage**,
aucune migration manuelle.

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

## 5. Garmin Connect (synchro automatique HRV / FC repos / sommeil)

L'intégration OAuth 1.0a est codée côté serveur ; il faut tes clés Garmin :

1. S'inscrire au **Garmin Developer Program** (Health API) → obtenir
   `consumer key` + `consumer secret` (l'accès demande une validation Garmin).
2. Déclarer l'URL de callback `https://<ton-api>/garmin/callback`.
3. Définir sur l'hébergeur :
   - `GARMIN_CONSUMER_KEY`, `GARMIN_CONSUMER_SECRET`
   - `GARMIN_REDIRECT_URL=https://<ton-api>/garmin/callback`
4. Dans l'app : Profil → **Connexion montre** → « Connecter mon compte Garmin »
   (autorisation sur connect.garmin.com), puis « Synchroniser ».

Sans ces clés, l'écran affiche « non configuré » et la **saisie manuelle**
(ou Apple Santé en build natif) reste disponible — l'app est utilisable sans Garmin.

Endpoints serveur : `/garmin/status`, `/garmin/connect`, `/garmin/callback`,
`/garmin/sync`, `/garmin/disconnect`. Les données alimentent le suivi et la
mise à niveau du plan (boucle adaptative), sans toucher aux boutons « Générer ».

## Récapitulatif des variables

| Variable | Où | Rôle |
|---|---|---|
| `EXPO_PUBLIC_API_URL` | app (web/dev) | URL de l'API |
| `expo.extra.apiUrl` | `app.json` | URL de l'API (repli build natif) |
| `CORS_ORIGINS` | backend (Render) | origines autorisées |
| `DATABASE_URL` | backend | PostgreSQL (données persistantes) ; si absent → SQLite |
| `RAID_COACH_DB` | backend | chemin SQLite (repli si pas de PostgreSQL) |
| `GARMIN_CONSUMER_KEY` / `GARMIN_CONSUMER_SECRET` | backend | OAuth Garmin |
| `GARMIN_REDIRECT_URL` | backend | callback OAuth Garmin |
