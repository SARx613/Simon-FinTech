"""
news_collector.py — Collecte automatique des actualités qui font bouger les marchés.

Ligne éditoriale : des FAITS (rachats, politique, régulation, géopolitique, banques
centrales, résultats stratégiques…), pas des commentaires de cours de Bourse ni des
opinions. Sources : agences et médias de référence uniquement (Reuters, Bloomberg,
AP, AFP, WSJ, FT, BBC, CNBC, Le Monde) + communiqués officiels (Fed, BCE, SEC).

Reuters, AP et AFP n'ont plus de flux RSS publics : on les interroge via des
recherches Google News restreintes à leur domaine (titre + source, sans clé API).
"""

import datetime
import logging
import re
from typing import Optional
from urllib.parse import quote_plus

import feedparser

logger = logging.getLogger(__name__)


def _gnews(query: str, lang: str = "en") -> str:
    """URL de recherche Google News (RSS) sur les dernières 24-36 h."""
    hl, gl, ceid = ("en-US", "US", "US:en") if lang == "en" else ("fr", "FR", "FR:fr")
    return f"https://news.google.com/rss/search?q={quote_plus(query)}&hl={hl}&gl={gl}&ceid={ceid}"


# Chaque source : nom interne → (libellé affiché, URL, fenêtre de fraîcheur en heures)
# Les communiqués officiels (Fed/BCE/SEC) sont rares : fenêtre plus large.
SOURCES = {
    # ── Agences de presse ──
    "reuters_business": ("Reuters", _gnews("site:reuters.com business OR markets when:1d"), 36),
    "reuters_deals": ("Reuters", _gnews("site:reuters.com (acquisition OR merger OR takeover OR buyout OR \"to buy\" OR \"agrees to\") when:1d"), 36),
    "reuters_policy": ("Reuters", _gnews("site:reuters.com (tariffs OR sanctions OR regulator OR antitrust OR \"central bank\" OR \"export controls\" OR ceasefire) when:1d"), 36),
    "ap_business": ("AP", _gnews("site:apnews.com (business OR economy OR companies) when:1d"), 36),
    "afp_eco": ("AFP", _gnews("AFP économie OR entreprises OR marchés when:1d", lang="fr"), 36),
    # ── Presse financière de référence ──
    "bloomberg_business": ("Bloomberg", "https://feeds.bloomberg.com/business/news.rss", 36),
    "bloomberg_politics": ("Bloomberg", "https://feeds.bloomberg.com/politics/news.rss", 36),
    "bloomberg_tech": ("Bloomberg", "https://feeds.bloomberg.com/technology/news.rss", 36),
    "bloomberg_markets": ("Bloomberg", "https://feeds.bloomberg.com/markets/news.rss", 36),
    "wsj_business": ("The Wall Street Journal", "https://feeds.content.dowjones.io/public/rss/WSJcomUSBusiness", 36),
    "wsj_world": ("The Wall Street Journal", "https://feeds.content.dowjones.io/public/rss/RSSWorldNews", 36),
    "wsj_markets": ("The Wall Street Journal", "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain", 36),
    "ft_companies": ("Financial Times", "https://www.ft.com/companies?format=rss", 36),
    "ft_home": ("Financial Times", "https://www.ft.com/rss/home", 36),
    "bbc_business": ("BBC", "https://feeds.bbci.co.uk/news/business/rss.xml", 36),
    "cnbc_world": ("CNBC", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362", 36),
    "cnbc_finance": ("CNBC", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664", 36),
    "cnbc_tech": ("CNBC", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910", 36),
    "lemonde_eco": ("Le Monde", "https://www.lemonde.fr/economie/rss_full.xml", 36),
    # ── Communiqués officiels ──
    "fed_press": ("Federal Reserve", "https://www.federalreserve.gov/feeds/press_all.xml", 96),
    "ecb_press": ("BCE", "https://www.ecb.europa.eu/rss/press.html", 96),
    "sec_press": ("SEC", "https://www.sec.gov/news/pressreleases.rss", 96),
}

# Exclusions : contenus d'opinion, de conseil, de commentaire de cours ou de service.
EXCLUDE_TITLE = re.compile(
    r"\b(opinion|editorial|column|commentary|breakingviews|op-ed|podcast|newsletter|"
    r"watch live|livestream|live blog|live updates|quiz|review:|how to|"
    r"stocks? to (buy|watch|sell)|best (stocks|etfs?|credit cards?)|should you|"
    r"price target|upgrades?|downgrades?|analysts? (say|says|expect)|"
    r"markets? wrap|stock market today|stocks? making the biggest moves|"
    r"biggest (stock )?movers|what to watch|futures (rise|fall|slip|edge)|"
    r"horoscope|recipe|sport|football|nba|nfl|celebrity)\b",
    re.IGNORECASE,
)
EXCLUDE_URL = re.compile(r"/(opinion|opinions|commentary|video|videos|podcasts?|newsletters?|lifestyle|sport)/", re.IGNORECASE)

# Signaux d'ÉVÉNEMENT (fait concret qui peut faire bouger un titre ou un secteur)
EVENT_KEYWORDS = re.compile(
    r"\b(acquire[sd]?|acquisition|merger|merge[sd]?|takeover|buyout|to buy|agrees? to|deal|bid|"
    r"stake|spin-?off|ipo|listing|bankruptcy|chapter 11|restructuring|layoffs?|"
    r"antitrust|probe|investigation|lawsuit|sues?|fine[sd]?|settlement|ruling|court|"
    r"regulat\w+|law|bill|ban(s|ned)?|sanctions?|tariffs?|export controls?|embargo|"
    r"central bank|rate (cut|hike|decision)|fed|ecb|boe|boj|imf|treasury|"
    r"election|president|minister|government|congress|senate|parliament|eu|china|russia|ukraine|"
    r"war|ceasefire|attack|strike|opec|supply chain|shortage|"
    r"approves?|blocks?|launch(es|ed)?|unveils?|announces?|partnership|contract|"
    r"rachat|fusion|offre|sanctions?|droits de douane|régulat\w+|accord|enquête|amende|"
    r"banque centrale|gouvernement|guerre|cessez-le-feu)\b",
    re.IGNORECASE,
)
# Titres qui ne font que commenter un mouvement de cours : on les rétrograde.
PRICE_MOVE_KEYWORDS = re.compile(
    r"\b(shares? (rise|fall|jump|slide|drop|surge|slump|climb|tumble)|stocks? (rise|fall|jump|slide|drop|surge|slump|climb|tumble|rally)|"
    r"record high|all-time high|rally|sell-?off|slump|slides?|tumbles?|soars?|plunges?|"
    r"oil prices?|gold prices?|bitcoin (price|falls|rises|hits)|dow|nasdaq|s&p 500|"
    r"cours|séance|clôture)\b",
    re.IGNORECASE,
)


def _strip_html(text: str) -> str:
    """Supprime les balises HTML d'un texte."""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def _score(entry: dict) -> int:
    """Plus le score est haut, plus le titre ressemble à un événement factuel."""
    text = f"{entry['title']} {entry['summary']}"
    events = len(set(m.group(0).lower() for m in EVENT_KEYWORDS.finditer(text)))
    price_moves = len(set(m.group(0).lower() for m in PRICE_MOVE_KEYWORDS.finditer(entry["title"])))
    return min(events, 4) * 2 - price_moves * 3


def _extract_article_text(url: str) -> Optional[str]:
    """Texte complet d'un article en accès libre (trafilatura). None si paywall/échec."""
    try:
        import trafilatura

        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False)
            if text and len(text) >= 300:
                return text
    except ImportError:
        logger.debug("trafilatura non installé")
    except Exception as e:
        logger.debug(f"trafilatura a échoué pour {url}: {e}")
    return None


def _clean_title(title: str, label: str) -> str:
    """Google News ajoute ' - Reuters' en fin de titre : on l'enlève."""
    return re.sub(r"\s+-\s+[^-]{2,40}$", "", title).strip() if " - " in title else title.strip()


def _collect_entries() -> list[dict]:
    """Parse tous les flux, filtre l'opinion/le service et les articles trop anciens."""
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    entries = []
    for name, (label, url, max_age) in SOURCES.items():
        logger.info(f"Flux : {name}")
        try:
            feed = feedparser.parse(url, agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
            if feed.bozo and not feed.entries:
                logger.warning(f"Erreur parsing {name}: {feed.bozo_exception}")
                continue
            for entry in feed.entries:
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                if published:
                    pub_date = datetime.datetime(*published[:6])
                    if (now - pub_date).total_seconds() / 3600 > max_age:
                        continue
                title = _clean_title(entry.get("title", ""), label)
                link = entry.get("link", "")
                if not title or EXCLUDE_TITLE.search(title) or EXCLUDE_URL.search(link):
                    continue
                summary = _strip_html(entry.get("summary", ""))
                # Les snippets Google News ne font que répéter le titre
                if summary.lower().startswith(title.lower()[:40]):
                    summary = ""
                entries.append({
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "source": label,
                    "feed": name,
                    "official": name.endswith("_press"),
                })
        except Exception as e:
            logger.error(f"Erreur lors du parsing de {name}: {e}")
    return entries


def _dedupe(entries: list[dict]) -> list[dict]:
    """Déduplique par titre normalisé ; garde l'entrée la plus riche (avec résumé)."""
    best: dict[str, dict] = {}
    for entry in entries:
        key = re.sub(r"\W+", " ", entry["title"].lower()).strip()
        if key and (key not in best or len(entry["summary"]) > len(best[key]["summary"])):
            best[key] = entry
    return list(best.values())


_STOPWORDS = {"the", "a", "an", "of", "to", "in", "on", "for", "and", "as", "at", "by", "with", "is", "are",
              "says", "say", "after", "over", "from", "its", "his", "her", "le", "la", "les", "de", "des", "du",
              "un", "une", "et", "en", "pour", "sur", "dans", "au", "aux", "que", "qui"}


def _tokens(title: str) -> set:
    return {w for w in re.findall(r"[a-zà-ÿ0-9]{3,}", title.lower()) if w not in _STOPWORDS}


def _same_story(a: set, b: set) -> bool:
    """Deux titres parlent du même événement s'ils partagent assez de mots-clés."""
    return len(a & b) >= 3 or (len(a & b) / max(1, min(len(a), len(b)))) >= 0.5


def _select_diverse(entries: list[dict], n: int, per_source_cap: int = 2) -> list[dict]:
    """Prend les mieux notés : max 2 par média, et jamais deux titres sur le même événement."""
    picked, counts, seen_tokens = [], {}, []
    for entry in sorted(entries, key=_score, reverse=True):
        if _score(entry) <= 0 and not entry["official"]:
            continue
        if counts.get(entry["source"], 0) >= per_source_cap:
            continue
        toks = _tokens(entry["title"])
        if any(_same_story(toks, t) for t in seen_tokens):
            continue
        seen_tokens.append(toks)
        counts[entry["source"]] = counts.get(entry["source"], 0) + 1
        picked.append(entry)
        if len(picked) >= n:
            break
    return picked


def get_daily_articles(max_articles: int = 10, extra_headlines: int = 25) -> dict:
    """
    Retourne les actualités factuelles du jour.

    Returns:
        {"articles": [...], "headlines": [...]} où chaque item contient
        title, text (texte complet, snippet ou ""), url, source.
        "articles" = les meilleurs sujets (texte complet quand l'accès est libre).
        "headlines" = autres titres de référence, pour élargir le choix des sujets.
    """
    entries = _dedupe(_collect_entries())
    logger.info(f"Entrées candidates après filtrage : {len(entries)}")

    top = _select_diverse(entries, max_articles)
    articles = []
    for entry in top:
        text = ""
        # Seuls les médias en accès libre se laissent extraire ; on n'insiste pas sur les paywalls.
        if "news.google.com" not in entry["link"] and entry["source"] in ("BBC", "CNBC", "Le Monde", "Federal Reserve", "BCE", "SEC"):
            logger.info(f"Extraction : {entry['title'][:70]}")
            text = _extract_article_text(entry["link"]) or ""
        articles.append({
            "title": entry["title"],
            "text": text or entry["summary"],
            "url": entry["link"],
            "source": entry["source"],
            "full_text": bool(text),
        })

    seen_tokens = [_tokens(e["title"]) for e in top]
    headlines = []
    for e in sorted(entries, key=_score, reverse=True):
        if len(headlines) >= extra_headlines:
            break
        toks = _tokens(e["title"])
        if _score(e) <= 0 or any(_same_story(toks, t) for t in seen_tokens):
            continue
        seen_tokens.append(toks)
        headlines.append({"title": e["title"], "text": "", "url": e["link"], "source": e["source"]})
    logger.info(f"Articles retenus : {len(articles)} (+{len(headlines)} titres)")
    return {"articles": articles, "headlines": headlines}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    result = get_daily_articles()
    for i, art in enumerate(result["articles"], 1):
        print(f"{i:2}. [{art['source']}] {art['title']}  ({len(art['text'])} car.)")
    print("\nAutres titres :")
    for h in result["headlines"]:
        print(f" - [{h['source']}] {h['title']}")
