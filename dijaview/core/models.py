from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SourceType(str, Enum):
    TERMINAL = "terminal"
    BROWSER = "browser"
    NOTES = "notes"
    GIT = "git"


@dataclass
class ActivityRecord:
    id: str
    source_type: str
    source_identifier: str
    timestamp: float
    datetime_iso: str
    title: str
    content: str
    location: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_type": self.source_type,
            "source_identifier": self.source_identifier,
            "timestamp": self.timestamp,
            "datetime_iso": self.datetime_iso,
            "title": self.title,
            "content": self.content,
            "location": self.location,
            "metadata": self.metadata,
        }


@dataclass
class TimeRange:
    start_timestamp: Optional[float] = None
    end_timestamp: Optional[float] = None
    description: Optional[str] = None


@dataclass
class QueryResult:
    query: str
    answer: str
    sources: List[ActivityRecord]
    time_range: Optional[TimeRange] = None
    model_used: str = "gemma2:2b"
    latency_seconds: float = 0.0
