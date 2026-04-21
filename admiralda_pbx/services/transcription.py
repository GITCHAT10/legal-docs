from typing import AsyncGenerator

class TranscriptionEngine:
    """
    SULTHANA Persona: Multilingual Transcription.
    """
    async def stream(self, audio_chunks: bytes, language: str = "en-US") -> AsyncGenerator[str, None]:
        # Mocking the progression based on language
        if language == "dv-MV":
             yield "Assalaamu Alaikum."
             yield "Mee SULTHANA."
        else:
             yield "Hello, this is SULTHANA."
             yield "I am processing your request."

transcription_engine = TranscriptionEngine()
