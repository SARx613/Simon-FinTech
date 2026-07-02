"""
update_rss.py — Génère le flux RSS pour le podcast Simon FinTech
Hébergé sur GitHub Pages : https://sarx613.github.io/Simon-FinTech/
"""

from feedgen.feed import FeedGenerator
import datetime
import os
import re


def generate_rss(audio_folder="podcasts", output_file="rss.xml"):
    """
    Génère un flux RSS à partir des fichiers MP3 dans le dossier podcasts.
    Compatible avec les formats de nommage :
      - podcast_YYYYMMDD.mp3
      - podcast_DD-MM-YYYY.mp3
    """
    fg = FeedGenerator()
    fg.load_extension("podcast")

    fg.title("Simon FinTech")
    fg.link(href="https://sarx613.github.io/Simon-FinTech/", rel="alternate")
    fg.logo("https://sarx613.github.io/Simon-FinTech/logo_podcast.png")
    fg.image("https://sarx613.github.io/Simon-FinTech/logo_podcast.png")
    fg.description("Le podcast qui rend la finance et la tech simples, vivantes et passionnantes.")
    fg.language("fr")
    fg.link(href="https://sarx613.github.io/Simon-FinTech/rss.xml", rel="self")

    # Parcourir les fichiers MP3
    if not os.path.exists(audio_folder):
        print(f"⚠️ Dossier '{audio_folder}' non trouvé. RSS vide généré.")
        fg.rss_file(output_file)
        return

    for filename in sorted(os.listdir(audio_folder), reverse=True):
        if not filename.endswith(".mp3"):
            continue

        # Extraire la date du nom de fichier
        date_obj = None

        # Format YYYYMMDD (nouveau)
        match = re.search(r"(\d{8})", filename)
        if match:
            try:
                date_obj = datetime.datetime.strptime(match.group(1), "%Y%m%d")
            except ValueError:
                pass

        # Format DD-MM-YYYY (ancien)
        if date_obj is None:
            match = re.search(r"(\d{2}-\d{2}-\d{4})", filename)
            if match:
                try:
                    date_obj = datetime.datetime.strptime(match.group(1), "%d-%m-%Y")
                except ValueError:
                    pass

        if date_obj is None:
            print(f"⚠️ Impossible de parser la date pour : {filename}")
            continue

        date_obj = date_obj.replace(tzinfo=datetime.timezone.utc)

        # Taille du fichier
        filepath = os.path.join(audio_folder, filename)
        file_size = os.path.getsize(filepath)

        # Ajouter l'épisode
        episode = fg.add_entry()
        episode.id(f"https://sarx613.github.io/Simon-FinTech/podcasts/{filename}")
        episode.title(f"Simon FinTech — Actu du {date_obj.strftime('%d %B %Y')}")
        episode.description("Épisode quotidien de Simon FinTech — Finance et tech décryptées.")
        episode.enclosure(
            url=f"https://sarx613.github.io/Simon-FinTech/podcasts/{filename}",
            length=str(file_size),
            type="audio/mpeg",
        )
        episode.pubDate(date_obj)

    fg.rss_file(output_file)
    print(f"✅ RSS mis à jour : {output_file}")


if __name__ == "__main__":
    generate_rss()
