#!/bin/bash
# run_daily.sh — Test manuel de la partie publication (voix + RSS) à partir de script_today.txt.
# La routine quotidienne complète (collecte + rédaction) est décrite dans ROUTINE_QUOTIDIENNE.md :
# c'est Claude qui l'exécute chaque matin.
set -e
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -d venv ] && source venv/bin/activate
python3 publish_episode.py --title "${1:?usage: ./run_daily.sh \"Titre\" [--push]}" ${2:+$2}
