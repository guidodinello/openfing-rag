from Logic.Procesor import Procesor
from fastapi import FastAPI, Response, status, HTTPException

app = FastAPI()
procesor = Procesor()

@app.get("/transcribe/{course_acronym}/{class_number}?model_size={model_size}", status_code=status.HTTP_200_OK)
async def get_transcription(course_acronym: str, class_number: str):
    isSuccesful, message = procesor.get_transcription(course_acronym, class_number)
    if not isSuccesful:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    return {"message": message}

@app.put("/transcribe/{course_acronym}/{class_number}", status_code=status.HTTP_200_OK)
async def update_transcription(course_acronym: str, class_number: str, model_size: str, language: str):
    isSuccesful, message = procesor.update_transcription(course_acronym, class_number, model_size, language)
    if not isSuccesful:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return {"message": "Started scraping"}

# poc/main.py
'''
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import whisper
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from prefect import flow, task

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
'''