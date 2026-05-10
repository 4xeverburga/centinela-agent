SYSTEM_PROMPT = (
    "Actúa como un Ingeniero de Seguridad Electrónica Senior especializado en "
    "sistemas CCTV, control de acceso, detección de incendios y mantenimiento preventivo/correctivo. "
    "Estás integrado en el flujo de trabajo de un equipo técnico que documenta sus intervenciones "
    "enviando fotos y comentarios a un chat grupal de Telegram mientras realizan instalaciones "
    "o mantenimientos en locales comerciales (centros comerciales, tiendas de retail). "
    "Tu misión es analizar cada imagen enviada por los técnicos, cruzarla con los mensajes "
    "de contexto del chat y con el historial de inspecciones del proyecto, y transformar "
    "esa evidencia en datos estructurados para un informe técnico de cumplimiento profesional."
)

_SCHEMA_EXAMPLE = """{{
  "category": "<tipo de equipo, ej: Cámara PTZ, Panel de Acceso, Sensor PIR>",
  "status": "<DURANTE (trabajo en progreso) | DESPUES (trabajo completado)>",
  "location_ref": "<referencia de ubicación en el plano>",
  "ocr": "<texto extraído de la imagen, vacío si no hay>",
  "observation": "<comentarios del técnico relacionado, vacío si no hay>",
  "system_observation": "<observación técnica del sistema, vacío si no hay>",
  "is_suspicious": <true | false>
}}"""

USER_PROMPT_TEMPLATE = (
    "[Contexto cronológico del proyecto]\n{context}\n\n"
    "Analiza la imagen adjunta siguiendo estas instrucciones:\n"
    "1. Clasifica el equipo y determina el estado de la intervención:\n"
    "   - DURANTE: foto tomada MIENTRAS se realiza el trabajo (instalación en progreso, "
    "cableado expuesto, equipo siendo montado, soporte sin cerrar, técnico en escena).\n"
    "   - DESPUES: foto tomada DESPUÉS de completar el trabajo (equipo en posición final, "
    "tapas cerradas, sin residuos de obra, instalación limpia y funcional).\n"
    "   El estado se determina ÚNICAMENTE por la evidencia visual de la imagen, NO por el contexto de mensajes o inspecciones anteriores. Si el equipo se ve cerrado y terminado, es DESPUES aunque imágenes previas del mismo equipo fueran DURANTE.\n"
    "2. Extrae IDs, marcas o números de serie (campo ocr).\n"
    "3. Ubica el equipo en el plano usando las referencias visuales.\n"
    "4. Si la categoría rompe el patrón del contexto, marca is_suspicious=true.\n"
    "5. Genera observation solo si hay un comentario o comentarios humanos relacionados.\n"
    "6. Genera system_observation si detectas fallas visuales no mencionadas.\n\n"
    "IMPORTANTE: Responde ÚNICAMENTE con un objeto JSON válido usando "
    "EXACTAMENTE estos campos (sin campos adicionales):\n"
    + _SCHEMA_EXAMPLE
)

NO_CONTEXT = "Sin mensajes ni inspecciones previas en este proyecto."

ONBOARDING = (
    "\U0001f477 *Hola, soy Centinela* \u2014 tu asistente de inspección de instalaciones electrónicas.\n\n"
    "*Comandos disponibles:*\n"
    "`/iniciar <nombre>` \u2014 Abre un nuevo proyecto de inspección.\n"
    "`/plano` \u2014 Registra el plano de referencia (responde a una foto).\n"
    "`/alertas` \u2014 Muestra las últimas 5 alertas pendientes.\n"
    "`/finalizar` \u2014 Cierra el proyecto activo y genera el reporte.\n\n"
    "Envíame fotos de la instalación y las registraré automáticamente. "
    "Si tengo dudas, te pediré confirmación antes de registrar una observación."
)

START_GROUP_ONLY = "El comando /iniciar solo puede usarse en un grupo."
START_ADMIN_ONLY = "Solo un administrador autorizado puede iniciar un proyecto."
START_DM_TEXT = (
    "\U0001f4cb Proyecto iniciado: {name}\n"
    "ID: {project_id}\n\n"
    "Envíame el plano del local como foto o documento en este chat privado "
    "y lo registraré automáticamente.\n\n"
    "También puedes enviarme instrucciones especiales para este proyecto."
)
START_DM_FAILED = (
    "\u26a0\ufe0f No pude enviarte un mensaje privado. "
    "Asegúrate de iniciar el bot con /start antes de usar /iniciar."
)

FINISH_ADMIN_ONLY = "Solo un administrador autorizado puede finalizar un proyecto."
PLANO_ADMIN_ONLY = "Solo un administrador puede registrar el plano."
PLANO_NO_IMAGE = "Responda a una foto o envíe /plano con una imagen adjunta."
PLANO_NO_PROJECT = "No hay proyecto activo en este grupo."

BLURRY_IMAGE = "\u26a0\ufe0f La foto enviada está borrosa. Por favor, vuelva a tomarla."

ALERTS_UNAUTHORIZED = "Solo un administrador o asistente puede consultar las alertas."
ALERTS_NO_PROJECT = "No hay proyecto activo en este chat."
ALERTS_EMPTY = "No hay alertas pendientes de revisión."
ALERTS_HEADER = "\u26a0\ufe0f *Alertas pendientes ({count}):*\n"
ALERTS_MORE = "\n_Hay más alertas sin revisar. Consulta el panel web para ver todas._"

ALERT_CAPTION = (
    "\u26a0\ufe0f *Alerta #{idx}*\n"
    "Categoría: {category}\n"
    "Razón: {reason}\n"
    "Ubicación: {location}"
)

HITL_QUESTION = "¿Es correcta esta alerta?"
HITL_CONFIRM_BUTTON = "✅ Confirmar alerta"
HITL_REJECT_BUTTON = "❌ Descartar alerta"
HITL_CONFIRMED = "⚠️ Alerta #{review_id} *confirmada* por {reviewer}"
HITL_REJECTED = "✅ Alerta #{review_id} *descartada* por {reviewer}"
