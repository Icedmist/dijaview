from abc import ABC, abstractmethod
from typing import List
from dijaview.core.models import ActivityRecord


class BaseSourceAdapter(ABC):
    """Abstract base class for all activity source adapters."""

    @abstractmethod
    def source_type(self) -> str:
        """Returns the source type identifier (e.g. 'terminal', 'browser', 'notes')."""
        pass

    @abstractmethod
    def scan_records(self, since_epoch: float = 0.0) -> List[ActivityRecord]:
        """Scans and yields ActivityRecord objects modified or created after since_epoch."""
        pass
