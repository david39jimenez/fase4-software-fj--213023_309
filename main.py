# Habilita la evaluación diferida de las anotaciones de tipo, lo cual es útil para evitar 
# errores de referencia circular en versiones de Python anteriores a la 3.10.
from __future__ import annotations

# Importa funciones de configuración de registro (logs) personalizadas del módulo interno software_fj.
from software_fj.logging_config import get_logger, log_error, log_event
# Importa la clase principal que maneja la lógica de negocio (el repositorio del sistema).
from software_fj.repositorio import SistemaSoftwareFJ
# Importa la función encargada de ejecutar un bloque de operaciones de prueba.
from software_fj.simulacion import ejecutar_simulacion
# Importa la clase base de excepciones personalizadas para el manejo de errores del sistema.
from software_fj.exceptions import SoftwareFJError


# Define una función auxiliar que pide texto al usuario garantizando que no esté vacío.
def _input_non_empty(prompt: str) -> str:
    # Inicia un bucle infinito que solo se romperá cuando el usuario dé una entrada válida.
    while True:
        # Imprime el mensaje 'prompt', lee la entrada del usuario y le quita los espacios al inicio y final con strip().
        value = input(prompt).strip()
        # Si la variable 'value' contiene texto (es decir, no está vacía):
        if value:
            # Retorna el valor válido capturado.
            return value
        # Si la cadena estaba vacía, avisa al usuario y el bucle vuelve a iniciar.
        print("Valor requerido. Intenta de nuevo.")


# Define una función auxiliar para pedirle de forma segura un número decimal (float) al usuario.
def _input_float(prompt: str) -> float:
    # Bucle infinito para forzar un ingreso correcto.
    while True:
        # Lee la entrada y elimina espacios vacíos en los extremos.
        raw = input(prompt).strip()
        # Inicia un bloque de control de errores para manejar posibles fallos al convertir el texto a número.
        try:
            # Intenta convertir el texto a float y lo retorna inmediatamente si tiene éxito.
            return float(raw)
        # Si ocurre un error (por ejemplo, el usuario escribió letras en lugar de números):
        except Exception:
            # Muestra un mensaje advirtiendo el error y el bucle recomienza.
            print("Número inválido. Intenta de nuevo.")


# Define una función auxiliar para pedir un número entero (int) de forma segura.
def _input_int(prompt: str) -> int:
    # Bucle infinito hasta que se ingrese un entero válido.
    while True:
        # Toma la entrada sin espacios vacíos residuales.
        raw = input(prompt).strip()
        # Bloque de captura de errores para la conversión.
        try:
            # Intenta convertir el texto ingresado a entero y retornarlo.
            return int(raw)
        # En caso de fallar (ej. si ingresa texto o decimales):
        except Exception:
            # Advierte que el número es inválido y reintenta.
            print("Número inválido. Intenta de nuevo.")


