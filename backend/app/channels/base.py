"""PulseRadar Channel Adapters Package"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

@dataclass
class ChannelItem:
    external_id: str
    channel: str
    url: str
    title: Optional[str]
    content: str
    author: Optional[str]
    engagement_score: int
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

class BaseChannel(ABC):
    name: str = "base"

    @abstractmethod
    async def search(self, query: str, limit: int = 30) -> list[ChannelItem]:
        """Search the platform for discussions matching the query."""
        pass
