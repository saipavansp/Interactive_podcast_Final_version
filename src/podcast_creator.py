import streamlit as st
from dataclasses import dataclass
from typing import Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor
import io
from gtts import gTTS

@dataclass
class PodcastResponse:
    """Data class for podcast response."""
    text_answer: str
    podcast_script: Optional[str]
    audio: Optional[bytes]
    error: Optional[str] = None

class AudioProcessor:
    """Handles text-to-speech conversion with audio concatenation."""

    def __init__(self):
        self._audio_cache = {}

    def get_audio(self, text: str, lang: str) -> Tuple[Optional[bytes], str]:
        """Get audio with caching."""
        if not text.strip():
            return None, ""

        cache_key = f"{text}:{lang}"
        if cache_key in self._audio_cache:
            return self._audio_cache[cache_key], ""

        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_data = audio_buffer.getvalue()

            self._audio_cache[cache_key] = audio_data
            return audio_data, ""
        except Exception as e:
            return None, str(e)

    @staticmethod
    def concatenate_audio_files(audio_segments: List[bytes]) -> bytes:
        """Concatenate multiple audio segments into a single audio stream."""
        return b''.join(audio_segments)

class PodcastCreator:
    def __init__(self):
        """Initialize podcast creator."""
        self.audio_processor = AudioProcessor()
        self.executor = ThreadPoolExecutor(max_workers=2)

    def clean_script(self, script: str) -> List[tuple]:
        """Process script into speaker-text pairs."""
        segments = []
        for line in script.split('\n'):
            if ':' in line:
                speaker, text = line.split(':', 1)
                segments.append((speaker.strip(), text.strip()))
        return segments

    def process_segment(self, speaker: str, text: str) -> Optional[bytes]:
        """Process a single conversation segment."""
        lang = 'en'
        audio_data, error = self.audio_processor.get_audio(text, lang)

        if error:
            st.error(f"Error processing segment: {error}")
            return None

        return audio_data

    def create_podcast(self, script: str) -> Optional[bytes]:
        """Create podcast with natural conversation flow."""
        try:
            segments = self.clean_script(script)
            if not segments:
                return None

            audio_segments = []
            for speaker, text in segments:
                audio_data = self.process_segment(speaker, text)
                if audio_data:
                    audio_segments.append(audio_data)

            if not audio_segments:
                return None

            return self.audio_processor.concatenate_audio_files(audio_segments)

        except Exception as e:
            st.error(f"Podcast creation error: {str(e)}")
            return None

    def process_answer(self, text_answer: str, podcast_script: Optional[str]) -> PodcastResponse:
        """Generate podcast response with progress tracking."""
        try:
            if not podcast_script:
                return PodcastResponse(
                    text_answer=text_answer,
                    podcast_script=None,
                    audio=None
                )

            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("Preparing script...")
            progress_bar.progress(0.2)

            status_text.text("Generating audio...")
            audio = self.create_podcast(podcast_script)
            progress_bar.progress(0.8)

            status_text.text("Finalizing podcast...")
            progress_bar.progress(1.0)

            progress_bar.empty()
            status_text.empty()

            return PodcastResponse(
                text_answer=text_answer,
                podcast_script=podcast_script,
                audio=audio
            )

        except Exception as e:
            return PodcastResponse(
                text_answer=text_answer,
                podcast_script=None,
                audio=None,
                error=str(e)
            )

    def __del__(self):
        """Cleanup resources."""
        self.executor.shutdown(wait=False)
