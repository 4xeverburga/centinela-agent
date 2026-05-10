# Project Status

**Project**: Centinela
**Date**: 2026-05-10
**Phase**: Development

## Team Ownership

| Role | Name | GithubHandle |
|---|---|---|
| Lead Developer and Product Owner | Ever Burga | `4xeverburga` |

## Done

- [x] **[Ever Burga]** Repository initialized with base template structure
- [x] **[Ever Burga]** Documentation navigation and artifact partitioning conventions added. See `docs/logbooks/2026-04-28.md` entry 1.
- [x] **[Ever Burga]** Phase 0: Bootstrap — folder tree, requirements.txt, config.py, pyproject.toml, .env, venv, verified
- [x] **[Ever Burga]** Phase 1: Domain entities (entities.py, inspection_schema.py), all ports (12 ABCs), all services (8 services + prompt builder)
- [x] **[Ever Burga]** Phase 2: SQLite persistence — db.py schema, 6 repository adapters
- [x] **[Ever Burga]** Phase 3: Telegram gateway adapter (PTB) + bot controller with /iniciar, /finalizar, /plano, photo/text handlers, HITL callbacks
- [x] **[Ever Burga]** Phase 4: Image pipeline — PillowImageProcessor (compress + Laplacian sharpness), PhashImageEmbedder, GreedyClusteringEngine
- [x] **[Ever Burga]** Phase 5: VllmLLMInspector — multimodal inspection via langchain-openai + guided_json
- [x] **[Ever Burga]** Phase 6: QueueWorker — async polling loop
- [x] **[Ever Burga]** Phase 7: HITL flow — HandleHITLResponseService + inline keyboard callbacks
- [x] **[Ever Burga]** Phase 8: VllmReportGenerator — Markdown report via LLM
- [x] **[Ever Burga]** Phase 9: Composition root (__main__.py) — full DI wiring, bot startup, worker task
- [x] **[Ever Burga]** Test fakes for all 13 ports + unit tests (4 passing)
- [x] **[Ever Burga]** Retroactive Optional cleanup — entities use empty strings/0 instead of None for non-lifecycle fields
- [x] **[Ever Burga]** Set real BOT_HTTP_API_TOKEN and HF_TOKEN in .env
- [x] **[Ever Burga]** vLLM nightly (v0.20.2rc1, ROCm) deployed on MI300X droplet — Gemma 4 31B loaded and serving. See `docs/logbooks/2026-05-08.md`.
- [x] **[Ever Burga]** Telegram bot (`@C3nt1nel_bot`) running end-to-end locally, connected to live vLLM
- [x] **[Ever Burga]** `containers/Containerfile.bot` — OCI image for containerised bot deployment
- [x] **[Ever Burga]** Refactored queue → `inspections_queue` with composite PK `(file_id, system_version)`. Moved preprocessing to ingest time — blurry images rejected before queueing. See `docs/logbooks/2026-05-08.md`.
- [x] **[Ever Burga]** Fixed HITL callback bug (was using inspection_id as review_id). Improved HITL UX with clear button labels. See `docs/logbooks/2026-05-08.md`.
- [x] **[Ever Burga]** Fixed media-group caption capture — photo captions now saved to chat_history. See `docs/logbooks/2026-05-08.md`.
- [x] **[Ever Burga]** Removed `validated_by_admin` from inspections; review state resolved exclusively via `human_reviews` table.
- [x] **[Ever Burga]** Composite PK chain: `chat_history(chat_id, message_id)` → `inspections_queue(chat_id, message_id, system_version)` → `inspections(chat_id, message_id, system_version)`. Dropped all auto-increment IDs. See `docs/logbooks/2026-05-10.md` entry 2.
- [x] **[Ever Burga]** Context window anchored by `ChatMessage` with `message_id` ordering and per-side limits.
- [x] **[Ever Burga]** Media group caption inheritance — later photos in a group inherit the caption from the first. See `docs/logbooks/2026-05-10.md` entry 2.
- [x] **[Ever Burga]** Removed `is_representative` from queue — non-representative images stay in `chat_history` only.
- [x] **[Ever Burga]** Bot deployed to AMD GPU droplet via `scripts/deploy-bot.sh`. `sentence-transformers` removed (pHash used instead). See `docs/logbooks/2026-05-10.md`.
- [x] **[Ever Burga]** `deploy-bot.sh` updated: deploys `centinela-demo` container (Flask API on `DEMO_PORT`), opens UFW port, prints demo URL. Dev→prod transition strategy documented. See `docs/logbooks/2026-05-10.md`.
- [x] **[Ever Burga]** `/iniciar` group reply now suggests `/plano` instead of printing project ID. `START_DM_TEXT` also updated (both locales). See `docs/logbooks/2026-05-10.md`.

