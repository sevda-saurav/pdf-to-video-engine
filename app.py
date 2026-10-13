import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
import streamlit as st

from src.extractor import PDFExtractor
from src.director import DirectorAgent
from src.audio_engine import AudioEngine
from src.visual_engine import VisualEngine
from src.video_engine import VideoEngine
from src.schemas import Storyboard, Beat

# --- Page Configuration ---
st.set_page_config(
    page_title="Autonomous PDF-to-Video Engine",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Path Constants ---
UPLOAD_PDF_PATH = "data/input/uploaded.pdf"
SAMPLE_PDF_PATH = "data/input/sample.pdf"
OUTPUT_VIDEO_PATH = "data/output/final_video.mp4"
OUTPUT_STORYBOARD_PATH = "data/output/storyboard.json"
TEMP_DIR = Path("data/temp")
AMBIENT_MUSIC_PATH = "data/ambient_music.mp3"

VOICE_MAP = {
    "Christopher (US Male - Professional)": "en-US-ChristopherNeural",
    "Jenny (US Female - Natural)": "en-US-JennyNeural",
    "Guy (US Male - Casual)": "en-US-GuyNeural",
    "Sonia (UK Female - Clear)": "en-GB-SoniaNeural",
}

# --- Custom Styling: Deep Slate #060913 + Cyan Accent Glow ---
CUSTOM_CSS = """
<style>
/* Global App Canvas */
.stApp {
    background-color: #060913 !important;
    color: #f1f5f9 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* Hide Streamlit default clutter */
header[data-testid="stHeader"] {
    background: transparent !important;
}
.stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] {
    display: none !important;
    visibility: hidden !important;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: #080d1a !important;
    border-right: 1px solid #1e293b !important;
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem !important;
}

/* File Uploader styling */
[data-testid="stFileUploader"] section,
[data-testid="stFileUploaderDropzone"] {
    background-color: #0f172a !important;
    border: 1px dashed rgba(56, 189, 248, 0.4) !important;
    border-radius: 12px !important;
    color: #cbd5e1 !important;
    transition: all 0.2s ease;
}
[data-testid="stFileUploaderDropzone"] * {
    background-color: transparent !important;
    color: #cbd5e1 !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background: #1e293b !important;
    color: #38bdf8 !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #22d3ee !important;
    box-shadow: 0 0 15px rgba(6, 182, 212, 0.15) !important;
}

/* Glassmorphic Containers */
.engine-card {
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(51, 65, 85, 0.65);
    border-radius: 16px;
    padding: 1.75rem;
    backdrop-filter: blur(16px);
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.7);
    margin-bottom: 1.5rem;
    transition: all 0.25s ease-in-out;
}
.engine-card:hover {
    border-color: rgba(34, 211, 238, 0.45);
    box-shadow: 0 14px 35px -8px rgba(6, 182, 212, 0.2);
}

/* Header typography */
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.85rem;
    background: rgba(6, 182, 212, 0.12);
    border: 1px solid rgba(34, 211, 238, 0.35);
    border-radius: 9999px;
    color: #22d3ee;
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
}

.hero-title {
    font-size: 2.6rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.15;
    background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}

.hero-subtitle {
    color: #94a3b8;
    font-size: 1.05rem;
    line-height: 1.55;
    max-width: 840px;
    margin-bottom: 0.5rem;
}

/* Storyboard Beat Card */
.beat-card {
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(51, 65, 85, 0.75);
    border-radius: 14px;
    padding: 1.35rem;
    margin-bottom: 1.15rem;
    border-left: 4px solid #22d3ee;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.beat-card:hover {
    transform: translateY(-2px);
    border-color: #22d3ee;
}

.beat-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.65rem;
}

.beat-tag {
    display: inline-block;
    padding: 0.25rem 0.65rem;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    border-radius: 6px;
    background: rgba(34, 211, 238, 0.15);
    color: #22d3ee;
    border: 1px solid rgba(34, 211, 238, 0.35);
}

.beat-archetype-tag {
    display: inline-block;
    padding: 0.25rem 0.65rem;
    font-size: 0.72rem;
    font-weight: 600;
    border-radius: 6px;
    background: rgba(99, 102, 241, 0.18);
    color: #a5b4fc;
    border: 1px solid rgba(99, 102, 241, 0.35);
    margin-left: 0.4rem;
}

.beat-title-text {
    font-size: 1.25rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.35rem;
}

.narration-box {
    background: rgba(3, 7, 18, 0.65);
    border: 1px dashed rgba(51, 65, 85, 0.9);
    border-radius: 10px;
    padding: 0.95rem 1.1rem;
    margin-top: 0.75rem;
    font-size: 0.93rem;
    line-height: 1.6;
    color: #e2e8f0;
}

.narration-label {
    font-weight: 700;
    color: #22d3ee;
    font-size: 0.75rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    display: block;
    margin-bottom: 0.35rem;
}

/* Primary Action Button */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0284c7 0%, #06b6d4 100%) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 1.25rem !important;
    box-shadow: 0 4px 18px rgba(6, 182, 212, 0.35) !important;
    transition: all 0.25s ease !important;
}
div.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #0369a1 0%, #0891b2 100%) !important;
    box-shadow: 0 6px 24px rgba(6, 182, 212, 0.55) !important;
    transform: translateY(-1px) !important;
}

/* Download Button */
div.stDownloadButton > button {
    background: linear-gradient(135deg, #059669 0%, #06b6d4 100%) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 1.5rem !important;
    box-shadow: 0 4px 18px rgba(16, 185, 129, 0.35) !important;
    transition: all 0.25s ease !important;
}
div.stDownloadButton > button:hover {
    background: linear-gradient(135deg, #047857 0%, #0891b2 100%) !important;
    box-shadow: 0 6px 24px rgba(16, 185, 129, 0.55) !important;
    transform: translateY(-1px) !important;
}

/* Expander Styling */
[data-testid="stExpander"] {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid rgba(51, 65, 85, 0.8) !important;
    border-radius: 12px !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# --- Load Cached Storyboard if Exists ---
def load_persisted_storyboard() -> Optional[Storyboard]:
    if os.path.isfile(OUTPUT_STORYBOARD_PATH):
        try:
            with open(OUTPUT_STORYBOARD_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Storyboard.model_validate(data)
        except Exception:
            pass
    return None

def save_persisted_storyboard(storyboard: Storyboard):
    try:
        with open(OUTPUT_STORYBOARD_PATH, "w", encoding="utf-8") as f:
            f.write(storyboard.model_dump_json(indent=2))
    except Exception:
        pass


# --- Initialize Session State ---
if st.session_state.get("storyboard") is None:
    st.session_state["storyboard"] = load_persisted_storyboard()

if not st.session_state.get("video_path") and os.path.isfile(OUTPUT_VIDEO_PATH):
    st.session_state["video_path"] = OUTPUT_VIDEO_PATH


# --- Sidebar Controls ---
st.sidebar.markdown("""
<div style="display: flex; align-items: center; gap: 0.65rem; margin-bottom: 1.25rem;">
    <span style="font-size: 1.85rem;">🎬</span>
    <div>
        <h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: #f8fafc;">Studio Pipeline</h3>
        <p style="margin: 0; font-size: 0.78rem; color: #94a3b8;">Autonomous Synthesis Controls</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("### 1. Document Input")
uploaded_file = st.sidebar.file_uploader(
    "Upload PDF Document",
    type=["pdf"],
    help="Upload an academic, technical, or conceptual PDF document to transform into video.",
)

use_sample_fallback = False
if not uploaded_file and os.path.isfile(SAMPLE_PDF_PATH):
    use_sample_fallback = st.sidebar.checkbox(
        "Use sample PDF (sample.pdf)",
        value=True,
        help="Check this to test with the bundled sample PDF document.",
    )

st.sidebar.markdown("---")
st.sidebar.markdown("### 2. Audio & Visuals")

selected_voice_label = st.sidebar.selectbox(
    "Voice Selector",
    options=list(VOICE_MAP.keys()),
    index=0,
    help="High-fidelity neural voice for synchronous pedagogical narration.",
)
selected_voice = VOICE_MAP[selected_voice_label]

scene_count = st.sidebar.slider(
    "Scene Count (Beats)",
    min_value=3,
    max_value=6,
    value=5,
    step=1,
    help="Number of storytelling beats to extract and visualize (3 to 6).",
)

st.sidebar.markdown("---")
generate_clicked = st.sidebar.button(
    "🚀 Generate Video",
    type="primary",
    use_container_width=True,
    help="Execute the full autonomous extraction, storyboarding, synthesis, and assembly pipeline.",
)


# --- Asynchronous Synthesis Pipeline Runner ---
async def execute_async_pipeline(
    pdf_source: str,
    voice_key: str,
    beats_num: int,
    status_box,
    progress_bar,
) -> Tuple[Storyboard, str]:
    """Executes the 4-phase PDF-to-Video synthesis pipeline asynchronously."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    Path("data/output").mkdir(parents=True, exist_ok=True)

    # Phase 1: Extract PDF text via PyMuPDF
    status_box.write("📄 **Phase 1/4:** Extracting PDF text via PyMuPDF...")
    document_text = PDFExtractor.extract_text(pdf_source)
    status_box.write(f"✓ Extracted **{len(document_text):,}** characters of context from document.")
    progress_bar.progress(15)

    # Phase 2: Pedagogical Storyboarding with Gemini 2.5 Flash
    status_box.write(f"🧠 **Phase 2/4:** Generating pedagogical storyboard with Gemini 2.5 Flash ({beats_num} beats)...")
    director = DirectorAgent()
    storyboard: Storyboard = director.create_storyboard(document_text, beat_count=beats_num)
    status_box.write(f"✓ Storyboard created: **{storyboard.project_title}** (*{len(storyboard.beats)} beats*)")
    save_persisted_storyboard(storyboard)
    progress_bar.progress(35)

    # Phase 3: Beat-by-beat voiceover and frame rendering
    status_box.write("🎙️ **Phase 3/4:** Synthesizing voiceover beats and rendering visual snapshots...")
    beats_data = []
    total_beats = len(storyboard.beats)

    for idx, beat in enumerate(storyboard.beats):
        beat_audio_path = str(TEMP_DIR / f"beat_{beat.beat_id}.mp3")
        status_box.write(
            f"  • *Beat {beat.beat_id}/{total_beats}:* '{beat.title}' "
            f"[{beat.visual_type.replace('_', ' ').upper()} • mascot: {beat.mascot_pose}]"
        )

        # Synthesize narration audio via Edge-TTS
        raw_dur = await AudioEngine.synthesize_beat_audio(
            narration_text=beat.narration,
            output_path=beat_audio_path,
            voice=voice_key,
        )
        padded_dur = AudioEngine.add_silence_padding(raw_dur, padding_sec=0.25)

        # Render 16:9 canvas slides with Playwright
        frame_paths = await VisualEngine.render_beat_states_async(beat, TEMP_DIR)
        beats_data.append((frame_paths, beat_audio_path, padded_dur))

        # Smooth dynamic progress calculation (35% to 80%)
        curr_prog = int(35 + (idx + 1) / total_beats * 45)
        progress_bar.progress(curr_prog)

    status_box.write("✓ Voiceover synthesis and visual snapshots complete.")

    # Phase 4: Stitch video timeline with MoviePy
    status_box.write("🎬 **Phase 4/4:** Stitching video timeline with MoviePy (Ken Burns 2% zoom & ambient audio)...")
    progress_bar.progress(85)
    VideoEngine.build_video(
        beats_data=beats_data,
        output_path=OUTPUT_VIDEO_PATH,
        bg_music_path=AMBIENT_MUSIC_PATH,
    )
    progress_bar.progress(100)
    status_box.write("✓ Final video composition and AAC encoding finished.")

    return storyboard, OUTPUT_VIDEO_PATH


# --- Main Application Page Layout ---
# Header
st.markdown("""
<div class="engine-card">
    <div class="hero-badge">⚡ AI-POWERED MULTIMODAL PRODUCTION</div>
    <h1 class="hero-title">Autonomous PDF-to-Video Engine</h1>
    <p class="hero-subtitle">
        Turn complex academic papers and technical documentation into high-retention 16:9 explainer videos 
        featuring pedagogical visual archetypes, animated mascot guides, and neural voiceovers.
    </p>
</div>
""", unsafe_allow_html=True)

# Trigger Video Generation if Requested
if generate_clicked:
    active_pdf_path = None
    if uploaded_file is not None:
        Path("data/input").mkdir(parents=True, exist_ok=True)
        with open(UPLOAD_PDF_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
        active_pdf_path = UPLOAD_PDF_PATH
    elif use_sample_fallback and os.path.isfile(SAMPLE_PDF_PATH):
        active_pdf_path = SAMPLE_PDF_PATH
    else:
        st.error("⚠️ Please upload a PDF document in the sidebar to begin video generation.")
        st.stop()

    st.markdown("### 🔄 Generation Pipeline In Progress")
    progress_bar = st.progress(5)

    with st.status("Executing Autonomous Video Pipeline...", expanded=True) as status_box:
        try:
            storyboard_res, video_path_res = asyncio.run(
                execute_async_pipeline(
                    pdf_source=active_pdf_path,
                    voice_key=selected_voice,
                    beats_num=scene_count,
                    status_box=status_box,
                    progress_bar=progress_bar,
                )
            )
            st.session_state["storyboard"] = storyboard_res
            st.session_state["video_path"] = video_path_res

            status_box.update(
                label="🎉 Video Generation Complete!",
                state="complete",
                expanded=False,
            )
            st.toast("Video generated successfully!", icon="🎬")
            st.success("✨ Your video has been assembled and exported in 1080p MP4 format!")

        except Exception as e:
            status_box.update(
                label=f"❌ Error during generation: {str(e)}",
                state="error",
                expanded=True,
            )
            st.error(f"Pipeline failed: {e}")
            st.exception(e)


# --- Output Showcase Section ---
video_to_show = st.session_state.get("video_path")
storyboard_data = st.session_state.get("storyboard")

if video_to_show and os.path.isfile(video_to_show):
    st.markdown("---")
    st.markdown("### 🎥 Generated Explainer Video")

    col_video, col_info = st.columns([8, 4])

    with col_video:
        st.video(video_to_show)

        with open(video_to_show, "rb") as vf:
            video_bytes = vf.read()

        file_size_mb = len(video_bytes) / (1024 * 1024)
        st.download_button(
            label=f"⬇️ Download Video ({file_size_mb:.1f} MB • 1080p MP4)",
            data=video_bytes,
            file_name="autonomous_explainer_video.mp4",
            mime="video/mp4",
            use_container_width=True,
            type="primary",
        )

    with col_info:
        st.markdown("""
        <div class="engine-card" style="margin-bottom: 0;">
            <h4 style="margin: 0 0 0.75rem 0; color: #38bdf8; font-size: 1.1rem; font-weight: 700;">Production Specs</h4>
            <div style="font-size: 0.92rem; line-height: 2; color: #cbd5e1;">
                <div>📐 <b>Resolution:</b> 1920 × 1080 (16:9 Full HD)</div>
                <div>🎞️ <b>Framerate:</b> 24 FPS (Cinematic)</div>
                <div>🎨 <b>Motion:</b> 2% Centered Ken Burns Zoom</div>
                <div>🎙️ <b>Voice:</b> Edge-TTS Neural Synthesis</div>
                <div>🎵 <b>Soundtrack:</b> Ambient Bed (6% Looped)</div>
                <div>🤖 <b>Presenter:</b> Dynamic Mascot Stage</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Storyboard Breakdown Expander
    if storyboard_data and hasattr(storyboard_data, "beats"):
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        with st.expander("📋 Storyboard Breakdown & Narration Script", expanded=True):
            st.markdown(f"#### **Topic:** {storyboard_data.project_title}")
            st.caption(f"**Overarching Analogy:** {storyboard_data.topic_analogy}")

            for beat in storyboard_data.beats:
                bullets_html = "".join([f"<li style='margin-bottom: 0.35rem;'>{pt}</li>" for pt in beat.on_screen_points])

                component_html = ""
                cards = getattr(beat, "visual_cards", None) or []
                if beat.visual_type == "comparison_matrix" and cards:
                    items_html = "".join([
                        f"<div style='border: 1px solid rgba(56,189,248,0.35); background: rgba(15,23,42,0.9); border-radius: 8px; padding: 0.5rem 0.75rem;'>"
                        f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.25rem;'>"
                        f"<span style='font-size: 0.7rem; font-family: monospace; font-weight: 800; color: #38bdf8; background: rgba(34,211,238,0.15); padding: 0.1rem 0.4rem; border-radius: 4px;'>{c.badge}</span>"
                        f"<span style='font-size: 0.65rem; color: #94a3b8; font-family: monospace;'>● {c.accent_color}</span>"
                        f"</div>"
                        f"<div style='font-weight: 700; font-size: 0.82rem; color: #ffffff;'>{c.title}</div>"
                        f"<div style='font-size: 0.74rem; color: #cbd5e1; margin-top: 0.15rem;'>{c.description}</div>"
                        f"</div>"
                        for c in cards
                    ])
                    component_html = f"<div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem; margin: 0.6rem 0;'>{items_html}</div>"
                elif beat.visual_type == "pipeline_flow" and cards:
                    steps_html = "".join([
                        f"<div style='display: flex; align-items: center; gap: 0.75rem; background: rgba(15,23,42,0.9); border: 1px solid rgba(56,189,248,0.3); border-radius: 8px; padding: 0.45rem 0.75rem; margin-bottom: 0.35rem;'>"
                        f"<span style='font-family: monospace; font-weight: 900; color: #38bdf8; font-size: 0.9rem; background: rgba(34,211,238,0.15); padding: 0.2rem 0.45rem; border-radius: 6px;'>{c.badge}</span>"
                        f"<div style='min-width: 0;'><div style='font-weight: 700; font-size: 0.82rem; color: #ffffff;'>{c.title}</div>"
                        f"<div style='font-size: 0.74rem; color: #94a3b8;'>{c.description}</div></div>"
                        f"</div>"
                        for c in cards
                    ])
                    component_html = f"<div style='margin: 0.6rem 0;'>{steps_html}</div>"
                elif beat.visual_type == "metaphor_illustration" and cards:
                    meta_html = "".join([
                        f"<div style='background: rgba(15,23,42,0.9); border-left: 3px solid rgba(56,189,248,0.5); padding: 0.5rem 0.75rem; border-radius: 6px; margin-bottom: 0.35rem;'>"
                        f"<span style='font-size: 0.7rem; font-family: monospace; font-weight: 800; color: #38bdf8;'>{c.badge}:</span> <b style='color:#f8fafc; font-size:0.82rem;'>{c.title}</b>"
                        f"<div style='font-size: 0.76rem; color: #cbd5e1; margin-top: 0.15rem; font-style: italic;'>“{c.description}”</div>"
                        f"</div>"
                        for c in cards
                    ])
                    component_html = f"<div style='margin: 0.6rem 0;'>{meta_html}</div>"
                elif getattr(beat, "code_snippet", ""):
                    lang = getattr(beat, "code_language", "python")
                    component_html = (
                        f"<div style='margin: 0.6rem 0;'>"
                        f"<div style='display:flex; justify-content:space-between; background: #0b1120; padding: 0.3rem 0.75rem; border-top-left-radius: 8px; border-top-right-radius: 8px; font-size: 0.72rem; font-family: monospace; color: #94a3b8; border: 1px solid #1e293b; border-bottom: none;'>"
                        f"<span>📄 pipeline.{lang}</span><span style='color: #10b981;'>● {lang.upper()}</span></div>"
                        f"<pre style='background: #020617; padding: 0.75rem; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; font-size: 0.82rem; color: #38bdf8; border: 1px solid #1e293b; margin: 0; overflow-x: auto;'><code>{beat.code_snippet}</code></pre>"
                        f"</div>"
                    )

                card_html = f"""<div class="beat-card">
<div class="beat-header-row">
<div>
<span class="beat-tag">BEAT {beat.beat_id:02d} • {beat.category_badge}</span>
<span class="beat-archetype-tag">{beat.visual_type.replace('_', ' ').upper()}</span>
</div>
<span style="font-size: 0.82rem; color: #94a3b8;">Mascot Pose: <b style="color: #f1f5f9;">{beat.mascot_pose}</b></span>
</div>
<div class="beat-title-text">{beat.title}</div>
<div style="font-size: 0.88rem; color: #94a3b8; margin-bottom: 0.6rem;">
<span style="background: rgba(34, 211, 238, 0.12); color: #38bdf8; padding: 0.15rem 0.55rem; border-radius: 4px; font-weight: 600;">{beat.caption_pill}</span>
&nbsp;•&nbsp; Visual Card: <b style="color: #cbd5e1;">{beat.visual_title}</b>
</div>
<ul style="color: #cbd5e1; font-size: 0.92rem; margin-bottom: 0.5rem; padding-left: 1.25rem;">
{bullets_html}
</ul>
{component_html}
<div class="narration-box">
<span class="narration-label">🎙️ Voiceover Script (Pedagogical 2-Part Formula):</span>
{beat.narration}
</div>
</div>"""
                st.markdown(card_html, unsafe_allow_html=True)

else:
    # If no video has been generated yet, show a welcome preview card
    st.markdown("""
    <div class="engine-card" style="text-align: center; padding: 3rem 1.5rem;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">📄 ➔ 🎬</div>
        <h3 style="margin-bottom: 0.5rem; color: #f8fafc;">Ready to Synthesize Your PDF</h3>
        <p style="color: #94a3b8; max-width: 580px; margin: 0 auto 1.5rem auto; font-size: 0.95rem;">
            Upload your technical documentation or paper in the sidebar and choose your preferred voiceover 
            and scene count to generate an interactive 16:9 explainer video.
        </p>
    </div>
    """, unsafe_allow_html=True)
