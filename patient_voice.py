from dotenv import load_dotenv
import os
import logging
import speech_recognition as sr
from pydub import AudioSegment
from io import BytesIO
from groq import Groq  

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def record_audio(file_path, timeout=20, phrase_time_limit=None):
    """
    Records audio from the microphone and saves it as an MP3 file.
    """
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            logging.info("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            logging.info("Start speaking now...")
            audio_data = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            logging.info("Recording complete.")
            wav_data = audio_data.get_wav_data()
            audio_segment = AudioSegment.from_wav(BytesIO(wav_data))
            audio_segment.export(file_path, format="mp3", bitrate="128k")
            logging.info(f"Audio saved to {file_path}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return  # Explicitly return None on error


def transcribe_with_groq(audio_filepath, GROQ_API_KEY, stt_model="whisper-large-v3"):
    """Transcribes audio using Groq's API."""
    if not audio_filepath: # check for valid audio file path
        return ""

    try:
        client = Groq(api_key=GROQ_API_KEY)
        with open(audio_filepath, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model=stt_model,
                file=audio_file,
                language="en"
            )
        return transcription.text
    except FileNotFoundError: # explicitly handle no file
        print(f"Error: Audio file not found at {audio_filepath}")
        return ""
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return ""  # Return empty string on error