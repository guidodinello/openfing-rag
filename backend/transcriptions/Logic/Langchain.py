from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from langchain_core.documents import Document
from langchain_elasticsearch import ElasticsearchStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from pathlib import Path
from pymongo import MongoClient
from typing import Optional, List, Dict, Any
import datetime
import json
import os

# Initialize Ollama model
class MongoElasticsearchSync:
    """
    Handles synchronization between MongoDB and Elasticsearch with timestamp-based incremental loading.
    """
    def __init__(self, mongo_uri: str, es_uri: str, db_name: str, collection_name: str, api_key: str):
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[db_name]
        self.collection = self.db[collection_name]
        self.es_client = Elasticsearch(hosts=[{"host": "localhost", "port": 9200, "scheme": "http"}])
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.index_name = f"{"all-MiniLM-L6-v2"}_{"COSINE"}_{"CHUNKS500"}".lower()
        self.llm = OllamaLLM(model="llama3.2")
        self.es_vectorstore = None
        self.timestamp_file = f"{self.index_name}_sync_timestamp.json"
    
    def get_mongo_iterable(self) -> dict:
        last_sync_timestamp=self.get_last_sync_timestamp()
        if last_sync_timestamp is not None:
            query = {"created_at": {"$gt": last_sync_timestamp}}
        else:
            query = {}
            last_sync_timestamp = datetime.datetime.now()
            self.save_last_sync_timestamp(last_sync_timestamp)
        cursor = self.collection.find(query).sort("_id", 1)
        return cursor, last_sync_timestamp
    
    def get_last_sync_timestamp(self) -> Optional[datetime]:
        """Retrieve the last sync timestamp from file."""
        try:
            if os.path.exists(self.timestamp_file):
                with open(self.timestamp_file, 'r') as f:
                    data = json.load(f)
                    return datetime.datetime.fromisoformat(data["last_sync"])
            return None
        except Exception as e:
            print(f"Error reading sync timestamp: {e}")
            return None

    def save_last_sync_timestamp(self, timestamp: datetime) -> None:
        """Save the last sync timestamp to file."""
        try:
            with open(self.timestamp_file, 'w') as f:
                json.dump({
                    'last_sync': timestamp.isoformat(),
                    'index_name': self.index_name
                }, f)
        except Exception as e:
            print(f"Error saving sync timestamp: {e}")
    
    def process_mongodb_documents(self) -> tuple[List[Document], Optional[datetime]]:
        """Process MongoDB documents and convert to LangChain documents (chunks only)."""
        cursor, last_sync_date = self.get_mongo_iterable()
        langchain_documents = []
        processed_count = 0
        
        for chunk_data in cursor:
            created_at = chunk_data.get("created_at")
            if not created_at or created_at >= last_sync_date:
                continue
            chunks500_list = chunk_data.get("chunks500")
            metadata = {
                "title": chunk_data.get("title"),
                "subtitle": chunk_data.get("subtitle"),
                "class": chunk_data.get("class"),
            }
            for chunk in chunks500_list:
                doc = Document(page_content=chunk, metadata=metadata)
                langchain_documents.append(doc)
            processed_count += 1
        
        print(f"Processed {processed_count} documents from MongoDB.")
        print(f"Created {len(langchain_documents)} documents for indexing.")
        return langchain_documents
    
    def initialize_vectorstore(self) -> ElasticsearchStore:
        """
        Initialize the Elasticsearch vector store.
        If the index exists, it will be used; otherwise, a new one will be created.
        """
        print(f"Initializing Elasticsearch vector store for index: {self.index_name}")
        self.es_vectorstore = ElasticsearchStore(
                es_connection=self.es_client,
                index_name=self.index_name,
                embedding=self.embeddings,
                distance_strategy="COSINE"
            )
        return self.es_vectorstore
        
    def sync_documents(self) -> None:
        """Main synchronization method."""
        print(f"Starting synchronization for index: {self.index_name}")
        self.es_vectorstore = self.initialize_vectorstore()
        langchain_documents= self.process_mongodb_documents()
        
        if langchain_documents:
                self.es_vectorstore.add_documents(langchain_documents) 

    def send_query(self, query: str="¿A partir de qué se puede generar el Biodisel y ?", k: int = 4, score_threshold: float = 0.7) -> dict:
        """
        Simple semantic search on pre-filtered chunks
        Args:
            query: The question to ask
            k: Number of chunks to retrieve
            score_threshold: Minimum similarity score threshold
        Returns:
            Dictionary with answer and source chunks
        """
        qa_chain = self.create_qa_chain()

        docs_with_scores = self.es_vectorstore.similarity_search_with_score(query, k=k)
        relevant_chunks = [
            (doc, score) for doc, score in docs_with_scores 
            if score >= score_threshold
        ]
        print(f"Retrieved {len(relevant_chunks)}.")
        print(f"Score threshold: {relevant_chunks}")

        if not relevant_chunks:
            return {
                "answer": "No semantically relevant chunks found above threshold.",
                "sources": []
            }
        docs = [doc for doc, score in relevant_chunks]
        print(f"Found {len(docs)} relevant chunks with scores above {score_threshold}.")
        
        answer = qa_chain.invoke({"query": query})["result"]
        
        return {
            "question": query,
            "answer": answer,
            "sources": [
                {
                    "content": doc.page_content,
                    "similarity_score": score
                }
                for doc, score in relevant_chunks
            ]
        }

    def send_query_with_filters(self, query: str, filters: dict = None, k: int = 4) -> dict:
        """
        Enhanced query with metadata-based filtering

        Args:
            query: The question to ask
            filters: Dictionary of metadata filters (e.g., {'language': 'spanish', 'class': 1})
            k: Number of chunks to retrieve
        """
        search_kwargs = {"k": k}
        if filters:
            search_kwargs["filter"] = filters
        try:
            if filters:
                relevant_chunks = self.es_vectorstore.similarity_search(
                    query, 
                    **search_kwargs
                )
            else:
                relevant_chunks = self.es_vectorstore.similarity_search(query, k=k)
            if filters:
                relevant_chunks = self._post_filter_chunks(relevant_chunks, filters)
        except Exception as e:
            print(f"Search error: {e}")
            return {"answer": "Error retrieving information", "sources": []}

        if not relevant_chunks:
            return {"answer": "No relevant information found", "sources": []}
        qa_chain = self.create_qa_chain()
        answer = qa_chain.invoke({"query": query})["result"]

        return {
            "question": query,
            "answer": answer,
            "sources": [
                {
                    "content": chunk.page_content,
                    "metadata": getattr(chunk, 'metadata', {})
                }
                for chunk in relevant_chunks
            ]
        }

    def _post_filter_chunks(self, chunks, filters):
        """Post-process filtering based on metadata"""
        filtered = []
        for chunk in chunks:
            metadata = getattr(chunk, 'metadata', {})
            matches = True
            for key, value in filters.items():
                if key not in metadata or metadata[key] != value:
                    matches = False
                    break

            if matches:
                filtered.append(chunk)

        return filtered
    
    def create_qa_chain(self, k: int = 4) -> RetrievalQA:
        """Create QA chain with retriever."""
        if self.es_vectorstore is None:
            raise ValueError("Vector store not initialized. Run sync_documents() first.")
        
        retriever = self.es_vectorstore.as_retriever(search_kwargs={'k': k})
        return RetrievalQA.from_llm(llm=self.llm, retriever=retriever)

    def close_connections(self) -> None:
        """Close database connections."""
        self.mongo_client.close()

def main():
    """Main execution function."""
    load_dotenv(dotenv_path="../.env")
    api_key = os.getenv("API_KEY_OPENAI")
    
    #if not api_key:
        #raise ValueError("API_KEY_OPENAI not found in .env file")
    config = {
        "mongo_uri": "mongodb://localhost:27017",
        "es_uri": "http://localhost:9200",
        "db_name": "transcriptions_db",
        "collection_name": "classes",
        "api_key": api_key
    }
    
    sync = MongoElasticsearchSync(**config)
    try:
        sync.sync_documents()
        print(f"ES_CLIENT.count: {sync.index_name}")
        documents= sync.es_client.count(index=sync.index_name)["count"]
        if documents > 0:
            answer=sync.send_query()
            print(f"Answer: {answer['answer']}")
        else:
            print("No documents available to process the query. Please add documents to MongoDB.")
    except Exception as e:
        print(f"Error during execution: {e}")
        raise
    finally:
        sync.close_connections()

if __name__ == "__main__":
    main()