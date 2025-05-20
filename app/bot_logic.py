import os
from openai import OpenAI
from app.tts import text_to_speech  # juist importeren

# Initialiseer OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_bot_reply(user_input: str) -> str:
    if not user_input or not isinstance(user_input, str):
        return "Sorry, ik heb geen invoer ontvangen. Kunt u dat herhalen?"

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Je bent een behulpzame digitale conciërge die gebruikers vriendelijk helpt met informatie of vragen."},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"⚠️ Fout in generate_bot_reply: {e}")
        return "Er ging iets mis bij het genereren van een antwoord."

