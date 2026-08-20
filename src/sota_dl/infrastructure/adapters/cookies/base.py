from typing import Protocol
from dataclasses import dataclass


@dataclass
class Cookie:
    domain: str
    name: str
    value: str
    path: str = "/"
    secure: bool = False


class ICookieStrategy(Protocol):
    def can_handle(self, source: str) -> bool: ...

    def extract(self) -> list[Cookie]: ...
