import os
import tempfile
import cloudinary
import cloudinary.uploader

client = ElevenLabs(
    api_key=os.getenv("ELEVEN_API_KEY")
)

voice_id = os.getenv("ELEVEN_VOICE_ID")

def text_to_speech(text: str):
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

    # Opslaan naar tijdelijk bestand
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        f.write(audio)
        temp_audio_path = f.name

    # Upload naar Cloudinary
    result = cloudinary.uploader.upload(temp_audio_path, resource_type="video")
    return result["secure_url"]
