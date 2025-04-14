from typing import Dict, List
from transcriptions.Constants.Constants import COLLECTION_NAME, CONNECTION_STRING
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores.pgvector import PGVector

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

