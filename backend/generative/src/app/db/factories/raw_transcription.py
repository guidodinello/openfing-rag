from app.db.factories.base import BaseFactory
from app.models import RawTranscription


class RawTranscriptionFactory(BaseFactory[RawTranscription]):
    def __init__(self, db):
        super().__init__(model=RawTranscription, db=db)

    def get_default_attributes(self):
        return {
            "content": self.faker.paragraph(nb_sentences=3),
            "metadata": {},  # Empty dict as per server_default
        }
