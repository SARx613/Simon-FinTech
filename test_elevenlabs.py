"""
test_elevenlabs.py — Script de diagnostic et test ElevenLabs
Vérifie la clé API, la voix configurée, et génère un extrait audio de 5 secondes.

Lancement :
    python test_elevenlabs.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "ZfzastaCQOj8iuzFZuWy")
MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
API_KEY = os.getenv("ELEVENLABS_API_KEY")


def test():
    print("=" * 60)
    print("🧪 Test de la configuration ElevenLabs pour Simon FinTech")
    print("=" * 60)

    if not API_KEY:
        print("❌ ERREUR : La variable ELEVENLABS_API_KEY n'est pas définie dans ton fichier .env.")
        print("   Ouvre le fichier .env et ajoute :")
        print("   ELEVENLABS_API_KEY=ta_clé_ici")
        print("   ELEVENLABS_VOICE_ID=" + VOICE_ID)
        return 1

    masked_key = API_KEY[:6] + "..." + API_KEY[-4:] if len(API_KEY) > 10 else "***"
    print(f"🔑 Clé API détectée : {masked_key}")
    print(f"🎙️ Voice ID : {VOICE_ID}")
    print(f"🧠 Modèle : {MODEL_ID}")

    try:
        from elevenlabs.client import ElevenLabs

        client = ElevenLabs(api_key=API_KEY)
        print("\n🔍 Vérification du compte et des voix...")

        # Lister les voix pour vérifier la validité de la clé
        voices = client.voices.get_all()
        voice_names = {v.voice_id: v.name for v in voices.voices}
        print(f"✅ Connexion réussie ! {len(voice_names)} voix trouvée(s) sur ton compte.")

        if VOICE_ID in voice_names:
            print(f"🎯 Voix ciblée confirmée : '{voice_names[VOICE_ID]}' (ID: {VOICE_ID})")
        else:
            print(f"ℹ️ Note : La voix {VOICE_ID} n'est pas listée dans les voix de base (peut être une voix partagée ou clonée spécifique).")

        print("\n🔊 Génération d'un court extrait audio de test (5 secondes)...")
        test_phrase = (
            "Salut c'est Simon, bienvenue dans Simon FinTech. "
            "La nouvelle voix ElevenLabs est opérationnelle !"
        )

        audio = client.text_to_speech.convert(
            text=test_phrase,
            voice_id=VOICE_ID,
            model_id=MODEL_ID,
            output_format="mp3_44100_128",
        )

        test_file = "test_voice.mp3"
        with open(test_file, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        file_size = os.path.getsize(test_file)
        print(f"✅ Extrait audio généré avec succès dans '{test_file}' ({file_size} octets) !")
        print("🎉 Tout est prêt pour la génération des épisodes complets.")
        return 0

    except Exception as e:
        print(f"\n❌ Erreur lors du test ElevenLabs : {e}")
        return 1


if __name__ == "__main__":
    sys.exit(test())

