from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ProjectStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    AUTO_CLOSED = "AUTO_CLOSED"


class UserRole(str, Enum):
    TECNICO = "TECNICO"
    ASISTENTE = "ASISTENTE"
    ADMIN = "ADMIN"


class QueueStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class InspectionStatus(str, Enum):
    DURANTE = "DURANTE"
    DESPUES = "DESPUES"


class ReviewTrigger(str, Enum):
    SUSPICIOUS_CATEGORY = "SUSPICIOUS_CATEGORY"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    INVALID_JSON = "INVALID_JSON"


@dataclass(frozen=True)
class Project:
    project_id: str
    chat_id: str
    local_name: str
    admin_user_id: str
    status: ProjectStatus
    started_at: datetime
    floor_plan_file_id: str
    finished_at: str
    closure_reason: str


@dataclass(frozen=True)
class User:
    telegram_user_id: str
    display_name: str
    role: UserRole


@dataclass(frozen=True)
class ImagePayload:
    data: bytes
    mime_type: str
    width: int
    height: int

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.data).hexdigest()

    @property
    def long_edge(self) -> int:
        return max(self.width, self.height)


@dataclass(frozen=True)
class EmbeddingVector:
    file_id: str
    vector: list[float]


@dataclass(frozen=True)
class SharpnessResult:
    file_id: str
    score: float
    width: int
    height: int


@dataclass(frozen=True)
class Cluster:
    cluster_id: str
    representative_file_id: str
    representative_sharpness: float
    member_file_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class QueueItem:
    project_id: str
    file_id: str
    chat_id: str
    cluster_id: str
    is_representative: bool
    sharpness_score: float
    status: QueueStatus
    attempts: int
    received_at: datetime
    last_error: str
    worker_id: str
    processed_at: str
    id: int = 0


@dataclass(frozen=True)
class ChatMessage:
    telegram_user_id: str
    display_name: str
    role: UserRole
    text: str
    timestamp: datetime


@dataclass(frozen=True)
class InspectionRecord:
    project_id: str
    queue_id: int
    image_file_id: str
    item_id: str
    category: str
    inspection_status: InspectionStatus
    location_on_map: str
    ocr_data: str
    tech_observation: str
    ai_system_observation: str
    is_suspicious: bool
    validated_by_admin: bool
    created_at: datetime
    anomaly_reason: str
    id: int = 0


@dataclass(frozen=True)
class HumanReviewRequest:
    project_id: str
    trigger: ReviewTrigger
    question: str
    asked_at: datetime
    queue_id: int
    answer: str
    reviewer_user_id: str
    answered_at: str
    id: int = 0
    id: int = 0


@dataclass(frozen=True)
class HumanReviewRequest:
    project_id: str
    trigger: ReviewTrigger
    question: str
    asked_at: datetime
    queue_id: int
    answer: str
    reviewer_user_id: str
    answered_at: str
    id: int = 0
