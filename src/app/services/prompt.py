from app.domain.entities import ChatMessage, InspectionRecord


def build_context_summary(recent_inspections: list[InspectionRecord]) -> str:
    if not recent_inspections:
        return "No hay inspecciones previas en este proyecto."

    lines = []
    for rec in recent_inspections:
        lines.append(
            f"- {rec.category} ({rec.inspection_status.value}): "
            f"ubicación={rec.location_on_map}, OCR={rec.ocr_data}"
        )
    return "Inspecciones recientes procesadas:\n" + "\n".join(lines)


def build_chat_window_text(messages: list[ChatMessage]) -> str:
    if not messages:
        return "Sin mensajes recientes del técnico."

    lines = []
    for msg in messages:
        lines.append(f"[{msg.role.value}] {msg.display_name}: {msg.text}")
    return "\n".join(lines)


SYSTEM_PROMPT = (
    "Actúa como un Ingeniero de Seguridad Electrónica Senior. "
    "Tu misión es transformar evidencia visual y mensajes de campo en datos "
    "estructurados para un informe de mantenimiento profesional."
)


def build_user_prompt(
    chat_window_text: str,
    context_summary: str,
) -> str:
    return (
        f"[Ventana de Chat]\n{chat_window_text}\n\n"
        f"[Metadata de Contexto]\n{context_summary}\n\n"
        "Analiza la imagen adjunta siguiendo estas instrucciones:\n"
        "1. Clasifica el equipo y determina si la foto es DURANTE o DESPUES.\n"
        "2. Extrae IDs, marcas o números de serie (campo ocr).\n"
        "3. Ubica el equipo en el plano usando las referencias visuales.\n"
        "4. Si la categoría rompe el patrón del contexto, marca is_suspicious=true.\n"
        "5. Genera observation solo si hay un comentario humano relacionado.\n"
        "6. Genera system_observation si detectas fallas visuales no mencionadas.\n"
        "Responde EXCLUSIVAMENTE con el JSON estructurado."
    )
