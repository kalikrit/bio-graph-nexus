"""Unit tests for NLP pipeline."""
import pytest
from app.nlp.pipeline import process_text

def test_process_text_entities():
    text = "Steve Jobs founded Apple Inc. in Cupertino."
    result = process_text(text)
    entity_names = [e["name"] for e in result["entities"]]
    assert "Steve Jobs" in entity_names
    assert "Apple Inc." in entity_names
    assert "Cupertino" in entity_names

def test_process_text_relations():
    text = "Ada Lovelace was born in London. She worked with Charles Babbage."
    result = process_text(text)
    relations = [(r["subject"]["name"], r["relation"], r["object"]["name"]) for r in result["relations"]]
    # ожидаем связь "born" и "work"
    assert ("Ada Lovelace", "bear", "London") in relations
    assert ("Ada Lovelace", "work", "Charles Babbage") in relations