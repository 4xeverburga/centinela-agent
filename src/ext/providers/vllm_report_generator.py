import json
import logging
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.domain.entities import ChatMessage, InspectionRecord, Project
from app.ports.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

REPORT_SYSTEM = (
    "Eres un redactor técnico especializado en informes de mantenimiento de seguridad electrónica. "
    "Genera un informe Markdown profesional a partir de las inspecciones y el historial del proyecto."
)


class VllmReportGenerator(ReportGenerator):
    def __init__(self, base_url: str, model: str, api_key: str):
        self._llm = ChatOpenAI(
            base_url=base_url,
            model=model,
            api_key=api_key,
            temperature=0.3,
        )

    async def generate(
        self,
        project: Project,
        inspections: list[InspectionRecord],
        chat_history: list[ChatMessage],
    ) -> str:
        inspection_data = []
        for r in inspections:
            inspection_data.append({
                "item_id": r.item_id,
                "category": r.category,
                "status": r.inspection_status.value,
                "location": r.location_on_map,
                "ocr": r.ocr_data,
                "observation": r.tech_observation,
                "system_observation": r.ai_system_observation,
                "suspicious": r.is_suspicious,
                "anomaly_reason": r.anomaly_reason,
            })

        chat_summary = []
        for m in chat_history[-20:]:
            chat_summary.append(f"[{m.role.value}] {m.display_name}: {m.text}")

        user_prompt = (
            f"Proyecto: {project.local_name} (ID: {project.project_id})\n"
            f"Inicio: {project.started_at.isoformat()}\n"
            f"Inspecciones: {len(inspections)}\n\n"
            f"Datos de inspecciones (JSON):\n```json\n{json.dumps(inspection_data, ensure_ascii=False, indent=2)}\n```\n\n"
            f"Historial de chat relevante:\n" + "\n".join(chat_summary) + "\n\n"
            "Genera el informe completo en Markdown con las siguientes secciones:\n"
            "1. Resumen Ejecutivo\n"
            "2. Tabla de Equipos Inspeccionados\n"
            "3. Observaciones y Anomalías\n"
            "4. Recomendaciones\n"
        )

        messages = [
            SystemMessage(content=REPORT_SYSTEM),
            HumanMessage(content=user_prompt),
        ]

        response = await self._llm.ainvoke(messages)
        return response.content
