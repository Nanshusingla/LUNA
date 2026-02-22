from elevenlabs.client import ElevenLabs
import os
from dotenv import load_dotenv

load_dotenv()

client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY")
)

def generate_fake_call_audio(text):
    # 1. Ensure the directory exists
    folder_path = "static/audio"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # 2. Generate Audio with the CORRECT model_id
    try:
        audio = client.text_to_speech.convert(
            voice_id="xctasy8XvGp2cVO9HL9k",
            model_id="eleven_multilingual_v2", # FIXED MODEL NAME
            text=text
        )

        file_name = "fake_call.mp3"
        full_path = os.path.join(folder_path, file_name)

        # 3. Save the file
        with open(full_path, "wb") as f:
            for chunk in audio:
                if chunk:
                    f.write(chunk)

        # Return the path for the browser
        return f"/static/audio/{file_name}"

    except Exception as e:
        print(f"❌ ElevenLabs Error: {e}")
        # Return the alarm as a fallback if the API fails
        return "/static/alarm.mp3"