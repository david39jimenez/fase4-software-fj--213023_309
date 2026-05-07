from __future__ import annotations

import logging
from typing import Optional

from .cliente import Cliente
from .exceptions import (
    BookingConflictError,
    ClienteError,
    InvalidValueError,
    MissingParameterError,
    OperationNotAllowedError,
    ReservaError,
    ServiceNotAvailableError,
    ServicioError,
)
from .logging_config import log_event
from .reserva import Reserva, EstadoReserva
from .servicios import AlquilerEquipo, AsesoriaEspecializada, ReservaSala, Servicio


class SistemaSoftwareFJ:
    """Orquestador del sistema.

    Mantiene la información en memoria mediante listas internas y expone
    operaciones de alto nivel para crear/buscar/listar clientes, servicios
    y reservas.
    """

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._logger = logger
        self._clientes: list[Cliente] = []
        self._servicios: list[Servicio] = []
        self._reservas: list[Reserva] = []

    # ---- Clientes ----
    def crear_cliente(self, nombre: str, documento: str, email: str, telefono: str) -> Cliente:
        """Crea y registra un cliente validando los datos."""
        cliente = Cliente(nombre=nombre, documento=documento, email=email, telefono=telefono)
        self.registrar_cliente(cliente)
        return cliente

    def registrar_cliente(self, cliente: Cliente) -> None:
        """Registra un cliente en la lista interna validando duplicados."""
        if any(c.documento == cliente.documento for c in self._clientes):
            raise ClienteError(f"Ya existe un cliente con documento {cliente.documento}.")
        self._clientes.append(cliente)
        log_event(f"Cliente registrado id={cliente.id} documento={cliente.documento}.")

    def buscar_cliente(self, cliente_id: str) -> Cliente:
        """Busca un cliente por id; si no existe lanza excepción de dominio."""
        cliente_id = (cliente_id or "").strip()
        if not cliente_id:
            raise MissingParameterError("cliente_id requerido.")
        for c in self._clientes:
            if c.id == cliente_id:
                return c
        raise ClienteError(f"Cliente no encontrado (id={cliente_id}).")

    def listar_clientes(self) -> list[Cliente]:
        return list(self._clientes)

    # ---- Servicios ----
    def crear_servicio_reserva_sala(self, nombre: str, capacidad: int, tarifa_hora: float, requiere_proyector: bool) -> Servicio:
        """Crea y registra un servicio de ReservaSala."""
        servicio = ReservaSala(nombre=nombre, capacidad=capacidad, tarifa_hora=tarifa_hora, requiere_proyector=requiere_proyector)
        self.registrar_servicio(servicio)
        return servicio

    def crear_servicio_alquiler_equipo(
        self,
        nombre: str,
        tipo_equipo: str,
        tarifa_dia: float,
        deposito: float,
        stock_disponible: int,
    ) -> Servicio:
        """Crea y registra un servicio de AlquilerEquipo."""
        servicio = AlquilerEquipo(
            nombre=nombre,
            tipo_equipo=tipo_equipo,
            tarifa_dia=tarifa_dia,
            deposito=deposito,
            stock_disponible=stock_disponible,
        )
        self.registrar_servicio(servicio)
        return servicio

    def crear_servicio_asesoria(self, nombre: str, especialidad: str, tarifa_hora: float, nivel: str) -> Servicio:
        """Crea y registra un servicio de AsesoriaEspecializada."""
        servicio = AsesoriaEspecializada(nombre=nombre, especialidad=especialidad, tarifa_hora=tarifa_hora, nivel=nivel)
        self.registrar_servicio(servicio)
        return servicio

    def registrar_servicio(self, servicio: Servicio) -> None:
        """Registra un servicio en la lista interna."""
        self._servicios.append(servicio)
        log_event(f"Servicio registrado id={servicio.id} tipo={servicio.__class__.__name__} nombre={servicio.nombre}.")

    def buscar_servicio(self, servicio_id: str) -> Servicio:
        servicio_id = (servicio_id or "").strip()
        if not servicio_id:
            raise MissingParameterError("servicio_id requerido.")
        for s in self._servicios:
            if s.id == servicio_id:
                return s
        raise ServicioError(f"Servicio no encontrado (id={servicio_id}).")

    def listar_servicios(self) -> list[Servicio]:
        return list(self._servicios)

    # ---- Reservas ----
    def crear_reserva(self, cliente_id: str, servicio_id: str, duracion: float) -> Reserva:
        """Crea una reserva integrando cliente, servicio y duración.

        Incluye una regla simple de conflicto para demostrar control del dominio.
        """
        cliente = self.buscar_cliente(cliente_id)
        servicio = self.buscar_servicio(servicio_id)

        # Ejemplo de conflicto simple: no permitir dos reservas pendientes iguales (cliente+servicio)
        for r in self._reservas:
            if r.estado != EstadoReserva.CANCELADA and r.cliente.id == cliente.id and r.servicio.id == servicio.id:
                raise BookingConflictError("Conflicto: ya existe una reserva activa para ese cliente y servicio.")

        reserva = Reserva(cliente=cliente, servicio=servicio, duracion=duracion)
        self._reservas.append(reserva)
        log_event(f"Reserva creada id={reserva.id} cliente={cliente.documento} servicio={servicio.nombre}.")
        return reserva

    def buscar_reserva(self, reserva_id: str) -> Reserva:
        reserva_id = (reserva_id or "").strip()
        if not reserva_id:
            raise MissingParameterError("reserva_id requerido.")
        for r in self._reservas:
            if r.id == reserva_id:
                return r
        raise ReservaError(f"Reserva no encontrada (id={reserva_id}).")

    def procesar_reserva(self, reserva_id: str, impuesto: float = 0.0, descuento: float = 0.0) -> float:
        """Procesa (valida, calcula costo y confirma) una reserva."""
        reserva = self.buscar_reserva(reserva_id)

        # Ejemplo de regla: si el servicio es alquiler y no hay stock, se falla.
        if isinstance(reserva.servicio, AlquilerEquipo) and getattr(reserva.servicio, "_stock_disponible", 0) <= 0:
            raise ServiceNotAvailableError("Servicio no disponible: stock en 0.")

        resultado = reserva.procesar(impuesto=impuesto, descuento=descuento)
        return resultado.costo

    def cancelar_reserva(self, reserva_id: str, motivo: str | None = None) -> None:
        """Cancela una reserva registrando el evento."""
        reserva = self.buscar_reserva(reserva_id)
        reserva.cancelar(motivo=motivo)
        log_event(f"Reserva cancelada id={reserva.id} motivo={motivo or ''}".strip())

    def listar_reservas(self) -> list[Reserva]:
        return list(self._reservas)
