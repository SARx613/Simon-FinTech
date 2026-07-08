"""
generate_podcast.py — Orchestrateur du podcast Simon FinTech (100 % gratuit)

C'est le chef d'orchestre du pipeline. Il enchaîne, de bout en bout :
  1. Collecte des actus du jour        (news_collector.py    — Google News RSS)
  2. Rédaction du script               (script_generator.py  — Groq / Llama 3.3)
  3. Génération d'un titre accrocheur  (Groq — pas de modèle payant)
  4. Synthèse vocale                   (voice_synth.py       — Edge-TTS gratuit)
  5. Sauvegarde script + MP3 + garde anti-doublon

Lancement :
    python generate_podcast.py
"""

import os
import sys
import datetime
import logging

from dotenv import load_dotenv

from news_collector import get_daily_articles
from script_generator import generate_script, _get_llm_client
from voice_synth import generate_podcast as synthesize_voice

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("simon_fintech")

SCRIPTS_DIR = "scripts"
PODCASTS_DIR = "podcasts"
LAST_SCRIPT_FILE = "script_hier.txt"          # mémoire de l'épisode précédent
TODAY_SCRIPT_FILE = "script_today.txt"        # dernier script généré (debug)

MAX_ARTICLES = int(os.getenv("MAX_ARTICLES", "6"))
MIN_WORDS = 700  # en dessous, script trop court pour un épisode 5-7 min


def _read_previous_script() -> str:
    if os.path.exists(LAST_SCRIPT_FILE):
        with open(LAST_SCRIPT_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def _generate_title(script: str) -> str:
    """Génère un titre court et accrocheur via le même LLM gratuit (Groq)."""
    # On s'appuie sur le début du script (après l'intro fixe) pour le contexte.
    paragraphs = [p for p in script.split("\n") if p.strip()]
    context = paragraphs[0][:600] if paragraphs else script[:600]

    prompt = (
        "Voici le début d'un épisode de podcast sur la finance et la tech :\n\n"
        f"{context}\n\n"
        "Donne-moi un titre accrocheur, percutant et court (max 12 mots) qui donne "
        "envie d'écouter. Pas de date, pas de guillemets, pas de ponctuation superflue. "
        "Réponds uniquement par le titre."
    )

    try:
        client, model = _get_llm_client()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=40,
        )
        title = response.choices[0].message.content.strip()
        # Nettoyage : retirer guillemets et retours à la ligne parasites
        title = title.strip('"').strip("«»").replace("\n", " ").strip()
        return title
    except Exception as e:
        logger.warning(f"Échec de génération du titre ({e}). Titre de secours utilisé.")
        return "Actu Finance & Tech du jour"


def _sanitize_filename(name: str) -> str:
    """Rend un titre utilisable comme nom de fichier."""
    for ch in '/\\:*?"<>|':
        name = name.replace(ch, "")
    return name.strip()[:120]


def main() -> int:
    today = datetime.date.today()
    date_tag = today.strftime("%d-%m-%Y")
    logger.info(f"=== Génération de l'épisode du {date_tag} ===")

    # 1. Collecte des actualités du jour
    logger.info("Étape 1/4 — Collecte des actualités…")
    articles = get_daily_articles(max_articles=MAX_ARTICLES)
    if not articles:
        logger.error("Aucun article collecté. Abandon (pas de podcast aujourd'hui).")
        return 1
    logger.info(f"{len(articles)} article(s) collecté(s).")

    # 2. Génération du script ancré sur ces articles
    logger.info("Étape 2/4 — Rédaction du script…")
    try:
        script = generate_script(articles, date=today)
    except Exception as e:
        logger.error(f"Échec de la génération du script : {e}")
        return 1

    # Garde-fous qualité
    word_count = len(script.split())
    if word_count < MIN_WORDS:
        logger.error(f"Script trop court ({word_count} mots < {MIN_WORDS}). Abandon.")
        return 1

    # Garde anti-doublon : ne pas republier un script identique à la veille
    previous = _read_previous_script()
    if script.strip() == previous:
        logger.info("Script identique à celui d'hier. Aucun nouvel épisode.")
        return 0

    # Sauvegarde du script du jour (debug/traçabilité)
    with open(TODAY_SCRIPT_FILE, "w", encoding="utf-8") as f:
        f.write(script)

    # 3. Titre accrocheur
    logger.info("Étape 3/4 — Génération du titre…")
    title = _generate_title(script)
    logger.info(f"Titre : {title}")

    safe_title = _sanitize_filename(title)
    base_name = f"{date_tag} - {safe_title}"

    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    script_path = os.path.join(SCRIPTS_DIR, base_name + ".txt")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)
    logger.info(f"Script sauvegardé : {script_path}")

    # 4. Synthèse vocale (voix gratuite)
    logger.info("Étape 4/4 — Synthèse vocale…")
    os.makedirs(PODCASTS_DIR, exist_ok=True)
    audio_path = os.path.join(PODCASTS_DIR, base_name + ".mp3")
    try:
        synthesize_voice(script, audio_path)
    except Exception as e:
        logger.error(f"Échec de la synthèse vocale : {e}")
        return 1
    logger.info(f"✅ Podcast généré : {audio_path}")

    # 5. Mémoriser le script du jour comme référence pour demain
    with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
        f.write(script)

    logger.info("=== Épisode généré avec succès ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
