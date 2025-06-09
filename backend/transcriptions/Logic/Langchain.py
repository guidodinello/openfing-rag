# from langchain.llms import Ollama
# from datetime import datetime  # Asegúrate de tener esta línea al inicio del archivo
# from langchain.llms import ChatGroq
# from langchain.llms import Cohere
# from langchain.llms import Together
# from langchain.llms import Cohere
# from datetime import datetime, UTC
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
    def __init__(self, mongo_uri: str, es_uri: str, db_name: str, collection_name: str, index_name: str, api_key: str):
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[db_name]
        self.collection = self.db[collection_name]
        
        self.es_client = Elasticsearch(hosts=[{"host": "localhost", "port": 9200, "scheme": "http"}])
        self.index_name = index_name
        self.timestamp_file = f"{index_name}_last_sync.json"
        
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        # llm = ChatGrok(
        #     groq_api_key="your-groq-api-key",
        #     model_name="mixtral-8x7b-32768"  # or "llama2-70b-4096"
        # )
        # llm = Together(
        #     model="togethercomputer/llama-2-7b-chat",
        #     together_api_key="your-together-api-key"
        # )
        self.llm = OllamaLLM(model="llama3.2")
        # llm = Cohere(cohere_api_key="your-cohere-api-key")
        # llm = ChatGroq(
        #     groq_api_key="your-groq-api-key",
        #     model_name="mixtral-8x7b-32768"  # or "llama2-70b-4096"
        # )
        # self.llm = ChatOpenAI(api_key=api_key, model="gpt-3.5-turbo")
        self.es_vectorstore = None
        
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

    def get_mongodb_query(self, last_sync_timestamp: Optional[datetime]) -> Dict[str, Any]:
        """Build MongoDB query based on last sync timestamp."""
        if last_sync_timestamp:
            return {
                "$or": [
                    {"created_at": {"$gt": last_sync_timestamp}},
                    {"updated_at": {"$gt": last_sync_timestamp}}
                ]
            }
        return {}

    def process_mongodb_documents(self, cursor) -> tuple[List[Document], Optional[datetime]]:
        """Process MongoDB documents and convert to LangChain documents (chunks only)."""
        langchain_documents = []
        processed_count = 0
        latest_timestamp = None
        
        for chunk_data in cursor:
            chunks_list = chunk_data.get("chunks")
            
            doc_timestamp = chunk_data.get("updated_at") or chunk_data.get("created_at")
            if doc_timestamp and (latest_timestamp is None or doc_timestamp > latest_timestamp):
                latest_timestamp = doc_timestamp
            
            if isinstance(chunks_list, list):
                for chunk in chunks_list:
                    if isinstance(chunk, str) and chunk.strip():
                        doc = Document(page_content=chunk)
                        langchain_documents.append(doc)
                    elif chunk and not isinstance(chunk, str):
                        print(f"Warning: Non-string chunk found: {type(chunk)}")
            else:
                print(f"Warning: 'chunks' field is not a list in document {chunk_data.get('_id')}")
            
            processed_count += 1
        
        print(f"Processed {processed_count} documents from MongoDB.")
        print(f"Created {len(langchain_documents)} documents for indexing.")
        
        return langchain_documents, latest_timestamp
    
    def initialize_vectorstore(self, create_new: bool = False) -> ElasticsearchStore:
        """Initialize or create Elasticsearch vector store."""
        return ElasticsearchStore(
            es_connection=self.es_client,
            index_name=self.index_name,
            embedding=self.embeddings,
            distance_strategy="COSINE"
        )

    def sync_documents(self) -> None:
        """Main synchronization method."""
        print(f"Starting synchronization for index: {self.index_name}")
        
        last_sync_timestamp = self.get_last_sync_timestamp()
        
        index_exists = self.es_client.indices.exists(index=self.index_name)
        has_documents = False
        
        if index_exists:
            doc_count = self.es_client.count(index=self.index_name)['count']
            has_documents = doc_count > 0
            print(f"Index '{self.index_name}' exists with {doc_count} documents.")
        else:
            print(f"Index '{self.index_name}' does not exist.")
        
        if has_documents and last_sync_timestamp:
            print(f"Checking for documents updated since: {last_sync_timestamp}")
            mongo_query = self.get_mongodb_query(last_sync_timestamp)
        else:
            print("Loading all documents from MongoDB...")
            mongo_query = {}
        
        cursor = self.collection.find(mongo_query).sort("_id", 1)
        langchain_documents, latest_timestamp = self.process_mongodb_documents(cursor)
        
        if langchain_documents:
            if not index_exists:
                self.es_vectorstore = ElasticsearchStore.from_documents(
                    documents=langchain_documents,
                    embedding=self.embeddings,
                    es_connection=self.es_client,
                    index_name=self.index_name,
                    distance_strategy="COSINE"
                )
                print(f"Created index and added {len(langchain_documents)} documents.")
            else:
                self.es_vectorstore = self.initialize_vectorstore()
                self.es_vectorstore.add_documents(langchain_documents)
                print(f"Added {len(langchain_documents)} new documents to existing index.")
            
            if latest_timestamp:
                self.save_last_sync_timestamp(latest_timestamp)
                print(f"Updated sync timestamp: {latest_timestamp}")
        else:
            self.es_vectorstore = self.initialize_vectorstore()
            print("No documents found to add, but initialized vector store.")
            
            if last_sync_timestamp is None:
                self.save_last_sync_timestamp(datetime.now())
                print("Initialized sync timestamp.")

    def send_query(self, query: str="¿Que fuerzas aplican sobre un auto en movimiento?", k: int = 6, score_threshold: float = 0.7) -> dict:
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

        if not relevant_chunks:
            return {
                "answer": "No semantically relevant chunks found above threshold.",
                "sources": []
            }
        docs = [doc for doc, score in relevant_chunks]
        answer = qa_chain.invoke({"query": query})["result"]
        print(answer)
        
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

    def send_query_with_filters(self, query: str, filters: dict = None, k: int = 6) -> dict:
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
    api_key = os.getenv("API_KEY")
    
    if not api_key:
        raise ValueError("API_KEY not found in .env file")
    config = {
        "mongo_uri": "mongodb://localhost:27017",
        "es_uri": "http://localhost:9200",
        "db_name": "transcriptions_db",
        "collection_name": "classes",
        "index_name": "my_index",
        "api_key": api_key
    }
    
    sync = MongoElasticsearchSync(**config)
    try:
        sync.sync_documents()
        
        langchain_documents, _ = sync.process_mongodb_documents(sync.collection.find({}))
        if langchain_documents:
            answer=sync.send_query()
        else:
            print("No documents available to process the query. Please add documents to MongoDB.")
        
    except Exception as e:
        print(f"Error during execution: {e}")
        raise
    finally:
        sync.close_connections()

if __name__ == "__main__":
    main()