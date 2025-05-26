import os
import tempfile
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings
from app.cloudinary_util import upload_to_cloudinary


def text_to_speech(text: str) -> str:
    try:
        # Initialiseer ElevenLabs client
        client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

        # Definieer voice met settings
        voice = Voice(
            voice_id=os.getenv("ELEVEN_VOICE_ID"),
            settings=VoiceSettings(stability=0.5, similarity_boost=0.8)
        )

        # Genereer spraak en schrijf naar tijdelijk mp3-bestand
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            for chunk in client.generate(text=text, voice=voice):
                f.write(chunk)
            temp_file_path = f.name

        # Upload naar Cloudinary en verwijder tijdelijk bestand
        audio_url = upload_to_cloudinary(temp_file_path)
        os.remove(temp_file_path)

        return audio_url

    except Exception as e:
        print(f"❌ Fout bij text_to_speech: {e}")
        raise
