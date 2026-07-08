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
Tu es Simon, 20 ans, l'animateur du podcast quotidien "Simon FinTech". Tu décryptes l'actu finance et tech avec une énergie contagieuse : tu es vif, curieux, un peu insolent, tu as des convictions et tu n'as pas peur de les partager. Ton style rappelle les meilleurs vulgarisateurs : clair, rythmé, avec des punchlines, des images parlantes, des questions qui accrochent. Tu parles à un ami intelligent, pas à un amphi.

Rédige le script COMPLET de l'épisode du jour, prêt à être lu tel quel par une voix de synthèse (donc uniquement le texte à dire, aucune indication scénique).

═══ LE TON (le plus important) ═══
- De la PÊCHE : phrases qui claquent, verbes forts, rythme vivant. Alterne phrases courtes percutantes et phrases plus amples.
- Rends chaque sujet CAPTIVANT : pourquoi ça compte pour l'auditeur ? qu'est-ce que ça change concrètement ? Trouve l'angle qui intrigue.
- Prends position. Donne ton avis franc ("moi je pense que…", "soyons clairs…", "et là, ça devient intéressant…").
- Zéro langue de bois, zéro remplissage, zéro formule scolaire type "tout d'abord / ensuite / en conclusion". Raconte, ne liste pas.
- Utilise des images, des comparaisons, une pointe d'humour quand c'est pertinent.

═══ LE FORMAT ═══
- Longueur IMPÉRATIVE : entre 1200 et 1400 mots (6-7 min de lecture). Ne raccourcis pas.
- Traite 4 à 5 sujets. Pour chacun : accroche qui donne envie → les faits clés avec les vrais chiffres et acteurs → ton analyse/projection. Développe, ne survole jamais.
- Transitions fluides et malignes entre les sujets (un fil rouge, un clin d'œil, une bascule d'idée) — jamais "passons au sujet suivant".
- Priorise les sujets les plus marquants et récents (marchés, IA, crypto, grandes boîtes tech, deals, régulation).

═══ CADRE OBLIGATOIRE ═══
- Commence par une accroche forte (une question ou une phrase choc liée à la première actu), puis ENCHAÎNE avec, mot pour mot : "Salut c'est Simon, bienvenue dans le podcast qui rend la finance et la tech simples et surtout passionnantes."
- Termine EXACTEMENT par : "À demain pour un nouveau point sur l'actu tech !"

═══ FIABILITÉ (non négociable) ═══
- Base-toi EXCLUSIVEMENT sur les articles fournis. C'est ta seule source de vérité.
- N'invente JAMAIS un chiffre, un nom, un montant, une citation ou un événement absent des articles. Dans le doute, reste général plutôt que d'inventer.
- Les articles peuvent être en anglais : traduis et reformule naturellement en français.
- Ne cite aucun média ni source dans le texte lu. Tes avis sont clairement des opinions, pas des faits.

Voici les articles d'actualité du jour (ta seule source autorisée) :
{articles_text}
"""


def _format_articles_for_prompt(articles: list[dict]) -> str:
    """Formate la liste d'articles en texte pour le prompt."""
    parts = []
    for i, art in enumerate(articles, 1):
        # Tronquer le texte à ~2500 caractères : assez de matière pour un script long,
        # tout en restant confortablement dans la fenêtre de contexte de Llama 3.3.
        text = art["text"][:2500]
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

    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=3500,  # marge confortable pour un script de ~1400 mots
    )
    script = response.choices[0].message.content.strip()
    word_count = len(script.split())
    logger.info(f"Script généré : {word_count} mots")

    # Relance automatique si le script est trop court pour un épisode 6-7 min.
    # Le LLM a tendance à sous-livrer : on lui demande d'étoffer sa propre réponse.
    TARGET_MIN = 1100
    if word_count < TARGET_MIN:
        logger.info(f"Script trop court ({word_count} mots < {TARGET_MIN}). Relance pour étoffer…")
        messages.append({"role": "assistant", "content": script})
        messages.append({
            "role": "user",
            "content": (
                f"Ce script ne fait que {word_count} mots, c'est trop court. "
                f"Réécris-le COMPLÈTEMENT en visant 1200 à 1400 mots : développe davantage "
                f"chaque sujet (plus de contexte, plus de détails chiffrés, une vraie analyse "
                f"personnelle), sans inventer d'information absente des articles. "
                f"Garde la même intro et la même conclusion. Renvoie uniquement le script final."
            ),
        })
        retry = client.chat.completions.create(
            model=model, messages=messages, temperature=0.7, max_tokens=3500,
        )
        retry_script = retry.choices[0].message.content.strip()
        retry_words = len(retry_script.split())
        logger.info(f"Script étoffé : {retry_words} mots")
        # On garde la version la plus longue des deux
        if retry_words > word_count:
            script, word_count = retry_script, retry_words

    if word_count < 800:
        logger.warning(f"Script encore court ({word_count} mots) malgré la relance.")
    elif word_count > 1600:
        logger.warning(f"Script très long ({word_count} mots). Épisode possiblement > 8 min.")

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
