# 🎙️ Simon FinTech

Podcast quotidien qui décrypte l'actualité de la finance et de la tech.
**Entièrement automatisé, 100 % gratuit**, publié automatiquement sur Spotify via un flux RSS.

## Comment ça marche

Chaque matin à **8h20 (heure de Paris)**, une routine **Claude** (sans clé API Anthropic) :

```
veille web + fetch_news.py  →  Claude rédige script_today.txt et resume_today.txt  →  publish_episode.py (ElevenLabs + RSS + git push)
```

1. **Fait sa veille** : recherche web ciblée sur les sources de référence (Reuters, Bloomberg, AP, AFP, WSJ, FT…), avec `fetch_news.py` comme radar de titres. Le podcast traite des événements qui font bouger les marchés (deals, politique, régulation, banques centrales), pas des cours de Bourse
2. **Rédige** lui-même le script (~1200-1400 mots) selon le brief de [ROUTINE_QUOTIDIENNE.md](ROUTINE_QUOTIDIENNE.md)
3. **Synthétise** le MP3 avec **ElevenLabs** (voix `ZfzastaCQOj8iuzFZuWy`)
4. **Met à jour** `rss.xml` et pousse sur GitHub Pages : Spotify lit le flux

Seule clé nécessaire : `ELEVENLABS_API_KEY`.

## Test local

```bash
pip install -r requirements.txt
cp .env.example .env          # renseigne ELEVENLABS_API_KEY
python test_elevenlabs.py     # vérifie la clé et la voix
python fetch_news.py          # écrit news_today.md
# rédige script_today.txt et resume_today.txt (3 à 6 puces pour la description), puis :
python publish_episode.py --title "Mon titre"        # ajoute --push pour publier
```

## Flux RSS et Spotify

```
https://sarx613.github.io/Simon-FinTech/rss.xml
```
À connecter une seule fois sur [Spotify for Podcasters](https://podcasters.spotify.com) (Add your podcast → RSS).

## Structure

| Fichier | Rôle |
|---|---|
| `ROUTINE_QUOTIDIENNE.md` | Procédure + brief éditorial suivis par Claude chaque matin |
| `fetch_news.py` / `news_collector.py` | Radar de titres (sources de référence, filtre opinions/cours) |
| `descriptions/` | Résumés en puces affichés comme description de chaque épisode |
| `publish_episode.py` | Voix + archivage + RSS + git push |
| `voice_synth.py` | Moteurs de synthèse vocale (ElevenLabs par défaut) |
| `update_rss.py` | Génération du flux RSS (balises iTunes) |
| `podcasts/`, `scripts/` | MP3 et scripts archivés |
