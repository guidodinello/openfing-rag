# Arquitectura RAG

## 1. Módulos Principales

### 1.1 Procesamiento de Audio (Audio Pipeline)
- **Función**: Transcripción y preprocesamiento de audio
- **Componentes**:
  - Whisper ASR (alternativas: Mozilla DeepSpeech, Google Speech-to-Text). 
    - Nos quedamos con Whisper.
  - Procesador de timestamps para mapear texto-tiempo. 
    - Whisper ya los da, pero seguro tengamos que hacer algun pasito extra.
  - Normalizador de texto (eliminar muletillas, corregir errores comunes de ASR). 
    - Seria un nice-to-have.
    

### 1.2 Ingesta y Procesamiento (Data Pipeline)
- **Función**: Preparación y estructuración de datos
- **Componentes**:
  - Chunker inteligente con overlap. 
    - Ya lo implementamos de forma un poco rustica en webir.
    - Facil de hacer con los text splitters de langchain, podriamos hacer algunas pruebitas con diferentes valores, seguramente no valga la pena mucho overlap igual.
    - [Text Splitters | 🦜️🔗 Langchain](https://js.langchain.com/v0.1/docs/modules/data_connection/document_transformers/)
    - [🦜️✂️ Chunk Division and Overlap: Understanding the Process | by Gustavo Espíndola | Medium](https://gustavo-espindola.medium.com/chunk-division-and-overlap-understanding-the-process-ade7eae1b2bd)
    - [what is the advantage of overlapping in chunking strategy : r/LangChain](https://www.reddit.com/r/LangChain/comments/1bjxvov/what_is_the_advantage_of_overlapping_in_chunking/)
  - Extractor de metadatos (tema, timestamp, clase, etc.). 
    - Habria que ver bien lo de los temas, es lo que hablamos en la reu anterior.

### 1.3 Embeddings y Vectorización
- **Función**: Generación y gestión de embeddings
- **Componentes**:
  - Generador de embeddings.
    - [Sentence-BERT (SBERT)](https://sbert.net/) esta bueno, open source, facil integracion con langchain, no es muy costoso de correr, estan hechos especialmente para que sean buenos para busquedas de similitud semantica.
  - Vector store (Chroma/Faiss/Pinecone/Pgvector)
    - Seguramente lo mejor sea pgvector, es open source, si ya usamos postgres para usuarios y eso queda todo consolidado. lo unico malo es que no tiene tantas features especiales que si tiene pinecone como filtrado por metadata y eso. TODO, no se que tan facil se integra con langchain.
    - investigar MyScaleDB parece interesante. [Two-Stage Retrieval with Reranking Functions and MyScale](https://myscale.com/blog/two-stage-retrieval-with-reranking-functions-and-myscale/) se integra con langchain.
    - leere [VDBs](./vdb.md)
  - Cache de embeddings.
    - TODO. No creo que valga la pena, seria un nice-to-have.
    - La idea es evitar recalcular embeddings de preguntas anteriores almacenandolos en una cache como Redis, y cuando llega una pregunta similar usar el valor cacheado.
  - Sistema de reindexación incremental.
    - Importante, feature esencial.
    - TODO. pgvector lo permite. FAISS me acuerdo de webir que podias mergear dos indices pero era bastante lento.

### 1.4 Recuperación
- **Función**: Búsqueda y recuperación contextual
- **Componentes**:
  - Reranker de resultados
    - Feature importante.
    - Mejora de la precisión y relevancia. Reordena los documentos recuperados (usan modelos rerankers, que devuelven un valor de relevancia semantica de un texto para una query) [Mejorando los modelos RAG con reranking y LangChain](https://myscale.com/blog/es/maximizing-advanced-rag-models-langchain-reranking-techniques/)
    - TODO leer [Enhancing Advanced RAG Systems Using Reranking with LangChain | by MyScale | Medium](https://medium.com/@myscale/enhancing-advanced-rag-systems-using-reranking-with-langchain-523a0b840311)
    - [FlashRank reranker | 🦜️🔗 LangChain](https://python.langchain.com/docs/integrations/retrievers/flashrank-reranker/)
    - TODO ver mas del servicio [Rerank Overview — Cohere](https://docs.cohere.com/docs/overview)
  - Sistema de filtrado por metadatos
    - Probablmente no se pueda a no ser que la vdb lo permita.

### 1.5 Generación de Respuestas
- **Función**: Generación de respuestas coherentes
- **Componentes**:
  - LLM (e.g., OpenAI GPT, Anthropic Claude, Llama).
    - Hay que investigar mas. En webir usamos GPT-4 que anda bien, pero seguramente la fing quiera (o tenga la necesidad por algun tema admininstrativo) de setear algo local con algun modelo open source.
    - ver [modelos-open-source](./modelos.md). ideal tener una gpu disponible para el servidor.
      - Mistral 7B, Llama-2 7B (~16GB VRAM para inferencia).
      - [Ǎguila-7B](https://huggingface.co/projecte-aina/aguila-7b) fine tunning sobre [Falcon-7B](https://huggingface.co/tiiuae/falcon-7b) para Catalan, Espanol e Ingles.
      - Phi-2 2.7B (4-8GB VRAM)
      - Tinyllama 1.1B (2-4GB VRAM)
    - Un proyecto a futuro de la facultad podria ser hacer un fine-tunning de algun modelo con contenido academico, como justamente transcripciones de las clases.
    - TODO investigar. Esto es lo mas complicado, el modelo tiene que andar bien sino pierde bastante la gracia del proyecto, pero por costos no podes tener muchas instancias. como haces para atender requests de varios usuarios? va a ser muy lento.
  - Buenos prompts.
    - Ya implementado en webir.
  - Sistema de citación de fuentes.
    - Ya implementado en webir
  - Validador de respuestas

### 1.6 API y Frontend
- **Función**: Interfaz de usuario y API
- **Componentes**:
  - API REST (FastAPI)
  - Sistema de chat UI
  - Sistema de autenticación
  - Endpoints para admin y monitoreo
  - Rate limiting
  - Sesiones y login?
