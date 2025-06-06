from pymongo import MongoClient
from langchain_core.documents import Document
# from langchain_community.vectorstores import ElasticsearchStore
from langchain_community.embeddings import SentenceTransformerEmbeddings
from elasticsearch import Elasticsearch  # Import the Elasticsearch client
# from langchain_huggingface import HuggingFaceEmbeddings
from langchain_elasticsearch import ElasticsearchStore

# Configura tu conexión a MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["transcriptions_db"]
collection = db["classes"]

# Configura tu conexión a Elasticsearch
es_url = "http://localhost:9200"
index_name = "my_index"  # Reemplaza con el nombre de tu índice
es = Elasticsearch([es_url])

# Configura tu modelo de embeddings
model_name = "all-MiniLM-L6-v2"
embeddings = SentenceTransformerEmbeddings(model_name=model_name)

if es.indices.exists(index=index_name) and es.count(index=index_name)['count'] > 0:
    print(f"El índice '{index_name}' ya existe y contiene documentos. Skipping la carga desde MongoDB.")
    # Initialize es_vectorstore for the case where the index already exists
    es = Elasticsearch(hosts=["http://localhost:9200"])
    es_vectorstore = ElasticsearchStore(
        es_url=[{"host": "localhost", "port": 9200}],
        index_name=index_name,
        embedding=embeddings,
        distance_strategy="COSINE"
    )
else:
    print(f"El índice '{index_name}' no existe o está vacío. Procediendo a cargar desde MongoDB...")
    chunks_from_mongodb = collection.find({})
    langchain_documents = []
    for chunk_data in chunks_from_mongodb:
        chunks_list = chunk_data.get("chunks")

        metadata = {key: value for key, value in chunk_data.items() if key not in ["_id", "chunks"]}

        if isinstance(chunks_list, list):
            for chunk in chunks_list:
                if isinstance(chunk, str) and chunk:
                    doc = Document(page_content=chunk, metadata=metadata.copy())
                    langchain_documents.append(doc)
                elif not isinstance(chunk, str):
                    print(f"Advertencia: Se encontró un elemento no string en la lista de chunks: {chunk}")
        else:
            print(f"Advertencia: El campo 'chunks' no contiene una lista en el documento con _id: {chunk_data.get('_id')}")

    print(f"Se leyeron {len(langchain_documents)} documentos desde MongoDB.")

    if langchain_documents:
        es_vectorstore = ElasticsearchStore.from_documents(
            documents=langchain_documents,
            embedding=embeddings,
            es_url=[{"host": "localhost", "port": 9200}],
            index_name=index_name,
            distance_strategy="COSINE"
        )
        print(f"Se añadieron {len(langchain_documents)} documentos a Elasticsearch.")
    else:
        es_vectorstore = ElasticsearchStore(  
            es_url=[{"host": "localhost", "port": 9200}],
            index_name=index_name,
            embedding=embeddings,
            distance_strategy="COSINE"
        )
        print("No se encontraron documentos para añadir a Elasticsearch, pero se inicializó el vector store.")


retriever = es_vectorstore.as_retriever(search_kwargs={'k': 4})
llm = ChatOpenAI(api_key="") 
qa_chain = RetrievalQA.from_llm(llm=llm, retriever=retriever)
pregunta = "¿Que fuerzas aplican en un auto que esta tomando una curva?"
respuesta = qa_chain.run(pregunta)
print(respuesta)