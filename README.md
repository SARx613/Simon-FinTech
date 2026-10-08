# 🎙️ Simon FinTech

Podcast quotidien qui décrypte l'actualité de la finance et de la tech.
**Entièrement automatisé, 100 % gratuit**, publié automatiquement sur Spotify via un flux RSS.

## Comment ça marche

Chaque matin à **8h20 (heure de Paris)**, GitHub Actions exécute automatiquement le pipeline complet :

```
news_collector.py  →  script_generator.py  →  voice_synth.py  →  update_rss.py
 (Sources actualités)     (Claude Anthropic)     (ElevenLabs)       (flux RSS)
```

1. **Collecte** les meilleures actus financières et tech du jour (CNBC, Bloomberg, TechCrunch, etc.)
2. **Rédige** un script rythmé et percutant de ~1200-1400 mots avec **Claude** (Anthropic)
3. **Génère** un titre accrocheur pour l'épisode
4. **Synthétise** le podcast en MP3 avec **ElevenLabs** (voix clonée `ZfzastaCQOj8iuzFZuWy`)
5. **Met à jour** le flux `rss.xml` et pousse le commit sur GitHub

Spotify et les autres plateformes de podcast lisent automatiquement ce flux RSS sur GitHub Pages : le nouvel épisode est immédiatement disponible pour tes auditeurs.

`generate_podcast.py` est le chef d'orchestre qui enchaîne la génération complète.

## Installation et test local

```bash
pip install -r requirements.txt
cp .env.example .env          # renseigne ANTHROPIC_API_KEY et ELEVENLABS_API_KEY
python generate_podcast.py    # génère l'épisode du jour
python update_rss.py          # met à jour le flux RSS
```

## Mise en route de l'automatisation quotidienne (à 8h20)

### 1. Configurer les Secrets GitHub
Sur ton dépôt GitHub → **Settings → Secrets and variables → Actions → New repository secret** :
- `ELEVENLABS_API_KEY` : ta clé API ElevenLabs (https://elevenlabs.io)
- `ANTHROPIC_API_KEY` : ta clé API Anthropic Claude (https://console.anthropic.com)
*(Optionnel si tu souhaites utiliser Groq ou OpenAI : `GROQ_API_KEY` ou `OPENAI_API_KEY`)*

### 2. Activer GitHub Pages (héberge les MP3 et le flux RSS)
Dans ton dépôt GitHub :
1. Va dans **Settings → Pages**
2. Dans **Build and deployment → Source**, choisis **Deploy from a branch**
3. Sélectionne la branche **main** et le dossier **/ (root)**, puis clique sur **Save**
Les fichiers sont ainsi accessibles publiquement sur `https://sarx613.github.io/Simon-FinTech/`.

### 3. Fonctionnement du déclencheur automatique
Le workflow `.github/workflows/podcast.yml` est programmé pour tourner automatiquement :
- **Tous les matins à 8h20 (heure de Paris)** toute l'année (gestion automatique heure d'été / heure d'hiver).
- À la demande en manuel : onglet **Actions → 🎙️ Podcast quotidien → Run workflow**.

### 4. Flux RSS et Spotify
Le flux RSS complet et conforme Spotify/Apple Podcasts est hébergé à cette adresse :
```
https://sarx613.github.io/Simon-FinTech/rss.xml
```
Pour le connecter à Spotify (à faire une seule fois si ce n'est pas déjà fait) :
1. Connecte-toi sur **[Spotify for Podcasters](https://podcasters.spotify.com)**
2. Clique sur **Add your podcast → I have a podcast → Continue with RSS**
3. Entre l'URL `https://sarx613.github.io/Simon-FinTech/rss.xml`
4. Valide le code envoyé par email et confirme. Spotify publiera ensuite automatiquement chaque nouvel épisode généré.

## Configuration (.env)

Toutes les options sont configurables dans `.env` :

| Variable | Description | Valeur par défaut |
|---|---|---|
| `LLM_PROVIDER` | Moteur LLM (`claude`, `groq`, `openai`) | `claude` |
| `ANTHROPIC_API_KEY` | Clé API Anthropic Claude | — |
| `ANTHROPIC_MODEL` | Modèle Claude | `claude-3-5-sonnet-20241022` |
| `TTS_ENGINE` | Synthèse vocale (`elevenlabs`, `edge`, `hf`) | `elevenlabs` |
| `ELEVENLABS_API_KEY` | Clé API ElevenLabs | — |
| `ELEVENLABS_VOICE_ID` | Identifiant de ta voix ElevenLabs | `ZfzastaCQOj8iuzFZuWy` |
| `ELEVENLABS_MODEL_ID` | Modèle ElevenLabs | `eleven_multilingual_v2` |
| `MAX_ARTICLES` | Nombre d'articles collectés | `5` |

## Structure du projet

| Fichier                 | Rôle                                          |
|-------------------------|-----------------------------------------------|
| `generate_podcast.py`   | Orchestrateur — point d'entrée principal      |
| `news_collector.py`     | Collecte des actus (Google News RSS)          |
| `script_generator.py`   | Rédaction du script (Groq)                    |
| `voice_synth.py`        | Synthèse vocale (Edge-TTS / Kyutai)           |
| `update_rss.py`         | Génération du flux RSS (balises iTunes)       |
| `podcasts/`             | Fichiers MP3 générés                          |
| `scripts/`              | Scripts texte archivés                        |
| `rss.xml`               | Flux RSS soumis à Spotify                      |
