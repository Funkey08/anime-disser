import os

# Fix Qt DPI awareness warning - must be set BEFORE Qt imports
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"

from datetime import datetime
from dotenv import load_dotenv
import queue
import threading

from talker import main_loop, list_monitors
from character_overlay import run_overlay

# Constants
MAIN_PROMPT_PATH = "prompts/main_prompt.md"
CHARACTER_PROMPT_PATH = "prompts/character_asuka.md"
GAME_PROMPT_PATH = "prompts/game_minecraft.md"
PNG_PATH = "assets/asuka_angryy.gif"
NUM_ITERATIONS = 10
SLEEP_BETWEEN_ITERATIONS = 3
MONITOR_INDEX = 0  # None = all monitors, 0 = first monitor, 1 = second monitor, etc.


if __name__ == "__main__":
    load_dotenv()

    # List available monitors
    list_monitors()

    # --------- Overlay Controller Setup ---------
    strength_q: "queue.Queue[float]" = queue.Queue()
    control_q: "queue.Queue[str]" = queue.Queue()

    # Start the main logic in a background thread
    logic_thread = threading.Thread(
        target=main_loop,
        args=(
            strength_q,
            control_q,
            MAIN_PROMPT_PATH,
            CHARACTER_PROMPT_PATH,
            GAME_PROMPT_PATH,
            NUM_ITERATIONS,
            SLEEP_BETWEEN_ITERATIONS,
            MONITOR_INDEX,
        ),
        daemon=True,
    )
    logic_thread.start()

    # Run the overlay in the MAIN thread (Qt requirement)
    run_overlay(PNG_PATH, strength_q, control_q)
