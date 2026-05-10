import json
from types import ModuleType

from app.domain.entities import ChatMessage


def _format_inspection(insp: dict) -> str:
    return json.dumps(insp, ensure_ascii=False)


def build_chronological_context(
    messages: list[ChatMessage],
    inspections_by_file_id: dict[str, dict],
    locale: ModuleType,
    current_file_id: str,
) -> str:
    lines = []
    rendered_clusters: set[str] = set()
    for msg in messages:
        is_current = msg.file_id and msg.file_id == current_file_id
        if msg.cluster_id:
            if msg.cluster_id in rendered_clusters:
                continue
            rendered_clusters.add(msg.cluster_id)
            cluster_msgs = [m for m in messages if m.cluster_id == msg.cluster_id]
            caption = next((m.text for m in cluster_msgs if m.text), "")
            has_current = any(m.file_id == current_file_id for m in cluster_msgs)
            parts = [
                _format_inspection(insp)
                for m in cluster_msgs
                if m.file_id
                for insp in [inspections_by_file_id.get(m.file_id)]
                if insp
            ]
            header = f"[{msg.role.value}] {msg.display_name}"
            if caption:
                header += f": {caption}"
            tag = ">>> grupo-fotos en an\u00e1lisis <<<" if has_current else "[grupo-fotos]"
            if parts:
                lines.append(header + f" {tag} " + " | ".join(parts))
            elif has_current:
                lines.append(header + f" {tag}")
        elif is_current:
            lines.append(f"[{msg.role.value}] {msg.display_name}: >>> imagen en an\u00e1lisis <<<")
        elif msg.text:
            lines.append(f"[{msg.role.value}] {msg.display_name}: {msg.text}")
        elif msg.file_id:
            insp = inspections_by_file_id.get(msg.file_id)
            if insp:
                lines.append(f"[{msg.role.value}] {msg.display_name}: [foto] " + _format_inspection(insp))
    return "\n".join(lines) if lines else locale.NO_CONTEXT


def build_user_prompt(context: str, locale: ModuleType) -> str:
    return locale.USER_PROMPT_TEMPLATE.format(context=context)
