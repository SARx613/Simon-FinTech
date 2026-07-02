"""
voice_synth.py — Synthèse vocale avec Kyutai Pocket TTS
Open source (MIT), tourne sur CPU Mac, supporte le clonage de voix zero-shot.
"""

import os
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Chemin vers le fichier audio de référence pour le clonage de voix
VOICE_REFERENCE_PATH = os.getenv("VOICE_REFERENCE", "voice_reference.wav")

# Voix par défaut si pas de fichier de référence
DEFAULT_VOICE = "alba"  # Voix française intégrée à Pocket TTS


def _convert_wav_to_mp3(wav_path: str, mp3_path: str) -> str:
    """
    Convertit un fichier WAV en MP3 via ffmpeg.
    Retourne le chemin du fichier MP3.
    """
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-qscale:a", "2", mp3_path],
            check=True,
            capture_output=True,
        )
        logger.info(f"Conversion WAV → MP3 : {mp3_path}")
        return mp3_path
    except FileNotFoundError:
        logger.warning("ffmpeg non trouvé. Tentative avec pydub...")
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_wav(wav_path)
            audio.export(mp3_path, format="mp3", bitrate="128k")
            logger.info(f"Conversion WAV → MP3 (pydub) : {mp3_path}")
            return mp3_path
        except ImportError:
            logger.error(
                "Impossible de convertir en MP3. Installe ffmpeg (`brew install ffmpeg`) "
                "ou pydub (`pip install pydub`)."
            )
            return wav_path


def _split_text_into_chunks(text: str, max_chars: int = 500) -> list[str]:
    """
    Découpe le texte en morceaux pour éviter les problèmes de mémoire
    sur les textes longs. Coupe aux fins de phrases.
    """
    sentences = []
    current = ""

    for char in text:
        current += char
        if char in ".!?" and len(current) > 50:
            sentences.append(current.strip())
            current = ""

    if current.strip():
        sentences.append(current.strip())

    # Regrouper les phrases en chunks
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += " " + sentence if current_chunk else sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks if chunks else [text]


def generate_podcast(
    script_text: str,
    output_path: str,
    voice_reference: str = None,
    output_format: str = "mp3",
) -> str:
    """
    Génère l'audio du podcast à partir du script texte.

    Args:
        script_text: Le texte du script podcast à synthétiser
        output_path: Chemin de sortie pour le fichier audio (sans extension)
        voice_reference: Chemin vers un fichier audio de référence pour le clonage
                         Si None, utilise VOICE_REFERENCE_PATH ou la voix par défaut
        output_format: "mp3" ou "wav"

    Returns:
        Chemin du fichier audio généré
    """
    import numpy as np

    try:
        from pocket_tts import TTSModel
    except ImportError:
        raise ImportError(
            "pocket-tts n'est pas installé. Installe-le avec : pip install pocket-tts"
        )

    # Déterminer le fichier de référence pour le clonage
    if voice_reference is None:
        voice_reference = VOICE_REFERENCE_PATH

    # Charger le modèle TTS
    logger.info("Chargement du modèle Pocket TTS...")
    tts_model = TTSModel.load_model()

    # Déterminer la voix à utiliser
    if os.path.exists(voice_reference):
        logger.info(f"Clonage de voix à partir de : {voice_reference}")
        voice = tts_model.get_state_for_audio_prompt(voice_reference)
    else:
        logger.info(f"Fichier de référence non trouvé ({voice_reference}). Utilisation de la voix '{DEFAULT_VOICE}'.")
        voice = DEFAULT_VOICE

    # Découper le texte en morceaux pour les textes longs
    chunks = _split_text_into_chunks(script_text, max_chars=500)
    logger.info(f"Texte découpé en {len(chunks)} morceaux")

    # Générer l'audio pour chaque morceau
    audio_parts = []
    for i, chunk in enumerate(chunks, 1):
        logger.info(f"Synthèse du morceau {i}/{len(chunks)} ({len(chunk)} chars)...")
        audio = tts_model.generate_audio(voice, chunk)
        audio_parts.append(audio.numpy())

    # Concaténer tous les morceaux audio
    import scipy.io.wavfile

    full_audio = np.concatenate(audio_parts)

    # Sauvegarder en WAV
    wav_path = output_path.rsplit(".", 1)[0] + ".wav" if "." in output_path else output_path + ".wav"
    os.makedirs(os.path.dirname(wav_path) or ".", exist_ok=True)
    scipy.io.wavfile.write(wav_path, tts_model.sample_rate, full_audio)
    logger.info(f"Audio WAV sauvegardé : {wav_path}")

    # Convertir en MP3 si demandé
    if output_format == "mp3":
        mp3_path = wav_path.replace(".wav", ".mp3")
        final_path = _convert_wav_to_mp3(wav_path, mp3_path)

        # Supprimer le WAV intermédiaire si la conversion a réussi
        if final_path.endswith(".mp3") and os.path.exists(wav_path):
            os.remove(wav_path)

        return final_path

    return wav_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    test_text = (
        "Bienvenue dans Simon FinTech, le podcast qui rend la finance et la tech "
        "simples, vivantes et surtout passionnantes. Aujourd'hui, on parle des dernières "
        "nouvelles du monde de la technologie et de la finance."
    )

    output = generate_podcast(
        script_text=test_text,
        output_path="test_podcast.mp3",
    )
    print(f"\n✅ Podcast de test généré : {output}")
