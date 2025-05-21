import os
import datetime
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

# 1. Charger les clés API depuis .env
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
eleven_api_key = os.getenv("ELEVENLABS_API_KEY")

# 2. Définir la date du jour automatiquement
today = datetime.date.today()
today_str = today.strftime("%d %B %Y")  # exemple : "20 mai 2025"
filename = f"podcasts/podcast_{today.strftime('%d-%m-%Y')}.mp3"

# 3. Initialiser OpenAI
client_openai = OpenAI(api_key=openai_api_key)

# 4. Prompt dynamique avec la date
prompt = f"""
Tu es le créateur éditorial du podcast Simon FinTech, un podcast animé par un étudiant de 20 ans qui décrypte l’actualité de la finance et de la technologie dans un ton dynamique, accessible et bienveillant.
À partir de 4 à 5 articles d’actualité récents datés du {today_str}, rédige un script complet de podcast prêt à être lu directement par une IA vocale.
Tu dois uniquement t’appuyer sur des articles issus de sources fiables et bien référencées, comme Bloomberg, Reuters, Financial Times, WSJ, CNBC, TechCrunch, Les Échos, BFM Business, Wired, The Economist, etc. Tu ne dois jamais mentionner le nom de ces sources dans le texte.
Le script doit faire entre 1000 et 1200 mots pour une lecture à voix haute d’environ 7 à 8 minutes.
Chaque sujet abordé doit inclure : un contexte clair, une explication structurée des faits, et une mini-analyse ou projection personnelle.
Le ton doit être naturel, fluide et parlé, sans titres ni structure visible, avec des transitions naturelles entre les sujets, et sans aucune mention de sources ou liens.
Commence toujours par : "Bienvenue dans Simon FinTech, le podcast qui rend la finance et la tech simples, vivantes et surtout passionnantes."
Termine systématiquement par : "À demain pour un nouveau point sur l’actu tech !"
"""

# 5. Appel API GPT
response = client_openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7,
    max_tokens=2000
)

script_text = response.choices[0].message.content.strip()

# 6. Initialiser le client ElevenLabs
client_elevenlabs = ElevenLabs(api_key=eleven_api_key)

# 7. Génération audio avec ElevenLabs
audio = client_elevenlabs.text_to_speech.convert(
    text= script_text[:200],
    voice_id="pNInz6obpgDQGcFmaJgB",  # Remplace par l'ID de la voix souhaitée
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_128"
)

os.makedirs("podcasts", exist_ok=True)
with open(filename, "wb") as f:
    for chunk in audio:
        f.write(chunk)

print(f"✅ Podcast généré et sauvegardé : {filename}")
