# 🎬 YT Insight

> **Understand any YouTube video or audio file in seconds — without watching it.**

YT Insight transcribes, summarizes, and lets you chat with the content of any YouTube video or local media file using Whisper, LangChain, FAISS, and Streamlit.

Available in two modes — a **Streamlit web app** (`app.py`) for a polished UI, and a lightweight **CLI** (`main.py`) for quick terminal use.

---

## ✨ Features

- 🔗 **YouTube URL support** — paste any YouTube link and get instant insights
- 📁 **Local file upload** — supports MP3, MP4, WAV, M4A, OGG, FLAC, WebM, MKV, AVI
- 🧠 **Auto-transcription** — powered by OpenAI Whisper
- 📝 **AI-generated summary & title** — concise overview generated automatically
- 💬 **RAG-powered Q&A** — ask anything about the content; answers are grounded in the actual transcript via FAISS vector search
- ⚡ **On-demand indexing** — the vector index is built only when you ask your first question, keeping initial load fast

---

## 🖼️ Demo

```
Paste a YouTube URL  →  Transcribe  →  Summarize  →  Chat with the content
```

---

## 🏗️ Architecture

```
Input (URL / File)
      │
      ▼
 process_input()          ← yt-dlp + pydub (audio extraction & chunking)
      │
      ▼
 transcript_extraction()  ← OpenAI Whisper (speech-to-text)
      │
      ▼
 summary() + title()      ← LLM-based summarization
      │
      ▼
 retrieve()               ← LangChain + FAISS (RAG on first question)
      │
      ▼
 Streamlit UI             ← Chat interface with session state
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- [FFmpeg](https://ffmpeg.org/download.html) installed and available in `PATH`

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/yt-insight.git
cd yt-insight

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Option A — Streamlit Web App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

### Option B — Command-Line Interface (CLI)

For a quick, no-browser experience, use `main.py` directly in your terminal:

```bash
python main.py
```

```
Enter the YouTube link: https://www.youtube.com/watch?v=...

📝 <Generated Title>

   <Generated Summary>

ENTER YOUR DESIRED QUESTION ?. PRESS EXIT TO END CONVERSATION.

Enter your question: What is the main topic?
→ ...answer grounded in the transcript...

Enter your question: exit
```

The CLI runs the same core pipeline — download → transcribe → summarize — then drops you into an interactive Q&A loop. Type `exit` at any time to quit.

---

## 📁 Project Structure

```
yt-insight/
├── app.py                  # Streamlit web application
├── main.py                 # CLI entry point (terminal-based Q&A)
├── core/
│   ├── rag_engine.py       # FAISS retrieval & LangChain RAG pipeline
│   ├── summary.py          # Summary and title generation
│   └── transcriber.py      # Transcript extraction from audio chunks
├── utils/
│   └── audioprocesser.py   # Audio downloading (yt-dlp) & chunking (pydub)
├── requirements.txt
└── README.md
```

---

## 🛠️ Tech Stack

| Component | Library |
|---|---|
| Audio download | `yt-dlp` |
| Audio processing | `pydub` |
| Transcription | `openai-whisper` |
| Embeddings & RAG | `LangChain` + `FAISS` |
| UI | `Streamlit` |

---

## 📦 Requirements

A typical `requirements.txt` for this project:

```
streamlit
yt-dlp
pydub
openai-whisper
langchain
langchain-community
faiss-cpu
openai
```

> **Note:** GPU-accelerated transcription is supported if you install `faiss-gpu` and have a CUDA-capable machine.

---

## ⚙️ Configuration

If your `rag_engine.py` or `summary.py` uses an LLM API (e.g. OpenAI), set your key as an environment variable:

```bash
export OPENAI_API_KEY="sk-..."
```

Or create a `.env` file at the project root:

```
OPENAI_API_KEY=sk-...
```

---

## 🧩 How It Works

Both `app.py` and `main.py` share the same core pipeline:

1. **Input** — A YouTube URL is provided (CLI prompts for it; the web app accepts URL or file upload).
2. **Audio extraction** — `yt-dlp` downloads the audio stream; `pydub` splits it into manageable chunks.
3. **Transcription** — Each chunk is transcribed by Whisper and stitched into a full transcript.
4. **Summarization** — An LLM generates a concise summary and a descriptive title.
5. **Q&A (RAG)** — The transcript is embedded and indexed with FAISS. Questions retrieve the most relevant passages before the LLM answers, keeping responses grounded in the actual content.

| Feature | `app.py` (Streamlit) | `main.py` (CLI) |
|---|---|---|
| Interface | Web browser | Terminal |
| File upload | ✅ | ❌ (URL only) |
| RAG indexing | On first question | On first question |
| Chat history | ✅ Persistent in session | ✅ Loop until `exit` |

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

*Built for curious minds who'd rather read than watch.*
