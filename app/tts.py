from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import tempfile
import os

client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

def text_to_speech(text: str) -> str:
    audio_stream = client.generate(
        text=text,
        voice="Rachel",
        model="eleven_multilingual_v2",
        voice_settings=VoiceSettings(stability=0.4, similarity_boost=0.8),
        stream=True
    )

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    for chunk in audio_stream:
        temp_file.write(chunk)
    temp_file.close()

    return temp_file.name
