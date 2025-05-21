from datetime import datetime

title = "Épisode 1 : Pourquoi l'IA va changer la finance"
description = "Aujourd'hui, on explore le lien entre IA et marchés financiers."
pub_date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
git_page = "https://sarx613.github.io/Simon-FinTech/"
audio_url = "episode1.mp3"

def generate_rss(title, description, pub_date, audio_url):
    global git_page
    rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Simon FinTech</title>
  <link>{git_page + audio_url}</link>
  <description>Un podcast quotidien sur la finance et l'IA.</description>
  <language>fr-fr</language>
  <lastBuildDate>{pub_date}</lastBuildDate>

  <item>
    <title>{title}</title>
    <description>{description}</description>
    <pubDate>{pub_date}</pubDate>
    <enclosure url="{audio_url}" length="12345678" type="audio/mpeg"/>
    <guid>{audio_url}</guid>
  </item>
</channel>
</rss>'''

    with open("podcast.xml", "w", encoding="utf-8") as f:
        f.write(rss)
    print("✅ Fichier RSS généré !")

generate_rss(title, description, pub_date, audio_url)
