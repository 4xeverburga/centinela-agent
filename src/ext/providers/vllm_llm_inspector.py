import base64
import json
import logging
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.domain.entities import (
    ChatMessage,
    ImagePayload,
    InspectionRecord,
    InspectionStatus,
)
from app.domain.inspection_schema import InspectionPayload
from app.ports.llm_inspector import LLMInspector
from app.services.prompt import (
    SYSTEM_PROMPT,
    build_chat_window_text,
    build_context_summary,
    build_user_prompt,
)

logger = logging.getLogger(__name__)


class VllmLLMInspector(LLMInspector):
    def __init__(self, base_url: str, model: str, api_key: str):
        self._model = model
        self._llm = ChatOpenAI(
            base_url=base_url,
            model=model,
            api_key=api_key,
            temperature=0.1,
        )
        self._guided_json = InspectionPayload.model_json_schema()

    async def inspect(
        self,
        image: ImagePayload,
        floor_plan_image: bytes,
        chat_window: list[ChatMessage],
        recent_inspections_json: list[dict],
        project_id: str,
        queue_id: int,
        image_file_id: str,
    ) -> InspectionRecord:
        from app.domain.entities import InspectionRecord as IR

        context_summary = build_context_summary(
            [self._dict_to_stub(d) for d in recent_inspections_json]
            if recent_inspections_json else []
        )
        chat_text = build_chat_window_text(chat_window)
        user_prompt = build_user_prompt(chat_text, context_summary)

        image_b64 = base64.b64encode(image.data).decode("utf-8")

        content = [
            {"type": "text", "text": user_prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{image.mime_type};base64,{image_b64}"},
            },
        ]

        if floor_plan_image:
            fp_b64 = base64.b64encode(floor_plan_image).decode("utf-8")
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{fp_b64}"},
            })

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=content),
        ]

        response = await self._llm.ainvoke(
            messages,
            extra_body={"guided_json": self._guided_json},
        )

        raw = response.content
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM response: %s", raw[:500])
            return InspectionRecord(
                project_id=project_id,
                queue_id=queue_id,
                image_file_id=image_file_id,
                item_id="PARSE_ERROR",
                category="UNKNOWN",
                inspection_status=InspectionStatus.DURANTE,
                location_on_map="",
                ocr_data="",
                tech_observation="",
                ai_system_observation=f"JSON parse error: {raw[:200]}",
                is_suspicious=True,
                validated_by_admin=False,
                created_at=datetime.now(),
                anomaly_reason="Invalid JSON from LLM",
            )

        return InspectionRecord(
            project_id=project_id,
            queue_id=queue_id,
            image_file_id=image_file_id,
            item_id=parsed.get("item_id", ""),
            category=parsed.get("category", "UNKNOWN"),
            inspection_status=InspectionStatus(parsed.get("status", "DURANTE")),
            location_on_map=parsed.get("location_ref", ""),
            ocr_data=parsed.get("ocr", ""),
            tech_observation=parsed.get("observation", ""),
            ai_system_observation=parsed.get("system_observation", ""),
            is_suspicious=parsed.get("is_suspicious", False),
            validated_by_admin=False,
            created_at=datetime.now(),
            anomaly_reason=parsed.get("anomaly_reason", ""),
        )

    @staticmethod
    def _dict_to_stub(d: dict) -> InspectionRecord:
        return InspectionRecord(
            project_id="",
            queue_id=0,
            image_file_id="",
            item_id="",
            category=d.get("category", ""),
            inspection_status=InspectionStatus(d.get("status", "DURANTE")),
            location_on_map=d.get("location_ref", ""),
            ocr_data="",
            tech_observation="",
            ai_system_observation="",
            is_suspicious=False,
            validated_by_admin=False,
            created_at=datetime.now(),
            anomaly_reason="",
        )
