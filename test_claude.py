"""
test_claude.py — Test de l'API Claude Anthropic pour Simon FinTech
Vérifie la clé API et génère une intro de podcast de test.

Lancement :
    python test_claude.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")


def test():
    print("=" * 60)
    print("🧠 Test de la configuration Claude Anthropic")
    print("=" * 60)

    if not API_KEY:
        print("❌ ERREUR : La variable ANTHROPIC_API_KEY n'est pas définie dans ton fichier .env.")
        print("   Ouvre le fichier .env et ajoute :")
        print("   ANTHROPIC_API_KEY=ta_clé_sk-ant-...")
        return 1

    masked_key = API_KEY[:10] + "..." + API_KEY[-4:] if len(API_KEY) > 14 else "***"
    print(f"🔑 Clé API détectée : {masked_key}")
    print(f"🤖 Modèle : {MODEL}")

    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=API_KEY)
        print("\n🔍 Envoi d'un prompt test à Claude...")

        resp = client.messages.create(
            model=MODEL,
            max_tokens=150,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": (
                    "Tu es Simon du podcast Simon FinTech. Écris une phrase d'intro ultra-punchy "
                    "en français pour saluer tes auditeurs aujourd'hui."
                ),
            }],
        )

        intro = resp.content[0].text.strip()
        print(f"\n✅ Réponse de Claude reçue avec succès :\n\n\"{intro}\"\n")
        print("🎉 Tout fonctionne pour la rédaction automatique des scripts.")
        return 0

    except Exception as e:
        print(f"\n❌ Erreur lors du test Claude Anthropic : {e}")
        return 1


if __name__ == "__main__":
    sys.exit(test())
