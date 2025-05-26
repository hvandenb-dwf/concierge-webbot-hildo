# app/tts.py

import os
import tempfile
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings
from app.cloudinary_util import upload_audio_to_cloudinary


def text_to_speech(text: str) -> str:
    try:
        # Voice configuratie (bijv. Ruth)
        voice = Voice(
            voice_id=os.getenv("ELEVEN_VOICE_ID"),  # Zorg dat deze in je Render env staat
            settings=VoiceSettings(stability=0.5, similarity_boost=0.8)
        )

        # ElevenLabs client
        client = ElevenLabs(
            api_key=os.getenv("ELEVEN_API_KEY"),
        )

        # Genereer spraak en schrijf naar tijdelijk bestand
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            for chunk in client.generate(text=text, voice=voice):
                temp_file.write(chunk)
            temp_path = temp_file.name

        # Upload audio naar Cloudinary
        audio_url = upload_audio_to_cloudinary(temp_path)

        # Verwijder lokaal bestand
        os.remove(temp_path)

        return audio_url

    except Exception as e:
        print(f"❌ Fout bij text_to_speech: {e}")
        raise
