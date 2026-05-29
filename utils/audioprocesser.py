import yt_dlp
from pydub import AudioSegment
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

FFMPEG_DIR = os.getenv("FFMPEG_DIR", "")
if FFMPEG_DIR:
    AudioSegment.converter = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
    AudioSegment.ffprobe   = os.path.join(FFMPEG_DIR, "ffprobe.exe")


def download_youtube_audio(url: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "ffmpeg_location": FFMPEG_DIR,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = os.path.splitext(ydl.prepare_filename(info))[0] + ".wav"
    return filename


def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format="wav")
    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 5) -> list:
    """
    Split audio into chunks.
    Default is 5 minutes (down from 10) so WAV chunks stay well under
    Groq's 25 MB request limit even for high-quality audio.
    Each chunk is also normalised to mono / 16 kHz to further reduce size.
    """
    audio = AudioSegment.from_file(wav_path)
    # Normalise to mono 16 kHz — Whisper doesn't need more and this halves file size
    audio = audio.set_channels(1).set_frame_rate(16000)

    chunk_ms = chunk_minutes * 60 * 1000
    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start: start + chunk_ms]
        chunk_path = f"{os.path.splitext(wav_path)[0]}_chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")
        size_mb = os.path.getsize(chunk_path) / (1024 * 1024)
        print(f"  Chunk {i}: {size_mb:.1f} MB → {chunk_path}")
        chunks.append(chunk_path)

    return chunks


def process_input(source: str) -> list:
    clear_downloads()
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks


def clear_downloads():
    shutil.rmtree(DOWNLOAD_DIR, ignore_errors=True)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)