from types import ModuleType

from app.domain.entities import ChatMessage, InspectionRecord
from app.domain.prompts import get_locale


def build_context_summary(
    recent_inspections: list[InspectionRecord], locale: ModuleType
) -> str:
    if not recent_inspections:
        return locale.NO_INSPECTIONS

    lines = []
    for rec in recent_inspections:
        lines.append(
            f"- {rec.category} ({rec.inspection_status.value}): "
            f"ubicación={rec.location_on_map}, OCR={rec.ocr_data}"
        )
    return locale.CONTEXT_SUMMARY_HEADER + "\n" + "\n".join(lines)


def build_chat_window_text(messages: list[ChatMessage], locale: ModuleType) -> str:
    text_msgs = [m for m in messages if not m.file_id]
    if not text_msgs:
        return locale.NO_CHAT_MESSAGES

    lines = []
    for msg in text_msgs:
        lines.append(f"[{msg.role.value}] {msg.display_name}: {msg.text}")
    return "\n".join(lines)


def build_user_prompt(
    chat_window_text: str,
    context_summary: str,
    locale: ModuleType,
) -> str:
    return locale.USER_PROMPT_TEMPLATE.format(
        chat_window=chat_window_text,
        context_summary=context_summary,
    )
