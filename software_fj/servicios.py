from __future__ import annotations

from abc import ABC, abstractmethod

from .entities import EntidadABC
from .exceptions import (
    InconsistentCalculationError,
    InvalidValueError,
    MissingParameterError,
    ServiceNotAvailableError,
)


class Servicio(EntidadABC, ABC):
    """Servicio abstracto del sistema.

    Las implementaciones concretas deben validar sus parámetros y definir
    cómo describen y calculan el costo del servicio (polimorfismo).
    """

    def __init__(self, nombre: str, entity_id: str | None = None) -> None:
        super().__init__(entity_id=entity_id)
        self._nombre = (nombre or "").strip()
        if not self._nombre:
            raise MissingParameterError("El nombre del servicio es requerido.")

    @property
    def nombre(self) -> str:
        return self._nombre

    @abstractmethod
    def validar(self, **kwargs) -> None:
        raise NotImplementedError

    @abstractmethod
    def calcular_costo(self, *args, **kwargs) -> float:
        raise NotImplementedError

    @abstractmethod
    def descripcion(self) -> str:
        raise NotImplementedError

    def resumen(self) -> str:
        return f"Servicio(id={self.id}, tipo={self.__class__.__name__}, nombre={self.nombre})"


def _parse_duracion_impuesto_descuento(*args, **kwargs) -> tuple[float, float, float]:
    """Implementa “sobrecarga” por parámetros opcionales.

    Normaliza:
    - `duracion`: requerido (posicional o keyword)
    - `impuesto`: proporción 0..1 (ej: 0.19)
    - `descuento`: acepta proporción 0..1 o porcentaje 0..100
    """
    if len(args) < 1 and "duracion" not in kwargs:
        raise MissingParameterError("Falta parámetro 'duracion'.")

    try:
        duracion = float(args[0] if len(args) >= 1 else kwargs["duracion"])
    except (TypeError, ValueError) as e:
        raise InvalidValueError("Duración inválida.") from e

    impuesto = kwargs.get("impuesto", 0.0)
    descuento = kwargs.get("descuento", 0.0)

    try:
        impuesto = float(impuesto)
        descuento = float(descuento)
    except (TypeError, ValueError) as e:
        raise InvalidValueError("Impuesto o descuento inválido.") from e

    if duracion <= 0:
        raise InvalidValueError("La duración debe ser mayor que 0.")

    if impuesto < 0 or impuesto > 1:
        # Se define como proporción 0..1 para evitar ambigüedades.
        raise InvalidValueError("Impuesto debe estar entre 0 y 1 (ej: 0.19).")

    # Descuento se acepta como proporción (0..1) o porcentaje (0..100)
    if descuento < 0:
        raise InvalidValueError("Descuento no puede ser negativo.")
    if descuento > 1:
        if descuento > 100:
            raise InvalidValueError("Descuento inválido (usa 0..1 o 0..100).")
        descuento = descuento / 100.0

    if descuento < 0 or descuento > 1:
        raise InvalidValueError("Descuento debe estar entre 0 y 1.")

    return duracion, impuesto, descuento


class ReservaSala(Servicio):
    def __init__(self, nombre: str, capacidad: int, tarifa_hora: float, requiere_proyector: bool = False) -> None:
        super().__init__(nombre=nombre)
        self._capacidad = capacidad
        self._tarifa_hora = tarifa_hora
        self._requiere_proyector = bool(requiere_proyector)
        self.validar()

    def validar(self, **kwargs) -> None:
        if not isinstance(self._capacidad, int) or self._capacidad <= 0:
            raise InvalidValueError("Capacidad inválida para sala.")
        try:
            self._tarifa_hora = float(self._tarifa_hora)
        except (TypeError, ValueError) as e:
            raise InvalidValueError("Tarifa por hora inválida.") from e
        if self._tarifa_hora <= 0:
            raise InvalidValueError("Tarifa por hora debe ser > 0.")

    def descripcion(self) -> str:
        proy = "con proyector" if self._requiere_proyector else "sin proyector"
        return f"Reserva de sala ({self._capacidad} personas, {proy})."

    def calcular_costo(self, *args, **kwargs) -> float:
        duracion, impuesto, descuento = _parse_duracion_impuesto_descuento(*args, **kwargs)
        base = self._tarifa_hora * duracion
        if self._requiere_proyector:
            base += 10.0 * duracion  # cargo fijo por hora por proyector
        total = base * (1 - descuento) * (1 + impuesto)
        if total <= 0:
            raise InconsistentCalculationError("Cálculo inconsistente para ReservaSala.")
        return total


