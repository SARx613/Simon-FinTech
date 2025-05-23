import os
import datetime
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

# 1. Charger les clés API
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
eleven_api_key = os.getenv("ELEVENLABS_API_KEY")

today = datetime.date.today()
today_str = today.strftime("%d %B %Y")
date_tag = today.strftime("%d-%m-%Y")

yesterday = today - datetime.timedelta(days=1)
yesterday_str = yesterday.strftime("%d %B %Y")

# 2. Initialiser OpenAI
client_openai = OpenAI(api_key=openai_api_key)

# 3. Prompt dynamique avec la date
script_prompt = f"""
Tu es le créateur éditorial du podcast Simon FinTech, un podcast animé par un étudiant de 20 ans qui décrypte l’actualité de la finance et de la technologie dans un ton dynamique, accessible et bienveillant.
À partir de 4 à 5 actualités marquantes du {yesterday_str}, rédige un script complet de podcast prêt à être lu directement par une IA vocale.
Tu dois uniquement t’appuyer sur des articles publiés le {yesterday_str}, issus de sources fiables et bien référencées comme Bloomberg, Reuters, Financial Times, WSJ, Forbes, CNBC, TechCrunch, Les Échos, BFM Business, Wired, The Economist, etc..
Le script doit faire entre 1000 et 1200 mots pour une lecture à voix haute d’environ 7 à 8 minutes.
Chaque sujet abordé doit inclure : un contexte clair, une explication structurée des faits, et une mini-analyse ou projection personnelle.
Le ton doit être naturel, fluide et parlé, sans titres ni structure visible, avec des transitions naturelles entre les sujets.
Commence toujours par : "Bienvenue dans Simon FinTech, le podcast qui rend la finance et la tech simples, vivantes et surtout passionnantes."
Termine systématiquement par : "À demain pour un nouveau point sur l’actu tech !"
"""

script_response = client_openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": script_prompt}],
    temperature=0.7,
    max_tokens=2000
)
script_text = script_response.choices[0].message.content.strip()

# 4. Extraire la première actualité du script
paragraphs = script_text.split("\n\n")
first_actu = paragraphs[1] if len(paragraphs) > 1 else script_text[:300]

# 5. Générer le titre basé sur la première actu uniquement
title_prompt = f"""
Voici le début d’un épisode de podcast sur la tech et la finance : 

{first_actu}

Donne-moi un titre accrocheur, percutant, original et court (max 15 mots), qui donne envie d’écouter cet épisode.
Ne mets pas la date. Pas de ponctuation superflue. Juste le titre.
"""

title_response = client_openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": title_prompt}],
    temperature=0.8,
    max_tokens=60
)
episode_title = title_response.choices[0].message.content.strip()
print(f"🎯 Titre généré : {episode_title}")

# 6. Sauvegarder le script texte
os.makedirs("scripts", exist_ok=True)
script_filename = f"scripts/{date_tag} - {episode_title}.txt"
with open(script_filename, "w", encoding="utf-8") as f:
    f.write(script_text)
print(f"📝 Script sauvegardé : {script_filename}")

# 7. Générer l'audio avec ElevenLabs
from elevenlabs.client import ElevenLabs
client_elevenlabs = ElevenLabs(api_key=eleven_api_key)

audio = client_elevenlabs.text_to_speech.convert(
    text=script_text,
    voice_id="pNInz6obpgDQGcFmaJgB",
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_128"
)

# 8. Sauvegarder l'audio
os.makedirs("podcasts", exist_ok=True)
audio_filename = f"podcasts/{date_tag} - {episode_title}.mp3"
with open(audio_filename, "wb") as f:
    for chunk in audio:
        f.write(chunk)

print(f"✅ Podcast généré et sauvegardé : {audio_filename}")
