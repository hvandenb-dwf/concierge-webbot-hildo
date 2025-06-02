from elevenlabs.client import ElevenLabs
from elevenlabs import Voice
import os

def generate_audio(text: str) -> bytes:
    eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
    audio_stream = eleven_client.generate(
        text=text,
        voice=Voice(voice_id="YUdpWWny7k5yb4QCeweX"),  # Ruth - Dutch voice
        model="eleven_multilingual_v2",
        output_format="mp3_44100_128"
    )
    return b"".join(audio_stream)