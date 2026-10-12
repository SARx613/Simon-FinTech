"""
fetch_news.py — Étape 1 de la routine quotidienne : collecte des faits du jour.

Écrit les articles dans news_today.md, que Claude lit pour rédiger le script.

Lancement :
    python fetch_news.py
"""

import os
import sys
import logging

from dotenv import load_dotenv

from news_collector import get_daily_articles

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

OUTPUT_FILE = "news_today.md"
MAX_ARTICLES = int(os.getenv("MAX_ARTICLES", "10"))
MAX_CHARS_PER_ARTICLE = 3000


def main() -> int:
    result = get_daily_articles(max_articles=MAX_ARTICLES)
    articles, headlines = result["articles"], result["headlines"]
    if not articles:
        print("Aucun article collecté.", file=sys.stderr)
        return 1

    parts = ["# Sujets du jour (agences et médias de référence)\n"]
    for i, art in enumerate(articles, 1):
        body = art["text"][:MAX_CHARS_PER_ARTICLE] or "(titre seul : à vérifier et compléter via WebSearch/WebFetch)"
        parts.append(
            f"## Sujet {i} — {art['title']}\n"
            f"Source : {art['source']} — {art.get('url', '')}\n\n"
            f"{body}\n"
        )

    if headlines:
        parts.append("# Autres titres du jour (pour élargir le choix)\n")
        parts.extend(f"- [{h['source']}] {h['title']}" for h in headlines)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(parts) + "\n")

    print(f"✅ {len(articles)} sujet(s) + {len(headlines)} titre(s) écrits dans {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
