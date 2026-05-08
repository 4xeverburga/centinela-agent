from pydantic import BaseModel, Field


class InspectionPayload(BaseModel):
    category: str = Field(description="Equipment category (e.g. CCTV, ALARMA_INCENDIO)")
    status: str = Field(description="DURANTE or DESPUES")
    location_ref: str = Field(description="Free-text location reference on the floor plan")
    ocr: str = Field(description="Extracted text / serial numbers from the image")
    observation: str = Field(description="Human comment from chat related to this image; empty if none")
    system_observation: str = Field(description="AI-detected issues not mentioned by humans; empty if none")
    is_suspicious: bool = Field(description="True when the category breaks the recent context pattern")
    anomaly_reason: str = Field(description="Explanation when is_suspicious is True; empty otherwise")
