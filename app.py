import os
from datetime import datetime

import streamlit as st


# Configuración general.
st.set_page_config(
    page_title="ObraPilot AI",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# Estilos para mejorar la presentación en escritorio y celular.
st.markdown(
    """
    <style>
        .block-container {
            max-width: 1100px;
            padding: 1.5rem 1rem 3rem 1rem;
        }

        h1 {
            font-size: clamp(1.8rem, 5vw, 2.6rem);
        }

        h2, h3 {
            overflow-wrap: anywhere;
        }

        div[data-testid="stMetric"] {
            background-color: rgba(128, 128, 128, 0.08);
            border: 1px solid rgba(128, 128, 128, 0.18);
            padding: 14px;
            border-radius: 12px;
        }

        div[data-testid="stMetricValue"] {
            font-size: clamp(1.4rem, 4vw, 2rem);
        }

        div.stButton > button,
        div[data-testid="stFormSubmitButton"] > button {
            width: 100%;
            min-height: 46px;
            border-radius: 10px;
            font-weight: 600;
        }

        div[data-testid="stTextArea"] textarea {
            font-size: 16px;
            line-height: 1.5;
        }

        .pendiente-card {
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            overflow-wrap: anywhere;
        }

        .pendiente-card h4 {
            margin-top: 0;
            margin-bottom: 12px;
        }

        .dato-label {
            font-size: 0.85rem;
            opacity: 0.75;
            margin-bottom: 2px;
        }

        .dato-valor {
            font-weight: 500;
            margin-bottom: 10px;
        }

        @media (max-width: 600px) {
            .block-container {
                padding: 1rem 0.75rem 2rem 0.75rem;
            }

            div[data-testid="stMetric"] {
                padding: 10px;
            }

            div[data-testid="stMetricLabel"] {
                font-size: 0.8rem;
            }

            .pendiente-card {
                padding: 13px;
            }
        }
    </style>
    """,
    unsafe_allow_html=True
)


# Cargar la API Key desde los secretos protegidos.
try:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

except Exception:
    st.error(
        "No se encontró la API Key de Groq. "
        "Revisa la configuración de secretos."
    )
    st.stop()


# Importar el agente.
from agente import analizar_minuta


# Minuta de ejemplo.
MINUTA_EJEMPLO = """
Proyecto residencial: seguimiento semanal.

1. El proveedor de cancelería informa que la entrega
   se realizará el 28 de octubre de 2026. No se ha indicado
   una nueva fecha de entrega.

2. El equipo de instalaciones eléctricas debe entregar
   los planos actualizados el 30 de octubre de 2026.

3. El área de diseño debe confirmar las especificaciones
   de los acabados de dos departamentos esta semana.

4. El área de maquinaria informa que las máquinas
   solicitadas llegarán el 29 de octubre de 2026.
"""


# Formatear fechas.
def formatear_fecha(fecha):
    if not fecha:
        return "Por confirmar"

    try:
        fecha_objeto = datetime.strptime(fecha, "%Y-%m-%d")
        return fecha_objeto.strftime("%d/%m/%Y")

    except (ValueError, TypeError):
        return "Por confirmar"


# Encabezado.
st.title("🏗️ ObraPilot AI")

st.caption(
    "Asistente inteligente para el seguimiento "
    "de proyectos inmobiliarios y de construcción."
)

st.divider()


# Formulario.
st.subheader("Analizar una minuta")

with st.form("formulario_minuta"):

    proyecto = st.text_input(
        "Nombre del proyecto",
        value="Proyecto residencial"
    )

    minuta = st.text_area(
        "Minuta o reporte de seguimiento",
        value=MINUTA_EJEMPLO,
        height=240,
        placeholder="Pega aquí el contenido de la minuta..."
    )

    analizar = st.form_submit_button("Analizar minuta")


# Analizar la minuta.
if analizar:

    if not minuta.strip():
        st.warning("Introduce el contenido de una minuta.")

    else:
        texto_analisis = (
            f"Nombre del proyecto: {proyecto}\n\n"
            f"{minuta}"
        )

        try:
            with st.spinner("Analizando la minuta..."):
                resultado = analizar_minuta(texto_analisis)

            reporte = resultado["reporte"]
            validacion = resultado["validacion"]
            pendientes = validacion["pendientes"]

            st.success("Análisis completado.")

            st.divider()
            st.header("Indicadores de seguimiento")

            total = len(pendientes)

            vencidas = sum(
                1 for p in pendientes
                if p.get("estado_fecha_original") == "Vencida"
            )

            vence_hoy = sum(
                1 for p in pendientes
                if p.get("estado_fecha") == "Vence hoy"
            )

            futuras = sum(
                1 for p in pendientes
                if p.get("estado_fecha") == "Pendiente"
            )

            sin_fecha = sum(
                1 for p in pendientes
                if p.get("estado_fecha") == "Sin fecha definida"
            )

            por_confirmar = sum(
                1 for p in pendientes
                if p.get("estado_fecha") == "Fecha por confirmar"
            )

            # Dos indicadores por fila para mejorar la lectura.
            indicadores = [
                ("Total de pendientes", total),
                ("Tareas vencidas", vencidas),
                ("Vencen hoy", vence_hoy),
                ("Con fecha futura", futuras),
                ("Sin fecha definida", sin_fecha),
                ("Fecha por confirmar", por_confirmar)
            ]

            for inicio in range(0, len(indicadores), 2):
                columnas = st.columns(2)

                for columna, indicador in zip(
                    columnas,
                    indicadores[inicio:inicio + 2]
                ):
                    columna.metric(
                        indicador[0],
                        indicador[1]
                    )

            st.caption(
                "Fecha de revisión: "
                + formatear_fecha(validacion["fecha_revision"])
            )

            st.divider()
            st.header("Detalle de pendientes")

            if pendientes:
                for numero, pendiente in enumerate(
                    pendientes, start=1
                ):
                    st.markdown(
                        f"""
                        <div class="pendiente-card">
                            <h4>{numero}. {pendiente["tarea"]}</h4>
                            <div class="dato-label">Responsable</div>
                            <div class="dato-valor">
                                {pendiente["responsable"]}
                            </div>
                            <div class="dato-label">Fecha límite</div>
                            <div class="dato-valor">
                                {formatear_fecha(pendiente["fecha_limite"])}
                            </div>
                            <div class="dato-label">Días restantes</div>
                            <div class="dato-valor">
                                {
                                    pendiente["dias_restantes"]
                                    if pendiente["dias_restantes"] is not None
                                    else "No disponible"
                                }
                            </div>
                            <div class="dato-label">Estado de la fecha</div>
                            <div class="dato-valor">
                                {pendiente["estado_fecha"]}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            else:
                st.info(
                    "No se identificaron pendientes válidos "
                    "en la minuta."
                )

            st.divider()
            st.header("Reporte ejecutivo")

            st.markdown(reporte)

            st.divider()

            st.caption(
                "Los indicadores se calculan con Python. "
                "El reporte y las recomendaciones son generados "
                "por IA y deben revisarse antes de tomar decisiones."
            )

        except Exception as error:
            st.error("No fue posible completar el análisis.")

            st.caption(
                f"Tipo de error: {type(error).__name__}"
            )

            print(f"[ERROR] {type(error).__name__}: {error}")