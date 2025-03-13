# poc/main.py
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import whisper
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.pgvector import PGVector
from prefect import flow, task
from sqlalchemy import create_engine, text

# Configuración básica
CONNECTION_STRING = "postgresql+psycopg2://user:pass@localhost:5432/db"
COLLECTION_NAME = "computacion_1"


class TranscriptionProcessor:
    def __init__(self):
        self.model = whisper.load_model("base")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def transcribe(self, audio_path: str) -> dict:
        """Transcribe audio and return text with metadata"""
        result = self.model.transcribe(audio_path)

        return {
            "text": result["text"],
            "segments": result["segments"],
            "metadata": {
                "source": Path(audio_path).name,
                "date_processed": datetime.now().isoformat(),
                "model": "whisper-base",
            },
        }

    def chunk_text(self, transcription: dict) -> list[dict]:
        """Split transcription into chunks with metadata"""
        texts = self.text_splitter.split_text(transcription["text"])

        chunks = []
        for i, text in enumerate(texts):
            chunks.append(
                {
                    "text": text,
                    "metadata": {
                        **transcription["metadata"],
                        "chunk_id": i,
                    },
                }
            )
        return chunks


class VectorStore:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/multi-qa-mpnet-base-dot-v1"
        )
        self.store = PGVector(
            connection_string=CONNECTION_STRING,
            collection_name=COLLECTION_NAME,
            embedding_function=self.embeddings,
        )

    def add_texts(self, chunks: List[Dict]):
        """Add text chunks to vector store"""
        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        self.store.add_texts(texts=texts, metadatas=metadatas)

    def get_retriever(self, k: int = 4):
        """Get retriever for QA"""
        return self.store.as_retriever(search_type="similarity", search_kwargs={"k": k})


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


@task
def process_video(video_path: str, processor: TranscriptionProcessor) -> Dict:
    """Process a single video file"""
    logging.info(f"Processing video: {video_path}")
    return processor.transcribe(video_path)


@task
def save_and_vectorize(
    transcription: Dict,
    processor: TranscriptionProcessor,
    db: DatabaseManager,
    vector_store: VectorStore,
):
    """Save transcription and update vector store"""
    # Save raw transcription
    db.save_transcription(transcription)

    # Chunk and vectorize
    chunks = processor.chunk_text(transcription)
    vector_store.add_texts(chunks)


@flow(name="process_new_video")
def process_new_video_flow(video_path: str):
    """Main flow for processing a new video"""
    # Initialize components
    processor = TranscriptionProcessor()
    db = DatabaseManager()
    vector_store = VectorStore()

    # Process video
    transcription = process_video(video_path, processor)

    # Save and vectorize
    save_and_vectorize(transcription, processor, db, vector_store)


def setup_qa_chain():
    """Setup QA chain for testing"""
    vector_store = VectorStore()

    # Define custom prompt
    prompt_template = """Utiliza el siguiente contexto para responder la pregunta.
    Si no sabes la respuesta, solo di que no tienes suficiente información.
    
    Contexto: {context}
    
    Pregunta: {question}
    
    Respuesta:"""

    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    # Create chain
    chain = RetrievalQA.from_chain_type(
        llm=OpenAI(),
        chain_type="stuff",
        retriever=vector_store.get_retriever(),
        chain_type_kwargs={"prompt": PROMPT},
    )

    return chain


def main():
    # 1. Process a sample video
    video_path = "sample/lecture1.mp4"
    process_new_video_flow(video_path)

    # 2. Test QA
    chain = setup_qa_chain()
    question = "¿Qué es una estructura de datos?"
    response = chain.run(question)
    print(f"Q: {question}\nA: {response}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
