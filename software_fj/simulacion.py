from __future__ import annotations

import logging
from dataclasses import dataclass

from .exceptions import SoftwareFJError
from .logging_config import log_error, log_event
from .repositorio import SistemaSoftwareFJ


@dataclass
class ResumenSimulacion:
    operaciones: int
    exitos: int
    errores_controlados: int
    errores_no_previstos: int

    def __str__(self) -> str:
        return (
            f"Operaciones: {self.operaciones}\n"
            f"Éxitos: {self.exitos}\n"
            f"Errores controlados: {self.errores_controlados}\n"
            f"Errores no previstos: {self.errores_no_previstos}\n"
            "Log: ./logs/software_fj.log"
        )


def ejecutar_simulacion(logger: logging.Logger | None = None) -> ResumenSimulacion:
    sistema = SistemaSoftwareFJ(logger=logger)

    ops = 0
    ok = 0
    err_ctrl = 0
    err_unk = 0

    def run(nombre: str, fn) -> None:
        nonlocal ops, ok, err_ctrl, err_unk
        ops += 1
        try:
            log_event(f"[SIM] {nombre} | inicio")
            fn()
        except SoftwareFJError as e:
            err_ctrl += 1
            log_error(f"[SIM] {nombre} | error controlado", e)
        except Exception as e:
            err_unk += 1
            log_error(f"[SIM] {nombre} | error no previsto", e)
        else:
            ok += 1
            log_event(f"[SIM] {nombre} | ok")
        finally:
            log_event(f"[SIM] {nombre} | fin")

    # ---- Operaciones (mezcla de válidas e inválidas) ----
    # 1) Cliente válido
    run(
        "Crear cliente válido",
        lambda: sistema.crear_cliente("Ana Pérez", "CC12345", "ana@correo.com", "3001234567"),
    )

    # 2) Cliente inválido (email)
    run(
        "Crear cliente inválido (email)",
        lambda: sistema.crear_cliente("Luis", "CC22222", "correo_sin_arroba", "3001234567"),
    )

    # 3) Servicio válido (sala)
    run(
        "Crear servicio sala válido",
        lambda: sistema.crear_servicio_reserva_sala("Sala A", capacidad=10, tarifa_hora=50.0, requiere_proyector=True),
    )

    # 4) Servicio inválido (tarifa negativa)
    run(
        "Crear servicio sala inválido (tarifa negativa)",
        lambda: sistema.crear_servicio_reserva_sala("Sala B", capacidad=8, tarifa_hora=-10.0, requiere_proyector=False),
    )

    # 5) Servicio válido (equipo)
    run(
        "Crear servicio equipo válido",
        lambda: sistema.crear_servicio_alquiler_equipo("Proyector", "proyector", tarifa_dia=80.0, deposito=50.0, stock_disponible=1),
    )

    # 6) Servicio inválido (stock negativo)
    run(
        "Crear servicio equipo inválido (stock negativo)",
        lambda: sistema.crear_servicio_alquiler_equipo("Cámara", "camara", tarifa_dia=60.0, deposito=30.0, stock_disponible=-1),
    )

    # 7) Servicio válido (asesoría)
    run(
        "Crear servicio asesoría válido",
        lambda: sistema.crear_servicio_asesoria("Asesoría Python", "python", tarifa_hora=100.0, nivel="senior"),
    )

    # Preparar IDs para reservas (si existen)
    def _pick_ids():
        clientes = sistema.listar_clientes()
        servicios = sistema.listar_servicios()
        if not clientes or not servicios:
            raise RuntimeError("No hay datos suficientes para reservas.")
        return clientes[0].id, servicios[0].id, servicios[1].id if len(servicios) > 1 else servicios[0].id

    # 8) Reserva exitosa (cliente0 + sala0)
    run(
        "Crear reserva válida",
        lambda: sistema.crear_reserva(cliente_id=_pick_ids()[0], servicio_id=_pick_ids()[1], duracion=2),
    )

    # 9) Reserva inválida (duración 0)
    run(
        "Crear reserva inválida (duración 0)",
        lambda: sistema.crear_reserva(cliente_id=_pick_ids()[0], servicio_id=_pick_ids()[1], duracion=0),
    )

    # 10) Procesar reserva con impuesto ok (si existe)
    def _procesar_primera():
        reservas = sistema.listar_reservas()
        if not reservas:
            raise RuntimeError("No hay reservas para procesar.")
        sistema.procesar_reserva(reserva_id=reservas[0].id, impuesto=0.19, descuento=10)  # 10% como porcentaje

    run("Procesar primera reserva (ok)", _procesar_primera)

    # 11) Procesar la misma reserva otra vez (operación no permitida si ya confirmada? -> lo dejamos permitido pero idempotente no garantizado)
    def _procesar_dos_veces():
        reservas = sistema.listar_reservas()
        if not reservas:
            raise RuntimeError("No hay reservas.")
        # si ya está confirmada, esto puede generar error por reglas internas o volver a confirmar; de cualquier modo debe estar controlado.
        sistema.procesar_reserva(reserva_id=reservas[0].id, impuesto=0.19, descuento=0)

    run("Procesar reserva (posible repetición)", _procesar_dos_veces)

    # 12) Crear y procesar alquiler de equipo (consume stock), luego intentar otra reserva igual para forzar 'no disponible'
    def _alquiler_sin_stock():
        cliente_id, _, servicio_equipo_id = _pick_ids()
        r1 = sistema.crear_reserva(cliente_id=cliente_id, servicio_id=servicio_equipo_id, duracion=1)
        sistema.procesar_reserva(reserva_id=r1.id, impuesto=0.0, descuento=0.0)
        # Segunda reserva al mismo equipo con stock ya en 0 (debe fallar controlado)
        r2 = sistema.crear_reserva(cliente_id=cliente_id, servicio_id=servicio_equipo_id, duracion=1)
        sistema.procesar_reserva(reserva_id=r2.id, impuesto=0.0, descuento=0.0)

    run("Alquiler de equipo y luego sin stock", _alquiler_sin_stock)

    # 13) Cancelar reserva y volver a cancelar (error controlado)
    def _cancelar_doble():
        reservas = sistema.listar_reservas()
        if not reservas:
            raise RuntimeError("No hay reservas.")
        sistema.cancelar_reserva(reserva_id=reservas[0].id, motivo="Cliente desistió")
        sistema.cancelar_reserva(reserva_id=reservas[0].id, motivo="Segundo intento")

    run("Cancelar reserva dos veces", _cancelar_doble)

    return ResumenSimulacion(
        operaciones=ops,
        exitos=ok,
        errores_controlados=err_ctrl,
        errores_no_previstos=err_unk,
    )

