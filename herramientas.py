from datetime import date, datetime


def validar_pendientes(pendientes: list) -> dict:
    """
    Valida los pendientes de una minuta y calcula
    los días restantes para sus fechas límite.

    Las fechas vencidas se clasifican operativamente
    como "Fecha por confirmar".
    """

    fecha_actual = date.today()
    resultados = []

    for pendiente in pendientes:

        tarea = pendiente.get("tarea", "").strip()
        responsable = pendiente.get("responsable")
        fecha_limite = pendiente.get("fecha_limite")
        motivo_fecha = pendiente.get(
            "motivo_fecha_pendiente",
            "sin_fecha"
        )

        # Ignorar registros sin descripción.
        if not tarea:
            continue

        resultado = {
            "tarea": tarea,
            "responsable": responsable or "No especificado",
            "fecha_limite": fecha_limite,
            "estado_fecha": "Sin fecha definida",
            "dias_restantes": None,
            "estado_fecha_original": "Sin fecha definida",
            "motivo_fecha_pendiente": motivo_fecha
        }

        if motivo_fecha in (
            "fecha_imprecisa",
            "requiere_confirmacion"
        ):
            resultado["estado_fecha"] = "Fecha por confirmar"

        elif motivo_fecha == "sin_fecha":
            resultado["estado_fecha"] = "Sin fecha definida"

        # Calcular el estado cuando existe una fecha.
        if fecha_limite:

            try:
                fecha = datetime.strptime(
                    fecha_limite,
                    "%Y-%m-%d"
                ).date()

                dias = (fecha - fecha_actual).days

                resultado["dias_restantes"] = dias

                # Conservar el estado de la fecha original.
                if dias < 0:
                    resultado["estado_fecha_original"] = "Vencida"

                    # Si la fecha venció, hay que confirmar
                    # un nuevo compromiso de entrega.
                    resultado["estado_fecha"] = (
                        "Fecha por confirmar"
                    )

                elif dias == 0:
                    resultado["estado_fecha_original"] = "Vence hoy"
                    resultado["estado_fecha"] = "Vence hoy"

                else:
                    resultado["estado_fecha_original"] = "Pendiente"
                    resultado["estado_fecha"] = "Pendiente"

            except ValueError:
                resultado["estado_fecha"] = "Fecha por confirmar"
                resultado["estado_fecha_original"] = (
                    "Fecha por confirmar"
                )

        resultados.append(resultado)

    return {
        "fecha_revision": fecha_actual.isoformat(),
        "total_pendientes": len(resultados),
        "pendientes": resultados
    }