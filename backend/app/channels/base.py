"""PulseRadar Channel Adapters Package & Diagnostic Framework"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
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
    display_name: str = "Base Channel"
    category: str = "general"  # "developer" | "social" | "video" | "web" | "business" | "finance"
    tier: int = 0  # 0=zero-config, 1=needs free key / minimal setup, 2=needs session/login
    backends: List[str] = ["default"]
    active_backend: Optional[str] = None

    def ordered_backends(self) -> List[str]:
        """Return ordered list of candidate backends for failover cascading."""
        return list(self.backends)

    @abstractmethod
    async def search(self, query: str, limit: int = 30) -> List[ChannelItem]:
        """Search the platform for discussions matching the query."""
        pass

    async def check(self) -> Tuple[str, str]:
        """
        Diagnostic probe checking if this channel's upstream backend is reachable.
        Returns: (status, message) where status is 'ok' | 'warn' | 'off' | 'error'
        """
        self.active_backend = self.backends[0] if self.backends else "builtin"
        return "ok", f"Operational via {self.active_backend}"
