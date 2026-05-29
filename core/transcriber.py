import os
from pydub import AudioSegment
from groq import Groq
from dotenv import load_dotenv
# Removed imageio_ffmpeg import

load_dotenv()

def transcribe_with_groq(audio_filepath):
    """Converts speech to text using Groq's Whisper model."""
    client = Groq()
    with open(audio_filepath, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=audio_file,
            language="en"
        )
    return transcription.text

def transcript_extraction(chunks: list) -> str:
    final_conversion = ""
    for chunk in chunks:
        text = transcribe_with_groq(chunk)
        final_conversion = final_conversion + text
    return final_conversion.strip()
