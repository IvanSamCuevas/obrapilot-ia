import json

from groq import Groq

from herramientas import validar_pendientes


# Crear el cliente de IA utilizando la clave protegida.
cliente = Groq()


# Definir la herramienta que puede utilizar el agente.
HERRAMIENTAS = [
    {
        "type": "function",
        "function": {
            "name": "validar_pendientes",
            "description": (
                "Valida los pendientes de una minuta y "
                "calcula los días restantes para sus fechas."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pendientes": {
                        "type": "array",
                        "description": (
                            "Lista de tareas identificadas."
                        ),
                        "items": {
                            "type": "object",
                            "properties": {
                                "tarea": {
                                    "type": "string",
                                    "description": (
                                        "Descripción de la tarea."
                                    )
                                },
                                "responsable": {
                                    "type": ["string", "null"],
                                    "description": (
                                        "Persona o área responsable."
                                    )
                                },
                                "fecha_limite": {
                                    "type": ["string", "null"],
                                    "description": (
                                        "Fecha exacta en formato YYYY-MM-DD. "
                                        "Utiliza null si no existe una fecha exacta."
                                    )
                                },
                                "motivo_fecha_pendiente": {
                                    "type": "string",
                                    "enum": [
                                        "ninguno",
                                        "sin_fecha",
                                        "fecha_imprecisa",
                                        "requiere_confirmacion"
                                    ],
                                    "description": (
                                        "Clasifica por qué no existe una fecha exacta. "
                                        "'ninguno' si existe una fecha exacta vigente; "
                                        "'sin_fecha' si no se menciona ninguna fecha; "
                                        "'fecha_imprecisa' si se indica un periodo "
                                        "como esta semana; "
                                        "'requiere_confirmacion' si la fecha debe "
                                        "confirmarse o establecerse nuevamente."
                                    )
                                }
                            },
                            "required": [
                                "tarea",
                                "responsable",
                                "fecha_limite",
                                "motivo_fecha_pendiente"
                            ],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["pendientes"],
                "additionalProperties": False
            }
        }
    }
]


def analizar_minuta(minuta: str) -> dict:
    """
    Analiza una minuta, ejecuta la herramienta de Python
    y devuelve el reporte y los datos estructurados.
    """

    if not minuta.strip():
        raise ValueError("Debes introducir una minuta.")

    mensajes = [
        {
            "role": "system",
            "content": """
Eres ObraPilot AI, un asistente para el seguimiento
de proyectos inmobiliarios y de construcción.

Tu trabajo es:
1. Identificar tareas, responsables y fechas límite.
2. Detectar incidencias y posibles riesgos.
3. Utilizar validar_pendientes para comprobar las tareas.
4. Elaborar un reporte ejecutivo en español.

Reglas importantes:
- No inventes responsables ni fechas.
- Convierte las fechas explícitas a YYYY-MM-DD.
- Si no se menciona ninguna fecha, utiliza null en fecha_limite y clasifica motivo_fecha_pendiente como sin_fecha.
- Si se menciona un periodo impreciso, como "esta semana", "próximamente" o "en los próximos días", utiliza null en fecha_limite y clasifica motivo_fecha_pendiente como fecha_imprecisa.
- Si se necesita establecer o confirmar una nueva fecha, utiliza null en fecha_limite y clasifica motivo_fecha_pendiente como requiere_confirmacion.
- Si existe una fecha exacta y vigente, conserva esa fecha y utiliza ninguno como motivo_fecha_pendiente.
- Si una fecha exacta ya venció y el texto indica que debe establecerse un nuevo compromiso, conserva la fecha original para identificar el retraso y clasifica motivo_fecha_pendiente como requiere_confirmacion.
- No asumas que una fecha anterior sigue vigente cuando el texto indique expresamente que ha sido cancelada o que requiere una nueva confirmación.
- No asumas que una fecha anterior ha sido cancelada solamente porque se mencione que todavía no existe una nueva fecha.
- Distingue los hechos de las recomendaciones.
- No afirmes que un retraso afecta otras actividades si no conoces sus dependencias.
- Utiliza la herramienta validar_pendientes para comprobar las tareas identificadas antes de generar el reporte final.
- Explica los riesgos potenciales sin presentarlos como hechos confirmados.
- Presenta el resultado con títulos y listas claras.
"""
        },
        {
            "role": "user",
            "content": (
                "Analiza esta minuta de proyecto:\n\n"
                + minuta
            )
        }
    ]

    # Aquí guardaremos el resultado real de Python.
    resultado_validacion = None

    # Permitir varias interacciones entre el modelo
    # y las herramientas, con un límite de seguridad.
    for _ in range(5):

        respuesta = cliente.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=mensajes,
            tools=HERRAMIENTAS,
            tool_choice="auto",
            temperature=0.2
        )

        mensaje = respuesta.choices[0].message
        mensajes.append(mensaje)

        # Si no hay llamadas a herramientas,
        # el modelo ha terminado su respuesta.
        if not mensaje.tool_calls:

            # Verificar que la herramienta se haya ejecutado.
            if resultado_validacion is None:
                raise RuntimeError(
                    "El agente terminó sin ejecutar "
                    "la herramienta de validación."
                )

            return {
                "reporte": (
                    mensaje.content
                    or "No se generó un reporte."
                ),
                "validacion": resultado_validacion
            }

        # Ejecutar las herramientas solicitadas.
        for llamada in mensaje.tool_calls:

            nombre = llamada.function.name

            print(
                f"\n[AGENTE] Herramienta solicitada: {nombre}"
            )

            argumentos = json.loads(
                llamada.function.arguments
            )

            if nombre == "validar_pendientes":

                print(
                    "[PYTHON] Validando pendientes y fechas..."
                )

                resultado_validacion = validar_pendientes(
                    argumentos["pendientes"]
                )

                print(
                    "[PYTHON] Pendientes validados: "
                    f"{resultado_validacion['total_pendientes']}"
                )

                resultado = resultado_validacion

            else:
                resultado = {
                    "error": "Herramienta no reconocida."
                }

            # Devolver el resultado de Python al modelo.
            mensajes.append({
                "role": "tool",
                "tool_call_id": llamada.id,
                "content": json.dumps(
                    resultado,
                    ensure_ascii=False
                )
            })

    raise RuntimeError(
        "El agente alcanzó el límite de interacciones."
    )