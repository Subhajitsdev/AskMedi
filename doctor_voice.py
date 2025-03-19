from dotenv import load_dotenv
import os
from gtts import gTTS
import elevenlabs
from elevenlabs.client import ElevenLabs
import subprocess
import platform
import librosa
import soundfile as sf
import time 

load_dotenv()

def text_to_speech_with_elevenlabs(input_text, output_filepath):
    """Converts text to speech using ElevenLabs, saves as MP3, and validates.
       Plays audio *only after* validation and in a separate thread.
       Includes a mechanism to stop playback if requested.
    """
    if not input_text:
        return None

    try:
        client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))
        audio = client.generate(
            text=input_text,
            voice="zT03pEAEi0VHKciJODfn",
            output_format="mp3_44100_128",  # Higher quality output
            model="eleven_turbo_v2"
        )
        elevenlabs.save(audio, output_filepath)

        # *** VALIDATION ***
        if not _validate_audio_file(output_filepath):
            print("Error: ElevenLabs generated an invalid audio file.")
            return None

        return output_filepath  # Return filepath on success

    except elevenlabs.api.error.APIError as e:  # Catch specific API Errors
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
            return False  # short file is invalid
        return True
    except Exception as e:
        print(f"Error validating audio file: {e}")
        return False


def _play_audio(output_filepath):
    """Plays the audio file (platform-specific), with fallbacks.
       Handles potential cracking sounds and provides a way to terminate.
    """
    os_name = platform.system()
    process = None  # Store the subprocess object

    if not os.path.exists(output_filepath):
        print(f"Error: Audio file not found at {output_filepath}")
        return

    try:
        if os_name == "Darwin":  # macOS
            command = ['afplay', output_filepath]
        elif os_name == "Windows":
            command = ['powershell', '-c', f'(New-Object Media.SoundPlayer "{output_filepath}").PlaySync();']
        elif os_name == "Linux":
             #Try ffplay first, as it generally has good buffering and is widely available.
            try:
                command = ['ffplay', '-nodisp', '-autoexit', output_filepath]
                process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) # Use Popen for ffplay
                return  # Return early since ffplay handles playback in the main loop
            except FileNotFoundError:
                print("ffplay not found, trying other methods...")
                try:
                    command = ['aplay', '-B', '50000', output_filepath]
                    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    return

                except (FileNotFoundError, subprocess.CalledProcessError):
                    try:
                        print("aplay failed, trying mpg123...")
                        command = ['mpg123', output_filepath]
                        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    except (FileNotFoundError, subprocess.CalledProcessError) as e:
                         print(f"Error: Could not play audio.  Tried aplay, mpg123, and ffplay. {e}")
                         return # return if failed
        else:
            print("Unsupported operating system for audio playback.")
            return

        #For commands that don't use Popen in their initial try block (macOS, Windows)
        if process is None:  # Only start a process if one wasn't already started
                process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


    except Exception as e: #Catch general exception
        print(f"Error playing audio: {e}")
        return  # Explicitly return on error

    # The following code provides a way to potentially interrupt playback,
    # *and* handles cases where the process might have already finished.

    try:
        while process.poll() is None:  # Check if the process is still running
            time.sleep(0.1)  # Short delay to avoid busy-waiting
    except KeyboardInterrupt:
        print("Audio playback interrupted.")
        if process:
            try:
                process.stdin.write(b'q') # Send 'q' to quit (works for ffplay, mpg123)
                process.stdin.flush()
            except (BrokenPipeError, AttributeError): # Handle cases where stdin is not available
                 try:
                    process.terminate() # Terminate as last resort
                 except Exception: # catch any other exception from terminate
                    pass
            finally:
                process.wait() # wait for the termination to happen
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if process:
            process.terminate() # Terminate if any other error occurred

# text_to_speech_with_gtts is still not relevant here