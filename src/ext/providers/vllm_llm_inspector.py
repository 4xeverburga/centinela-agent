import base64
import json
import logging
from datetime import datetime

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.domain.entities import (
    ChatMessage,
    ImagePayload,
    InspectionRecord,
    InspectionStatus,
)
from app.domain.inspection_schema import InspectionPayload
from app.domain.prompts import get_locale
from app.ports.llm_inspector import LLMInspector
from app.services.prompt import (
    build_chronological_context,
    build_user_prompt,
)

logger = logging.getLogger(__name__)


class VllmLLMInspector(LLMInspector):
    def __init__(self, base_url: str, model: str, api_key: str, locale: str):
        self._model = model
        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self._locale = get_locale(locale)

    @staticmethod
    def _normalize_response(d: dict) -> dict:
        """Map common field aliases the model uses to the expected schema keys."""
        # category
        if "category" not in d:
            for key in ("equipment_classification", "equipment_type", "tipo_equipo", "type"):
                if key in d:
                    val = d[key]
                    d["category"] = val if isinstance(val, str) else str(val)
                    break

        # location_ref
        if "location_ref" not in d:
            for key in ("location", "ubicacion", "location_reference"):
                if key in d:
                    val = d[key]
                    d["location_ref"] = val if isinstance(val, str) else (
                        val.get("area") or val.get("reference") or str(val)
                    )
                    break

        # ocr — flatten nested ocr.text_detected
        if "ocr" in d and isinstance(d["ocr"], dict):
            d["ocr"] = d["ocr"].get("text_detected") or d["ocr"].get("text") or ""

        # status — normalise value
        status = d.get("status", "")
        if isinstance(status, str) and status.upper() not in ("DURANTE", "DESPUES"):
            d["status"] = "DURANTE"

        # defaults for optional fields
        d.setdefault("observation", "")
        d.setdefault("system_observation", "")
        d.setdefault("is_suspicious", False)
        d.setdefault("ocr", "")
        d.setdefault("category", "UNKNOWN")
        d.setdefault("location_ref", "")
        return d

    async def inspect(
        self,
        image: ImagePayload,
        floor_plan_image: bytes,
        chat_window: list[ChatMessage],
        inspections_by_file_id: dict[str, dict],
        chat_id: str,
        message_id: int,
        project_id: str,
        system_version: str,
        image_file_id: str,
    ) -> InspectionRecord:
        from app.domain.entities import InspectionRecord as IR

        context = build_chronological_context(
            chat_window, inspections_by_file_id, self._locale,
            current_file_id=image_file_id,
        )
        user_prompt = build_user_prompt(context, self._locale)

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
            {"role": "system", "content": self._locale.SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ]

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=0.1,
            timeout=120.0,
        )

        raw = response.choices[0].message.content or ""

        try:
            # Strip markdown fences if present
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("```", 2)[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.rsplit("```", 1)[0].strip()
            parsed_dict = json.loads(text)
            parsed_dict = self._normalize_response(parsed_dict)
            payload_obj = InspectionPayload.model_validate(parsed_dict)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.error("Failed to parse LLM response: %s", raw[:500])
            return InspectionRecord(
                chat_id=chat_id,
                message_id=message_id,
                system_version=system_version,
                project_id=project_id,
                image_file_id=image_file_id,
                item_id="PARSE_ERROR",
                category="UNKNOWN",
                inspection_status=InspectionStatus.DURANTE,
                location_on_map="",
                ocr_data="",
                tech_observation="",
                ai_system_observation=f"Schema error: {exc}",
                is_suspicious=True,
                created_at=datetime.now(),
            )

        return InspectionRecord(
            chat_id=chat_id,
            message_id=message_id,
            system_version=system_version,
            project_id=project_id,
            image_file_id=image_file_id,
            item_id="",
            category=payload_obj.category,
            inspection_status=InspectionStatus(payload_obj.status),
            location_on_map=payload_obj.location_ref,
            ocr_data=payload_obj.ocr,
            tech_observation=payload_obj.observation,
            ai_system_observation=payload_obj.system_observation,
            is_suspicious=payload_obj.is_suspicious,
            created_at=datetime.now(),
        )


