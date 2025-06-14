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
import itertools
from dataclasses import dataclass

@dataclass
class TestConfiguration:
    """Configuration for a single test run"""
    chunk_field: str
    distance_strategy: str
    embedding_model: str
    llm_model: str
    metadata_option: str
    index_suffix: str
    question:str

class ParametrizedMongoElasticsearchSync:
    """
    Parametrized version for testing different combinations of parameters.
    """
    def __init__(self, config: dict, test_config: TestConfiguration):
        self.config = config
        self.test_config = test_config
        
        # MongoDB setup
        self.mongo_client = MongoClient(config['constants']['mongo_uri'])
        self.db = self.mongo_client[config['constants']['db_name']]
        self.collection = self.db[config['constants']['collection_name']]
        
        # Elasticsearch setup
        self.es_client = Elasticsearch(hosts=[{"host": "localhost", "port": 9200, "scheme": "http"}])
        self.index_name = f"test_index_{test_config.distance_strategy}_{test_config.embedding_model}".lower()
        
        # Initialize components with test parameters
        self.embeddings = HuggingFaceEmbeddings(model_name=test_config.embedding_model)
        self.llm = OllamaLLM(
            model=test_config.llm_model,
            base_url=f"http://{config['constants']['ollama_server']}"
        )
        self.question = test_config.question
        self.es_vectorstore = None
        self.timestamp_file = f"{self.index_name}_sync_timestamp.json"
    
    def get_mongo_iterable(self) -> tuple:
        """Get MongoDB cursor with timestamp filtering"""
        last_sync_timestamp = self.get_last_sync_timestamp()
        if last_sync_timestamp is not None:
            query = {"created_at": {"$gt": last_sync_timestamp}}
        else:
            query = {}
            last_sync_timestamp = datetime.datetime.now()
            self.save_last_sync_timestamp(last_sync_timestamp)
        cursor = self.collection.find(query).sort("_id", 1)
        return cursor, last_sync_timestamp
    
    def get_last_sync_timestamp(self) -> Optional[datetime.datetime]:
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

    def save_last_sync_timestamp(self, timestamp: datetime.datetime) -> None:
        """Save the last sync timestamp to file."""
        try:
            with open(self.timestamp_file, 'w') as f:
                json.dump({
                    'last_sync': timestamp.isoformat(),
                    'index_name': self.index_name
                }, f)
        except Exception as e:
            print(f"Error saving sync timestamp: {e}")
    
    def process_mongodb_documents(self) -> List[Document]:
        """Process MongoDB documents using the specified chunk field"""
        cursor, last_sync_date = self.get_mongo_iterable()
        langchain_documents = []
        processed_count = 0
        
        for chunk_data in cursor:
            created_at = chunk_data.get("created_at")
            if not created_at or created_at >= last_sync_date:
                continue
                
            # Use the parametrized chunk field
            chunks_list = chunk_data.get(self.test_config.chunk_field, [])
            if not chunks_list:
                continue
                
            # Build metadata based on metadata option
            metadata = self._build_metadata(chunk_data)
            
            for chunk in chunks_list:
                doc = Document(page_content=chunk, metadata=metadata)
                langchain_documents.append(doc)
            processed_count += 1
        
        print(f"Processed {processed_count} documents from MongoDB using {self.test_config.chunk_field}.")
        print(f"Created {len(langchain_documents)} documents for indexing.")
        return langchain_documents
    
    def _build_metadata(self, chunk_data: dict) -> dict:
        """Build metadata based on the metadata option"""
        base_metadata = {
            "title": chunk_data.get("title"),
            "subtitle": chunk_data.get("subtitle"),
            "class": chunk_data.get("class"),
        }
        
        if self.test_config.metadata_option == "no":
            return {}
        elif self.test_config.metadata_option == "title":
            return {"title": base_metadata["title"]}
        elif self.test_config.metadata_option == "title_subtitle":
            return {
                "title": base_metadata["title"],
                "subtitle": base_metadata["subtitle"]
            }
        elif self.test_config.metadata_option == "title_subtitle_class":
            return base_metadata
        else:
            return base_metadata
    
    def initialize_vectorstore(self) -> ElasticsearchStore:
        """Initialize the Elasticsearch vector store with parametrized distance strategy"""
        self.es_vectorstore = ElasticsearchStore(
            es_connection=self.es_client,
            index_name=self.index_name,
            embedding=self.embeddings,
            distance_strategy=self.test_config.distance_strategy.upper()
        )
        return self.es_vectorstore
        
    def sync_documents(self) -> None:
        """Main synchronization method"""
        print(f"Starting synchronization for index: {self.index_name}")
        self.es_vectorstore = self.initialize_vectorstore()
        langchain_documents = self.process_mongodb_documents()
        
        if langchain_documents:
            self.es_vectorstore.add_documents(langchain_documents)
            print(f"Added {len(langchain_documents)} documents to Elasticsearch")
    
    def send_query_with_metadata_filters(self, question: str, query_metadata: dict, k: int = 6) -> dict:
        """Send query with metadata filtering based on current configuration"""
        if self.es_vectorstore is None:
            raise ValueError("Vector store not initialized. Run sync_documents() first.")
        print("b")
        # Build filters based on metadata option and available query metadata        
        filters = self._build_query_filters(query_metadata)        
        print("c")
        try:
            # Search with or without filters
            if filters and self.test_config.metadata_option != "no":                
                print("d")
                relevant_chunks = self.es_vectorstore.similarity_search(
                    question, 
                    k=k,
                    filter=filters
                )
                print("e")
            else:         
                print("f")       
                relevant_chunks = self.es_vectorstore.similarity_search(question, k=k)
            print("g")
            if not relevant_chunks:                
                print("h")
                return {
                    "question": question,
                    "answer": "No relevant information found",
                    "sources": []
                }            
            # Create QA chain and get answer
            print("i")
            qa_chain = self.create_qa_chain()            
            print("j")
            answer = qa_chain.invoke({"query": question})["result"]            
            print("k")
            return {
                "question": question,
                "answer": answer,
                "sources": [
                    {
                        "content": chunk.page_content,
                        "metadata": getattr(chunk, 'metadata', {})
                    }
                    for chunk in relevant_chunks  # Limit to top 3 sources
                ]
            }
            
        except Exception as e:
            print(f"Query error: {e}")
            return {
                "question": question,
                "answer": f"Error processing query: {str(e)}",
                "sources": []
            }
    
    def _build_query_filters(self, query_metadata: dict) -> dict:
        """Build query filters based on metadata option"""
        if self.test_config.metadata_option == "no":
            return {}
        
        filters = {}
        if self.test_config.metadata_option in ["title", "title_subtitle", "title_subtitle_class"]:
            if query_metadata.get("title"):
                filters["title"] = query_metadata["title"]
        
        if self.test_config.metadata_option in ["title_subtitle", "title_subtitle_class"]:
            if query_metadata.get("subtitle"):
                filters["subtitle"] = query_metadata["subtitle"]
        
        if self.test_config.metadata_option == "title_subtitle_class":
            if query_metadata.get("class"):
                filters["class"] = query_metadata["class"]
        
        return filters
    
    def create_qa_chain(self, k: int = 4) -> RetrievalQA:
        """Create QA chain with retriever."""
        if self.es_vectorstore is None:
            raise ValueError("Vector store not initialized. Run sync_documents() first.")
        
        retriever = self.es_vectorstore.as_retriever(search_kwargs={'k': k})
        return RetrievalQA.from_llm(llm=self.llm, retriever=retriever)

    def close_connections(self) -> None:
        """Close database connections."""
        self.mongo_client.close()

