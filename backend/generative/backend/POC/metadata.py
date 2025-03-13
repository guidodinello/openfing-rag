import spacy
from bertopic import BERTopic
from keybert import KeyBERT
from transformers import pipeline


# TODO: not used atm
class TopicExtractor:
    def __init__(self):
        self.nlp = spacy.load("es_core_news_lg")
        self.kw_model = KeyBERT()
        self.bertopic = BERTopic(language="spanish")
        self.zero_shot = pipeline(
            "zero-shot-classification", model="facebook/bart-large-mnli"
        )

    def extract_keywords_keybert(self, text, top_n=5):
        """Extrae keywords usando KeyBERT"""
        keywords = self.kw_model.extract_keywords(
            text, keyphrase_ngram_range=(1, 2), stop_words="spanish", top_n=top_n
        )
        return [keyword for keyword, _ in keywords]

    def extract_topics_bertopic(self, texts):
        """Extrae topics usando BERTopic"""
        topics, _ = self.bertopic.fit_transform(texts)
        return self.bertopic.get_topic_info()

    def extract_entities(self, text):
        """Extrae entidades nombradas usando spaCy"""
        doc = self.nlp(text)
        entities = {}
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            entities[ent.label_].append(ent.text)
        return entities

    def classify_zero_shot(self, text, candidate_topics):
        """Clasifica el texto en temas predefinidos usando zero-shot"""
        result = self.zero_shot(text, candidate_topics)
        return dict(zip(result["labels"], result["scores"]))

    def extract_topics_comprehensive(self, text, course_topics=None):
        """Pipeline completo de extracción de temas"""
        results = {
            "keywords": self.extract_keywords_keybert(text),
            "entities": self.extract_entities(text),
        }

        # Si tenemos temas predefinidos del curso, usamos zero-shot
        if course_topics:
            results["topic_classification"] = self.classify_zero_shot(
                text, course_topics
            )

        return results


# Ejemplo de uso para una clase de Computación 1
course_topics = [
    "Algoritmos",
    "Estructuras de Datos",
    "Programación Orientada a Objetos",
    "Complejidad Computacional",
    "Variables y Tipos de Datos",
    "Control de Flujo",
    "Funciones",
    "Arrays y Listas",
]


# Ejemplo de procesamiento de una transcripción
def process_transcript_segment(text, timestamp, extractor):
    metadata = {
        "timestamp": timestamp,
        "length": len(text),
        "topics": extractor.extract_topics_comprehensive(text, course_topics),
    }
    return metadata


# Ejemplo de cómo estructurar los metadatos en la base de datos
metadata_schema = {
    "transcript_id": "uuid",
    "segment_id": "integer",
    "timestamp_start": "timestamp",
    "timestamp_end": "timestamp",
    "text": "text",
    "keywords": "text[]",
    "main_topic": "text",
    "topic_confidence": "float",
    "subtopics": "jsonb",
    "entities": "jsonb",
    "course_section": "text",
    "lecture_number": "integer",
}
