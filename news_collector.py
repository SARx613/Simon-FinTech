"""
news_collector.py — Collecte automatique des actualités Finance & Tech
Utilise Google News RSS (100% gratuit, sans clé API) + newspaper4k pour le texte complet.
"""

import feedparser
import datetime
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Sources premium finance & tech (anglophones : les plus en avance et réactives).
# Bloomberg/Reuters/FT donnent surtout titres + tendances (paywall) ; CNBC/Yahoo/
# MarketWatch/TechCrunch offrent en général le texte complet. Le script étant en
# français, le LLM traduit et reformule — les sources anglaises ne posent pas de souci.
RSS_FEEDS = {
    # Texte complet accessible — on les tente en premier (extraction fiable)
    "cnbc_finance": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
    "cnbc_tech": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910",
    "yahoo_finance": "https://finance.yahoo.com/news/rssindex",
    "marketwatch": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "techcrunch": "https://techcrunch.com/feed/",
    # Écho francophone (pour ancrer certains sujets côté Europe/France)
    "latribune": "https://www.latribune.fr/rss/rubriques/entreprises-finance.html",
    "lesechos_finance": "https://services.lesechos.fr/rss/les-echos-finance-marches.xml",
    # Références premium paywallées — extraction full-text rarement possible,
    # mais leurs titres + snippets restent une excellente matière (fin de liste)
    "bloomberg_markets": "https://feeds.bloomberg.com/markets/news.rss",
    "bloomberg_tech": "https://feeds.bloomberg.com/technology/news.rss",
    "ft_home": "https://www.ft.com/rss/home",
}

# Filet de sécurité : Google News si les sources premium ne donnent pas assez.
FALLBACK_FEEDS = {
    "google_business": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=fr&gl=FR&ceid=FR:fr",
    "google_tech": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=fr&gl=FR&ceid=FR:fr",
}

# Conservé pour compatibilité (ancien nom)
EXTRA_FEEDS = FALLBACK_FEEDS

# Fenêtre de fraîcheur : on ne garde que les articles publiés dans les dernières
# MAX_AGE_HOURS heures (24 par défaut → actu d'aujourd'hui / hier soir).
MAX_AGE_HOURS = 24


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


def _collect_entries(feeds: dict) -> list[dict]:
    """Parse une série de flux RSS et retourne les entrées récentes (< 48h)."""
    entries = []
    for feed_name, feed_url in feeds.items():
        logger.info(f"Parsing flux RSS : {feed_name}")
        try:
            feed = feedparser.parse(feed_url)
            if feed.bozo and not feed.entries:
                logger.warning(f"Erreur parsing {feed_name}: {feed.bozo_exception}")
                continue

            for entry in feed.entries:
                # Certains flux exposent published_parsed, d'autres updated_parsed.
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                if published:
                    pub_date = datetime.datetime(*published[:6])
                    age_hours = (datetime.datetime.utcnow() - pub_date).total_seconds() / 3600
                    if age_hours > MAX_AGE_HOURS:
                        continue

                entries.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "feed": feed_name,
                })
        except Exception as e:
            logger.error(f"Erreur lors du parsing de {feed_name}: {e}")
            continue
    return entries


def _dedupe(entries: list[dict]) -> list[dict]:
    """Déduplique les entrées par titre."""
    seen, unique = set(), []
    for entry in entries:
        key = entry["title"].lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(entry)
    return unique


def _interleave_by_feed(entries: list[dict]) -> list[dict]:
    """
    Panache les entrées en alternant les sources (1 CNBC, 1 Yahoo, 1 TechCrunch…)
    pour que l'épisode couvre plusieurs médias au lieu de vider le premier flux.
    L'ordre des flux dans RSS_FEEDS est préservé à chaque tour.
    """
    by_feed: dict[str, list[dict]] = {}
    for entry in entries:
        by_feed.setdefault(entry["feed"], []).append(entry)

    interleaved = []
    while any(by_feed.values()):
        for feed_entries in by_feed.values():
            if feed_entries:
                interleaved.append(feed_entries.pop(0))
    return interleaved


def get_daily_articles(max_articles: int = 6, include_extra: bool = True) -> list[dict]:
    """
    Récupère les meilleurs articles finance & tech du jour, avec texte complet.

    Stratégie : on privilégie les flux spécialisés (RSS_FEEDS). Si on n'a pas
    assez d'articles exploitables, on complète avec Google News (FALLBACK_FEEDS).
    On préfère les articles au texte complet (>= 200 caractères) ; les snippets
    RSS courts ne sont utilisés qu'en dernier recours.

    Args:
        max_articles: Nombre d'articles visés (défaut: 6, pour un épisode 6-7 min).
        include_extra: Autoriser le complément Google News si nécessaire.

    Returns:
        Liste de dicts avec les clés: title, text, url, source.
    """
    # 1) Sources spécialisées d'abord, panachées pour la diversité des médias
    entries = _interleave_by_feed(_dedupe(_collect_entries(RSS_FEEDS)))
    logger.info(f"Entrées (sources spécialisées) : {len(entries)}")

    # Budget de tentatives d'extraction : évite de perdre des minutes sur des
    # paywalls successifs (Bloomberg/FT). Au-delà, on complète avec les snippets.
    attempts_left = max_articles * 4

    def _extract_from(entries_list, articles):
        """Extrait le texte des entrées, ajoute aux articles jusqu'à max_articles."""
        nonlocal attempts_left
        snippets_fallback = []
        for entry in entries_list:
            if len(articles) >= max_articles or attempts_left <= 0:
                break
            url = entry["link"]
            if "news.google.com" in url:
                url = _resolve_google_news_url(url)

            attempts_left -= 1
            logger.info(f"Extraction : {entry['title'][:60]}...")
            article = _extract_article_text(url)
            if article and len(article["text"]) >= 200:
                articles.append(article)
            elif entry.get("summary") and len(_strip_html(entry["summary"])) > 100:
                # On garde le snippet de côté : utilisé seulement si on manque d'articles
                snippets_fallback.append({
                    "title": entry["title"],
                    "text": _strip_html(entry["summary"]),
                    "url": url,
                    "source": "RSS snippet",
                })
        return snippets_fallback

    articles = []
    snippets = _extract_from(entries, articles)

    # 2) Complément Google News si pas assez d'articles full-text
    if len(articles) < max_articles and include_extra:
        logger.info("Pas assez d'articles spécialisés — complément via Google News.")
        extra_entries = _dedupe(_collect_entries(FALLBACK_FEEDS))
        snippets += _extract_from(extra_entries, articles)

    # 3) En dernier recours, compléter avec les snippets récoltés
    for snip in snippets:
        if len(articles) >= max_articles:
            break
        logger.info(f"Complément via snippet RSS : {snip['title'][:60]}")
        articles.append(snip)

    logger.info(f"Articles retenus : {len(articles)}/{max_articles}")
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
