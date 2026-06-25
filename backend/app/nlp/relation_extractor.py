"""Relation extraction using dependency parsing and verb patterns."""

from typing import Dict, List, Optional

from spacy.tokens import Doc

VERB_PATTERNS = {
    "found": ("PERSON", {"ORG"}),
    "establish": ("PERSON", {"ORG"}),
    "create": ("PERSON", {"ORG"}),
    "start": ("PERSON", {"ORG"}),
    "join": ("PERSON", {"ORG"}),
    "work": ("PERSON", {"ORG", "PERSON"}),
    "live": ("PERSON", {"GPE"}),
    "marry": ("PERSON", {"PERSON"}),
    "befriend": ("PERSON", {"PERSON"}),
    "divorce": ("PERSON", {"PERSON"}),
    "bear": ("PERSON", {"GPE"}), 
    "co": ("PERSON", {"ORG"}),
    "co-found": ("PERSON", {"ORG"}),
    "die": ("PERSON", {"GPE"}),
    "study": ("PERSON", {"ORG"}),
    "attend": ("PERSON", {"ORG"}),
    "move": ("PERSON", {"GPE"}),
}


def _find_entity_by_position(entities: List[Dict], pos: int) -> Optional[Dict]:
    """Возвращает сущность, в чей span (start <= pos < end) попадает позиция pos."""
    for ent in entities:
        if ent["start"] <= pos < ent["end"]:
            return ent
    return None


def extract_relations(doc: Doc, entities: List[Dict]) -> List[Dict]:
    """
    Извлекает связи между сущностями на основе глагольных паттернов.
    entities — список словарей с ключами name, type, start, end, entity_id.
    Возвращает список словарей с ключами: subject, relation, object.
    """
    relations = []
    last_person = None  # хранит последнюю персону из предыдущих предложений

    for sent in doc.sents:
        # Запоминаем last_person на начало предложения
        prev_person = last_person

        # Собираем персоны из текущего предложения (обновим last_person позже)
        persons_in_sent = [ent.text for ent in sent.ents if ent.label_ == "PERSON"]

        for token in sent:
            if token.pos_ != "VERB":
                continue
            lemma = token.lemma_
            if lemma not in VERB_PATTERNS:
                continue

            subj_type, obj_types = VERB_PATTERNS[lemma]

            subj = next(
                (child for child in token.children
                 if child.dep_ in ("nsubj", "nsubjpass")),
                None,
            )

            obj = next(
                (child for child in token.children
                 if child.dep_ in ("dobj", "pobj")),
                None,
            )
            if not obj:
                for child in token.children:
                    if child.dep_ == "prep":
                        obj = next(
                            (c for c in child.children if c.dep_ == "pobj"),
                            None,
                        )
                        if obj:
                            break

            if not subj or not obj:
                continue

            subj_ent = _find_entity_by_position(entities, subj.idx)
            obj_ent = _find_entity_by_position(entities, obj.idx)

            # Разрешение местоимений: используем prev_person (персона из предыдущих предложений)
            if not subj_ent and subj.text.lower() in {"he", "she", "they"} and prev_person:
                subj_ent = next(
                    (e for e in entities
                     if e["name"] == prev_person and e["type"] == "PERSON"),
                    None,
                )

            if subj_ent and obj_ent:
                if subj_ent["type"] == subj_type and obj_ent["type"] in obj_types:
                    relations.append({
                        "subject": {
                            "name": subj_ent["name"],
                            "type": subj_ent["type"],
                            "entity_id": subj_ent["entity_id"],
                        },
                        "relation": lemma,
                        "object": {
                            "name": obj_ent["name"],
                            "type": obj_ent["type"],
                            "entity_id": obj_ent["entity_id"],
                        },
                    })

        # Обновляем last_person после обработки предложения
        if persons_in_sent:
            last_person = persons_in_sent[-1]   # берём последнюю персону в этом предложении

    return relations