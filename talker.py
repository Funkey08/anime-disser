from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
from io import BytesIO
from screeninfo import get_monitors
import json
import os
import pyscreenshot
import queue
import re
import threading
import time

from overlay_controller import speak_streaming_with_overlay
from character_overlay import run_overlay
from tts_engine import stream_audio


def get_md_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def list_monitors():
    """List all available monitors with their details."""
    monitors = get_monitors()
    print("\nAvailable monitors:")
    for i, monitor in enumerate(monitors):
        print(
            f"  Monitor {i}: {monitor.width}x{monitor.height} at ({monitor.x}, {monitor.y})"
        )
        if monitor.is_primary:
            print(f"    (Primary monitor)")
    return monitors


def take_screenshot(monitor_index: int = None):
    """
    Take a screenshot from a specific monitor or all monitors.

    Args:
        monitor_index: Index of the monitor to capture (0, 1, 2, etc.)
                      If None, captures all monitors (entire virtual desktop)
    """
    print(f"({datetime.now()}) ", "TAKING SCREENSHOT...")

    if monitor_index is not None:
        monitors = get_monitors()
        if monitor_index < 0 or monitor_index >= len(monitors):
            raise ValueError(
                f"Monitor index {monitor_index} out of range (0-{len(monitors)-1})"
            )

        monitor = monitors[monitor_index]
        bbox = (
            monitor.x,
            monitor.y,
            monitor.x + monitor.width,
            monitor.y + monitor.height,
        )
        screenshot = pyscreenshot.grab(bbox=bbox)
        print(
            f"({datetime.now()}) ",
            f"Captured monitor {monitor_index}: {screenshot.size[0]}x{screenshot.size[1]} pixels",
        )
    else:
        screenshot = pyscreenshot.grab()
        print(
            f"({datetime.now()}) ",
            f"Captured all monitors: {screenshot.size[0]}x{screenshot.size[1]} pixels",
        )

    return screenshot


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


def main_loop(
    strength_q,
    control_q,
    main_prompt_path: str,
    character_prompt_path: str,
    game_prompt_path: str,
    num_iterations: int = 2,
    sleep_duration: float = 3,
    monitor_index: int = None,
):
    """Background thread that handles screenshot/TTS logic."""
    SYSTEM_PROMPT: str = get_md_text(main_prompt_path)
    CHARACTER_PROMPT: str = get_md_text(character_prompt_path)
    GAME_PROMPT: str = get_md_text(game_prompt_path)

    recent_events: list[str] = []
    past_context: str = ""

    try:
        for i in range(num_iterations):

            complete_prompt = get_complete_prompt(
                SYSTEM_PROMPT,
                CHARACTER_PROMPT,
                GAME_PROMPT,
                recent_events,
                past_context,
            )

            screenshot = take_screenshot(monitor_index)
            model_return = send_prompt_to_model(complete_prompt, screenshot)

            print(model_return)

            # Parse JSON
            data = json.loads(strip_code_fences(model_return))

            should_comment = bool(data.get("should_comment", False))
            message = (
                data.get("commentary", "No message returned.") if should_comment else ""
            )

            print(f"({datetime.now()}) ", " COMMENTARY: ", message)

            # Speak + show overlay only if there's something to say
            if should_comment and message.strip():
                speak_streaming_with_overlay(
                    text=message,
                    strength_queue=strength_q,
                    control_queue=control_q,
                )

            # Update memory
            recent_events = add_to_recent_events(
                recent_events, data.get("recent_events", [])
            )
            past_context = data.get("past_context", past_context)

            print(f"({datetime.now()}) ", "UPDATED RECENT EVENTS: ", recent_events)
            print(f"({datetime.now()}) ", "UPDATED PAST CONTEXT: ", past_context)

            time.sleep(sleep_duration)
    finally:
        control_q.put("quit")
