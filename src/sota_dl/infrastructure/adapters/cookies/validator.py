"""Cookie validation logic."""

from datetime import datetime, timezone
from typing import cast, Any
from collections.abc import Mapping
import structlog

logger = structlog.get_logger(__name__)


class CookieValidator:
    """Utility to handle business logic of cookie validation."""

    @staticmethod
    def _is_expired(expires: object, now: datetime, domain: str | None) -> bool:
        """Checks if a cookie has expired."""
        if not isinstance(expires, datetime):
            return False
        
        if expires <= now:
            logger.debug("Cookie expired", domain=domain)
            return True
        return False

    @staticmethod
    def _domain_matches(cookie_domain: str, domain: str) -> bool:
        """Verifies if the cookie domain matches the target domain."""
        stripped = cookie_domain.lstrip(".")
        if not stripped or not domain:
            return True
            
        return any([
            stripped == domain,
            domain.endswith(f".{stripped}"),
            stripped.endswith(f".{domain}")
        ])

    @staticmethod
    def is_valid(
        cookie_meta: Mapping[str, Any], domain: str, now: datetime | None = None
    ) -> bool:
        """Validates a cookie against a domain and expiration."""
        if now is None:
            now = datetime.now(timezone.utc)

        cookie_domain = cast(str, cookie_meta.get("domain", ""))
        expires = cookie_meta.get("expires")

        if CookieValidator._is_expired(expires, now, cookie_domain):
            return False

        if not CookieValidator._domain_matches(cookie_domain, domain):
            logger.debug("Cookie domain mismatch", domain=cookie_domain, target=domain)
            return False
            
        return True
