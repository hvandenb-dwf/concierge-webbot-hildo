from elevenlabs import ElevenLabs, Voice, VoiceSettings
import os
import tempfile
import cloudinary
import cloudinary.uploader

# Initialiseer ElevenLabs client
client = ElevenLabs(
    api_key=os.getenv("ELEVEN_API_KEY")
)

# Haal voice_id uit omgeving (bijv. "Rachel")
voice_id = os.getenv("ELEVEN_VOICE_ID")

def text_to_speech(text: str) -> str:
    """Converteer tekst naar spraak, upload naar Cloudinary, retourneer mp3-url."""
    audio = client.generate(
        text=text,
        voice=voice_id,
        model="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=0.3,
            similarity_boost=0.7,
            style=0.0,
            use_speaker_boost=True
        )
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(audio)
        temp_path = tmp.name

    upload_result = cloudinary.uploader.upload(temp_path, resource_type="video")
    return upload_result["secure_url"]
