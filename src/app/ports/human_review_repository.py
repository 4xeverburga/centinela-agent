from abc import ABC, abstractmethod

from app.domain.entities import HumanReviewRequest


class HumanReviewRepository(ABC):
    @abstractmethod
    async def save(self, review: HumanReviewRequest) -> int: ...

    @abstractmethod
    async def get_pending_for_project(self, project_id: str) -> list[HumanReviewRequest]: ...

    @abstractmethod
    async def answer(self, review_id: int, answer: str, reviewer_user_id: str, answered_at: str) -> None: ...
