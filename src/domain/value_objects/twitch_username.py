import re
from dataclasses import dataclass

@dataclass(frozen=True)
class TwitchUsername:
    value: str

    def __post_init__(self):
        if not re.fullmatch(r"[a-zA-Z0-9_]{4,25}", self.value):
            raise ValueError(f"Username Twitch inválido: {self.value}")
        object.__setattr__(self, "value", self.value.lower())