class ParameterTester:
    """Handles parameter combination testing"""
    
    def __init__(self, config_path: str = "parameters.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    def generate_combinations(self) -> List[TestConfiguration]:
        """Generate all parameter combinations, including questions."""
        params = self.config['parameters']
        prompts = params["prompts"]  # Assume questions are defined in config

        # Extract parameter values
        chunks = list(params['chunks'].values())
        distances = list(params['distance'].values())
        embeddings = list(params['embeddings'].values())
        llms = list(params['llms'].values())
        metadata_options = list(params['metadata'].values())

        combinations = []
        combo_id = 0

        # Iterate over all possible combinations (including questions)
        for question in prompts:
            for chunk, distance, embedding, llm, metadata in itertools.product(
                chunks, distances, embeddings, llms, metadata_options
            ):
                config = TestConfiguration(
                    chunk_field=chunk,
                    distance_strategy=distance,
                    embedding_model=embedding,
                    llm_model=llm,
                    metadata_option=metadata,
                    index_suffix=f"combo_{combo_id + 1}",
                    question=question 
                )
                combinations.append(config)
                combo_id += 1
    
        return combinations
    
    def run_single_test(self, test_config: TestConfiguration, test_questions: List[dict] = None) -> None:
        """Run a single parameter combination test"""
        print(f"\n{'='*80}")
        print(f"TESTING COMBINATION: {test_config.index_suffix}")
        print(f"Chunk Field: {test_config.chunk_field}")
        print(f"Distance: {test_config.distance_strategy}")
        print(f"Embedding: {test_config.embedding_model}")
        print(f"LLM: {test_config.llm_model}")
        print(f"Metadata: {test_config.metadata_option}")
        print(f"Question: {test_config.question}")
        print(f"{'='*80}")
        
        sync = ParametrizedMongoElasticsearchSync(self.config, test_config)
        
        try:
            # Sync documents
            sync.sync_documents()
            
            # Check if documents were indexed
            doc_count = sync.es_client.count(index=sync.index_name)["count"]
            print(f"Documents in index: {doc_count}")
            
            if doc_count > 0:
                # Use provided test questions or default ones
                questions_to_test = test_config.question
            
                print(f"Metadata: {questions_to_test['metadata']}")
                print(f"Testing question: {questions_to_test['question']}")
                print(f"{"a"}")
                result = sync.send_query_with_metadata_filters(
                    questions_to_test['question'], 
                    questions_to_test['metadata']
                )
                print(f"Q: {result['question']}")
                print(f"A: {result['answer']}")
                print(f"Sources found: {len(result['sources'])}")
                
                if result['sources']:
                    print("Top source preview:")
                    print(f"  Content: {result['sources'][0]['content']}")
                    print(f"  Metadata: {result['sources'][0]['metadata']}")
            else:
                print("No documents available for testing queries.")
                
        except Exception as e:
            print(f"Error in test: {e}")
        finally:
            sync.close_connections()
    
    def run_all_tests(self, max_combinations: int = None) -> None:
        """Run tests for all parameter combinations"""
        combinations = self.generate_combinations()
        
        if max_combinations:
            combinations = combinations[:max_combinations]
        
        # Filter out already tested combinations
        untested_combinations = [
            combo for combo in combinations 
            if not self.is_combination_tested(combo)
        ]
        
        print(f"Total combinations: {len(combinations)}")
        print(f"Already tested: {len(combinations) - len(untested_combinations)}")
        print(f"Remaining to test: {len(untested_combinations)}")
        
        if not untested_combinations:
            print("All combinations have already been tested!")
            return
        
        for i, test_config in enumerate(untested_combinations, 1):
            combo_id = f"{test_config.chunk_field}_{test_config.distance_strategy}_{test_config.embedding_model}_{test_config.llm_model}_{test_config.metadata_option}_{test_config.question}"

            print(f"\n🔄 Running test {i}/{len(untested_combinations)}")
            print(f"📋 Testing: {combo_id}")
            
            try:
                self.run_single_test(test_config)
                # Save combination as tested after successful completion
                self.save_tested_combination(test_config)
            except Exception as e:
                print(f"❌ Error in combination {combo_id}: {e}")
                # Still save it to avoid retesting failed combinations
                self.save_tested_combination(test_config)
            
            # Small break between tests
            import time
            time.sleep(2)

    def load_tested_combinations(self) -> List[str]:
        """Load already tested combinations from file"""
        try:
            if os.path.exists("tested_combinations.json"):
                with open("tested_combinations.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("tested_combinations", [])
            return []
        except Exception as e:
            print(f"Error loading tested combinations: {e}")
            return []
        
    def save_tested_combination(self, test_config: TestConfiguration) -> None:
        """Save a tested combination to file"""
        try:
            # Load existing data
            tested_combinations = self.load_tested_combinations()
            
            # Create combination identifier
            combo_id = f"{test_config.chunk_field}_{test_config.distance_strategy}_{test_config.embedding_model}_{test_config.llm_model}_{test_config.metadata_option}"
            
            # Add if not already present
            if combo_id not in tested_combinations:
                tested_combinations.append(combo_id)
                
                # Save back to file
                with open("tested_combinations.json", 'w', encoding='utf-8') as f:
                    json.dump({"tested_combinations": tested_combinations}, f, indent=2)
                print(f"✅ Saved tested combination: {combo_id}")
            
        except Exception as e:
            print(f"Error saving tested combination: {e}")
    
    def is_combination_tested(self, test_config: TestConfiguration) -> bool:
        """Check if a combination has already been tested"""
        tested_combinations = self.load_tested_combinations()
        combo_id = f"{test_config.chunk_field}_{test_config.distance_strategy}_{test_config.embedding_model}_{test_config.llm_model}_{test_config.metadata_option}"
        return combo_id in tested_combinations

def main():
    """Main execution function with parameter testing"""
    load_dotenv(dotenv_path="../.env")
    
    tester = ParameterTester("parameters.json")
    
    # Option 1: Run all combinations (warning: this could be many!)
    # tester.run_all_tests(max_combinations=5)  # Limit to first 5 for testing
    
    # Option 2: Run a single combination for debugging
    combinations = tester.generate_combinations()
    if combinations:
        print(f"Available combinations: {len(combinations)}")
        tester.run_single_test(combinations[0])  # Test first combination
    
    # Option 3: Run specific test questions only
    # test_questions = tester.config['parameters']['prompts'][:2]  # First 2 questions
    # tester.run_single_test(combinations[0], test_questions)

if __name__ == "__main__":
    main()