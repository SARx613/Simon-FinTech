from feedgen.feed import FeedGenerator
import datetime
import os
import shutil
import re

def generate_rss(audio_folder="podcasts", output_file="rss.xml"):
    fg = FeedGenerator()
    fg.load_extension('podcast')

    fg.title("Simon FinTech")
    fg.link(href="https://sarx613.github.io/Simon-FinTech/", rel="alternate")
    fg.logo("https://sarx613.github.io/Simon-FinTech/logo-podcast.png")
    fg.image("https://sarx613.github.io/Simon-FinTech/logo-podcast.png")
    fg.description("Le podcast qui rend la finance et la tech simples, vivantes et passionnantes.")
    fg.language("fr")
    fg.author({'name': 'Simon FinTech', 'email': 'simon5.amar@gmail.com'})
    fg.podcast.itunes_author("Simon FinTech")
    fg.podcast.itunes_explicit("no")
    fg.link(href="https://sarx613.github.io/Simon-FinTech/rss.xml", rel="self")

    # Regex pour détecter les fichiers avec nom commençant par dd-mm-YYYY
    pattern = re.compile(r"^\d{2}-\d{2}-\d{4} - .*\.mp3$")

    for filename in sorted(os.listdir(audio_folder)):
        if filename.endswith(".mp3") and pattern.match(filename):
            base = filename.replace(".mp3", "")
            date_part, title_part = base.split(" - ", 1)

            try:
                date_obj = datetime.datetime.strptime(date_part.strip(), "%d-%m-%Y").replace(tzinfo=datetime.timezone.utc)

                entry = fg.add_entry()
                entry.id(f"https://sarx613.github.io/Simon-FinTech/podcasts/{filename}")
                entry.title(title_part.strip())
                entry.description("Épisode quotidien de Simon FinTech.")
                entry.enclosure(
                    url=f"https://sarx613.github.io/Simon-FinTech/podcasts/{filename}",
                    length=0,
                    type="audio/mpeg"
                )
                entry.pubDate(date_obj)
            except ValueError:
                print(f"❌ Erreur de date dans le fichier : {filename}")

    fg.rss_file(output_file)

    # Sauvegarde historique du RSS
    today = datetime.date.today()
    os.makedirs("rss_history", exist_ok=True)
    backup_name = f"rss_history/rss_{today.strftime('%d-%m-%Y')}.xml"
    shutil.copyfile(output_file, backup_name)

    print("✅ RSS mis à jour")
    print(f"🗂️ RSS sauvegardé dans : {backup_name}")

# Exécution
generate_rss()
