import os
import datetime
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
import math
import re
from pydub import AudioSegment

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
    first_actu = paragraphs[1] if len(paragraphs) > 1 else script_today[:300]

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
    os.makedirs("scripts", exist_ok=True)
    script_filename = f"scripts/{date_tag} - {episode_title}.txt"
    print(f"📝 Script sauvegardé : {script_filename}")

    # 8. Générer l'audio
    # 8. Diviser en blocs (1 paragraphe = 1 bloc)
    blocs = [p.strip() for p in paragraphs if p.strip()]
    os.makedirs("podcasts", exist_ok=True)
    morceaux_paths = []

    for idx, bloc in enumerate(blocs, start=1):
        try:
            audio = generate(
                text=bloc,
                voice="OPCL81coXM3AEo8gUxHM",  # Ta voix personnalisée
                model="eleven_multilingual_v2",
                api_key=eleven_api_key
            )
            morceau_path = f"podcasts/tmp_{idx}.mp3"
            save(audio, morceau_path)
            morceaux_paths.append(morceau_path)
            print(f"✅ Audio {idx} généré.")
        except Exception as e:
            print(f"❌ Erreur génération audio {idx} : {e}")

    # 9. Fusionner tous les morceaux
    try:
        podcast_final = AudioSegment.empty()
        for morceau in morceaux_paths:
            segment = AudioSegment.from_mp3(morceau)
            podcast_final += segment
        final_path = f"podcasts/{date_tag} - {safe_title}.mp3"
        podcast_final.export(final_path, format="mp3")
        print(f"🎧 Podcast final exporté : {final_path}")
    except Exception as e:
        print(f"❌ Erreur fusion audio : {e}")

    # 10. Nettoyer fichiers intermédiaires
    for morceau in morceaux_paths:
        os.remove(morceau)


    # 9. Sauvegarder le fichier audio
    os.makedirs("podcasts", exist_ok=True)
    audio_filename = f"podcasts/{date_tag} - {episode_title}.mp3"
    with open(audio_filename, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    print(f"✅ Podcast généré et sauvegardé : {audio_filename}")

    # 10. Mettre à jour le script d’hier
    with open("script_hier.txt", "w", encoding="utf-8") as f:
        f.write(script_today)
    print("📝 script_hier.txt mis à jour.")

else:
    print("🟡 Aucun changement détecté dans le script. Aucun podcast généré.")
