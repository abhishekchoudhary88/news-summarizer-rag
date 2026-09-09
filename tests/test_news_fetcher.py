"""
Unit tests for news_fetcher.py

Run with: pytest tests/test_news_fetcher.py -v

We mock feedparser.parse so tests don't depend on network access -
this makes tests fast, reliable, and runnable in CI/CD pipelines.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import news_fetcher


class FakeEntry(dict):
    """Mimics feedparser's entry object (supports .get())"""
    def get(self, key, default=""):
        return dict.get(self, key, default)


class FakeFeed:
    def __init__(self, entries):
        self.entries = entries


def test_fetch_articles_parses_entries_correctly(monkeypatch):
    fake_entries = [
        FakeEntry(title="Test Headline 1", summary="Summary 1", link="http://example.com/1"),
        FakeEntry(title="Test Headline 2", summary="Summary 2", link="http://example.com/2"),
    ]

    def fake_parse(url):
        return FakeFeed(fake_entries)

    monkeypatch.setattr(news_fetcher.feedparser, "parse", fake_parse)

    articles = news_fetcher.fetch_articles(selected_feeds=["BBC World"], limit_per_feed=10)

    assert len(articles) == 2
    assert articles[0]["title"] == "Test Headline 1"
    assert articles[0]["source"] == "BBC World"


def test_fetch_articles_respects_limit_per_feed(monkeypatch):
    fake_entries = [FakeEntry(title=f"Headline {i}", summary="x", link="http://x.com") for i in range(20)]

    def fake_parse(url):
        return FakeFeed(fake_entries)

    monkeypatch.setattr(news_fetcher.feedparser, "parse", fake_parse)

    articles = news_fetcher.fetch_articles(selected_feeds=["BBC World"], limit_per_feed=5)

    assert len(articles) == 5


def test_fetch_articles_handles_empty_feed_list():
    articles = news_fetcher.fetch_articles(selected_feeds=[], limit_per_feed=10)
    assert articles == []
