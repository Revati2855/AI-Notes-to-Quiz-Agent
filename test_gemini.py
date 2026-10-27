import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("API key loaded:", bool(api_key))

if not api_key:
    print("ERROR: GEMINI_API_KEY not found")
    exit()

print("Connecting to Gemini...")

client = genai.Client(api_key=api_key)

print("Sending request...")

interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input="Explain artificial intelligence in 2 simple sentences.",
    generation_config={
        "thinking_level": "low"
    }
)

print("Gemini response:")
print(interaction.output_text)