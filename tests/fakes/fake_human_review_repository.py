from app.domain.entities import HumanReviewRequest
from app.ports.human_review_repository import HumanReviewRepository


class FakeHumanReviewRepository(HumanReviewRepository):
    def __init__(self):
        self._store: dict[int, HumanReviewRequest] = {}
        self._counter = 0

    async def save(self, review: HumanReviewRequest) -> int:
        self._counter += 1
        from dataclasses import replace
        stored = replace(review, id=self._counter)
        self._store[self._counter] = stored
        return self._counter

    async def get_pending_for_project(self, project_id: str) -> list[HumanReviewRequest]:
        return [
            r for r in self._store.values()
            if r.project_id == project_id and r.answer == ""
        ]

    async def answer(
        self, review_id: int, answer: str, reviewer_user_id: str, answered_at: str
    ) -> None:
        from dataclasses import replace
        r = self._store[review_id]
        self._store[review_id] = replace(
            r, answer=answer, reviewer_user_id=reviewer_user_id, answered_at=answered_at
        )
