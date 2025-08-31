# --- doctor_voice.py (fixed TTS) ---
import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import save
from elevenlabs.core.api_error import ApiError  # <-- correct exception
import librosa

load_dotenv()

ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Use a valid existing voice_id. Replace with yours if needed.
# (Example: Rachel)
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

# Pick a valid output format from the allowed list
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"

def text_to_speech_with_elevenlabs(input_text: str, output_filepath: str):
    """
    Converts text to speech via ElevenLabs and saves to output_filepath.
    Returns the output filepath on success, or None on failure.
    """
    if not input_text:
        return None

    if not ELEVEN_API_KEY:
        print("Missing ELEVENLABS_API_KEY.")
        return None

    client = ElevenLabs(api_key=ELEVEN_API_KEY)

    try:
        # Use the v1 client "convert" endpoint explicitly with a voice_id
        audio = client.text_to_speech.convert(
            voice_id=DEFAULT_VOICE_ID,          # your voice_id here
            model_id="eleven_turbo_v2",         # model you have access to
            text=input_text,
            output_format=DEFAULT_OUTPUT_FORMAT # <-- valid format
        )

        save(audio, output_filepath)

        # simple validation
        if not _validate_audio_file(output_filepath):
            print("Generated audio failed validation.")
            return None

        return output_filepath

    except ApiError as e:
        # Parse structured error (403 invalid_output_format, 401 unauthorized, etc.)
        body = getattr(e, "body", {}) or {}
        detail = body.get("detail", {})
        status = detail.get("status")
        message = detail.get("message") or str(e)

        if status == "invalid_output_format":
            print(f"ElevenLabs error: {message}")
            print("Fix: set output_format to one of the allowed values.")
        elif status == "voice_limit_reached":
            print("ElevenLabs error: custom voice limit reached. Use a built-in voice_id or free a slot.")
        elif status == "unauthorized":
            print("ElevenLabs error: unauthorized. Check ELEVENLABS_API_KEY.")
        else:
            print(f"ElevenLabs API error: {message}")
        return None

    except Exception as e:
        print(f"TTS failed: {e}")
        return None


def _validate_audio_file(filepath: str) -> bool:
    try:
        y, sr = librosa.load(filepath, sr=None)
        dur = librosa.get_duration(y=y, sr=sr)
        return dur >= 0.5
    except Exception as e:
        print(f"Validation error: {e}")
        return False
