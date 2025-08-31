from dotenv import load_dotenv
import os
import gradio as gr
from doctor_brain import encode_image, analyze_image_with_query
from patient_voice import transcribe_with_groq
from doctor_voice import text_to_speech_with_elevenlabs

load_dotenv()

system_prompt = """You have to act as a professional doctor. I know you are not, but this is for learning purposes.
            What's wrong, if anything, medically?
            If you make a differential diagnosis, suggest some remedies. Don't add any numbers or special characters in
            your response. Your response should be in one long paragraph. Always answer as if you are answering a real person.
            Don't respond as an AI model in markdown. Your answer should mimic that of an actual doctor, not an AI bot.
            Keep your answer concise. No preamble, start your answer right away, please."""

def process_inputs(text_input, audio_filepath, image_filepath):
    """Processes inputs (text, audio, image) and generates doctor's response."""

    # 1. Prioritize Text Input, then Audio
    if text_input:
        patient_query = text_input
    elif audio_filepath:
        patient_query = transcribe_with_groq(
            audio_filepath=audio_filepath,
            GROQ_API_KEY=os.environ.get("GROQ_API_KEY")
        )
    else:
        patient_query = ""  # Empty if no text or audio


    # 2. Combine with System Prompt
    combined_query = system_prompt + " " + patient_query

    # 3. Encode Image (if provided)
    encoded_image = encode_image(image_filepath)

   # 4. Determine Model and Analyze
    if image_filepath and encoded_image:
        model = "meta-llama/llama-4-scout-17b-16e-instruct"  # Use vision model
    else:
        model = "llama-3.1-8b-instant"  # Use text-only model
    doctor_response = analyze_image_with_query(query=combined_query, encoded_image=encoded_image, model=model)



    # 5. Text-to-Speech
    if doctor_response:  # Only generate audio if there's a response
        voice_of_doctor = text_to_speech_with_elevenlabs(input_text=doctor_response, output_filepath="final.mp3")
        if voice_of_doctor is None:  # Check for invalid audio (from doctor_voice.py)
            doctor_response += " (Error: Could not generate audio response.)"
            voice_of_doctor = None  # Explicitly set to None
    else:
        voice_of_doctor = None


    return patient_query, doctor_response, voice_of_doctor


# Create the Gradio Interface
text_input = gr.Textbox(label="Patient Text Input", placeholder="Type your question here...")
audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Patient Voice Input")
image_input = gr.Image(type="filepath", label="Image Input")

patient_output = gr.Textbox(label="Patient Input (Text or Transcribed Voice)")
doctor_text_output = gr.Textbox(label="Doctor's Response (Text)")
doctor_audio_output = gr.Audio(label="Doctor's Response (Audio)")

clear_button = gr.ClearButton([text_input, audio_input, image_input, patient_output, doctor_text_output, doctor_audio_output])

iface = gr.Interface(
    fn=process_inputs, 
    inputs=[text_input, audio_input, image_input],
    outputs=[patient_output, doctor_text_output, doctor_audio_output],
    title="ASKMEDI🧑‍⚕️ - Your AI Medical Assistant",
)

iface.launch(debug=True, share=True)