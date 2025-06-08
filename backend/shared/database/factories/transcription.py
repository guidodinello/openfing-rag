from shared.database.factories.base import BaseFactory
from shared.database.models.rag.transcription import Transcription
from transcriber.schemas.enums import WhisperModelLanguage, WhisperModelSize


class TranscriptionFactory(BaseFactory[Transcription]):
    def __init__(self, db):
        super().__init__(model=Transcription, db=db)

    def get_default_attributes(self):
        model_size = self.faker.random_element(elements=list(WhisperModelSize))
        language = self.faker.random_element(elements=list(WhisperModelLanguage))

        course_code = self.faker.lexify(text="????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        lesson_number = self.faker.random_int(min=1, max=20)
        file_extension = self.faker.random_element(elements=[".mp3", ".m4a", ".wav", ".mp4"])

        duration_seconds = self.faker.random.uniform(1800, 7200)

        content_text = self.faker.paragraph(nb_sentences=100)

        metadata = {
            "asr_model": "whisper",
            "asr_model_size": model_size.value,
            "asr_language": language.value,
            "duration_seconds": duration_seconds,
            "segments_count": int(duration_seconds / 10),
            "content_length": len(content_text),
            "processing_time": duration_seconds * self.faker.random.uniform(0.1, 0.3),
            "source_file": f"./audios/{course_code}/{course_code}_{lesson_number:02d}{file_extension}",
            "file_size_bytes": int((duration_seconds / 60) * self.faker.random.uniform(100000, 500000)),
            "vectorized": False,
            "embedding_model": None,
            "created_by": "transcription_factory",
        }

        return {
            "content": content_text,
            "transcription_metadata": metadata,
        }
