from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .cliente import Cliente
from .entities import EntidadABC
from .exceptions import (
    InvalidValueError,
    OperationNotAllowedError,
    ReservaError,
    SoftwareFJError,
)
from .logging_config import log_error, log_event
from .servicios import Servicio, AlquilerEquipo


class EstadoReserva(str, Enum):
    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"


@dataclass
class ResultadoProcesamiento:
    costo: float
    estado_final: EstadoReserva


class Reserva(EntidadABC):
    """Representa una reserva de un cliente sobre un servicio.

    Maneja estado (pendiente/confirmada/cancelada) y provee `procesar()` con
    manejo avanzado de excepciones y logging para asegurar estabilidad.
    """

    def __init__(
        self,
        cliente: Cliente,
        servicio: Servicio,
        duracion: float,
        entity_id: str | None = None,
    ) -> None:
        super().__init__(entity_id=entity_id)
        self._cliente = cliente
        self._servicio = servicio
        self._duracion = duracion
        self._estado: EstadoReserva = EstadoReserva.PENDIENTE
        self._motivo_cancelacion: Optional[str] = None

        self._validar_base()

    @property
    def cliente(self) -> Cliente:
        return self._cliente

    @property
    def servicio(self) -> Servicio:
        return self._servicio

    @property
    def duracion(self) -> float:
        return self._duracion

    @property
    def estado(self) -> EstadoReserva:
        return self._estado

    def _validar_base(self) -> None:
        try:
            self._duracion = float(self._duracion)
        except (TypeError, ValueError) as e:
            raise InvalidValueError("Duración inválida en la reserva.") from e
        if self._duracion <= 0:
            raise InvalidValueError("La duración de la reserva debe ser > 0.")

    def confirmar(self) -> None:
        if self._estado == EstadoReserva.CANCELADA:
            raise OperationNotAllowedError("No se puede confirmar una reserva cancelada.")
        self._estado = EstadoReserva.CONFIRMADA

    def cancelar(self, motivo: str | None = None) -> None:
        if self._estado == EstadoReserva.CANCELADA:
            raise OperationNotAllowedError("La reserva ya está cancelada.")
        if self._estado == EstadoReserva.CONFIRMADA:
            # Regla conservadora: sí se puede cancelar confirmada, pero queda trazabilidad.
            log_event(f"Cancelación de reserva confirmada (id={self.id}).")
        self._estado = EstadoReserva.CANCELADA
        self._motivo_cancelacion = (motivo or "").strip() or None

    def procesar(self, impuesto: float = 0.0, descuento: float = 0.0) -> ResultadoProcesamiento:
        """Procesa la reserva.

        - try/except: captura errores del dominio y los registra.
        - try/except/else: confirma la reserva cuando no hay fallos.
        - try/except/finally: registra cierre de operación siempre.
        - encadenamiento: envuelve errores no previstos con `raise ... from e`.
        """
        log_event(f"Inicio procesamiento reserva id={self.id} (estado={self._estado}).")
        try:
            if self._estado == EstadoReserva.CANCELADA:
                raise OperationNotAllowedError("No se puede procesar una reserva cancelada.")

            # Validación del servicio (polimórfica)
            self._servicio.validar()

            # Cálculo de costos con “sobrecarga” por kwargs
            costo = self._servicio.calcular_costo(self._duracion, impuesto=impuesto, descuento=descuento)

        except SoftwareFJError as e:
            # Error controlado: se registra y no se cae la aplicación.
            log_error(f"Error controlado al procesar reserva id={self.id}.", e)
            raise
        except Exception as e:
            wrapped = ReservaError(f"Fallo no previsto procesando reserva id={self.id}.")  # noqa: TRY003
            log_error("Error no previsto (se envuelve a ReservaError).", wrapped)
            raise wrapped from e
        else:
            # Si es alquiler de equipo, consumir stock al confirmar.
            if isinstance(self._servicio, AlquilerEquipo):
                self._servicio.descontar_stock()
            self.confirmar()
            log_event(f"Reserva confirmada id={self.id}. Costo={costo:.2f}")
            return ResultadoProcesamiento(costo=costo, estado_final=self._estado)
        finally:
            log_event(f"Fin procesamiento reserva id={self.id} (estado={self._estado}).")

    def resumen(self) -> str:
        return (
            f"Reserva(id={self.id}, cliente={self._cliente.documento}, "
            f"servicio={self._servicio.nombre}, duracion={self._duracion}, estado={self._estado})"
        )
