"""
script_generator.py — Génération du script podcast via LLM gratuit
Utilise Groq (API gratuite) avec Llama 3 ou Mistral, compatible OpenAI.
Peut aussi fonctionner avec Gemini ou Ollama.
"""

import os
import datetime
import logging
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

# Configuration du provider LLM
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")  # "groq", "gemini", "ollama", "openai"

LLM_CONFIGS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "model": "llama-3.3-70b-versatile",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "api_key_env": None,  # Pas de clé pour Ollama
        "model": "mistral",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "model": "gpt-4o",
    },
}

PODCAST_PROMPT_TEMPLATE = """
Tu es le créateur éditorial du podcast Simon FinTech, un podcast animé par un étudiant de 20 ans qui décrypte l'actualité de la finance et de la technologie dans un ton dynamique, accessible et bienveillant. 

À partir de plusieurs actualités marquantes d'aujourd'hui, rédige un script complet de podcast prêt à être lu directement par une IA vocale. Tu dois uniquement t'appuyer sur des articles publiés aujourd'hui (fournis ci-dessous), issus de sources fiables et bien référencées. 

Le script doit faire entre 600 et 700 mots pour une lecture à voix haute d'environ 5 minutes. Chaque sujet abordé doit inclure : un contexte clair, une explication structurée des faits, et une mini-analyse ou projection personnelle. Le ton doit être naturel, fluide et parlé, sans titres ni structure visible, avec des transitions naturelles entre les sujets. 

Commence toujours par une amorce contenant une question pour mettre en bouche la première actualité puis enchaine avec : "Salut c'est Simon, bienvenue dans le podcast qui rend la finance et la tech simples et surtout passionnantes." 
Termine systématiquement par : "À demain pour un nouveau point sur l'actu tech !"

IMPORTANT : Base-toi UNIQUEMENT sur les articles fournis ci-dessous. N'invente aucune information. Ne mentionne pas de sources dans le texte lu.

Voici les articles d'actualité du jour :
{articles_text}
"""


def _format_articles_for_prompt(articles: list[dict]) -> str:
    """Formate la liste d'articles en texte pour le prompt."""
    parts = []
    for i, art in enumerate(articles, 1):
        # Tronquer le texte à ~1500 caractères pour rester dans les limites de tokens
        text = art["text"][:1500]
        parts.append(f"--- Article {i} ---\nTitre : {art['title']}\n\n{text}\n")
    return "\n".join(parts)


def _get_llm_client() -> tuple[OpenAI, str]:
    """Initialise et retourne le client LLM selon la configuration."""
    config = LLM_CONFIGS.get(LLM_PROVIDER)
    if not config:
        raise ValueError(f"Provider LLM inconnu : {LLM_PROVIDER}. Choix : {list(LLM_CONFIGS.keys())}")

    api_key = "ollama"  # Valeur par défaut pour Ollama
    if config["api_key_env"]:
        api_key = os.getenv(config["api_key_env"])
        if not api_key:
            raise ValueError(
                f"Clé API manquante : {config['api_key_env']}. "
                f"Ajoute-la dans ton fichier .env"
            )

    client = OpenAI(
        api_key=api_key,
        base_url=config["base_url"],
    )

    return client, config["model"]


def generate_script(articles: list[dict], date: datetime.date = None) -> str:
    """
    Génère un script de podcast à partir des articles collectés.

    Args:
        articles: Liste de dictionnaires avec les clés title, text, url
        date: Date du podcast (défaut: aujourd'hui)

    Returns:
        Script du podcast (texte brut, prêt pour le TTS)
    """
    if not articles:
        raise ValueError("Aucun article fourni pour générer le script.")

    if date is None:
        date = datetime.date.today()

    # Formatter la date en français
    import locale
    try:
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, "fr_FR")
        except locale.Error:
            pass  # On garde le format par défaut

    date_str = date.strftime("%d %B %Y")

    # Construire le prompt
    articles_text = _format_articles_for_prompt(articles)
    prompt = PODCAST_PROMPT_TEMPLATE.format(
        date=date_str,
        articles_text=articles_text,
    )

    # Appel au LLM
    logger.info(f"Génération du script avec {LLM_PROVIDER} (modèle: {LLM_CONFIGS[LLM_PROVIDER]['model']})")

    client, model = _get_llm_client()

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2500,
    )

    script = response.choices[0].message.content.strip()

    # Validation basique
    word_count = len(script.split())
    logger.info(f"Script généré : {word_count} mots")

    if word_count < 500:
        logger.warning(f"Script anormalement court ({word_count} mots). Vérifier la qualité.")
    elif word_count > 1500:
        logger.warning(f"Script anormalement long ({word_count} mots). Possible dépassement.")

    return script


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Test avec des articles factices
    test_articles = [
        {
            "title": "Apple présente son nouveau casque de réalité mixte",
            "text": "Apple a dévoilé aujourd'hui son nouveau casque de réalité mixte lors de sa keynote annuelle. "
                    "Le produit, qui sera commercialisé à 3499 dollars, intègre des capteurs de pointe et un "
                    "processeur M4 Ultra. Les analystes s'interrogent sur l'adoption par le grand public.",
            "url": "https://example.com/apple",
        },
        {
            "title": "La BCE maintient ses taux directeurs inchangés",
            "text": "La Banque centrale européenne a décidé de maintenir ses taux d'intérêt inchangés lors de "
                    "sa dernière réunion. Christine Lagarde a souligné que l'inflation reste sous contrôle "
                    "mais que la croissance économique ralentit dans la zone euro.",
            "url": "https://example.com/bce",
        },
    ]

    script = generate_script(test_articles)
    print("\n" + "=" * 80)
    print("SCRIPT GÉNÉRÉ :")
    print("=" * 80)
    print(script)
