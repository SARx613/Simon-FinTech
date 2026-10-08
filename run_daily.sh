#!/bin/bash
# ==============================================================================
# run_daily.sh — Exécution locale quotidienne du podcast Simon FinTech
# ==============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "🎙️ [$(date '+%Y-%m-%d %H:%M:%S')] Démarrage de la génération Simon FinTech..."

# Activer l'environnement Python si présent
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "$HOME/miniconda3" ]; then
    source "$HOME/miniconda3/bin/activate" base 2>/dev/null || true
fi

# 1. Génération de l'épisode (collecte -> script -> voix MP3)
python3 generate_podcast.py

# 2. Mise à jour du flux RSS
python3 update_rss.py

# 3. Synchronisation git optionnelle (si exécuté localement et qu'on veut pusher)
if [ "$1" == "--push" ]; then
    echo "🚀 Publication vers GitHub Pages..."
    git add podcasts/*.mp3 scripts/*.txt rss.xml script_hier.txt script_today.txt
    git commit -m "🎙️ Épisode du $(date '+%d-%m-%Y')" || echo "Rien à committer"
    git push origin main
    echo "✅ Publié et disponible pour Spotify."
fi

echo "🎉 [$(date '+%Y-%m-%d %H:%M:%S')] Terminé avec succès !"
