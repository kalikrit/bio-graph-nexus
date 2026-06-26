"""Entity extraction and normalization using spaCy."""

from hashlib import md5
from typing import Dict, List

from spacy.tokens import Doc


def extract_entities(doc: Doc) -> List[Dict]:
    """
    Извлекает сущности из spaCy Doc, объединяя составные токены (B+I).
    Возвращает список словарей с ключами: name, type, start, end, entity_id.
    """
    entities = []
    current_ent = None

    for token in doc:
        if token.ent_iob_ == "B":  # начало новой сущности
            if current_ent:
                entities.append(current_ent)
            current_ent = {
                "name": token.text,
                "type": token.ent_type_,
                "start": token.idx,
                "end": token.idx + len(token.text),
            }
        elif token.ent_iob_ == "I" and current_ent:  # продолжение
            current_ent["name"] += " " + token.text
            current_ent["end"] = token.idx + len(token.text)
        else:
            if current_ent:
                entities.append(current_ent)
                current_ent = None

    if current_ent:
        entities.append(current_ent)

    # Фильтруем только нужные типы (расширенный набор для биографий)
    allowed_types = {
        "PERSON", "ORG", "GPE", "DATE",
        "WORK_OF_ART",   # книги, фильмы, картины
        "EVENT",         # соревнования, конференции
        "FAC",           # здания, аэропорты
        "PRODUCT",       # автомобили, оружие
        "LAW",           # законы, постановления
    }
    entities = [e for e in entities if e["type"] in allowed_types]

    # Добавляем entity_id
    for ent in entities:
        ent["entity_id"] = entity_id(ent["name"], ent["type"])

    return entities


def normalize_entity_name(name: str, type_: str) -> str:
    """
    Нормализует имя сущности:
    - нижний регистр,
    - удаление суффиксов (Inc., Corp. и т.п.).
    """
    name = name.lower().strip()
    # Распространённые корпоративные суффиксы
    suffixes = [
        " inc.", " inc", " corp.", " corp",
        " ltd.", " ltd", " llc", " plc", " limited",
        " incorporated", " corporation", " co.", " co"
    ]
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    name = name.rstrip(".")
    return f"{name}::{type_}"


def entity_id(name: str, type_: str) -> str:
    """
    Генерирует уникальный MD5-хэш для сущности на основе нормализованного имени и типа.
    """
    normalized = normalize_entity_name(name, type_)
    return md5(normalized.encode("utf-8")).hexdigest()