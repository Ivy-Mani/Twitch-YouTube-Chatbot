import os
import tempfile
import streamlit as st
from core.rag_engine import retrieve
from utils.audioprocesser import process_input
from core.summary import summary, title
from core.transcriber import transcript_extraction

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="YT Insight",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Session state defaults ────────────────────────────────────────────────────
for key, default in {
    "caption": "",
    "summary_text": "",
    "title_text": "",
    "pipeline_done": False,
    "rag_ready": False,
    "chat_history": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── Sidebar · About ───────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/youtube-play.png", width=64)
    st.title("YT Insight")
    st.markdown(
        """
**YT Insight** lets you understand any YouTube video — or your own audio/video file — in seconds, without watching it.

**How it works**

- Paste a **YouTube link** *or* upload a **local audio/video file**
- The audio is downloaded (or read), chunked, and transcribed via Whisper
- A concise **summary** is generated automatically
- When you ask your first question, the transcript is indexed for **RAG** so every answer is grounded in the actual content

**Why RAG on demand?**

Indexing only runs when you ask a question, keeping the initial processing fast.

---
**Stack**  
`yt-dlp` · `pydub` · `Whisper` · `LangChain` · `FAISS` · `Streamlit`

---
*Built for curious minds who'd rather read than watch.*
        """
    )


# ── Helpers ───────────────────────────────────────────────────────────────────
def run_pipeline(source: str):
    """source can be a URL or a local file path."""
    chunks = process_input(source)
    caption = transcript_extraction(chunks)
    summ = summary(caption)
    heading = title(summ)
    st.session_state.caption = caption
    st.session_state.summary_text = summ
    st.session_state.title_text = heading
    st.session_state.pipeline_done = True
    st.session_state.rag_ready = False
    st.session_state.chat_history = []


def ensure_rag_ready():
    if not st.session_state.rag_ready:
        with st.spinner("Indexing transcript for Q&A — one moment…"):
            retrieve(st.session_state.caption, "__init__")
        st.session_state.rag_ready = True


def ask_question(question: str) -> str:
    ensure_rag_ready()
    return retrieve(st.session_state.caption, question)


def reset_state():
    for key in ("caption", "summary_text", "title_text"):
        st.session_state[key] = ""
    st.session_state.pipeline_done = False
    st.session_state.rag_ready = False
    st.session_state.chat_history = []


# ── Main UI ───────────────────────────────────────────────────────────────────
st.title("🎬 YT Insight")
st.caption("YouTube link or local file · Get a summary · Chat with the content")

st.divider()

# ── Input · tabs for URL vs file upload ──────────────────────────────────────
tab_url, tab_file = st.tabs(["🔗  YouTube URL", "📁  Upload File"])

source = None
submitted = False

with tab_url:
    with st.form("url_form", clear_on_submit=False):
        url_input = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
            label_visibility="collapsed",
        )
        url_submitted = st.form_submit_button(
            "▶  Analyse Video", use_container_width=True, type="primary"
        )
    if url_submitted:
        if not url_input.strip():
            st.warning("⚠️ Please paste a YouTube URL first.")
        else:
            source = url_input.strip()
            submitted = True

with tab_file:
    uploaded_file = st.file_uploader(
        "Upload an audio or video file",
        type=["mp3", "mp4", "wav", "m4a", "ogg", "flac", "webm", "mkv", "avi"],
        label_visibility="collapsed",
    )
    file_submitted = st.button(
        "▶  Analyse File", use_container_width=True, type="primary",
        disabled=(uploaded_file is None),
    )
    if file_submitted and uploaded_file:
        # Save to a temp file so process_input() gets a real path
        suffix = os.path.splitext(uploaded_file.name)[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.read())
            source = tmp.name
        submitted = True

# ── Run pipeline ──────────────────────────────────────────────────────────────
if submitted and source:
    with st.spinner("Processing audio — this may take a minute…"):
        try:
            run_pipeline(source)
        except Exception as e:
            st.error(f"Pipeline failed: {e}")
            st.stop()
    st.success("✅ Done! Summary is ready below.")

# ── Summary ───────────────────────────────────────────────────────────────────
if st.session_state.pipeline_done:

    st.divider()

    col_icon, col_heading = st.columns([0.05, 0.95])
    with col_icon:
        st.markdown("### 📝")
    with col_heading:
        st.markdown(f"### {st.session_state.title_text}")

    st.info(st.session_state.summary_text, icon="💡")

    with st.expander("📄 Full transcript"):
        st.text_area(
            "transcript",
            value=st.session_state.caption,
            height=240,
            disabled=True,
            label_visibility="collapsed",
        )

    # ── Q&A ───────────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 💬 Ask anything about the content")
    st.caption(
        "Answers are retrieval-augmented — grounded in the actual transcript. "
        "The index is built on your first question."
    )

    for msg in st.session_state.chat_history:
        avatar = "🧑" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])

    user_q = st.chat_input("Type your question here…")
    if user_q:
        st.session_state.chat_history.append({"role": "user", "content": user_q})
        with st.chat_message("user", avatar="🧑"):
            st.write(user_q)
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Searching transcript…"):
                try:
                    answer = ask_question(user_q)
                except Exception as e:
                    answer = f"Sorry, something went wrong: {e}"
            st.write(answer)
            st.session_state.chat_history.append(
                {"role": "assistant", "content": answer}
            )

    st.divider()
    if st.button("🔄  Analyse another video / file", use_container_width=True):
        reset_state()
        st.rerun()