## Pending

- [ ] **[Ever Burga]** Integration tests (SQLite repos, vLLM inspector with live model)
- [ ] **[Ever Burga]** Auto-close stale projects after PROJECT_AUTO_CLOSE_HOURS
- [ ] **[Ever Burga]** CLIP-based image embedder adapter — currently using pHash (`imagehash`); CLIP would improve semantic similarity but requires `sentence-transformers` + `torch` (~1 GB) back as dependencies
- [ ] **[Ever Burga]** Disable /plano, /alertas, /start, /hola commands in group chats (group-only: /iniciar, /finalizar)

## Risks / Blockers

- `sentence-transformers` was listed as a dependency but never imported in production code. Removed to keep the Docker image lean (~1.5 GB saved). If CLIP-based deduplication is implemented, it must be re-added with a CPU-only torch pin (`--extra-index-url https://download.pytorch.org/whl/cpu`).

- Gemma 4 requires vLLM **nightly** (>= v0.20.x); stable v0.17.1 does not support the `gemma4` architecture. Alternatives identified: SGLang, HF Inference Providers, llama.cpp GGUF.
- Bot currently runs locally — needs cloud deployment for production use.

## Dev → Production Transition Strategy

**Problem**: avoiding conflicting file versions between dev and prod when both run on the same droplet (or any shared host).

**Decided approach — image tagging + env-file separation:**

1. **Single image, multiple environments**: `deploy-bot.sh` always builds from the current `HEAD` (via `git archive`). Before a prod deploy the commit is tagged (`git tag v1.x.x && git push --tags`). The remote image is tagged identically (`docker tag centinela-bot centinela-bot:v1.x.x`).
2. **No code duplication on the host**: only one image build at a time. Containers (`centinela-bot`, `centinela-demo`) are always recreated from that image. There is no "dev clone" and "prod clone" co-existing on the droplet — dev testing happens locally.
3. **Env-file separation**: secrets and runtime config live in `~/centinela.env` (prod) on the droplet, never in the repo. A local `.env` is used for local dev. If a staging environment is ever needed, it gets its own droplet with its own `~/centinela.env`, not a second env file on the same host.
4. **Data isolation**: the SQLite volume (`~/centinela-data/`) is prod data. The demo server uses a separate `centinela_demo.db` inside the same volume. Never share a DB file between prod bot and dev experiments.
5. **Rollback**: to roll back, re-run `deploy-bot.sh` from a previous tagged commit (`git checkout v1.x.x` → `deploy-bot.sh`). The `--restart=unless-stopped` policy keeps containers alive across reboots automatically.

**Ports in use on the droplet:**

| Port | Service | Notes |
|------|---------|-------|
| 22 | SSH | always open |
| 8000 | vLLM OpenAI-compat API | internal; open only to bot container |
| 5000 | centinela-demo Flask API | opened by `deploy-bot.sh` via `ufw allow` |

> ⚠️ Port 8000 (vLLM) should **not** be exposed to the public internet. If the droplet firewall (DigitalOcean Cloud Firewall) is configured, ensure 8000 is blocked externally. The bot container reaches vLLM via `VLLM_BASE_URL=http://localhost:8000/v1` on the host network.

## TBD / Open Questions

- **`TelegramGateway` in `app/ports/`**: Telegram is a 3rd-party concern and arguably should not leak into the application core as a named port. Options: (a) rename to a generic `MessagingGateway` / `NotificationGateway` with Telegram as one adapter, (b) move download/send responsibilities to separate `FileDownloader` and `Notifier` ports so the core stays transport-agnostic. No decision yet — revisit before adding a second channel.

## Next Milestone

**Milestone**: Demo API live on droplet and accessible from browser; bot fully headless (vLLM + bot + demo all running on droplet, surviving reboots).
