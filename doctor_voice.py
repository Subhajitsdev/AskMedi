# doctor_voice.py (FURTHER REFINED)
from dotenv import load_dotenv
import os
from gtts import gTTS
import elevenlabs
from elevenlabs.client import ElevenLabs
import subprocess
import platform
import librosa  # NEW: Install librosa: pip install librosa
import soundfile as sf # NEW Import

load_dotenv()

def text_to_speech_with_elevenlabs(input_text, output_filepath):
    """Converts text to speech using ElevenLabs, saves as MP3, and validates."""
    if not input_text:
        return None

    try:
        client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))
        audio = client.generate(
            text=input_text,
            voice="zT03pEAEi0VHKciJODfn",
            output_format="mp3_22050_32",
            model="eleven_turbo_v2"
        )
        elevenlabs.save(audio, output_filepath)

        # *** VALIDATION ***
        if not _validate_audio_file(output_filepath):
            print("Error: ElevenLabs generated an invalid audio file.")
            return None

        _play_audio(output_filepath) #play after validation
        return output_filepath  # Return filepath on success

    except elevenlabs.api.error.APIError as e: # Catch specific API Errors
        print(f"ElevenLabs API Error: {e}")
        return None
    except Exception as e:
        print(f"Error in ElevenLabs Text-to-Speech: {e}")
        return None


def _validate_audio_file(filepath):
    """Checks if an audio file is valid and has a reasonable duration."""
    try:
        # Use librosa to load and check duration
        y, sr = librosa.load(filepath, sr=None)  # Load with original sample rate
        duration = librosa.get_duration(y=y, sr=sr)

        if duration < 0.5:  # Check for a minimum duration (e.g., 0.5 seconds)
            print(f"Warning: Audio file is very short ({duration:.2f} seconds).")
            return False # short file is invalid
        return True
    except Exception as e:
        print(f"Error validating audio file: {e}")
        return False


def _play_audio(output_filepath):
    """Plays the audio file (platform-specific), with fallbacks."""
    os_name = platform.system()

    if not os.path.exists(output_filepath):
        print(f"Error: Audio file not found at {output_filepath}")
        return

    try:
        if os_name == "Darwin":  # macOS
            subprocess.run(['afplay', output_filepath], check=True)
        elif os_name == "Windows":  # Windows
            subprocess.run(['powershell', '-c', f'(New-Object Media.SoundPlayer "{output_filepath}").PlaySync();'], check=True)
        elif os_name == "Linux":  # Linux
            # Try aplay first, then mpg123, then ffplay
            try:
                subprocess.run(['aplay', output_filepath], check=True, capture_output=True)
            except (FileNotFoundError, subprocess.CalledProcessError):
                try:
                    print("aplay failed, trying mpg123...")
                    subprocess.run(['mpg123', output_filepath], check=True, capture_output=True)
                except (FileNotFoundError, subprocess.CalledProcessError):
                    try:
                        print("mpg123 failed, trying ffplay...")
                        subprocess.run(['ffplay', '-nodisp', '-autoexit', output_filepath], check=True, capture_output=True)
                    except (FileNotFoundError, subprocess.CalledProcessError) as e:
                         print(f"Error: Could not play audio.  Tried aplay, mpg123, and ffplay. {e}")
        else:
            print("Unsupported operating system for audio playback.")
    except subprocess.CalledProcessError as e:
        print(f"Error playing audio: {e}")
        print(f"  Return code: {e.returncode}")
        if hasattr(e, 'output'):
          print(f"  Output: {e.output.decode()}")
        if hasattr(e, 'stderr'):
          print(f"  Stderr: {e.stderr.decode()}")

# text_to_speech_with_gtts remains the same as in the previous response