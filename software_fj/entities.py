from __future__ import annotations

from abc import ABC, abstractmethod
import uuid


class EntidadABC(ABC):
    def __init__(self, entity_id: str | None = None) -> None:
        self._id = entity_id or str(uuid.uuid4())

    @property
    def id(self) -> str:
        return self._id

    @abstractmethod
    def resumen(self) -> str:
        raise NotImplementedError

