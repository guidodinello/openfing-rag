from dataclasses import dataclass
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from langchain_core.documents import Document
from langchain_elasticsearch import ElasticsearchStore
from langchain_ollama import OllamaLLM
from langchain.chains import RetrievalQA
from pathlib import Path
from pymongo import MongoClient
from langchain_huggingface import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from typing import Optional, List, Dict, Any
import datetime ,itertools ,json ,os,traceback

@dataclass
class TestConfiguration:
    """Configuration for a single test run"""
    chunk_field: str
    distance_strategy: str
    embedding_model: str
    llm_model: str
    metadata_option: str
    index_suffix: int
    question:str

result_path = "/home/diego/_Modulos/Facu/tesis/backend/transcriptions/Logic/testing_parameters.json"
parametes_path = "/home/diego/_Modulos/Facu/tesis/backend/transcriptions/Logic/parameters_lunes.json"

PARAMETERS={
  "constants": {
    "mongo_uri": "mongodb://localhost:27017",
    "db_name": "transcriptions_db",
    "collection_name": "classes",
    "es_uri": "http://localhost:9200",
    "ollama_server": "127.0.0.1:11434"
  },
  "parameters": {
    "chunks": {
      "option1": "chunks500",
      "option2": "chunks400",
      "option3": "chunks300"
    },
    "distance": {
      "option1": "COSINE",
      "option2": "DOT_PRODUCT",
      "option3": "EUCLIDEAN_DISTANCE"
    },
    "embeddings": {
      "option1": "jaimevera1107/all-MiniLM-L6-v2-similarity-es",
      "option2": "hackathon-pln-es/paraphrase-spanish-distilroberta",
      "option3": "thenlper/gte-base"
    },
    "llms": {
      "option1": "llama3.2",
      "option2": "mixtral:8x22b",
      "option3": "llama3:8b-instruct"
    },    
    "metadata": {
        "option1": "no",
        "option2": "related_course",
        "option3": "course",
        "option4": "course_and_class"
    },
    "prompts": [
        {
            "metadata":{
                "course": "en1-2023",
                "related_course": "en1-2023",
                "class":14,
            },
            "question":"¿Qué determina el análisis próximo o inmediato en un combustible sólido?",
            "answer":"El análisis próximo determina la humedad, el porcentaje de cenizas, el porcentaje de materia volátil y el porcentaje de carbono fijo."
        },
      {
        "metadata":{
            "course": "en1-2023",
            "related_course": "en1-2023",
            "class":14
        },
        "question":"¿Por qué la cantidad de cenizas en un combustible puede afectar su calidad como fuente de energía?",
        "answer":"Aunque no se dice directamente, se infiere que una mayor cantidad de cenizas reduce la calidad del combustible, ya que generan más residuos no combustibles, lo cual puede afectar la eficiencia de la combustión y requerir mayor tratamiento de residuos."
      },{
          "metadata":{
            "course": "en1-2023",
            "related_course": "en1-2023",
            "class":18
        },
        "question":"¿Cuál es el primer proceso que ocurre cuando una partícula de biomasa se introduce en un horno a alta temperatura?",
        "answer":"Se seca. El agua que contiene se evapora y sale por difusión desde el interior de la partícula."
   },{
          "metadata":{
            "course": "en1-2023",
            "related_course": "en1-2023",
            "class":18
        },
        "question":"¿Por qué se prefiere analizar partículas pequeñas al estudiar los procesos térmicos de combustión?",
        "answer":"Porque en partículas pequeñas la temperatura puede considerarse uniforme durante el proceso, lo que facilita entender y modelar qué está ocurriendo. Esto se infiere del contraste con los troncos grandes donde ocurren muchos procesos simultáneamente y con gradientes de temperatura."
      },
      {
        "metadata":{
            "course": "adadr-2023",
            "related_course": "adadr",
            "class":1
        },
        "question":"¿Qué convención se asume en el curso para simplificar el modelado de enlaces bidireccionales?",
        "answer":"Que hay una sola arista que representa el enlace y que las etiquetas de entrada y salida son compartidas."
      },
       {
        "metadata":{
            "course": "adadr-2023",
            "related_course": "adadr",
            "class":1
        },
        "question":"¿Por qué es útil imponer restricciones adicionales, como confiabilidad de los mensajes o entrega en orden, en los modelos de comunicación?",
        "answer":"Porque permiten adaptar el modelo a las condiciones específicas del problema y pueden afectar directamente la ejecución y validez de los algoritmos distribuidos. Esto se infiere del texto cuando se menciona que las restricciones dependen del problema y que conocer el historial de fallos puede cambiar el estado en el que se encuentra el algoritmo."
      }
    ],

  }
}

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
        self.index_name = f"test_index_{test_config.distance_strategy}_{test_config.embedding_model}_{test_config.chunk_field}".lower()
        
        # Initialize components with test parameters
        safe_embedding_model = test_config.embedding_model.replace("/", "_").replace(" ", "_")
        self.index_name = f"test_index_{test_config.distance_strategy}_{safe_embedding_model}_{test_config.chunk_field}".lower()
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
            chunks_list = chunk_data.get(self.test_config.chunk_field)
            if not chunks_list:
                continue
            course_acronym = chunk_data.get("course_acronym")    
            related_courses = chunk_data.get("related_courses")
            class_number = chunk_data.get("class")    
            metadata : Dict[str, str] = {
                    "course": course_acronym,
                    "related_course": related_courses,
                    "class": class_number
                }
            
            for chunk in chunks_list:
                doc = Document(page_content=chunk, metadata=metadata)
                langchain_documents.append(doc)
            processed_count += 1
        return langchain_documents
    
    def build_query_filters(query_metadata):
        must_clauses = []
        if query_metadata.get("course"):
            must_clauses.append({"match": {"metadata.course": query_metadata["course"]}})
        if query_metadata.get("class"):
            must_clauses.append({"match": {"metadata.class": query_metadata["class"]}})
        if must_clauses:
            return {"query": {"bool": {"must": must_clauses}}}
        else:
            return {"query": {"match_all": {}}}
    
    def _build_query_filters(self, query_metadata: dict) -> dict:
        """Build query filters based on metadata option"""
        if self.test_config.metadata_option == "no":
            return {}
        must_clauses = []
        if self.test_config.metadata_option == "related_course":
            must_clauses.append({"match": {"metadata.related_course": query_metadata["related_course"]}})
        elif self.test_config.metadata_option == "course":
            must_clauses.append({"match": {"metadata.course": query_metadata["course"]}})
        elif self.test_config.metadata_option == "course_and_class":
            must_clauses.append({"match": {"metadata.course": query_metadata["course"],"metadata.class": query_metadata["class"]}})
        if not must_clauses:
            return {}
        return {
            "bool": {
                "must": must_clauses
            }
        }    

    def initialize_vectorstore(self) -> ElasticsearchStore:
        """Initialize the Elasticsearch vector store with parametrized distance strategy"""
        if not self.es_client.indices.exists(index=self.index_name):
            print(f"Index {self.index_name} does not exist. Creating index...")
            self.es_client.indices.create(index=self.index_name)
        self.es_vectorstore = ElasticsearchStore(
            es_connection=self.es_client,
            index_name=self.index_name,
            embedding=self.embeddings,
            distance_strategy=self.test_config.distance_strategy
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
    
    def send_query_with_metadata_filters(self, question: str, query_metadata: dict, k: int = 4) -> dict:
        """Send query with metadata filtering based on current configuration"""
        if self.es_vectorstore is None:
            raise ValueError("Vector store not initialized. Run sync_documents() first.")
        filters = self._build_query_filters(query_metadata)
        try:
            if filters and self.test_config.metadata_option != "no":    
                relevant_chunks = self.es_vectorstore.similarity_search(
                    question, 
                    k=k,
                    filter=filters
                )
            else:
                relevant_chunks = self.es_vectorstore.similarity_search(question, k=k)
            
            if not relevant_chunks:                
                return {
                    "question": question,
                    "answer": "No se encontró información relevante.",
                    "sources": []
                }            

            qa_chain = self.create_qa_chain()            
            answer = qa_chain.invoke({"query": question})["result"]            
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
            print(f"Error procesando{self.test_config.index_suffix}: {str(e)}")
            return {
                "question": question,
                "answer": f"Error procesando{self.test_config.index_suffix}: {str(e)}",
                "sources": []
            }
    
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
    
    def __init__(self, config_path: str = parametes_path):
        self.config = PARAMETERS
    
    def generate_combinations(self) -> List[TestConfiguration]:
        """Generate all parameter combinations, including questions."""
        params = self.config['parameters']
        prompts = params["prompts"] 

        chunks = list(params['chunks'].values())
        distances = list(params['distance'].values())
        embeddings = list(params['embeddings'].values())
        llms = list(params['llms'].values())
        metadata_options = list(params['metadata'].values())

        base = {
            'chunk': chunks[0],
            'distance': distances[0],
            'embedding': embeddings[0],
            'llm': llms[0],
            'metadata': metadata_options[0]
        }

        combo_id = 0
        combinations = []

        for question in prompts:
            config = TestConfiguration(
                index_suffix=f"{combo_id}",
                chunk_field=base['chunk'],
                distance_strategy=base['distance'],
                embedding_model=base['embedding'],
                llm_model=base['llm'],
                metadata_option=base['metadata'],
                question=question
            )
            combinations.append(config)
            combo_id += 1
    
        for i, param_list in enumerate([chunks, distances, embeddings, llms, metadata_options]):
            param_name = ['chunk', 'distance', 'embedding', 'llm', 'metadata'][i]
            for value in param_list[1:]:  # Skip the base value
                config_kwargs = base.copy()
                config_kwargs[param_name] = value
                for question in prompts:
                    config = TestConfiguration(
                        index_suffix=f"{combo_id}",
                        chunk_field=config_kwargs['chunk'],
                        distance_strategy=config_kwargs['distance'],
                        embedding_model=config_kwargs['embedding'],
                        llm_model=config_kwargs['llm'],
                    metadata_option=config_kwargs['metadata'],
                    question=question
                )
                combinations.append(config)
                combo_id += 1


        return combinations
    
    def save_results(self, test:TestConfiguration,results: List[Dict[str, Any]]) -> None:
        self.save_answer(test,results)
        self.save_context(test,results)
    
    def save_answer(self, test: TestConfiguration, result: Dict[str, Any]) -> None:
    # Load existing data or initialize if file doesn't exist
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if self.combo_id not in data["tested_combinations"]:
            data["tested_combinations"][self.combo_id] = {
                "config": {
                    "chunks": test.chunk_field,
                    "distance": test.distance_strategy,
                    "embeddings": test.embedding_model,
                    "llms": test.llm_model,
                    "metadata_option": test.metadata_option,
                    "question": test.question["question"],
                    "metadata": test.question["metadata"],
                },
                "question":test.question["question"],
                "metadata": test.question["metadata"],
                "answers": result['answer'],
                "context": []
            }

        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)

    def save_context(self,test: TestConfiguration, results: List[Dict[str, Any]]) -> None:
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        combo_id = f"{test.index_suffix}"
        if combo_id not in data["tested_combinations"]:
            data["tested_combinations"][combo_id] = {
                "config": {
                    "chunks": test.chunk_field,
                    "distance": test.distance_strategy,
                    "embeddings": test.embedding_model,
                    "llms": test.llm_model,
                    "metadata_option": test.metadata_option,
                    "question": test.question["question"],
                    "metadata": test.question["metadata"],
                },
                "question": test.question["question"],
                "metadata": test.question["metadata"],
                "answers": results['answer'],
                "context": []
            }
        data["tested_combinations"][combo_id]["context"] = [
            {
                "content": source['content'],
                "metadata": source['metadata']
            }
            for source in results['sources']
        ]
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False,indent=1)

    def run_single_test(self, test_config: TestConfiguration) -> None:
        """Run a single parameter combination test"""
        print(f"\n{'='*80}")
        print(f"TESTING COMBINATION: {test_config.index_suffix}")
        print(f"Chunk Field: {test_config.chunk_field}")
        print(f"Distance: {test_config.distance_strategy}")
        print(f"Embedding: {test_config.embedding_model}")
        print(f"LLM: {test_config.llm_model}")
        print(f"metadata: {test_config.metadata_option}")
        print(f"Metadata: {test_config.question["metadata"]}")
        print(f"Question: {test_config.question["question"]}")
        print(f"{'='*80}")
        
        sync = ParametrizedMongoElasticsearchSync(self.config, test_config)
        sync.sync_documents()
        
        doc_count = sync.es_client.count(index=sync.index_name)["count"]
        print(f"Documents in index: {doc_count}")

        if doc_count > 0:
            questions_to_test = test_config.question
        
            result = sync.send_query_with_metadata_filters(
                questions_to_test['question'], 
                questions_to_test['metadata']
            )
            print(f"Q: {result['question']}")
            print(f"A: {result['answer']}")
            print(f"Sources found: {len(result['sources'])}")
            
            if result['sources']:
                self.save_results(test_config, result)
        else:
            print("No documents available for testing queries.")
        sync.close_connections()
    
    def run_all_tests(self, max_combinations: int = None) -> None:
        """Run tests for all parameter combinations"""
        combinations = self.generate_combinations()
        combinations = combinations[:max_combinations]
        
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
        
        for i, test_config in enumerate(untested_combinations, 0):
            self.combo_id = test_config.index_suffix
            if self.is_combination_tested(test_config):
                print(f"⚠️ Combination {self.combo_id} has already been tested. Skipping...")
                continue
            try:
                self.run_single_test(test_config)
                # Save combination as tested after successful completion
                #self.save_tested_combination(test_config)
            except Exception as e:
                print(f"❌ Error in combination {self.combo_id}: {e}")
                print(traceback.format_exc())              

    def load_tested_combinations(self) -> List[str]:
        """Load already tested combinations from file"""
        try:
            with open(result_path, 'r',encoding='utf-8') as f:
                data = json.load(f)
                return data.get("tested_combinations", [])
            return []
        except Exception as e:
            print(f"Error loading tested combinations: {e}")
            return []
        
    def save_tested_combination(self, test_config: TestConfiguration) -> None:
        """Save a tested combination to file"""
        try:
            tested_combinations = self.load_tested_combinations()
            combo_id = self.generate_combo_id(test_config)    
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump({"tested_combinations": tested_combinations}, f,ensure_ascii=False,indent=1)
            print(f"✅ Saved tested combination")
            
        except Exception as e:
            print(traceback.format_exc())
            print(f"Error saving tested combination: {e}")
    
    def is_combination_tested(self, test_config: TestConfiguration) -> bool:
        """Check if a combination has already been tested"""
        tested_combinations = self.load_tested_combinations()
        return test_config.index_suffix in tested_combinations
    
    def generate_combo_id(self, test_config: TestConfiguration) -> Dict[str,Dict[str,str]]:
        """Generate a unique ID for the test configuration"""
        return {
        f"{test_config.index_suffix}": {
            "config": {
        "chunks": test_config.chunk_field,
        "distance": test_config.distance_strategy,
        "embedding": test_config.embedding_model,
        "llms": test_config.llm_model,
        "metadata": test_config.metadata_option,
        "question": test_config.question,
        }}
    }

def main():
    """Main execution function with parameter testing"""
    tester = ParameterTester()
    tester.run_all_tests()  

    
if __name__ == "__main__":
    main()