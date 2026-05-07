from __future__ import annotations

from software_fj.logging_config import get_logger, log_error, log_event
from software_fj.repositorio import SistemaSoftwareFJ
from software_fj.simulacion import ejecutar_simulacion
from software_fj.exceptions import SoftwareFJError


def _input_non_empty(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Valor requerido. Intenta de nuevo.")


def _input_float(prompt: str) -> float:
    while True:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except Exception:
            print("Número inválido. Intenta de nuevo.")


def _input_int(prompt: str) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            return int(raw)
        except Exception:
            print("Número inválido. Intenta de nuevo.")


def _menu() -> None:
    logger = get_logger()
    sistema = SistemaSoftwareFJ(logger=logger)

    while True:
        print("\n=== Software FJ | Gestión de Clientes, Servicios y Reservas ===")
        print("1. Registrar cliente")
        print("2. Crear servicio (3 tipos)")
        print("3. Crear reserva")
        print("4. Procesar/confirmar reserva")
        print("5. Cancelar reserva")
        print("6. Listar (clientes/servicios/reservas)")
        print("7. Ejecutar simulación (10+ operaciones)")
        print("0. Salir")

        opcion = input("Opción: ").strip()

        try:
            if opcion == "1":
                nombre = _input_non_empty("Nombre: ")
                documento = _input_non_empty("Documento: ")
                email = _input_non_empty("Email: ")
                telefono = _input_non_empty("Teléfono: ")
                cliente = sistema.crear_cliente(nombre=nombre, documento=documento, email=email, telefono=telefono)
                print(f"Cliente registrado: {cliente.resumen()}")

            elif opcion == "2":
                print("\nTipos de servicio:")
                print("1) Reserva de sala")
                print("2) Alquiler de equipo")
                print("3) Asesoría especializada")
                tipo = input("Tipo: ").strip()

                if tipo == "1":
                    nombre = _input_non_empty("Nombre del servicio: ")
                    capacidad = _input_int("Capacidad (personas): ")
                    tarifa_hora = _input_float("Tarifa por hora: ")
                    requiere = input("¿Requiere proyector? (s/n): ").strip().lower() == "s"
                    servicio = sistema.crear_servicio_reserva_sala(
                        nombre=nombre,
                        capacidad=capacidad,
                        tarifa_hora=tarifa_hora,
                        requiere_proyector=requiere,
                    )
                elif tipo == "2":
                    nombre = _input_non_empty("Nombre del servicio: ")
                    tipo_equipo = _input_non_empty("Tipo de equipo: ")
                    tarifa_dia = _input_float("Tarifa por día: ")
                    deposito = _input_float("Depósito: ")
                    stock = _input_int("Stock disponible: ")
                    servicio = sistema.crear_servicio_alquiler_equipo(
                        nombre=nombre,
                        tipo_equipo=tipo_equipo,
                        tarifa_dia=tarifa_dia,
                        deposito=deposito,
                        stock_disponible=stock,
                    )
                elif tipo == "3":
                    nombre = _input_non_empty("Nombre del servicio: ")
                    especialidad = _input_non_empty("Especialidad: ")
                    tarifa_hora = _input_float("Tarifa por hora: ")
                    nivel = _input_non_empty("Nivel (junior/mid/senior): ")
                    servicio = sistema.crear_servicio_asesoria(
                        nombre=nombre,
                        especialidad=especialidad,
                        tarifa_hora=tarifa_hora,
                        nivel=nivel,
                    )
                else:
                    print("Tipo inválido.")
                    continue

                print(f"Servicio registrado: {servicio.resumen()}")

            elif opcion == "3":
                cliente_id = _input_non_empty("ID cliente: ")
                servicio_id = _input_non_empty("ID servicio: ")
                duracion = _input_float("Duración (horas o días): ")
                reserva = sistema.crear_reserva(cliente_id=cliente_id, servicio_id=servicio_id, duracion=duracion)
                print(f"Reserva creada: {reserva.resumen()}")

            elif opcion == "4":
                reserva_id = _input_non_empty("ID reserva: ")
                impuesto = _input_float("Impuesto (ej 0.19): ")
                descuento = _input_float("Descuento (0-1 o 0-100, según regla): ")
                costo = sistema.procesar_reserva(reserva_id=reserva_id, impuesto=impuesto, descuento=descuento)
                print(f"Reserva procesada/confirmada. Costo: {costo:.2f}")

            elif opcion == "5":
                reserva_id = _input_non_empty("ID reserva: ")
                motivo = input("Motivo (opcional): ").strip() or None
                sistema.cancelar_reserva(reserva_id=reserva_id, motivo=motivo)
                print("Reserva cancelada.")

            elif opcion == "6":
                print("\n--- Clientes ---")
                for c in sistema.listar_clientes():
                    print(c.resumen())
                print("\n--- Servicios ---")
                for s in sistema.listar_servicios():
                    print(s.resumen())
                print("\n--- Reservas ---")
                for r in sistema.listar_reservas():
                    print(r.resumen())

            elif opcion == "7":
                resultado = ejecutar_simulacion(logger=logger)
                print("\n=== Simulación finalizada ===")
                print(resultado)

            elif opcion == "0":
                log_event("Aplicación finalizada por el usuario.")
                print("Saliendo...")
                break
            else:
                print("Opción inválida.")

        except SoftwareFJError as e:
            log_error("Error controlado en menú.", e)
            print(f"ERROR (controlado): {e}")
        except Exception as e:
            # Cualquier error no previsto: se registra y el sistema sigue vivo.
            log_error("Error no previsto en menú.", e)
            print(f"ERROR (no previsto): {e}")


if __name__ == "__main__":
    _menu()

