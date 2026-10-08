"""
voice_synth.py — Synthèse vocale 100 % gratuite pour Simon FinTech

Moteur principal : Edge-TTS (voix neuronales Microsoft, gratuit, sans quota,
sans clé API — parfait pour GitHub Actions).
Fallback optionnel : Kyutai Pocket TTS (local, clonage de voix) si tu préfères
utiliser ta propre voix.

Choix du moteur via la variable d'environnement TTS_ENGINE ("edge" par défaut).
"""

import os
import asyncio
import logging

logger = logging.getLogger(__name__)

# Moteur TTS : "elevenlabs" (défaut), "edge", "kyutai" (local), ou "hf" (cloud)
TTS_ENGINE = os.getenv("TTS_ENGINE", "elevenlabs")

# --- Options ElevenLabs ---
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "ZfzastaCQOj8iuzFZuWy")
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")

# Voix Edge-TTS française (fallback ou alternative sans coût).
#   fr-FR-DeniseNeural  (femme, chaleureuse)
#   fr-FR-HenriNeural   (homme, posé)
#   fr-FR-RemyMultilingualNeural (homme, moderne)
EDGE_VOICE = os.getenv("EDGE_VOICE", "fr-FR-HenriNeural")

# Débit / hauteur. "+0%" = débit naturel posé (recommandé pour un rendu qualitatif).
EDGE_RATE = os.getenv("EDGE_RATE", "+0%")
EDGE_PITCH = os.getenv("EDGE_PITCH", "+0Hz")

# --- Options Kyutai (clonage de voix, local) ---
VOICE_REFERENCE_PATH = os.getenv("VOICE_REFERENCE", "voice_reference.wav")
DEFAULT_KYUTAI_VOICE = "estelle"  # voix française intégrée à Pocket TTS

# --- Options Hugging Face Space (clonage de voix, cloud) ---
# Space privé hébergeant Kyutai + la voix clonée (voir dossier hf_space/).
HF_SPACE_ID = os.getenv("HF_SPACE_ID", "")   # ex : "simon5amar/simon-fintech-tts"
HF_TOKEN = os.getenv("HF_TOKEN", "")


