import argparse
import asyncio
import os
import sys
from pathlib import Path
from src.extractor import PDFExtractor
from src.director import DirectorAgent
from src.audio_engine import AudioEngine
from src.visual_engine import VisualEngine
from src.video_engine import VideoEngine

DEFAULT_INPUT_PDF = "data/input/sample.pdf"
DEFAULT_OUTPUT_MP4 = "data/output/final_video.mp4"
DEFAULT_TEMP_DIR = Path("data/temp")
DEFAULT_BG_MUSIC = "data/ambient_music.mp3"
DEFAULT_VOICE = "en-US-ChristopherNeural"

async def run_pipeline(
    pdf_path: str,
    output_path: str,
    beat_count: int = 5,
    voice: str = DEFAULT_VOICE,
    temp_dir: Path = DEFAULT_TEMP_DIR,
    bg_music_path: str = DEFAULT_BG_MUSIC,
):
    pdf_path_obj = Path(pdf_path)
    if not pdf_path_obj.is_file():
        raise FileNotFoundError(f"Input PDF not found: {pdf_path}")

    temp_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Text extraction
    print(f"[*] Step 1: Extracting text from {pdf_path}...")
    document_text = PDFExtractor.extract_text(str(pdf_path_obj))

    # Step 2: Storyboard generation with Gemini 2.5
    print(f"[*] Step 2: Generating pedagogical storyboard ({beat_count} beats) using Gemini...")
    director = DirectorAgent()
    storyboard = director.create_storyboard(document_text, beat_count=beat_count)
    print(f"    Title: '{storyboard.project_title}'")
    print(f"    Analogy: '{storyboard.topic_analogy}' ({len(storyboard.beats)} beats generated)")

    # Step 3: Beat-by-beat audio-visual synthesis
    print("[*] Step 3: Synthesizing beat voiceovers and 16:9 mascot visual slides...")
    beats_data = []

    for beat in storyboard.beats:
        audio_file = str(temp_dir / f"beat_{beat.beat_id}.mp3")

        # Synthesize narration audio & measure exact duration
        raw_duration = await AudioEngine.synthesize_beat_audio(
            narration_text=beat.narration,
            output_path=audio_file,
            voice=voice,
        )
        padded_duration = AudioEngine.add_silence_padding(raw_duration, padding_sec=0.25)
        print(f"    Beat {beat.beat_id}: {padded_duration:.2f}s | Archetype: '{beat.visual_type}' | Pose: '{beat.mascot_pose}' | Title: '{beat.title}'")

        # Render 16:9 progressive frame slides (Entrance & Resolution) with mascot and dynamic visual
        frame_paths = await VisualEngine.render_beat_states_async(beat, temp_dir)

        beats_data.append((frame_paths, audio_file, padded_duration))

    # Step 4: Stitch final video
    print("[*] Step 4: Assembling beats into final 16:9 video...")
    VideoEngine.build_video(beats_data, output_path, bg_music_path=bg_music_path)
    print(f"[✓] Pipeline complete! Video saved to: {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Autonomous 16:9 Mascot-Driven PDF-to-Video Synthesis Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-i", "--input",
        dest="input_pdf",
        type=str,
        default=DEFAULT_INPUT_PDF,
        help="Path to the input PDF document",
    )
    parser.add_argument(
        "-o", "--output",
        dest="output_video",
        type=str,
        default=DEFAULT_OUTPUT_MP4,
        help="Path for the generated output MP4 video",
    )
    parser.add_argument(
        "-v", "--voice",
        dest="voice",
        type=str,
        default=DEFAULT_VOICE,
        help="Edge-TTS voice key to use for narration",
    )
    parser.add_argument(
        "-b", "--beats",
        dest="beat_count",
        type=int,
        default=5,
        help="Number of storytelling beats in the generated storyboard (default: 5)",
    )
    parser.add_argument(
        "--temp-dir",
        dest="temp_dir",
        type=str,
        default=str(DEFAULT_TEMP_DIR),
        help="Directory to store intermediate audio and slide assets",
    )
    parser.add_argument(
        "--bg-music",
        dest="bg_music",
        type=str,
        default=DEFAULT_BG_MUSIC,
        help="Path to background ambient music file",
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    input_path = Path(args.input_pdf)
    if not input_path.is_file():
        print(f"[!] Error: Input PDF file not found: '{args.input_pdf}'")
        sys.exit(1)

    asyncio.run(
        run_pipeline(
            pdf_path=str(input_path),
            output_path=args.output_video,
            beat_count=args.beat_count,
            voice=args.voice,
            temp_dir=Path(args.temp_dir),
            bg_music_path=args.bg_music,
        )
    )