from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
from io import BytesIO
import json
import os
import pyscreenshot
import re
import time

from tts_tester import stream_audio


def get_md_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def take_screenshot():
    print(f"({datetime.now()}) ", "TAKING SCREENSHOT...")
    return pyscreenshot.grab()


def pil_to_png_bytes(image) -> bytes:
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def get_complete_prompt(
    system_prompt: str,
    character_prompt: str,
    game_prompt: str,
    recent_events: str,
    past_context: str,
) -> str:
    return f"""
        SYSTEM / INSTRUCTIONS
        ---------------------
        {system_prompt}
        
        CHARACTER DESCRIPTION
        ---------------------
        {character_prompt}

        GAME CONTEXT
        ---------------------
        {game_prompt}

        MEMORY
        ---------------------
        RECENT EVENTS: {recent_events or "(none)"}

        PAST_CONTEXT: {past_context or "(none)"}
        """.strip()


def send_prompt_to_model(prompt_text: str, screenshot_img) -> str:

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY in environment (.env).")

    client = genai.Client(api_key=api_key)

    image_bytes = pil_to_png_bytes(screenshot_img)
    image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")

    print(f"({datetime.now()}) ", "SENDING PROMPT TO MODEL...")

    # Best practice: when using a single image, put the image part before the text prompt
    response = client.models.generate_content(
        model=os.getenv("MODEL", "gemini-2.5-flash"),
        contents=[image_part, prompt_text],
    )

    return response.text or ""


def add_to_recent_events(
    prev_recent_events: list[str], new_recent_events: list[str], max_items: int = 10
) -> list[str]:
    updated = (prev_recent_events or []) + (new_recent_events or [])
    # keep newest last, trimming to last max_items
    return updated[-max_items:]


def strip_code_fences(text: str) -> str:
    # Remove code fences from the text
    return re.sub(r"```(json)?\n(.*?)```", r"\2", text, flags=re.DOTALL).strip()


if __name__ == "__main__":
    load_dotenv()

    MAIN_PROMPT_PATH = "prompts/main_prompt.md"
    CHARACTER_PROMPT_PATH = "prompts/character_asuka.md"
    GAME_PROMPT_PATH = "prompts/game_test.md"

    SYSTEM_PROMPT: str = get_md_text(MAIN_PROMPT_PATH)
    CHARACTER_PROMPT: str = get_md_text(CHARACTER_PROMPT_PATH)
    GAME_PROMPT: str = get_md_text(GAME_PROMPT_PATH)
    recent_events: list[str] = []
    past_context: str = ""

    for i in range(2):

        complete_prompt = get_complete_prompt(
            SYSTEM_PROMPT, CHARACTER_PROMPT, GAME_PROMPT, recent_events, past_context
        )

        screenshot = take_screenshot()
        model_return = send_prompt_to_model(complete_prompt, screenshot)

        print(model_return)

        # Parse JSON
        data = json.loads(strip_code_fences(model_return))

        message = data.get("commentary", "No message returned.")

        print(f"({datetime.now()}) ", " COMMENTARY: ", message)

        stream_audio(message)

        # Update memory
        recent_events = add_to_recent_events(
            recent_events, data.get("recent_events", [])
        )
        past_context = data.get("past_context", past_context)
        print(f"({datetime.now()}) ", "UPDATED RECENT EVENTS: ", recent_events)
        print(f"({datetime.now()}) ", "UPDATED PAST CONTEXT: ", past_context)

        time.sleep(3)
