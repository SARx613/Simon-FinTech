"""
news_collector.py — Collecte automatique des actualités Finance & Tech
Utilise Google News RSS (100% gratuit, sans clé API) + newspaper4k pour le texte complet.
"""

import feedparser
import datetime
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Flux RSS Google News en français (Finance + Tech)
RSS_FEEDS = {
    "business": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=fr&gl=FR&ceid=FR:fr",
    "technology": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=fr&gl=FR&ceid=FR:fr",
}

# Sources supplémentaires (optionnel)
EXTRA_FEEDS = {
    "techcrunch": "https://techcrunch.com/feed/",
}


def _resolve_google_news_url(google_url: str) -> str:
    """
    Les URLs Google News sont des redirections (https://news.google.com/rss/articles/...).
    On suit la redirection pour obtenir l'URL originale de l'article.
    Google News bloque les requêtes HEAD, il faut faire un GET avec un User-Agent de navigateur.
    """
    import requests
    import re

    try:
        resp = requests.get(
            google_url,
            allow_redirects=True,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36"
            },
        )
        # Si on a été redirigé, retourner l'URL finale
        if resp.url and "news.google.com" not in resp.url:
            return resp.url

        # Sinon, chercher l'URL originale dans le contenu HTML
        match = re.search(r'data-n-au="([^"]+)"', resp.text)
        if match:
            return match.group(1)

        return google_url
    except Exception:
        return google_url


def _strip_html(text: str) -> str:
    """Supprime les balises HTML d'un texte."""
    import re

    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def _extract_article_text(url: str) -> Optional[dict]:
    """
    Extrait le titre et le texte complet d'un article.
    Essaie d'abord avec newspaper4k, puis avec trafilatura en fallback.
    Retourne None si l'extraction échoue.
    """
    # Méthode 1 : newspaper4k
    try:
        from newspaper import Article

        article = Article(url, language="fr")
        article.download()
        article.parse()

        if len(article.text) >= 200:
            return {
                "title": article.title,
                "text": article.text,
                "url": url,
                "source": article.source_url or url,
            }
    except Exception as e:
        logger.debug(f"newspaper4k a échoué pour {url}: {e}")

    # Méthode 2 : trafilatura (souvent plus robuste)
    try:
        import trafilatura

        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False)
            if text and len(text) >= 200:
                # Extraire un titre approximatif (première ligne ou premiers mots)
                metadata = trafilatura.extract(downloaded, output_format="json", include_comments=False)
                title = url  # Par défaut
                if metadata:
                    import json
                    meta = json.loads(metadata)
                    title = meta.get("title", url)

                return {
                    "title": title,
                    "text": text,
                    "url": url,
                    "source": url,
                }
    except ImportError:
        logger.debug("trafilatura non installé, fallback ignoré")
    except Exception as e:
        logger.debug(f"trafilatura a échoué pour {url}: {e}")

    logger.warning(f"Article trop court ou inaccessible, ignoré : {url}")
    return None


def get_daily_articles(max_articles: int = 5, include_extra: bool = False) -> list[dict]:
    """
    Récupère les articles d'actualité du jour en finance et tech.

    Args:
        max_articles: Nombre maximum d'articles à retourner (défaut: 5)
        include_extra: Inclure les sources supplémentaires (TechCrunch, etc.)

    Returns:
        Liste de dictionnaires avec les clés: title, text, url, source
    """
    feeds = dict(RSS_FEEDS)
    if include_extra:
        feeds.update(EXTRA_FEEDS)

    all_entries = []

    for feed_name, feed_url in feeds.items():
        logger.info(f"Parsing flux RSS : {feed_name}")
        try:
            feed = feedparser.parse(feed_url)

            if feed.bozo and not feed.entries:
                logger.warning(f"Erreur parsing {feed_name}: {feed.bozo_exception}")
                continue

            for entry in feed.entries:
                # Vérifier que l'article est récent (dernières 48h)
                published = entry.get("published_parsed")
                if published:
                    pub_date = datetime.datetime(*published[:6])
                    age = datetime.datetime.now() - pub_date
                    if age.days > 2:
                        continue

                all_entries.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "feed": feed_name,
                })

        except Exception as e:
            logger.error(f"Erreur lors du parsing de {feed_name}: {e}")
            continue

    logger.info(f"Total d'entrées RSS collectées : {len(all_entries)}")

    # Dédupliquer par titre (Google News peut avoir des doublons)
    seen_titles = set()
    unique_entries = []
    for entry in all_entries:
        title_lower = entry["title"].lower().strip()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            unique_entries.append(entry)

    # Extraire le texte complet de chaque article
    articles = []
    for entry in unique_entries:
        if len(articles) >= max_articles:
            break

        url = entry["link"]

        # Résoudre les redirections Google News
        if "news.google.com" in url:
            url = _resolve_google_news_url(url)

        logger.info(f"Extraction de l'article : {entry['title'][:60]}...")
        article = _extract_article_text(url)

        if article:
            articles.append(article)
        else:
            # Fallback : utiliser le snippet RSS si l'extraction échoue
            if entry.get("summary") and len(entry["summary"]) > 100:
                logger.info(f"Fallback sur le snippet RSS pour : {entry['title'][:60]}")
                articles.append({
                    "title": entry["title"],
                    "text": _strip_html(entry["summary"]),
                    "url": url,
                    "source": "RSS snippet",
                })

    logger.info(f"Articles extraits avec succès : {len(articles)}/{max_articles}")
    return articles


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    articles = get_daily_articles(max_articles=5)

    for i, art in enumerate(articles, 1):
        print(f"\n{'='*80}")
        print(f"Article {i}: {art['title']}")
        print(f"URL: {art['url']}")
        print(f"Longueur: {len(art['text'])} caractères")
        print(f"Extrait: {art['text'][:300]}...")
