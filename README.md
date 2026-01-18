# 🔥 Anime Disser 🔥

<img src="assets/asuka_angryy.gif" width="200">

<font size="5">*"Anta baka?"*</font>- Asuka Langley Soryu


This project uses the power of AI and screen capture technology to spawn an animated anime character overlay that watches your gameplay and roasts you harder than Tokyo-3 after it was attacked by Armisael.


## What the heck is this?

**Anime Disser** is a Python application that:

1. Takes screenshots of your game
2. Sends them to Google's Gemini AI
3. Generates toxic commentary in character (currently featuring Asuka Langley Soryu)
4. Converts that roast into speech using TTS
5. Displays an animated character overlay that **shakes aggressively** when they're particularly disappointed in you
6. Destroys your self-esteem gradually

Think of it as having a backseat gamer except she's 2D and powered by AI.

## Installation

### Prerequisites

- **Python 3.14** (or compatible version)
- **Conda/Miniconda** (because we're fancy like that)
- **A Google Gemini API key** (get one at [Google AI Studio](https://aistudio.google.com/apikey))
- **Windows OS** (the overlay uses `win32gui` because compatibility is for the weak)
- **Thick skin** (not installable via pip, unfortunately)

### Step 1: Clone This Mistake

```bash
git clone https://github.com/Funkey08/anime-disser.git
cd anime-disser
```

### Step 2: Create the Conda Environment

```bash
conda env create -f environment.yml
conda activate anime-disser
```

### Step 3: Install Additional Dependencies

Some packages aren't in the conda environment file, so install them with pip:

```bash
pip install google-generativeai python-dotenv pyscreenshot screeninfo pywin32 pyttsx3
```

### Step 4: Set Up Your API Keys

Create a `.env` file in the project root with the following:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
MODEL=gemini-2.5-flash
DEEP_INFRA_API_KEY=your_deep_infra_api_key_here
```

Replace the placeholder values with your actual API keys:
- `GEMINI_API_KEY`: Get from [Google AI Studio](https://aistudio.google.com/apikey)
- `MODEL`: The Gemini model to use (default: `gemini-2.5-flash`)
- `DEEP_INFRA_API_KEY`: Your [Deep Infra API key](https://deepinfra.com/dash) (if using alternative models)


### Step 5: Prepare Your Assets

Make sure you have character images in the `assets/` folder. The project currently uses `asuka_angryy.gif` because of course it does.

---

## Running It

```bash
python main.py
```

### What Happens Next:

1. The terminal lists your available monitors
2. A character overlay appears on your screen (top-right by default)
3. The program starts taking screenshots every few seconds
4. AI analyzes your gameplay
5. Character roasts you verbally
6. The overlay **shakes violently** when they're extra mad
7. You question your life choices

### Customization

Edit the constants in [`main.py`](main.py) to adjust:

- `CHARACTER_PROMPT_PATH` - Change the character (if you dare)
- `GAME_PROMPT_PATH` - Tell the AI what game you're playing
- `PNG_PATH` - Use a different character image/gif
- `NUM_ITERATIONS` - How many roasts you can take (default: 10)
- `SLEEP_BETWEEN_ITERATIONS` - Breathing room between insults (default: 3 seconds)
- `MONITOR_INDEX` - Which monitor to screenshot (None = all, 0 = first, etc.)



## Project Structure

```
anime-disser/
├── main.py                    # The orchestrator of your suffering
├── talker.py                  # Handles AI chat and screenshots
├── character_overlay.py       # The overlay widget (your new "friend")
├── overlay_controller.py      # Manages TTS + overlay shake intensity
├── tts_engine.py             # Text-to-speech engine
├── environment.yml           # Conda environment setup
├── .env                      # Your API keys (DO NOT COMMIT)
├── assets/                   # Character images/gifs
│   └── asuka_angryy.gif     # Default: Maximum sass
└── prompts/                  # AI personality files
    ├── main_prompt.md        # Base instructions
    ├── character_asuka.md    # Asuka's personality
    └── game_minecraft.md     # Game context
```


## Adding New Characters

Want a different anime character to judge you?

1. Create a new character file in `prompts/` (e.g., `character_rei.md`)
2. Add a corresponding image/gif to `assets/`
3. Update `CHARACTER_PROMPT_PATH` and `PNG_PATH` in [`main.py`](main.py)

<br>

<img src="assets/asuka_angryy.gif" width="200">

<font size="5">*"Anta baka!"*</font>- Asuka Langley Soryu
