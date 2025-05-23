import os
import datetime
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

# 1. Charger les clés API
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
eleven_api_key = os.getenv("ELEVENLABS_API_KEY")

# 2. Initialiser les clients API
client_openai = OpenAI(api_key=openai_api_key)
client_elevenlabs = ElevenLabs(api_key=eleven_api_key)

# 3. Dates
today = datetime.date.today()
date_tag = today.strftime("%d-%m-%Y")

# 4. Lire les scripts
def lire_script(fichier):
    if os.path.exists(fichier):
        with open(fichier, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

script_today = lire_script("script_today.txt")
script_hier = lire_script("script_hier.txt")
print(script_today)
print("_______________")
print(script_hier)
