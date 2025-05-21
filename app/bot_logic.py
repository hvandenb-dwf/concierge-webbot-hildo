from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_bot_reply(user_input: str) -> str:
    if not user_input or not isinstance(user_input, str):
        return "Geen geldige input ontvangen."

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Je bent een behulpzame conciërge."},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"❌ Fout bij generate_bot_reply: {e}")
        return "Er ging iets mis bij het genereren van een antwoord."
