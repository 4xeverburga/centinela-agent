from app.ports.human_review_repository import HumanReviewRepository
from app.ports.clock import Clock


class HandleHITLResponseService:
    def __init__(
        self,
        review_repo: HumanReviewRepository,
        clock: Clock,
    ):
        self._review_repo = review_repo
        self._clock = clock

    async def execute(
        self, review_id: int, answer: str, reviewer_user_id: str
    ) -> None:
        now = self._clock.now().isoformat()
        await self._review_repo.answer(review_id, answer, reviewer_user_id, now)
