import os
from pathlib import Path
from typing import Union
import edge_tts
from mutagen.mp3 import MP3

class AudioEngine:
    DEFAULT_VOICE = "en-US-ChristopherNeural"

    @classmethod
    async def synthesize_beat_audio(
        cls,
        narration_text: str,
        output_path: Union[str, Path],
        voice: str = DEFAULT_VOICE
    ) -> float:
        """
        Synthesizes beat narration text to an MP3 audio file using edge-tts
        and returns the exact duration in seconds.
        """
        path_obj = Path(output_path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        try:
            communicate = edge_tts.Communicate(narration_text, voice)
            await communicate.save(str(path_obj))
            duration = cls.get_audio_duration(str(path_obj))
            return duration
        except Exception as e:
            print(f"[!] AudioEngine Error synthesizing speech to '{output_path}': {e}")
            raise e

    @staticmethod
    def add_silence_padding(duration: float, padding_sec: float = 0.25) -> float:
        """Returns total beat duration including a slight natural pause to prevent word clipping."""
        return max(0.0, float(duration) + float(padding_sec))

    @classmethod
    async def synthesize_speech(
        cls, 
        text: str, 
        output_path: Union[str, Path], 
        voice: str = DEFAULT_VOICE
    ) -> str:
        """Synthesizes text to an MP3 audio file using edge-tts."""
        await cls.synthesize_beat_audio(text, output_path, voice=voice)
        return str(output_path)

    @classmethod
    def get_audio_duration(cls, file_path: Union[str, Path]) -> float:
        """Calculates precise audio runtime in seconds using mutagen."""
        audio = MP3(str(file_path))
        return float(audio.info.length)

    # Aliases
    synthesize = synthesize_speech
    generate_audio = synthesize_speech