import os
from openai import OpenAI
from app.tts import generate_audio  # voeg deze regel toe

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_bot_reply(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Je bent een vriendelijke digitale assistent."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        reply = response.choices[0].message.content.strip()

        # Convert antwoord naar spraak
        audio_url = generate_audio(reply)
        return audio_url

    except Exception as e:
        return f"Er is iets misgegaan: {e}"
