"""Unit tests for TextCleaner and Deduplication Engine"""
from app.engine.cleaner import TextCleaner
from app.channels.base import ChannelItem

def test_text_cleaner_noise_removal():
    cleaner = TextCleaner()
    raw = "Here is my honest opinion. I am a bot, and this action was performed automatically. Please contact the moderators."
    cleaned = cleaner.clean_text(raw)
    assert "i am a bot" not in cleaned.lower()
    assert "honest opinion" in cleaned

def test_deduplication():
    cleaner = TextCleaner()
    items = [
        ChannelItem(
            external_id="1", channel="reddit", url="http://a", title="Post A",
            content="This is a great complaint about latency and database performance.",
            author="u/test1", engagement_score=10
        ),
        ChannelItem(
            external_id="2", channel="reddit", url="http://b", title="Post B",
            content="This is a great complaint about latency and database performance.",  # duplicate
            author="u/test2", engagement_score=15
        ),
        ChannelItem(
            external_id="3", channel="youtube", url="http://c", title="Post C",
            content="A completely different topic discussing missing edge runtime support.",
            author="u/test3", engagement_score=20
        ),
        ChannelItem(
            external_id="4", channel="reddit", url="http://d", title="Short",
            content="Too short",  # < 40 chars
            author="u/test4", engagement_score=5
        )
    ]
    
    deduped = cleaner.deduplicate_and_clean(items)
    assert len(deduped) == 2
    assert deduped[0].external_id == "1"
    assert deduped[1].external_id == "3"
