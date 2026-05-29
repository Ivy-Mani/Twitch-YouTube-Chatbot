import yt_dlp
from pydub import AudioSegment
import os
import shutil
import tempfile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# Always use temp directory - works everywhere
DOWNLOAD_DIR = tempfile.mkdtemp()

# No FFMPEG_DIR needed - system finds it automatically


def download_youtube_audio(url: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
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
        base_filename = ydl.prepare_filename(info)
        filename = os.path.splitext(base_filename)[0] + ".wav"
        
        if not os.path.exists(filename):
            for ext in ['.wav', '.webm', '.m4a', '.mp3']:
                test_file = os.path.splitext(base_filename)[0] + ext
                if os.path.exists(test_file):
                    filename = test_file
                    break
    
    return filename


def convert_to_wav(input_path: str) -> str:
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format="wav")
    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 5) -> list:
    audio = AudioSegment.from_file(wav_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    
    chunk_ms = chunk_minutes * 60 * 1000
    chunks = []
    
    if len(audio) <= chunk_ms:
        chunk_path = f"{os.path.splitext(wav_path)[0]}_chunk_0.wav"
        audio.export(chunk_path, format="wav")
        chunks.append(chunk_path)
    else:
        for i, start in enumerate(range(0, len(audio), chunk_ms)):
            chunk = audio[start: start + chunk_ms]
            chunk_path = f"{os.path.splitext(wav_path)[0]}_chunk_{i}.wav"
            chunk.export(chunk_path, format="wav")
            chunks.append(chunk_path)
    
    return chunks


def process_input(source: str) -> list:
    clear_downloads()
    
    if source.startswith(("http://", "https://")):
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
    global DOWNLOAD_DIR
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR, ignore_errors=True)
    DOWNLOAD_DIR = tempfile.mkdtemp()
