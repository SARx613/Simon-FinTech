---
title: Simon FinTech TTS
emoji: 🎙️
colorFrom: green
colorTo: gray
sdk: gradio
sdk_version: "5.9.1"
app_file: app.py
pinned: false
---

# Simon FinTech TTS

Space privé qui héberge la synthèse vocale du podcast Simon FinTech :
Kyutai Pocket TTS (modèle français 24 couches) + clonage de la voix de Simon.

Appelé en API par le workflow GitHub Actions du dépôt
[Simon-FinTech](https://github.com/SARx613/Simon-FinTech).

## Déploiement (une seule fois)

1. Accepter les conditions du modèle : https://huggingface.co/kyutai/pocket-tts
2. Créer un Space **privé** (SDK : Gradio, hardware : CPU basic gratuit)
3. Uploader les 3 fichiers de ce dossier : `app.py`, `requirements.txt`, `README.md`
4. Uploader `voice_reference.wav` (l'échantillon de voix de Simon) à la racine
5. Dans Settings → Variables and secrets du Space, ajouter le secret
   `HF_TOKEN` = un token de ton compte (nécessaire pour télécharger le
   modèle gated de clonage)
6. Attendre le build (~5 min la première fois)
