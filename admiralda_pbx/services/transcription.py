from typing import AsyncGenerator

class TranscriptionEngine:
    """
    SULTHANA Persona: Real-time Transcription Pipeline.
    """
    async def stream(self, audio_chunks: bytes) -> AsyncGenerator[str, None]:
        # Mocking the progression of a call
        yield "Hello, this is SALA Resort."
        yield "I am calling to confirm my booking."
        yield "Yes, please go ahead and lock it."

transcription_engine = TranscriptionEngine()
