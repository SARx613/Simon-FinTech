# 🎙️ Simon FinTech

Podcast quotidien qui décrypte l'actualité de la finance et de la tech.
**Entièrement automatisé, 100 % gratuit**, publié automatiquement sur Spotify via un flux RSS.

## Comment ça marche

Chaque matin, GitHub Actions exécute le pipeline :

```
news_collector.py  →  script_generator.py  →  voice_synth.py  →  update_rss.py
   (Google News)        (Groq / Llama 3.3)      (Edge-TTS)         (flux RSS)
```

1. **Collecte** les actus du jour (Google News RSS, sans clé API)
2. **Rédige** un script de ~650 mots ancré sur ces articles (Groq, gratuit)
3. **Génère** un titre accrocheur (Groq)
4. **Synthétise** la voix en MP3 (Edge-TTS, gratuit et sans quota)
5. **Met à jour** le flux `rss.xml` et pousse le tout sur GitHub

Spotify lit ce flux RSS automatiquement → chaque nouvel épisode apparaît tout seul.

`generate_podcast.py` est le chef d'orchestre qui enchaîne les 4 premières étapes.

## Installation locale

```bash
pip install -r requirements.txt
cp .env.example .env          # puis renseigne ta clé GROQ_API_KEY
python generate_podcast.py    # génère l'épisode du jour
python update_rss.py          # met à jour le flux RSS
```

## Mise en route de l'automatisation (à faire une seule fois)

### 1. Ajouter le secret GitHub
Dans le dépôt GitHub → **Settings → Secrets and variables → Actions → New repository secret** :
- Nom : `GROQ_API_KEY`
- Valeur : ta clé Groq (https://console.groq.com)

> ⚠️ L'ancien workflow attendait une clé ElevenLabs : ce n'est plus nécessaire.
> Seul `GROQ_API_KEY` est requis. Edge-TTS ne demande aucune clé.

### 2. Activer GitHub Pages (héberge les MP3)
**Settings → Pages** → Source : branche `main`, dossier `/ (root)`.
Les fichiers seront servis sur `https://sarx613.github.io/Simon-FinTech/`.

### 3. Vérifier le déclenchement
Le workflow `.github/workflows/podcast.yml` tourne :
- automatiquement à **06:00 UTC** chaque jour ;
- ou à la demande via **Actions → Podcast quotidien → Run workflow**.

Lance-le une première fois à la main pour valider que tout passe.

### 4. Soumettre le flux à Spotify (une seule fois)
1. Va sur **[Spotify for Podcasters](https://podcasters.spotify.com)** et connecte-toi.
2. **Add your podcast → I have a podcast → Continue with RSS**.
3. Colle l'URL du flux :
   ```
   https://sarx613.github.io/Simon-FinTech/rss.xml
   ```
4. Valide la propriété (code envoyé par mail) et confirme les métadonnées.

À partir de là, **plus rien à faire** : Spotify relit le flux régulièrement et publie
chaque nouvel épisode automatiquement. (La même URL fonctionne pour Apple Podcasts,
Deezer, Amazon Music, etc.)

## Configuration

Tout se règle dans `.env` (voir `.env.example`) :

| Variable        | Rôle                                  | Défaut               |
|-----------------|---------------------------------------|----------------------|
| `GROQ_API_KEY`  | Clé LLM (gratuite)                    | —                    |
| `EDGE_VOICE`    | Voix française Edge-TTS               | `fr-FR-HenriNeural`  |
| `TTS_ENGINE`    | `edge`, `hf` (voix clonée) ou `kyutai`| `edge`               |
| `HF_SPACE_ID`   | Space HF de la voix clonée (`hf`)     | —                    |
| `HF_TOKEN`      | Token Hugging Face (`hf`)             | —                    |

**Voix clonée** : le dossier `hf_space/` contient un Space Hugging Face prêt à
déployer (Kyutai + ta voix). Une fois le Space en ligne, bascule la variable
GitHub `TTS_ENGINE=hf` — voir `hf_space/README.md` pour les étapes.
| `MAX_ARTICLES`  | Nombre d'articles par épisode         | `5`                  |

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
