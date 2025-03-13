# app/database/factories/chunk.py
from app.core.config import get_settings
from app.models import Chunk

from tests.factories.base import BaseFactory

settings = get_settings()


class ChunkFactory(BaseFactory[Chunk]):
    def __init__(self, db):
        super().__init__(model=Chunk, db=db)

    def get_default_attributes(self):
        start_time = self.faker.random_int(min=0, max=3600)  # 1 hour max
        return {
            "content": self.faker.paragraph(nb_sentences=3),
            "start_time": start_time,
            "end_time": start_time + self.faker.random_int(min=10, max=30),
            "embedding": [0.0] * settings.EMBEDDINGS.DIMENSION,
        }
