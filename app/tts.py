from elevenlabs.client import ElevenLabsClient, VoiceSettings
from elevenlabs import Voice
import os
import tempfile
import cloudinary
import cloudinary.uploader

# Initialiseer ElevenLabs client
client = ElevenLabsClient(
    api_key=os.getenv("ELEVEN_API_KEY")
)

# Stel gewenste stem en instellingen in
voice_id = os.getenv("ELEVEN_VOICE_ID", "Rachel")
voice = Voice(voice_id=voice_id)

voice_settings = VoiceSettings(
    stability=0.5,
    similarity_boost=0.75,
    style=0.0,
    use_speaker_boost=True
)

# Configureer Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def text_to_speech(text: str) -> str:
    """Converteer tekst naar spraak, sla op als MP3 en upload naar Cloudinary."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            audio = client.text_to_speech.convert(
                voice=voice,
                text=text,
                voice_settings=voice_settings,
                model_id="eleven_monolingual_v1"
            )
            tmp.write(audio)
            tmp_path = tmp.name

        # Upload naar Cloudinary
        upload_result = cloudinary.uploader.upload(tmp_path, resource_type="video")
        audio_url = upload_result["secure_url"]

        # Verwijder lokaal bestand
        os.remove(tmp_path)

        return audio_url

    except Exception as e:
        print(f"❌ Fout bij text_to_speech: {e}")
        raise
