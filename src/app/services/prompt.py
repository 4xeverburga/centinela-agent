from types import ModuleType

from app.domain.entities import ChatMessage


def _format_inspection(insp: dict) -> str:
    part = f"{insp.get('category', '')} {insp.get('status', '')} loc={insp.get('location_ref', '')}"
    if insp.get("tech_observation"):
        part += f" | obs_t: {insp['tech_observation']}"
    if insp.get("system_observation"):
        part += f" | obs_s: {insp['system_observation']}"
    return part


def build_chronological_context(
    messages: list[ChatMessage],
    inspections_by_file_id: dict[str, dict],
    locale: ModuleType,
) -> str:
    lines = []
    i = 0
    while i < len(messages):
        msg = messages[i]
        if msg.cluster_id:
            # Collect all consecutive messages belonging to the same cluster
            cid = msg.cluster_id
            cluster_msgs: list[ChatMessage] = []
            while i < len(messages) and messages[i].cluster_id == cid:
                cluster_msgs.append(messages[i])
                i += 1
            caption = next((m.text for m in cluster_msgs if m.text), "")
            parts = [
                _format_inspection(insp)
                for m in cluster_msgs
                if m.file_id
                for insp in [inspections_by_file_id.get(m.file_id)]
                if insp
            ]
            if parts:
                header = f"[{cluster_msgs[0].role.value}] {cluster_msgs[0].display_name}"
                if caption:
                    header += f": {caption}"
                lines.append(header + " [grupo-fotos] " + " | ".join(parts))
        elif msg.text:
            lines.append(f"[{msg.role.value}] {msg.display_name}: {msg.text}")
            i += 1
        elif msg.file_id:
            insp = inspections_by_file_id.get(msg.file_id)
            if insp:
                lines.append(f"[{msg.role.value}] {msg.display_name}: [foto] " + _format_inspection(insp))
            i += 1
        else:
            i += 1
    return "\n".join(lines) if lines else locale.NO_CONTEXT


def build_user_prompt(context: str, locale: ModuleType) -> str:
    return locale.USER_PROMPT_TEMPLATE.format(context=context)
