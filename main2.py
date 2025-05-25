import os
import datetime
import math
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

# 1. Charger les clés API
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
eleven_api_key = os.getenv("SERGE100_AUDIO")

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

# 5. Comparaison des scripts
if script_today != script_hier and script_today:
    # 6. Générer un titre avec GPT
    paragraphs = script_today.split("\n\n")
    print(p for p in paragraphs)
    first_actu = next((p for p in paragraphs if p.strip()), script_today[:300])

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

    # 7. Sauvegarder script avec titre
    import re
    safe_title = re.sub(r'[\\/*?:"<>|]', "", episode_title)
    os.makedirs("scripts", exist_ok=True)
    script_filename = f"scripts/{date_tag} - {safe_title}.txt"
    with open(script_filename, "w", encoding="utf-8") as f:
        f.write(script_today)
    print(f"📝 Script sauvegardé : {script_filename}")

    # 8. Découpage en parties
    def decouper_paragraphes(paragraphes, nb_parts=4):
        total = len(paragraphes)
        taille = math.ceil(total / nb_parts)
        return [paragraphes[i:i+taille] for i in range(0, total, taille)]

    blocs = decouper_paragraphes(paragraphs, nb_parts=4)
    os.makedirs("podcasts", exist_ok=True)
    print(b for b in blocs)

else:
    print("🟡 Aucun changement détecté dans le script. Aucun podcast généré.")