# Define la función principal que pinta la interfaz de consola e interactúa con el usuario.
def _menu() -> None:
    # Inicializa el registrador (logger) para llevar el rastro de la actividad del sistema.
    logger = get_logger()
    # Crea una instancia de la clase base del sistema inyectando el logger.
    sistema = SistemaSoftwareFJ(logger=logger)

    # Inicia el bucle principal infinito de la aplicación interactiva.
    while True:
        # Imprime el título y todas las opciones disponibles del sistema en la consola.
        print("\n=== Software FJ | Gestión de Clientes, Servicios y Reservas ===")
        print("1. Registrar cliente")
        print("2. Crear servicio (3 tipos)")
        print("3. Crear reserva")
        print("4. Procesar/confirmar reserva")
        print("5. Cancelar reserva")
        print("6. Listar (clientes/servicios/reservas)")
        print("7. Ejecutar simulación (10+ operaciones)")
        print("0. Salir")

        # Pide al usuario que escriba un número de opción y limpia espacios no deseados.
        opcion = input("Opción: ").strip()

        # Inicia un bloque try general para que un error en cualquier proceso no "crashee" todo el sistema.
        try:
            # Si el usuario elige la opción 1 (Registrar cliente):
            if opcion == "1":
                # Solicita nombre, documento, email y teléfono asegurándose que no estén vacíos.
                nombre = _input_non_empty("Nombre: ")
                documento = _input_non_empty("Documento: ")
                email = _input_non_empty("Email: ")
                telefono = _input_non_empty("Teléfono: ")
                # Llama al método interno del sistema que instancia un cliente nuevo.
                cliente = sistema.crear_cliente(nombre=nombre, documento=documento, email=email, telefono=telefono)
                # Confirma al usuario que todo salió bien usando el método resumen() del cliente.
                print(f"Cliente registrado: {cliente.resumen()}")

            # Si el usuario elige la opción 2 (Crear un servicio):
            elif opcion == "2":
                # Despliega un pequeño submenú con las variantes de servicio.
                print("\nTipos de servicio:")
                print("1) Reserva de sala")
                print("2) Alquiler de equipo")
                print("3) Asesoría especializada")
                # Lee la opción de tipo de servicio elegida.
                tipo = input("Tipo: ").strip()

                # Si es tipo 1 (Reserva de sala):
                if tipo == "1":
                    # Pide los atributos concretos de las salas.
                    nombre = _input_non_empty("Nombre del servicio: ")
                    capacidad = _input_int("Capacidad (personas): ")
                    tarifa_hora = _input_float("Tarifa por hora: ")
                    # Pregunta por el proyector. Convierte 's' a True y cualquier otra cosa a False.
                    requiere = input("¿Requiere proyector? (s/n): ").strip().lower() == "s"
                    # Invoca la creación de una sala en el sistema pasándole sus parámetros puntuales.
                    servicio = sistema.crear_servicio_reserva_sala(
                        nombre=nombre,
                        capacidad=capacidad,
                        tarifa_hora=tarifa_hora,
                        requiere_proyector=requiere,
                    )
                # Si es tipo 2 (Alquiler de equipo):
                elif tipo == "2":
                    # Recolecta los campos específicos para la categoría de alquiler de equipos.
                    nombre = _input_non_empty("Nombre del servicio: ")
                    tipo_equipo = _input_non_empty("Tipo de equipo: ")
                    tarifa_dia = _input_float("Tarifa por día: ")
                    deposito = _input_float("Depósito: ")
                    stock = _input_int("Stock disponible: ")
                    # Lo registra en el sistema.
                    servicio = sistema.crear_servicio_alquiler_equipo(
                        nombre=nombre,
                        tipo_equipo=tipo_equipo,
                        tarifa_dia=tarifa_dia,
                        deposito=deposito,
                        stock_disponible=stock,
                    )
                # Si es tipo 3 (Asesoría especializada):
                elif tipo == "3":
                    # Toma la información propia del rol de asesorías.
                    nombre = _input_non_empty("Nombre del servicio: ")
                    especialidad = _input_non_empty("Especialidad: ")
                    tarifa_hora = _input_float("Tarifa por hora: ")
                    nivel = _input_non_empty("Nivel (junior/mid/senior): ")
                    # Ordena la creación del servicio tipo asesoría.
                    servicio = sistema.crear_servicio_asesoria(
                        nombre=nombre,
                        especialidad=especialidad,
                        tarifa_hora=tarifa_hora,
                        nivel=nivel,
                    )
                # Si el usuario ingresó un tipo que no es ni 1, ni 2, ni 3:
                else:
                    print("Tipo inválido.")
                    # El comando continue ignora el código restante y salta a la siguiente iteración del while True.
                    continue

                # Una vez que la variable servicio se asignó exitosamente en alguno de los 'if', imprime un resumen.
                print(f"Servicio registrado: {servicio.resumen()}")

            # Si el usuario elige la opción 3 (Crear reserva):
            elif opcion == "3":
                # Pide los datos base para enlazar cliente, servicio y la cantidad de tiempo a reservar.
                cliente_id = _input_non_empty("ID cliente: ")
                servicio_id = _input_non_empty("ID servicio: ")
                duracion = _input_float("Duración (horas o días): ")
                # Trata de crear la reserva en el sistema (el sistema internamente validará los IDs y stock).
                reserva = sistema.crear_reserva(cliente_id=cliente_id, servicio_id=servicio_id, duracion=duracion)
                # Informa que se agendó.
                print(f"Reserva creada: {reserva.resumen()}")

            # Si el usuario elige la opción 4 (Procesar / facturar reserva):
            elif opcion == "4":
                # Solicita el ID específico de la reserva.
                reserva_id = _input_non_empty("ID reserva: ")
                # Solicita detalles monetarios.
                impuesto = _input_float("Impuesto (ej 0.19): ")
                descuento = _input_float("Descuento (0-1 o 0-100, según regla): ")
                # Cambia el estado de la reserva y calcula el valor a pagar total.
                costo = sistema.procesar_reserva(reserva_id=reserva_id, impuesto=impuesto, descuento=descuento)
                # Muestra el costo por pantalla forzando un formato de 2 números decimales (.2f).
                print(f"Reserva procesada/confirmada. Costo: {costo:.2f}")

            # Si el usuario elige la opción 5 (Cancelar reserva):
            elif opcion == "5":
                # Pide el ID de la reserva a anular.
                reserva_id = _input_non_empty("ID reserva: ")
                # Permite escribir un motivo. Si está vacío, 'or None' transforma la cadena vacía en un dato nulo (None).
                motivo = input("Motivo (opcional): ").strip() or None
                # Ordena al sistema ejecutar la lógica de cancelación (ej. liberar stock y cambiar estados).
                sistema.cancelar_reserva(reserva_id=reserva_id, motivo=motivo)
                # Informa del éxito de la operación.
                print("Reserva cancelada.")

            # Si el usuario elige la opción 6 (Listar datos globales):
            elif opcion == "6":
                print("\n--- Clientes ---")
                # Itera uno por uno en la lista de clientes devuelta por el sistema y llama a su función de resumen.
                for c in sistema.listar_clientes():
                    print(c.resumen())
                
                print("\n--- Servicios ---")
                # Itera e imprime cada servicio existente.
                for s in sistema.listar_servicios():
                    print(s.resumen())
                
                print("\n--- Reservas ---")
                # Itera e imprime todas las reservas realizadas.
                for r in sistema.listar_reservas():
                    print(r.resumen())

            # Si el usuario elige la opción 7 (Automatización de pruebas / Simulación):
            elif opcion == "7":
                # Dispara la función importar de otro archivo pasándole el logger para seguimiento.
                resultado = ejecutar_simulacion(logger=logger)
                print("\n=== Simulación finalizada ===")
                # Imprime el veredicto final devuelto por la función de simulación.
                print(resultado)

            # Si el usuario elige la opción 0 (Salir):
            elif opcion == "0":
                # Registra en los logs internos que el fin de ejecución fue por decisión directa del usuario.
                log_event("Aplicación finalizada por el usuario.")
                print("Saliendo...")
                # Rompe el bucle while True principal; esto hará que la función _menu() termine por fin.
                break
            
            # Cualquier otra tecla numérica o letra que no esté mapeada:
            else:
                # Advierte y reinicia el menú.
                print("Opción inválida.")

        # Si dentro del bloque "try" general se lanza un error propio de las reglas de negocio (SoftwareFJError):
        except SoftwareFJError as e:
            # Registra como error "controlado" en el archivo log.
            log_error("Error controlado en menú.", e)
            # Imprime amigablemente el problema para que el usuario entienda qué falló (ej. "Cliente no existe").
            print(f"ERROR (controlado): {e}")
            
        # Si se levanta cualquier otro error general de Python no esperado (Exception):
        except Exception as e:
            # Cualquier error no previsto: se registra en logs de manera independiente.
            log_error("Error no previsto en menú.", e)
            # Imprime el error para visibilidad pero, vitalmente, previene que la aplicación haga "crash" y se cierre sola.
            print(f"ERROR (no previsto): {e}")


# Este bloque revisa si el archivo se está ejecutando directamente desde consola (python main.py).
if __name__ == "__main__":
    # Si la condición se cumple (no estamos siendo importados por otro módulo), lanza la función del menú.
    _menu()
