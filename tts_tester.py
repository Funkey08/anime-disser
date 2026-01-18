import os
import numpy as np
import sounddevice as sd
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    base_url="https://api.deepinfra.com/v1/openai",
    api_key=os.getenv("DEEP_INFRA_API_KEY"),
)

SAMPLE_RATE = 24000  # Kokoro models typically use 24kHz
CHANNELS = 1


def stream_audio(message: str):
    with client.audio.speech.with_streaming_response.create(
        model="hexgrad/Kokoro-82M",
        voice="af_bella",
        input=message,
        response_format="pcm",  # <-- IMPORTANT
    ) as response:

        with sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
        ) as stream:

            buffer = b""
            for chunk in response.iter_bytes():
                buffer += chunk
                # Process complete int16 samples (2 bytes each)
                samples_size = (len(buffer) // 2) * 2
                if samples_size > 0:
                    audio = np.frombuffer(buffer[:samples_size], dtype=np.int16)
                    stream.write(audio)
                    buffer = buffer[samples_size:]  # Keep any remaining partial byte
