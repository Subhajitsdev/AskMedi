from dotenv import load_dotenv
import os
import base64
from groq import Groq

load_dotenv()

def encode_image(image_path):
    if image_path is None:
        return None
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
        return None
    except Exception as e:
        print(f"Error encoding image: {e}")
        return None

def analyze_image_with_query(query, encoded_image, model):
    if encoded_image is None and "vision" in model:  # Crucial check for vision model
        return "I cannot analyze the image because it couldn't be loaded or is missing."

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))  # Initialize with API Key
    messages = [
        {
            "role": "user",
            "content": [],  # Initialize content as an empty list
        }
    ]
    # Add text content
    messages[0]["content"].append({"type": "text", "text": query})

    # Add image content if available
    if encoded_image:
        messages[0]["content"].append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"},
        })


    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error during Groq API call: {e}")
        return "I'm sorry, I encountered an error while trying to analyze the input."