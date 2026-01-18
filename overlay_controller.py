import os, time, queue, threading
import numpy as np
import sounddevice as sd
from openai import OpenAI
from dotenv import load_dotenv

from character_overlay import run_overlay

load_dotenv()

client = OpenAI(
    base_url="https://api.deepinfra.com/v1/openai",
    api_key=os.getenv("DEEP_INFRA_API_KEY"),
)

SAMPLE_RATE = 24000
CHANNELS = 1
DTYPE = np.int16
BYTES_PER_SAMPLE = 2

# Overlay queues
strength_q: "queue.Queue[float]" = queue.Queue()
control_q: "queue.Queue[str]" = queue.Queue()


def rms_strength_int16(audio_i16: np.ndarray) -> float:
    # RMS normalized to 0..1-ish
    if audio_i16.size == 0:
        return 0.0
    x = audio_i16.astype(np.float32) / 32768.0
    rms = float(np.sqrt(np.mean(x * x)))
    # Boost + clamp for more visible shake (tune)
    return min(1.0, rms * 6.0)


def speak_streaming_with_overlay(
    text: str,
    strength_queue: "queue.Queue[float]" = None,
    control_queue: "queue.Queue[str]" = None,
):
    # Use provided queues or fall back to module-level ones
    sq = strength_queue if strength_queue is not None else strength_q
    cq = control_queue if control_queue is not None else control_q

    overlay_shown = False  # Track if we've shown the overlay yet

    with client.audio.speech.with_streaming_response.create(
        model="hexgrad/Kokoro-82M",
        voice="af_bella",
        input=text,
        response_format="pcm",
    ) as response:

        buffer = b""

        with sd.OutputStream(
            samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16"
        ) as stream:
            for chunk in response.iter_bytes():
                buffer += chunk

                remainder = len(buffer) % BYTES_PER_SAMPLE
                if remainder:
                    audio_bytes = buffer[:-remainder]
                    buffer = buffer[-remainder:]
                else:
                    audio_bytes = buffer
                    buffer = b""

                if not audio_bytes:
                    continue

                # Show overlay only when first audio chunk is ready to play
                if not overlay_shown:
                    cq.put("show")
                    overlay_shown = True

                audio = np.frombuffer(audio_bytes, dtype=np.int16)
                stream.write(audio)

                sq.put(rms_strength_int16(audio))

    # Speech ended
    sq.put(0.0)
    cq.put("hide")


# if __name__ == "__main__":

#     CHARACTER_PNG_PATH = "assets/asuka.png"
#     # Start overlay on a separate thread
#     overlay_thread = threading.Thread(
#         target=run_overlay,
#         args=(CHARACTER_PNG_PATH, strength_q, control_q),
#         daemon=True,
#     )
#     overlay_thread.start()

#     # Test
#     speak_streaming_with_overlay("Baka. At least the overlay works now.")
#     time.sleep(1)

#     control_q.put("quit")
