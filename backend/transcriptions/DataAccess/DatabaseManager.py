from typing import Dict
from backend.transcriptions.Constants.Constants import CONNECTION_STRING
from sqlalchemy import create_engine, text
import json

class DatabaseManager:
    def __init__(self):
        self.engine = create_engine(CONNECTION_STRING)

    def save_transcription(self, transcription: Dict):
        """Save raw transcription to PostgreSQL"""
        with self.engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO transcriptions (source, content, metadata)
                    VALUES (:source, :content, :metadata)
                """),
                {
                    "source": transcription["metadata"]["source"],
                    "content": json.dumps(transcription["text"]),
                    "metadata": json.dumps(transcription["metadata"]),
                },
            )
            conn.commit()
