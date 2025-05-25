from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings
from app.cloudinary_util import upload_audio_to_cloudinary
import os
import tempfile

def text_to_speech(text):
    try:
        voice = Voice(
            voice_id=os.getenv("ELEVEN_VOICE_ID"),
            settings=VoiceSettings(stability=0.5, similarity_boost=0.8)
        )

        client = ElevenLabs(
            api_key=os.getenv("ELEVEN_API_KEY"),
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            for chunk in client.generate(text=text, voice=voice):
                f.write(chunk)
            temp_file_path = f.name

        cloudinary_url = upload_audio_to_cloudinary(temp_file_path)
        os.remove(temp_file_path)

        return cloudinary_url

    except Exception as e:
        print(f"❌ Fout bij text_to_speech: {e}")
        raise
