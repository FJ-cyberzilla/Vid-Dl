from sota_dl.infrastructure.adapters.cookies.strategy import CookieExtractionStrategy
from sota_dl.infrastructure.adapters.cookies.types import ExtractionResult
from sota_dl.config.settings import COOKIES_PATH


class NetscapeCookieStrategy(CookieExtractionStrategy):
    """Strategy for Netscape/Mozilla formatted cookies.txt file."""

    def extract(self, domain: str) -> ExtractionResult:
        """
        Extract cookies from a Netscape/Mozilla formatted cookies.txt file
        filtered by domain.
        """
        if not COOKIES_PATH.exists():
            return self._error_result("cookies.txt not found")

        try:
            return self._process_cookies_file(domain)
        except Exception as e:
            return self._error_result(f"cookies.txt read failed: {e}")

    def _process_cookies_file(self, domain: str) -> ExtractionResult:
        """Reads and processes the cookie file."""
        cookies_dict: dict[str, str] = {}
        with open(COOKIES_PATH, encoding="utf-8") as f:
            for line in f:
                self._parse_netscape_line(line, domain, cookies_dict)

        if not cookies_dict:
            return self._error_result("No matching cookies in cookies.txt")

        return ExtractionResult(
            success=True, cookies=cookies_dict, source="cookies_txt"
        )

    def _error_result(self, error: str) -> ExtractionResult:
        """Helper to create an error ExtractionResult."""
        return ExtractionResult(success=False, cookies={}, error=error)

    def _parse_netscape_line(
        self, line: str, domain: str, cookies_dict: dict[str, str]
    ) -> None:
        """Parses a single line from Netscape cookie file."""
        line = line.strip()
        if self._is_ignorable(line):
            return

        parts = line.split("\t")
        if self._is_valid_parts(parts) and self._domain_match(parts[0], domain):
            cookies_dict[parts[5]] = parts[6]

    def _is_ignorable(self, line: str) -> bool:
        """Checks if a line should be ignored."""
        return not line or line.startswith("#")

    def _is_valid_parts(self, parts: list[str]) -> bool:
        """Checks if the parsed line has enough components."""
        return len(parts) >= 7

    def _domain_match(self, cookie_domain: str, domain: str) -> bool:
        """Checks if the domain matches."""
        return domain in cookie_domain or cookie_domain in domain
