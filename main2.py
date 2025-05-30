import os
import datetime
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

    # 7. Sauvegarder le script avec le titre
    os.makedirs("scripts", exist_ok=True)
    script_filename = f"scripts/{date_tag} - {episode_title}.txt"
    with open(script_filename, "w", encoding="utf-8") as f:
        f.write(script_today)
    print(f"📝 Script sauvegardé : {script_filename}")

    # 8. Générer l'audio ligne par ligne
    voice_id = "6C8Cux23MlWRYPZwEh55"
    model_id = "eleven_flash_v2_5"
    output_dir = "temp_audio"
    os.makedirs(output_dir, exist_ok=True)

    audio_parts = []
    for i, line in enumerate(script_today.splitlines()):
        line = line.strip()
        if line:
            audio = client_elevenlabs.text_to_speech.convert(
                text=line,
                voice_id=voice_id,
                model_id=model_id,
                output_format="mp3_44100_128"
            )
            part_filename = os.path.join(output_dir, f"part_{i:03}.mp3")
            with open(part_filename, "wb") as f:
                for chunk in audio:
                    f.write(chunk)
            audio_parts.append(part_filename)
            print(f"🔊 Segment {i+1} généré.")

    # 9. Fusionner les fichiers audio (via pydub)
    from pydub import AudioSegment

    final_audio = AudioSegment.empty()
    for part in audio_parts:
        segment = AudioSegment.from_mp3(part)
        final_audio += segment

    os.makedirs("podcasts", exist_ok=True)
    audio_filename = f"podcasts/{date_tag} - {episode_title}.mp3"
    final_audio.export(audio_filename, format="mp3", bitrate="128k")
    print(f"✅ Podcast généré et sauvegardé : {audio_filename}")

    # 10. Mettre à jour le script d’hier
    with open("script_hier.txt", "w", encoding="utf-8") as f:
        f.write(script_today)
    print("📝 script_hier.txt mis à jour.")

else:
    print("🟡 Aucun changement détecté dans le script. Aucun podcast généré.")