# ─────────────────────────────────────────────────────────────────────────────
# Moteur 1 : ElevenLabs (Voix clonée ou premium, haute qualité)
# ─────────────────────────────────────────────────────────────────────────────
def _chunk_text_for_elevenlabs(text: str, max_chars: int = 4000) -> list[str]:
    """Découpe un script en blocs respectant la limite de caractères d'ElevenLabs."""
    if len(text) <= max_chars:
        return [text]

    import re
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_len = 0

    for p in paragraphs:
        p_clean = p.strip()
        if not p_clean:
            continue

        if len(p_clean) > max_chars:
            sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', p_clean) if s.strip()]
            for s in sentences:
                if current_len + len(s) + 1 > max_chars and current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = [s]
                    current_len = len(s)
                else:
                    current_chunk.append(s)
                    current_len += len(s) + 1
        elif current_len + len(p_clean) + 2 > max_chars and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [p_clean]
            current_len = len(p_clean)
        else:
            current_chunk.append(p_clean)
            current_len += len(p_clean) + 2

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def _generate_with_elevenlabs(
    script_text: str,
    mp3_path: str,
    voice_id: str = None,
    model_id: str = None,
) -> str:
    """Synthétise le script via l'API ElevenLabs avec découpage automatique si nécessaire."""
    try:
        from elevenlabs.client import ElevenLabs
    except ImportError:
        raise ImportError(
            "elevenlabs n'est pas installé. Installe-le avec : pip install elevenlabs"
        )

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError(
            "Clé API manquante : ELEVENLABS_API_KEY. "
            "Ajoute-la dans ton fichier .env ou dans les Secrets GitHub."
        )

    voice = voice_id or os.getenv("ELEVENLABS_VOICE_ID", ELEVENLABS_VOICE_ID)
    model = model_id or os.getenv("ELEVENLABS_MODEL_ID", ELEVENLABS_MODEL_ID)

    logger.info(f"Synthèse vocale via ElevenLabs (Voix : {voice}, Modèle : {model})…")
    client = ElevenLabs(api_key=api_key)

    chunks = _chunk_text_for_elevenlabs(script_text, max_chars=4000)
    logger.info(f"Texte découpé en {len(chunks)} bloc(s) pour ElevenLabs.")

    os.makedirs(os.path.dirname(mp3_path) or ".", exist_ok=True)

    if len(chunks) == 1:
        audio = client.text_to_speech.convert(
            text=chunks[0],
            voice_id=voice,
            model_id=model,
            output_format="mp3_44100_128",
        )
        with open(mp3_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
    else:
        import tempfile
        temp_files = []
        try:
            for idx, chunk_text in enumerate(chunks, 1):
                logger.info(f"Génération bloc {idx}/{len(chunks)} ElevenLabs…")
                audio = client.text_to_speech.convert(
                    text=chunk_text,
                    voice_id=voice,
                    model_id=model,
                    output_format="mp3_44100_128",
                )
                tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                for chunk in audio:
                    tmp.write(chunk)
                tmp.close()
                temp_files.append(tmp.name)

            try:
                from pydub import AudioSegment
                combined = AudioSegment.empty()
                for tf in temp_files:
                    combined += AudioSegment.from_mp3(tf)
                combined.export(mp3_path, format="mp3", bitrate="128k")
            except Exception as e:
                logger.warning(f"Assemblage via pydub non disponible ({e}), concaténation directe.")
                with open(mp3_path, "wb") as outfile:
                    for tf in temp_files:
                        with open(tf, "rb") as infile:
                            outfile.write(infile.read())
        finally:
            for tf in temp_files:
                if os.path.exists(tf):
                    try:
                        os.remove(tf)
                    except OSError:
                        pass

    logger.info(f"Audio ElevenLabs généré avec succès : {mp3_path}")
    return mp3_path


# ─────────────────────────────────────────────────────────────────────────────
# Moteur 2 : Edge-TTS (gratuit, sans quota)
# ─────────────────────────────────────────────────────────────────────────────
async def _edge_tts_to_mp3(script_text: str, mp3_path: str) -> str:
    """Synthétise le texte en MP3 via Edge-TTS (asynchrone)."""
    import edge_tts

    communicate = edge_tts.Communicate(
        text=script_text,
        voice=EDGE_VOICE,
        rate=EDGE_RATE,
        pitch=EDGE_PITCH,
    )
    await communicate.save(mp3_path)
    return mp3_path


def _generate_with_edge(script_text: str, mp3_path: str) -> str:
    """Wrapper synchrone autour d'Edge-TTS."""
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        raise ImportError(
            "edge-tts n'est pas installé. Installe-le avec : pip install edge-tts"
        )

    logger.info(f"Synthèse vocale via Edge-TTS (voix : {EDGE_VOICE})…")
    os.makedirs(os.path.dirname(mp3_path) or ".", exist_ok=True)

    # Edge-TTS est asynchrone : on l'exécute proprement selon le contexte.
    try:
        asyncio.run(_edge_tts_to_mp3(script_text, mp3_path))
    except RuntimeError:
        # Cas où une boucle événementielle tourne déjà (ex. Jupyter)
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_edge_tts_to_mp3(script_text, mp3_path))
        finally:
            loop.close()

    logger.info(f"Audio généré : {mp3_path}")
    return mp3_path


# ─────────────────────────────────────────────────────────────────────────────
# Moteur 2 : Kyutai Pocket TTS (local, clonage de voix) — optionnel
# ─────────────────────────────────────────────────────────────────────────────
def _convert_wav_to_mp3(wav_path: str, mp3_path: str) -> str:
    """Convertit un WAV en MP3 via ffmpeg, avec fallback pydub."""
    import subprocess

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-qscale:a", "2", mp3_path],
            check=True,
            capture_output=True,
        )
        logger.info(f"Conversion WAV → MP3 : {mp3_path}")
        return mp3_path
    except FileNotFoundError:
        logger.warning("ffmpeg non trouvé. Tentative avec pydub…")
        from pydub import AudioSegment

        AudioSegment.from_wav(wav_path).export(mp3_path, format="mp3", bitrate="128k")
        return mp3_path


def _split_text_into_chunks(text: str, max_chars: int = 500) -> list[str]:
    """Découpe le texte en morceaux aux fins de phrases (pour Kyutai)."""
    sentences, current = [], ""
    for char in text:
        current += char
        if char in ".!?" and len(current) > 50:
            sentences.append(current.strip())
            current = ""
    if current.strip():
        sentences.append(current.strip())

    chunks, current_chunk = [], ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += " " + sentence if current_chunk else sentence
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks if chunks else [text]


