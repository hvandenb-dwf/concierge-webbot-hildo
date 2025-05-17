import os
from openai import OpenAI
from app.tts import text_to_speech  # juist importeren

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_bot_reply(prompt: str) -> str:
    try:
        print("🤖 Start GPT-generatie...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Je bent een vriendelijke digitale assistent."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        message = response.choices[0].message.content.strip()
        print("✅ GPT-response ontvangen.")

        # Genereer audio via ElevenLabs + Cloudinary
        audio_url = text_to_speech(message)
        return audio_url

    except Exception as e:
        print(f"❌ Fout in generate_bot_reply: {e}")
        return f"Er is iets misgegaan: {e}"
