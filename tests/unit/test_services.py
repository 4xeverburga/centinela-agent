from datetime import datetime

import pytest

from app.domain.entities import ProjectStatus
from app.services.start_project import StartProjectService
from tests.fakes.fake_project_repository import FakeProjectRepository
from tests.fakes.fake_user_repository import FakeUserRepository
from tests.fakes.fake_telegram_gateway import FakeTelegramGateway
from tests.fakes.fake_clock import FakeClock, FakeIdGenerator


@pytest.fixture
def deps():
    project_repo = FakeProjectRepository()
    user_repo = FakeUserRepository()
    telegram = FakeTelegramGateway()
    clock = FakeClock(datetime(2026, 7, 15, 10, 0, 0))
    id_gen = FakeIdGenerator()
    svc = StartProjectService(project_repo, user_repo, telegram, clock, id_gen)
    return svc, project_repo, user_repo, telegram


async def test_start_project_creates_project(deps):
    svc, project_repo, user_repo, telegram = deps
    project = await svc.execute("123", "Local Alpha", "u1", "Ever")

    assert project.status == ProjectStatus.ACTIVE
    assert project.local_name == "Local Alpha"
    assert project.chat_id == "123"
    assert len(telegram.sent_messages) == 1
    assert "Local Alpha" in telegram.sent_messages[0][1]

    stored = await project_repo.get_by_id(project.project_id)
    assert stored is not None
    assert stored.project_id == project.project_id


async def test_start_project_rejects_duplicate(deps):
    svc, project_repo, user_repo, telegram = deps
    await svc.execute("123", "Local Alpha", "u1", "Ever")

    with pytest.raises(ValueError, match="Already an active project"):
        await svc.execute("123", "Local Beta", "u1", "Ever")


async def test_ingest_photo_queues_item():
    from app.services.ingest_photo import IngestPhotoService
    from tests.fakes.fake_project_repository import FakeProjectRepository
    from tests.fakes.fake_queue_repository import FakeQueueRepository
    from tests.fakes.fake_clock import FakeClock
    from app.domain.entities import Project, ProjectStatus

    project_repo = FakeProjectRepository()
    queue_repo = FakeQueueRepository()
    clock = FakeClock(datetime(2026, 7, 15, 10, 0, 0))

    project = Project(
        project_id="p1",
        chat_id="123",
        local_name="Test",
        admin_user_id="u1",
        status=ProjectStatus.ACTIVE,
        started_at=datetime(2026, 7, 15, 9, 0, 0),
        floor_plan_file_id="",
        finished_at="",
        closure_reason="",
    )
    await project_repo.save(project)

    svc = IngestPhotoService(project_repo, queue_repo, clock)
    item_id = await svc.execute("123", "file-abc")

    assert item_id == 1
    item = await queue_repo.get_by_id(item_id)
    assert item is not None
    assert item.file_id == "file-abc"
    assert item.project_id == "p1"


async def test_ingest_message_saves_to_history():
    from app.services.ingest_message import IngestMessageService
    from tests.fakes.fake_project_repository import FakeProjectRepository
    from tests.fakes.fake_history_repository import FakeHistoryRepository
    from tests.fakes.fake_user_repository import FakeUserRepository
    from tests.fakes.fake_clock import FakeClock
    from app.domain.entities import Project, ProjectStatus

    project_repo = FakeProjectRepository()
    history_repo = FakeHistoryRepository()
    user_repo = FakeUserRepository()
    clock = FakeClock(datetime(2026, 7, 15, 10, 0, 0))

    project = Project(
        project_id="p1",
        chat_id="123",
        local_name="Test",
        admin_user_id="u1",
        status=ProjectStatus.ACTIVE,
        started_at=datetime(2026, 7, 15, 9, 0, 0),
        floor_plan_file_id="",
        finished_at="",
        closure_reason="",
    )
    await project_repo.save(project)

    svc = IngestMessageService(project_repo, history_repo, user_repo, clock)
    result = await svc.execute("123", "u2", "Tech Juan", "Cámara IP reemplazada")

    assert result is True
    messages = await history_repo.get_all_for_project("p1")
    assert len(messages) == 1
    assert messages[0].text == "Cámara IP reemplazada"
