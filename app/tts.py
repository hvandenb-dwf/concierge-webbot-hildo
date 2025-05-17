from elevenlabs import ElevenLabs
from elevenlabs.client import VoiceSettings
import os
from app.cloudinary_util import upload_audio_to_cloudinary

# Initieer ElevenLabs client
eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

# Steminstellingen
voice_id = os.getenv("ELEVEN_VOICE_ID")  # Zorg dat dit is gezet in je .env
voice_settings = VoiceSettings(
    stability=0.5,
    similarity_boost=0.7,
    style=0.0,
    use_speaker_boost=True,
)

def text_to_speech(text: str, filename: str = "test_output.mp3") -> str:
    try:
        print("🎤 Start TTS generatie...")
        audio = eleven_client.generate(
            text=text,
            voice=voice_id,
            model="eleven_multilingual_v2",
            voice_settings=voice_settings
        )

        audio_bytes = bytes(audio)
        print(f"🔊 Lengte audio-output: {len(audio_bytes)} bytes")

        if len(audio_bytes) < 100:
            raise ValueError("⚠️ Audio-output is te klein of leeg. TTS mogelijk mislukt.")

        with open(filename, "wb") as f:
            f.write(audio_bytes)

        print(f"✅ Audio opgeslagen als: {filename}")

        # Upload naar Cloudinary
        print("☁️ Upload naar Cloudinary gestart...")
        cloudinary_url = upload_audio_to_cloudinary(filename)
        print(f"✅ Upload succesvol: {cloudinary_url}")

        return cloudinary_url

    except Exception as e:
        print(f"❌ Fout in text_to_speech: {e}")
        raise
