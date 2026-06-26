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
    "bear": ("PERSON", {"GPE"}),
    "die": ("PERSON", {"GPE"}),
    "study": ("PERSON", {"ORG"}),
    "attend": ("PERSON", {"ORG"}),
    "move": ("PERSON", {"GPE"}),
    "win": ("PERSON", {"EVENT", "PRODUCT", "WORK_OF_ART"}),
    "elect": ("PERSON", {"ORG", "GPE"}),
    "serve": ("PERSON", {"ORG", "GPE"}),
    "star": ("PERSON", {"WORK_OF_ART"}),
    "appear": ("PERSON", {"WORK_OF_ART"}),
    "write": ("PERSON", {"WORK_OF_ART"}),
    "direct": ("PERSON", {"WORK_OF_ART"}),
    "compete": ("PERSON", {"PERSON", "EVENT"}),
    "marry": ("PERSON", {"PERSON"}),
    "divorce": ("PERSON", {"PERSON"}),
    "befriend": ("PERSON", {"PERSON"}),
}

GREEDY_MODE = True
GREEDY_STOP_LEMMAS = {"do", "can", "will", "shall", "may", "must"}
COPULA_LEMMAS = {"be", "become"}
BIRTH_VERBS = {"have", "bear", "father", "mother"}
PREPOSITION_LEMMAS = {"in", "at", "on", "from", "to"}


def _find_entity_by_position(entities: List[Dict], pos: int) -> Optional[Dict]:
    for ent in entities:
        if ent["start"] <= pos < ent["end"]:
            return ent
    return None


def _find_entity_in_subtree(token, entities: List[Dict]) -> Optional[Dict]:
    ent = _find_entity_by_position(entities, token.idx)
    if ent:
        return ent
    for child in token.children:
        ent = _find_entity_in_subtree(child, entities)
        if ent:
            return ent
    return None


def _collect_all_subjects(verb_token):
    subjects = []
    primary = next((child for child in verb_token.children if child.dep_ in ("nsubj", "nsubjpass")), None)
    if primary:
        subjects.append(primary)
        for child in primary.children:
            if child.dep_ == "conj":
                subjects.append(child)
    return subjects


def extract_relations(doc: Doc, entities: List[Dict]) -> List[Dict]:
    relations = []
    last_person = None

    for sent in doc.sents:
        prev_person = last_person
        persons_in_sent = [ent.text for ent in sent.ents if ent.label_ == "PERSON"]

        for token in sent:
            if token.pos_ not in ("VERB", "AUX"):
                continue
            if token.pos_ == "AUX" and token.lemma_ not in COPULA_LEMMAS:
                continue

            lemma = token.lemma_
            is_greedy = False
            is_copula = False
            is_birth = lemma in BIRTH_VERBS

            if lemma in VERB_PATTERNS:
                subj_type, obj_types = VERB_PATTERNS[lemma]
            elif is_birth:
                subj_type = "PERSON"
                obj_types = {"PERSON"}
            elif GREEDY_MODE and lemma not in GREEDY_STOP_LEMMAS and lemma not in COPULA_LEMMAS:
                subj_type = "ANY"
                obj_types = {"PERSON", "ORG", "GPE", "WORK_OF_ART", "EVENT", "FAC", "PRODUCT", "LAW"}
                is_greedy = True
            elif lemma in COPULA_LEMMAS:
                is_copula = True
                subj_type = "ANY"
                obj_types = {"PERSON", "ORG", "GPE", "WORK_OF_ART", "EVENT", "FAC", "PRODUCT", "LAW"}
            else:
                continue

            subjects = _collect_all_subjects(token)

            # Поиск первого объекта
            obj = next((child for child in token.children if child.dep_ in ("dobj", "pobj")), None)
            if not obj:
                for child in token.children:
                    if child.dep_ == "prep":
                        obj = next((c for c in child.children if c.dep_ == "pobj"), None)
                        if obj:
                            break
            if not obj:
                for child in token.children:
                    if child.dep_ in ("attr", "acomp", "oprd"):
                        if is_copula:
                            lemma = child.lemma_
                        for subchild in child.children:
                            if subchild.dep_ == "prep":
                                obj = next((c for c in subchild.children if c.dep_ == "pobj"), None)
                                if obj:
                                    break
                        if obj:
                            break

            if not obj and subjects and is_birth:
                dobj_token = next((child for child in token.children if child.dep_ == "dobj"), None)
                if dobj_token:
                    obj = dobj_token

            if not obj and not subjects:
                continue
            if not obj:
                continue

            # Собираем все сочинённые объекты (conj) для obj
            obj_tokens = [obj]
            for child in obj.children:
                if child.dep_ == "conj":
                    obj_tokens.append(child)

            for subj in subjects:
                subj_ent = _find_entity_by_position(entities, subj.idx)
                if not subj_ent and subj.text.lower() in {"he", "she", "they"} and prev_person:
                    subj_ent = next(
                        (e for e in entities if e["name"] == prev_person and e["type"] == "PERSON"),
                        None,
                    )

                if not subj_ent:
                    continue

                for obj_token in obj_tokens:
                    obj_ent = _find_entity_by_position(entities, obj_token.idx)
                    if not obj_ent and is_birth:
                        obj_ent = _find_entity_in_subtree(obj_token, entities)
                    if not obj_ent:
                        continue

                    # Проверка типов и добавление связи
                    if is_greedy or is_copula or is_birth:
                        if subj_ent["type"] in ("PERSON", "ORG", "GPE") and obj_ent["type"] in obj_types:
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

        # Предложные связи (места и даты)
        for token in sent:
            if token.pos_ != "ADP" or token.lemma_ not in PREPOSITION_LEMMAS:
                continue
            obj = next((child for child in token.children if child.dep_ == "pobj"), None)
            if not obj:
                continue
            obj_ent = _find_entity_by_position(entities, obj.idx)
            if not obj_ent:
                continue
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

        if persons_in_sent:
            last_person = persons_in_sent[-1]

    return relations