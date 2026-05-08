from datetime import datetime

import aiosqlite

from app.domain.entities import HumanReviewRequest, ReviewTrigger
from app.ports.human_review_repository import HumanReviewRepository


class SqliteHumanReviewRepository(HumanReviewRepository):
    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    async def save(self, review: HumanReviewRequest) -> int:
        cursor = await self._conn.execute(
            """INSERT INTO human_reviews
               (project_id, trigger, question, asked_at, queue_id,
                answer, reviewer_user_id, answered_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                review.project_id,
                review.trigger.value,
                review.question,
                review.asked_at.isoformat(),
                review.queue_id,
                review.answer,
                review.reviewer_user_id,
                review.answered_at,
            ),
        )
        await self._conn.commit()
        return cursor.lastrowid

    async def get_pending_for_project(self, project_id: str) -> list[HumanReviewRequest]:
        cursor = await self._conn.execute(
            "SELECT * FROM human_reviews WHERE project_id = ? AND answer = ''",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_review(r) for r in rows]

    async def answer(
        self, review_id: int, answer: str, reviewer_user_id: str, answered_at: str
    ) -> None:
        await self._conn.execute(
            """UPDATE human_reviews
               SET answer = ?, reviewer_user_id = ?, answered_at = ?
               WHERE id = ?""",
            (answer, reviewer_user_id, answered_at, review_id),
        )
        await self._conn.commit()

    @staticmethod
    def _row_to_review(row: aiosqlite.Row) -> HumanReviewRequest:
        return HumanReviewRequest(
            id=row["id"],
            project_id=row["project_id"],
            trigger=ReviewTrigger(row["trigger"]),
            question=row["question"],
            asked_at=datetime.fromisoformat(row["asked_at"]),
            queue_id=row["queue_id"],
            answer=row["answer"],
            reviewer_user_id=row["reviewer_user_id"],
            answered_at=row["answered_at"],
        )
