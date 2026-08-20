from abc import ABC, abstractmethod
from sota_dl.infrastructure.adapters.cookies.types import ExtractionResult

class CookieExtractionStrategy(ABC):
    """Abstract base class for browser-specific cookie extraction strategies."""

    @abstractmethod
    def extract(self, domain: str) -> ExtractionResult:
        """Extract cookies for a specific domain."""
        ...
