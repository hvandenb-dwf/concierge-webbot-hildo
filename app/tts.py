import os
import tempfile
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings
from app.cloudinary_util import upload_audio_to_cloudinary


def text_to_speech(text: str) -> str:
    try:
        voice = Voice(
            voice_id=os.getenv("ELEVEN_VOICE_ID"),
            settings=VoiceSettings(stability=0.5, similarity_boost=0.8)
        )

        client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            for chunk in client.generate(text=text, voice=voice):
                tmp.write(chunk)
            tmp_path = tmp.name

        audio_url = upload_audio_to_cloudinary(tmp_path)
        os.remove(tmp_path)

        return audio_url

    except Exception as e:
        print(f"❌ Fout in text_to_speech: {e}")
        raise


def speech_to_speech(text: str) -> str:
    try:
        voice_id = os.getenv("ELEVEN_VOICE_ID")
        if not voice_id:
            raise ValueError("ELEVEN_VOICE_ID is niet ingesteld.")

        client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

        print(f"🎙️ STS met voice_id: {voice_id}")

        response = client.speech_to_speech.generate(
            text=text,
            voice=voice_id,
            model="eleven_multilingual_v2"
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            for chunk in response:
                tmp.write(chunk)
            tmp_path = tmp.name

        audio_url = upload_audio_to_cloudinary(tmp_path)
        os.remove(tmp_path)

        return audio_url

    except Exception as e:
        print(f"❌ Fout in speech_to_speech: {e}")
        raise
