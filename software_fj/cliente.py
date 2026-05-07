from __future__ import annotations

import re

from .entities import EntidadABC
from .exceptions import InvalidValueError, MissingParameterError, ValidationError


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_DOC_RE = re.compile(r"^[A-Za-z0-9\-\.]{4,30}$")
_PHONE_RE = re.compile(r"^[0-9]{7,15}$")


class Cliente(EntidadABC):
    def __init__(self, nombre: str, documento: str, email: str, telefono: str, entity_id: str | None = None) -> None:
        super().__init__(entity_id=entity_id)
        self._nombre = ""
        self._documento = ""
        self._email = ""
        self._telefono = ""

        self.nombre = nombre
        self.documento = documento
        self.email = email
        self.telefono = telefono

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, value: str) -> None:
        value = (value or "").strip()
        if not value:
            raise MissingParameterError("El nombre es requerido.")
        if len(value) < 2 or len(value) > 80:
            raise InvalidValueError("El nombre debe tener entre 2 y 80 caracteres.")
        self._nombre = value

    @property
    def documento(self) -> str:
        return self._documento

    @documento.setter
    def documento(self, value: str) -> None:
        value = (value or "").strip()
        if not value:
            raise MissingParameterError("El documento es requerido.")
        if not _DOC_RE.match(value):
            raise InvalidValueError("Documento inválido (4-30, alfanumérico con - o .).")
        self._documento = value

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        value = (value or "").strip()
        if not value:
            raise MissingParameterError("El email es requerido.")
        if not _EMAIL_RE.match(value):
            raise ValidationError("Email inválido.")
        self._email = value

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, value: str) -> None:
        value = (value or "").strip()
        if not value:
            raise MissingParameterError("El teléfono es requerido.")
        if not _PHONE_RE.match(value):
            raise InvalidValueError("Teléfono inválido (solo números, 7-15 dígitos).")
        self._telefono = value

    def resumen(self) -> str:
        return f"Cliente(id={self.id}, documento={self.documento}, nombre={self.nombre}, email={self.email}, tel={self.telefono})"

