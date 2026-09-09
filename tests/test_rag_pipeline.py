"""
Unit tests for rag_pipeline.py

Run with: pytest tests/test_rag_pipeline.py -v

Tests the pure logic (chunking) that doesn't require loading the
embedding model, keeping tests fast.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_pipeline import NewsRAGStore


def test_chunk_article_combines_title_and_summary():
    article = {
        "title": "Breaking News",
        "summary": "Something important happened.",
        "link": "http://example.com",
        "source": "Test Source",
    }
    chunks = NewsRAGStore.chunk_article(article)

    assert len(chunks) == 1
    assert "Breaking News" in chunks[0]
    assert "Something important happened." in chunks[0]


def test_chunk_article_returns_single_chunk_for_short_article():
    article = {"title": "T", "summary": "S", "link": "", "source": ""}
    chunks = NewsRAGStore.chunk_article(article)
    assert isinstance(chunks, list)
    assert len(chunks) == 1


def test_retrieve_returns_empty_list_when_index_not_built():
    # Bypass __init__ (which loads the embedding model) since we only
    # want to test behaviour before build_index() has been called.
    store = NewsRAGStore.__new__(NewsRAGStore)
    store.index = None
    store.chunks = []
    store.chunk_metadata = []

    results = store.retrieve("any query")
    assert results == []
