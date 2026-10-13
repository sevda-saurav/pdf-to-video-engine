import os
from pathlib import Path
from typing import List, Tuple, Union

import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
    concatenate_videoclips,
)
from moviepy.audio.fx.all import audio_loop

class VideoEngine:
    @classmethod
    def create_beat_clip(
        cls,
        image_path: str,
        audio_path: str,
        duration: float,
    ) -> CompositeVideoClip:
        """
        Creates a beat clip with subtle 2% Ken Burns zoom pinned inside a 1920x1080 canvas.
        Formula:
          clip = ImageClip(image_path).set_duration(duration)
          clip = clip.resize(lambda t: 1.0 + 0.02 * (t / duration))
          CompositeVideoClip([clip.set_position("center")], size=(1920, 1080))
        """
        duration = max(0.1, duration)
        base_clip = ImageClip(str(image_path)).set_duration(duration)
        zoomed_clip = base_clip.resize(lambda t: 1.0 + 0.02 * (t / duration))
        comp_clip = CompositeVideoClip(
            [zoomed_clip.set_position("center")],
            size=(1920, 1080)
        ).set_duration(duration)

        if os.path.isfile(audio_path):
            audio_clip = AudioFileClip(str(audio_path))
            comp_clip = comp_clip.set_audio(audio_clip)

        return comp_clip

    @classmethod
    def create_animated_beat_clip(
        cls,
        frame_paths: Union[str, List[str]],
        audio_path: str,
        duration: float,
    ):
        """
        Creates a beat clip from one or more frame paths, applying a subtle 2% centered
        Ken Burns zoom and attaching the beat narration audio track.
        """
        if isinstance(frame_paths, str):
            frame_list = [frame_paths]
        else:
            frame_list = frame_paths or []

        if not frame_list:
            raise ValueError("No frame paths provided for beat clip creation.")

        if len(frame_list) == 1:
            return cls.create_beat_clip(frame_list[0], audio_path, duration)

        sub_duration = max(0.1, duration / len(frame_list))
        frame_clips = []
        for frame_path in frame_list:
            base_clip = ImageClip(str(frame_path)).set_duration(sub_duration)
            zoomed_clip = base_clip.resize(lambda t: 1.0 + 0.02 * (t / sub_duration))
            comp_clip = CompositeVideoClip(
                [zoomed_clip.set_position("center")],
                size=(1920, 1080)
            ).set_duration(sub_duration)
            frame_clips.append(comp_clip)

        beat_video = concatenate_videoclips(frame_clips, method="compose")
        if os.path.isfile(audio_path):
            audio_clip = AudioFileClip(str(audio_path))
            beat_video = beat_video.set_audio(audio_clip)

        return beat_video

    @classmethod
    def build_video(
        cls,
        beats_data: List[Union[Tuple[Union[str, List[str]], str, float], Tuple[str, str, float]]],
        output_path: str = "data/output/final_video.mp4",
        bg_music_path: str = "data/ambient_music.mp3",
    ) -> str:
        """
        Assembles beat clips into a 16:9 widescreen MP4 video:
        - Applies subtle Ken Burns zoom per beat clip.
        - Uses immediate cuts between beats (no black fading).
        - Attaches beat audio tracks.
        - Mixes background ambient music at 6% volume (.volumex(0.06)) if available.
        - Renders to output_path at 1920x1080, 24 fps.
        """
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        clips = []

        for item in beats_data:
            frame_paths, audio_path, duration = item
            clip = cls.create_animated_beat_clip(frame_paths, audio_path, duration)
            clips.append(clip)

        # Immediate cuts between beats (no black fading)
        final_clip = concatenate_videoclips(clips, method="compose")

        # Mix background ambient music at 6% volume if file exists
        bg_music_file = Path(bg_music_path)
        if bg_music_file.is_file():
            try:
                bg_music = AudioFileClip(str(bg_music_file))
                if bg_music.duration < final_clip.duration:
                    bg_music = audio_loop(bg_music, duration=final_clip.duration)
                else:
                    bg_music = bg_music.subclip(0, final_clip.duration)
                bg_music = bg_music.volumex(0.06)

                if final_clip.audio is not None:
                    final_audio = CompositeAudioClip([final_clip.audio, bg_music])
                else:
                    final_audio = bg_music
                final_clip = final_clip.set_audio(final_audio)
            except Exception as e:
                print(f"[!] Warning: Could not mix background music: {e}")

        final_clip.write_videofile(
            str(out_file),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            preset="fast"
        )
        return str(out_file)