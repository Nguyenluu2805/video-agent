import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("No API key found.")
    exit(1)

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents='Say hello to test the connection.',
    )
    print("Connection successful! Response from Gemini:")
    print(response.text)
except Exception as e:
    print("Connection failed! Error:")
    print(e)
