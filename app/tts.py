from elevenlabs import generate
from elevenlabs.client import VoiceSettings
import os
from app.cloudinary_util import upload_audio_to_cloudinary

# Steminstellingen
voice_id = os.getenv("ELEVEN_VOICE_ID")
voice_settings = VoiceSettings(
    stability=0.5,
    similarity_boost=0.7,
    style=0.0,
    use_speaker_boost=True,
)

def text_to_speech(text: str, filename: str = "test_output.mp3") -> bytes:
    try:
        print("🎤 Start TTS generatie...")

        # Generator omzetten naar volledige bytes
        audio_generator = eleven_client.generate(
            text=text,
            voice=voice_id,
            model="eleven_multilingual_v2",
            voice_settings=voice_settings
        )

        audio_bytes = b"".join(audio_generator)  # << FIX HIER

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

        return audio_bytes  # Je kan ook cloudinary_url returnen als je dat prefereert

    except Exception as e:
        print(f"❌ Fout in text_to_speech: {e}")
        raise
