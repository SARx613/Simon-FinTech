"""
Simon FinTech TTS — Hugging Face Space
Héberge Kyutai Pocket TTS (français) avec la voix clonée de Simon,
exposé en API pour GitHub Actions.

Prérequis côté Space :
  - Secret HF_TOKEN (token d'un compte ayant accepté les conditions
    de https://huggingface.co/kyutai/pocket-tts — requis pour le clonage)
  - Fichier voice_reference.wav uploadé à la racine du Space
"""

import os
import tempfile

import numpy as np
import scipy.io.wavfile
import gradio as gr
from pocket_tts import TTSModel

VOICE_REFERENCE = "voice_reference.wav"

print("Chargement du modèle Pocket TTS (français)…")
model = TTSModel.load_model(language="french_24l")

print(f"Clonage de la voix depuis {VOICE_REFERENCE}…")
voice_state = model.get_state_for_audio_prompt(VOICE_REFERENCE, truncate=True)
print("Voix prête.")

SAMPLE_RATE = getattr(model, "sample_rate", 24000)


def _split_text_into_chunks(text: str, max_chars: int = 500) -> list[str]:
    """Découpe le texte aux fins de phrases pour une synthèse stable."""
    sentences, current = [], ""
    for char in text:
        current += char
        if char in ".!?" and len(current) > 50:
            sentences.append(current.strip())
            current = ""
    if current.strip():
        sentences.append(current.strip())

    chunks, chunk = [], ""
    for sentence in sentences:
        if len(chunk) + len(sentence) > max_chars and chunk:
            chunks.append(chunk.strip())
            chunk = sentence
        else:
            chunk += " " + sentence if chunk else sentence
    if chunk.strip():
        chunks.append(chunk.strip())
    return chunks if chunks else [text]


def synthesize(text: str) -> str:
    """Synthétise le texte avec la voix clonée. Retourne le chemin d'un WAV."""
    if not text or not text.strip():
        raise gr.Error("Texte vide.")

    chunks = _split_text_into_chunks(text)
    parts = []
    for i, chunk in enumerate(chunks, 1):
        print(f"Synthèse {i}/{len(chunks)}…")
        audio = model.generate_audio(voice_state, chunk, copy_state=True)
        parts.append(audio.detach().cpu().numpy())

    full = np.concatenate(parts)
    out = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    scipy.io.wavfile.write(out.name, SAMPLE_RATE, full)
    return out.name


demo = gr.Interface(
    fn=synthesize,
    inputs=gr.Textbox(lines=12, label="Script du podcast"),
    outputs=gr.Audio(label="Audio généré", type="filepath"),
    title="Simon FinTech TTS",
    description="Synthèse vocale Kyutai avec la voix clonée de Simon. Utilisé en API par GitHub Actions.",
    flagging_mode="never",
)

demo.launch()
