from typing import Any, Protocol


class ProtoLoadable(Protocol):
    @classmethod
    def load(cls, proto: bytes) -> Any:
        ...
