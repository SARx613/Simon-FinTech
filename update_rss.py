"""
update_rss.py — Génère le flux RSS du podcast Simon FinTech

Le flux inclut les balises iTunes/Spotify obligatoires pour être accepté et
correctement affiché par Spotify, Apple Podcasts, etc.

Hébergé sur GitHub Pages : https://sarx613.github.io/Simon-FinTech/
"""

from feedgen.feed import FeedGenerator
import datetime
import os
import re

# ─── Métadonnées du podcast (à personnaliser au besoin) ───
SITE_BASE = "https://sarx613.github.io/Simon-FinTech"
PODCAST_TITLE = "Simon FinTech"
PODCAST_AUTHOR = "Simon"
PODCAST_EMAIL = "simon5.amar@gmail.com"
PODCAST_DESCRIPTION = "Le podcast qui rend la finance et la tech simples, vivantes et passionnantes. Un décryptage quotidien de l'actualité."
PODCAST_LANGUAGE = "fr"
PODCAST_IMAGE = f"{SITE_BASE}/logo_podcast.png"
# Catégorie iTunes valide (voir liste Apple). "Business" convient à la FinTech.
PODCAST_CATEGORY = "Business"
PODCAST_SUBCATEGORY = "Investing"
PODCAST_EXPLICIT = "no"


def _parse_date_from_filename(filename: str):
    """Extrait un objet date depuis le nom de fichier (2 formats supportés)."""
    # Format DD-MM-YYYY (nommage actuel : "25-06-2025 - Titre.mp3")
    match = re.search(r"(\d{2}-\d{2}-\d{4})", filename)
    if match:
        try:
            return datetime.datetime.strptime(match.group(1), "%d-%m-%Y")
        except ValueError:
            pass

    # Format YYYYMMDD (ancien : "podcast_20250521.mp3")
    match = re.search(r"(\d{8})", filename)
    if match:
        try:
            return datetime.datetime.strptime(match.group(1), "%Y%m%d")
        except ValueError:
            pass

    return None


def _title_from_filename(filename: str, date_obj) -> str:
    """Reconstruit un titre lisible depuis le nom de fichier."""
    # Nom du type "25-06-2025 - Mon titre accrocheur.mp3" → "Mon titre accrocheur"
    stem = os.path.splitext(filename)[0]
    parts = stem.split(" - ", 1)
    if len(parts) == 2 and parts[1].strip():
        return parts[1].strip()
    # Sinon, titre générique daté
    return f"Actu du {date_obj.strftime('%d/%m/%Y')}"


def generate_rss(audio_folder="podcasts", output_file="rss.xml"):
    fg = FeedGenerator()
    fg.load_extension("podcast")

    # ─── En-tête du flux ───
    fg.title(PODCAST_TITLE)
    fg.link(href=f"{SITE_BASE}/", rel="alternate")
    fg.link(href=f"{SITE_BASE}/rss.xml", rel="self")
    fg.description(PODCAST_DESCRIPTION)
    fg.language(PODCAST_LANGUAGE)
    fg.logo(PODCAST_IMAGE)
    fg.image(PODCAST_IMAGE)

    # ─── Balises iTunes / Spotify (obligatoires) ───
    fg.podcast.itunes_author(PODCAST_AUTHOR)
    fg.podcast.itunes_summary(PODCAST_DESCRIPTION)
    fg.podcast.itunes_owner(name=PODCAST_AUTHOR, email=PODCAST_EMAIL)
    fg.podcast.itunes_image(PODCAST_IMAGE)
    fg.podcast.itunes_category(itunes_category=[{"cat": PODCAST_CATEGORY, "sub": PODCAST_SUBCATEGORY}])
    fg.podcast.itunes_explicit(PODCAST_EXPLICIT)
    fg.podcast.itunes_type("episodic")

    if not os.path.exists(audio_folder):
        print(f"⚠️ Dossier '{audio_folder}' introuvable. RSS vide généré.")
        fg.rss_file(output_file, pretty=True)
        return

    episodes_added = 0
    # reverse=True : les plus récents en premier
    for filename in sorted(os.listdir(audio_folder), reverse=True):
        if not filename.endswith(".mp3"):
            continue

        date_obj = _parse_date_from_filename(filename)
        if date_obj is None:
            print(f"⚠️ Date non reconnue, épisode ignoré : {filename}")
            continue
        date_obj = date_obj.replace(tzinfo=datetime.timezone.utc)

        filepath = os.path.join(audio_folder, filename)
        file_size = os.path.getsize(filepath)

        title = _title_from_filename(filename, date_obj)
        url = f"{SITE_BASE}/podcasts/{filename}"

        episode = fg.add_entry()
        episode.id(url)
        episode.title(title)
        episode.description(
            f"Épisode de Simon FinTech — {title}. Finance et tech décryptées."
        )
        episode.enclosure(url=url, length=str(file_size), type="audio/mpeg")
        episode.pubDate(date_obj)
        # Balises iTunes au niveau de l'épisode
        episode.podcast.itunes_author(PODCAST_AUTHOR)
        episode.podcast.itunes_summary(title)
        episode.podcast.itunes_explicit(PODCAST_EXPLICIT)
        episodes_added += 1

    fg.rss_file(output_file, pretty=True)
    print(f"✅ RSS mis à jour : {output_file} ({episodes_added} épisode(s))")


if __name__ == "__main__":
    generate_rss()
