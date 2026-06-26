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
    "bear": ("PERSON", {"GPE"}),               # was born → лемма "bear"
    "die": ("PERSON", {"GPE"}),
    "study": ("PERSON", {"ORG"}),
    "attend": ("PERSON", {"ORG"}),
    "move": ("PERSON", {"GPE"}),
}

# Жадный режим: извлекать любые глагольные связи между людьми, организациями и местами
GREEDY_MODE = True
GREEDY_STOP_LEMMAS = {"be", "have", "do", "can", "will", "shall", "may", "must", "become"}

# Предлоги, которые могут создавать связи (место, время)
PREPOSITION_LEMMAS = {"in", "at", "on", "from", "to"}


def _find_entity_by_position(entities: List[Dict], pos: int) -> Optional[Dict]:
    """Возвращает сущность, в чей span (start <= pos < end) попадает позиция pos."""
    for ent in entities:
        if ent["start"] <= pos < ent["end"]:
            return ent
    return None


def extract_relations(doc: Doc, entities: List[Dict]) -> List[Dict]:
    """
    Извлекает связи между сущностями на основе глагольных паттернов или жадного режима,
    а также предложные связи для мест и дат.
    entities — список словарей с ключами name, type, start, end, entity_id.
    Возвращает список словарей с ключами: subject, relation, object.
    """
    relations = []
    last_person = None  # хранит последнюю персону из предыдущих предложений

    for sent in doc.sents:
        prev_person = last_person

        # Собираем персоны из текущего предложения (обновим last_person позже)
        persons_in_sent = [ent.text for ent in sent.ents if ent.label_ == "PERSON"]

        # --- Глагольные связи ---
        for token in sent:
            if token.pos_ != "VERB":
                continue

            lemma = token.lemma_
            is_greedy = False

            if lemma in VERB_PATTERNS:
                subj_type, obj_types = VERB_PATTERNS[lemma]
            elif GREEDY_MODE and lemma not in GREEDY_STOP_LEMMAS:
                subj_type = "ANY"
                obj_types = {"PERSON", "ORG", "GPE"}
                is_greedy = True
            else:
                continue

            # Субъект (nsubj или nsubjpass)
            subj = next(
                (child for child in token.children
                 if child.dep_ in ("nsubj", "nsubjpass")),
                None,
            )

            # Объект (прямой или через предлог)
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
            # Если объект не найден, проверим атрибутивные конструкции (became friends with...)
            if not obj:
                for child in token.children:
                    if child.dep_ == "attr":
                        for subchild in child.children:
                            if subchild.dep_ == "prep":
                                obj = next(
                                    (c for c in subchild.children if c.dep_ == "pobj"),
                                    None,
                                )
                                if obj:
                                    break
                        if obj:
                            break

            if not subj or not obj:
                continue

            subj_ent = _find_entity_by_position(entities, subj.idx)
            obj_ent = _find_entity_by_position(entities, obj.idx)

            # Разрешение местоимений
            if not subj_ent and subj.text.lower() in {"he", "she", "they"} and prev_person:
                subj_ent = next(
                    (e for e in entities
                     if e["name"] == prev_person and e["type"] == "PERSON"),
                    None,
                )

            if subj_ent and obj_ent:
                if is_greedy:
                    if subj_ent["type"] in ("PERSON", "ORG", "GPE") and obj_ent["type"] in obj_types:
                        relations.append({
                            "subject": {
                                "name": subj_ent["name"],
                                "type": subj_ent["type"],
                                "entity_id": subj_ent["entity_id"],
                            },
                            "relation": token.lemma_,
                            "object": {
                                "name": obj_ent["name"],
                                "type": obj_ent["type"],
                                "entity_id": obj_ent["entity_id"],
                            },
                        })
                else:
                    if subj_ent["type"] == subj_type and obj_ent["type"] in obj_types:
                        relations.append({
                            "subject": {
                                "name": subj_ent["name"],
                                "type": subj_ent["type"],
                                "entity_id": subj_ent["entity_id"],
                            },
                            "relation": token.lemma_,
                            "object": {
                                "name": obj_ent["name"],
                                "type": obj_ent["type"],
                                "entity_id": obj_ent["entity_id"],
                            },
                        })

        # --- Предложные связи (места и даты) ---
        for token in sent:
            if token.pos_ != "ADP" or token.lemma_ not in PREPOSITION_LEMMAS:
                continue

            obj = next((child for child in token.children if child.dep_ == "pobj"), None)
            if not obj:
                continue

            obj_ent = _find_entity_by_position(entities, obj.idx)
            if not obj_ent:
                continue

            # Субъект — последняя персона текущего предложения (если есть)
            current_person = persons_in_sent[-1] if persons_in_sent else None
            if not current_person:
                continue

            subj_ent = next(
                (e for e in entities if e["name"] == current_person and e["type"] == "PERSON"),
                None,
            )
            if not subj_ent:
                continue

            if obj_ent["type"] not in {"GPE", "LOC", "DATE"}:
                continue

            relations.append({
                "subject": {
                    "name": subj_ent["name"],
                    "type": subj_ent["type"],
                    "entity_id": subj_ent["entity_id"],
                },
                "relation": token.lemma_,
                "object": {
                    "name": obj_ent["name"],
                    "type": obj_ent["type"],
                    "entity_id": obj_ent["entity_id"],
                },
            })

        # Обновляем last_person после обработки предложения
        if persons_in_sent:
            last_person = persons_in_sent[-1]

    return relations