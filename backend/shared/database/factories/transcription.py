from shared.database.factories.base import BaseFactory
from shared.database.models import Transcription


class TranscriptionFactory(BaseFactory[Transcription]):
    def __init__(self, db):
        super().__init__(model=Transcription, db=db)

    def get_default_attributes(self):
        return {
            "content": self.faker.paragraph(nb_sentences=100),
            "metadata": {"whisper_model": "medium", "language": "en"},
        }
