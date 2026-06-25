"""Main NLP pipeline: extract entities and relations from text."""

from typing import Dict, List

import spacy

from app.nlp.entity_extractor import extract_entities
from app.nlp.relation_extractor import extract_relations

# Загружаем модель один раз при старте приложения
nlp = spacy.load("en_core_web_lg")
# nlp = spacy.load("ru_core_news_lg")


def process_text(text: str) -> Dict[str, List[Dict]]:
    """
    Принимает текст, возвращает словарь:
    {
        "entities": [...],
        "relations": [...]
    }
    """
    doc = nlp(text)
    entities = extract_entities(doc)
    relations = extract_relations(doc, entities)

    return {
        "entities": entities,
        "relations": relations,
    }