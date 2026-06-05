from dotenv import load_dotenv
from google import genai
import os
import json
import re
from json_format.json_format import extract_json
from ai.prompt import build_plan_trip_prompt,build_road_trip_prompt

load_dotenv()

# Gemini client
client = genai.Client(api_key=os.getenv("gemini_api_key"))

MODEL = os.getenv("gemini_model")

def call_gemini(prompt: str) -> dict:
    """Send prompt to Gemini and return a parsed structured dict."""
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
    config={"max_output_tokens": 8192},
    )
    return extract_json(response.text)