class AlquilerEquipo(Servicio):
    def __init__(self, nombre: str, tipo_equipo: str, tarifa_dia: float, deposito: float, stock_disponible: int) -> None:
        super().__init__(nombre=nombre)
        self._tipo_equipo = (tipo_equipo or "").strip()
        self._tarifa_dia = tarifa_dia
        self._deposito = deposito
        self._stock_disponible = stock_disponible
        self.validar()

    def validar(self, **kwargs) -> None:
        if not self._tipo_equipo:
            raise MissingParameterError("Tipo de equipo requerido.")
        try:
            self._tarifa_dia = float(self._tarifa_dia)
            self._deposito = float(self._deposito)
        except (TypeError, ValueError) as e:
            raise InvalidValueError("Tarifa o depósito inválido.") from e
        if self._tarifa_dia <= 0:
            raise InvalidValueError("Tarifa por día debe ser > 0.")
        if self._deposito < 0:
            raise InvalidValueError("Depósito no puede ser negativo.")
        if not isinstance(self._stock_disponible, int) or self._stock_disponible < 0:
            raise InvalidValueError("Stock disponible inválido.")

    def descripcion(self) -> str:
        return f"Alquiler de equipo ({self._tipo_equipo}, stock={self._stock_disponible})."

    def calcular_costo(self, *args, **kwargs) -> float:
        duracion, impuesto, descuento = _parse_duracion_impuesto_descuento(*args, **kwargs)
        if self._stock_disponible <= 0:
            raise ServiceNotAvailableError("No hay stock disponible para el equipo.")
        base = self._tarifa_dia * duracion + self._deposito
        total = base * (1 - descuento) * (1 + impuesto)
        if total <= 0:
            raise InconsistentCalculationError("Cálculo inconsistente para AlquilerEquipo.")
        return total

    def descontar_stock(self) -> None:
        if self._stock_disponible <= 0:
            raise ServiceNotAvailableError("No se puede descontar stock: 0 disponible.")
        self._stock_disponible -= 1


class AsesoriaEspecializada(Servicio):
    def __init__(self, nombre: str, especialidad: str, tarifa_hora: float, nivel: str) -> None:
        super().__init__(nombre=nombre)
        self._especialidad = (especialidad or "").strip()
        self._tarifa_hora = tarifa_hora
        self._nivel = (nivel or "").strip().lower()
        self.validar()

    def validar(self, **kwargs) -> None:
        if not self._especialidad:
            raise MissingParameterError("Especialidad requerida.")
        try:
            self._tarifa_hora = float(self._tarifa_hora)
        except (TypeError, ValueError) as e:
            raise InvalidValueError("Tarifa por hora inválida.") from e
        if self._tarifa_hora <= 0:
            raise InvalidValueError("Tarifa por hora debe ser > 0.")
        if self._nivel not in {"junior", "mid", "senior"}:
            raise InvalidValueError("Nivel inválido (junior/mid/senior).")

    def descripcion(self) -> str:
        return f"Asesoría especializada ({self._especialidad}, nivel={self._nivel})."

    def calcular_costo(self, *args, **kwargs) -> float:
        duracion, impuesto, descuento = _parse_duracion_impuesto_descuento(*args, **kwargs)
        multiplicador = {"junior": 1.0, "mid": 1.2, "senior": 1.5}[self._nivel]
        base = self._tarifa_hora * multiplicador * duracion
        total = base * (1 - descuento) * (1 + impuesto)
        if total <= 0:
            raise InconsistentCalculationError("Cálculo inconsistente para AsesoriaEspecializada.")
        return total