def _generate_with_kyutai(script_text: str, mp3_path: str, voice_reference: str = None) -> str:
    """Synthèse via Kyutai Pocket TTS (local, supporte le clonage de voix)."""
    import numpy as np
    import scipy.io.wavfile

    try:
        from pocket_tts import TTSModel
    except ImportError:
        raise ImportError(
            "pocket-tts n'est pas installé. Installe-le avec : pip install pocket-tts"
        )

    if voice_reference is None:
        voice_reference = VOICE_REFERENCE_PATH

    # Le français n'existe qu'en modèle 24 couches.
    logger.info("Chargement du modèle Pocket TTS (français)…")
    tts_model = TTSModel.load_model(language="french_24l")

    # Construire l'état de voix (toujours un dict).
    if os.path.exists(voice_reference):
        # Clonage de TA voix à partir du fichier de référence.
        logger.info(f"Clonage de voix à partir de : {voice_reference}")
        voice = tts_model.get_state_for_audio_prompt(voice_reference, truncate=True)
    else:
        # Voix française intégrée par défaut (ex. "estelle").
        logger.info(f"Référence absente ({voice_reference}). Voix intégrée '{DEFAULT_KYUTAI_VOICE}'.")
        voice = tts_model._cached_get_state_for_audio_prompt(DEFAULT_KYUTAI_VOICE)

    chunks = _split_text_into_chunks(script_text, max_chars=500)
    logger.info(f"Texte découpé en {len(chunks)} morceaux")

    audio_parts = []
    for i, chunk in enumerate(chunks, 1):
        logger.info(f"Synthèse du morceau {i}/{len(chunks)}…")
        # copy_state=True : chaque morceau repart de l'état de voix propre.
        audio = tts_model.generate_audio(voice, chunk, copy_state=True)
        audio_parts.append(audio.detach().cpu().numpy())

    # Fréquence d'échantillonnage du modèle (24 kHz pour Kyutai).
    sample_rate = getattr(tts_model, "sample_rate", 24000)
    wav_path = mp3_path.rsplit(".", 1)[0] + ".wav"
    os.makedirs(os.path.dirname(wav_path) or ".", exist_ok=True)
    scipy.io.wavfile.write(wav_path, sample_rate, np.concatenate(audio_parts))

    _convert_wav_to_mp3(wav_path, mp3_path)
    if os.path.exists(wav_path):
        os.remove(wav_path)
    return mp3_path


# ─────────────────────────────────────────────────────────────────────────────
# Moteur 3 : Hugging Face Space (ta voix clonée, appelée en API depuis le cloud)
# ─────────────────────────────────────────────────────────────────────────────
def _generate_with_hf_space(script_text: str, mp3_path: str) -> str:
    """
    Appelle le Space HF privé (dossier hf_space/) qui héberge Kyutai + la voix
    clonée de Simon. Le Space renvoie un WAV, converti ici en MP3.
    """
    try:
        from gradio_client import Client
    except ImportError:
        raise ImportError(
            "gradio-client n'est pas installé. Installe-le avec : pip install gradio-client"
        )

    if not HF_SPACE_ID:
        raise ValueError("HF_SPACE_ID manquant (ex: 'simon5amar/simon-fintech-tts').")
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN manquant (token Hugging Face, le Space est privé).")

    logger.info(f"Synthèse via le Space HF : {HF_SPACE_ID} (peut prendre plusieurs minutes)…")
    client = Client(HF_SPACE_ID, hf_token=HF_TOKEN)
    wav_path = client.predict(script_text, api_name="/predict")

    os.makedirs(os.path.dirname(mp3_path) or ".", exist_ok=True)
    _convert_wav_to_mp3(wav_path, mp3_path)
    logger.info(f"Audio généré : {mp3_path}")
    return mp3_path


# ─────────────────────────────────────────────────────────────────────────────
# Point d'entrée public
# ─────────────────────────────────────────────────────────────────────────────
def generate_podcast(script_text: str, output_path: str, voice_reference: str = None) -> str:
    """
    Génère l'audio MP3 du podcast à partir du script texte.

    Args:
        script_text: Le texte du script à synthétiser.
        output_path: Chemin de sortie du fichier .mp3.
        voice_reference: (Kyutai uniquement) fichier audio de référence pour le clonage.

    Returns:
        Le chemin du fichier MP3 généré.
    """
    if not script_text or not script_text.strip():
        raise ValueError("Script vide : rien à synthétiser.")

    # Garantir l'extension .mp3
    mp3_path = output_path if output_path.endswith(".mp3") else output_path + ".mp3"

    if TTS_ENGINE == "elevenlabs":
        return _generate_with_elevenlabs(script_text, mp3_path)
    elif TTS_ENGINE == "edge":
        return _generate_with_edge(script_text, mp3_path)
    elif TTS_ENGINE == "kyutai":
        return _generate_with_kyutai(script_text, mp3_path, voice_reference)
    elif TTS_ENGINE == "hf":
        return _generate_with_hf_space(script_text, mp3_path)
    else:
        raise ValueError(f"Moteur TTS inconnu : {TTS_ENGINE}. Choix : 'elevenlabs', 'edge', 'kyutai' ou 'hf'.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    test_text = (
        "Salut c'est Simon, bienvenue dans le podcast qui rend la finance et la tech "
        "simples et surtout passionnantes. Ceci est un test de la voix gratuite."
    )
    output = generate_podcast(test_text, "test_podcast.mp3")
    print(f"\n✅ Podcast de test généré : {output}")
