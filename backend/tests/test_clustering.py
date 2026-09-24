"""Unit tests for Embedding and Clustering Engine"""
from app.engine.embedder import EmbeddingEngine
from app.engine.clusterer import SemanticClusterer
from app.channels.base import ChannelItem

def test_embedding_and_clustering():
    embedder = EmbeddingEngine()
    clusterer = SemanticClusterer()

    items = [
        ChannelItem(
            external_id="1", channel="reddit", url="http://1", title="Database Slow",
            content="The database latency is terribly slow and connection pools crash under high load.",
            author="u/dev1", engagement_score=50
        ),
        ChannelItem(
            external_id="2", channel="reddit", url="http://2", title="Connection Pool Issues",
            content="We see constant timeout errors and broken pool limits when scaling up queries.",
            author="u/dev2", engagement_score=45
        ),
        ChannelItem(
            external_id="3", channel="youtube", url="http://3", title="Pricing Review",
            content="The pricing cliff is insane when moving from free tier to enterprise tier.",
            author="u/dev3", engagement_score=80
        ),
        ChannelItem(
            external_id="4", channel="youtube", url="http://4", title="Feature Wish",
            content="I really wish there was native edge streaming support and better webhook integration.",
            author="u/dev4", engagement_score=60
        )
    ]

    texts = [it.content for it in items]
    embeddings = embedder.generate_embeddings(texts)
    assert embeddings.shape[0] == 4

    clusters = clusterer.cluster_items(items, embeddings)
    assert len(clusters) > 0
    for c in clusters:
        assert "title" in c
        assert "category" in c
        assert "quotes" in c
        assert len(c["quotes"]) > 0
