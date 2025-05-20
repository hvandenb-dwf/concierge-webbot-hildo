def generate_bot_reply(user_input: str) -> str:
    print(f"📥 Ontvangen input: {user_input!r}")

    if not user_input or not isinstance(user_input, str):
        print("⚠️ Ongeldige invoer ontvangen.")
        return "Sorry, ik heb geen invoer ontvangen. Kunt u dat herhalen?"

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Je bent een behulpzame conciërge."},
                {"role": "user", "content": user_input}
            ]
        )
        output = response.choices[0].message.content.strip()
        print(f"🧠 GPT-antwoord: {output!r}")
        return output

    except Exception as e:
        print(f"❌ Fout bij generate_bot_reply: {e}")
        return "Er ging iets mis bij het genereren van een antwoord."
