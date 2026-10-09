"""
publish_episode.py — Étape 3 de la routine quotidienne : voix + RSS (+ git).

Prend le script rédigé par Claude, le passe à ElevenLabs, range le MP3 et le
texte, met à jour rss.xml, puis commit/push si --push est demandé.

Lancement :
    python publish_episode.py --title "Titre de l'épisode" [--script script_today.txt] [--push]
"""

import argparse
import datetime
import logging
import os
import subprocess
import sys

from dotenv import load_dotenv

load_dotenv()

from voice_synth import generate_podcast as synthesize_voice  # noqa: E402
from update_rss import generate_rss  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("simon_fintech")

SCRIPTS_DIR = "scripts"
PODCASTS_DIR = "podcasts"
LAST_SCRIPT_FILE = "script_hier.txt"
MIN_WORDS = 700
INTRO = "Salut c'est Simon, bienvenue dans le podcast qui rend la finance et la tech simples et surtout passionnantes."
OUTRO = "À demain pour un nouveau point sur l'actu tech !"


def _sanitize_filename(name: str) -> str:
    for ch in '/\\:*?"<>|':
        name = name.replace(ch, "")
    return name.strip()[:120]


def _git(*args: str) -> None:
    subprocess.run(["git", *args], check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True, help="Titre de l'épisode (sans date)")
    parser.add_argument("--script", default="script_today.txt")
    parser.add_argument("--push", action="store_true", help="commit + push vers GitHub Pages")
    args = parser.parse_args()

    with open(args.script, "r", encoding="utf-8") as f:
        script = f.read().strip()

    # Garde-fous qualité avant de dépenser des crédits ElevenLabs
    words = len(script.split())
    if words < MIN_WORDS:
        logger.error(f"Script trop court ({words} mots < {MIN_WORDS}). Abandon.")
        return 1
    if INTRO not in script:
        logger.error("L'intro obligatoire est absente du script. Abandon.")
        return 1
    if not script.endswith(OUTRO):
        logger.error("Le script ne se termine pas par la phrase de conclusion obligatoire. Abandon.")
        return 1
    if os.path.exists(LAST_SCRIPT_FILE):
        with open(LAST_SCRIPT_FILE, "r", encoding="utf-8") as f:
            if f.read().strip() == script:
                logger.error("Script identique à celui d'hier. Abandon.")
                return 1

    date_tag = datetime.date.today().strftime("%d-%m-%Y")
    base_name = f"{date_tag} - {_sanitize_filename(args.title)}"
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    os.makedirs(PODCASTS_DIR, exist_ok=True)
    script_path = os.path.join(SCRIPTS_DIR, base_name + ".txt")
    audio_path = os.path.join(PODCASTS_DIR, base_name + ".mp3")

    if os.path.exists(audio_path):
        logger.error(f"L'épisode existe déjà : {audio_path}. Abandon.")
        return 1

    logger.info(f"Synthèse vocale ({words} mots)…")
    synthesize_voice(script, audio_path)

    # La voix a réussi : on archive le script et on le mémorise comme « hier » de demain
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)
    with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
        f.write(script)

    generate_rss()

    if args.push:
        _git("add", audio_path, script_path, "rss.xml", LAST_SCRIPT_FILE, "script_today.txt")
        _git("commit", "-m", f"🎙️ Épisode du {date_tag} — {args.title}")
        _git("push", "origin", "main")
        logger.info("✅ Publié sur GitHub Pages (Spotify lit le flux RSS).")

    logger.info(f"✅ Épisode prêt : {audio_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
