"""
fetch_news.py — Étape 1 de la routine quotidienne : collecte des actus du jour.

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
MAX_ARTICLES = int(os.getenv("MAX_ARTICLES", "8"))
MAX_CHARS_PER_ARTICLE = 3000


def main() -> int:
    articles = get_daily_articles(max_articles=MAX_ARTICLES)
    if not articles:
        print("Aucun article collecté.", file=sys.stderr)
        return 1

    parts = []
    for i, art in enumerate(articles, 1):
        parts.append(
            f"## Article {i} — {art['title']}\n"
            f"URL : {art.get('url', '')}\n\n"
            f"{art['text'][:MAX_CHARS_PER_ARTICLE]}\n"
        )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))

    print(f"✅ {len(articles)} article(s) écrits dans {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
