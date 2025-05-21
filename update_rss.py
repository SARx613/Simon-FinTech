from feedgen.feed import FeedGenerator
import datetime
import os

def generate_rss(audio_folder="podcasts", output_file="rss.xml"):
    fg = FeedGenerator()
    fg.load_extension('podcast')

    fg.title("Simon FinTech")
    fg.link(href="https://sarx613.github.io/Simon-FinTech/", rel="alternate")
    fg.logo("https://sarx613.github.io/Simon-FinTech/logo-podcast.png")
    fg.image("https://sarx613.github.io/Simon-FinTech/logo-podcast.png")
    fg.description("Le podcast qui rend la finance et la tech simples, vivantes et passionnantes.")
    fg.language("fr")
    fg.link(href="https://sarx613.github.io/Simon-FinTech/rss.xml", rel="self")

    for filename in sorted(os.listdir(audio_folder)):
        if filename.endswith(".mp3"):
            date_str = filename.replace("podcast_", "").replace(".mp3", "")
            date_obj = datetime.datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=datetime.timezone.utc)

            episode = fg.add_entry()
            episode.id(f"https://sarx613.github.io/simon-fintech/podcasts/{filename}")
            episode.title(f"Simon FinTech – Actu du {date_obj.strftime('%d %B %Y')}")
            episode.description("Épisode quotidien de Simon FinTech.")
            episode.enclosure(
                url=f"https://sarx613.github.io/simon-fintech/podcasts/{filename}",
                length=0,
                type="audio/mpeg"
            )
            episode.pubDate(date_obj)

    fg.rss_file(output_file)
    print("✅ RSS mis à jour")

# Exemple d’utilisation
generate_rss()
