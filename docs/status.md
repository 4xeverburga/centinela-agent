# Project Status

**Project**: Centinela
**Date**: 2026-05-08
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

## Pending

- [ ] **[Ever Burga]** Deploy bot container to cloud (DigitalOcean App Platform / Fly.io / etc.)
- [ ] **[Ever Burga]** Integration tests (SQLite repos, vLLM inspector with live model)
- [ ] **[Ever Burga]** Auto-close stale projects after PROJECT_AUTO_CLOSE_HOURS
- [ ] **[Ever Burga]** CLIP-based image embedder adapter (sentence-transformers)

## Risks / Blockers

- Gemma 4 requires vLLM **nightly** (>= v0.20.x); stable v0.17.1 does not support the `gemma4` architecture. Alternatives identified: SGLang, HF Inference Providers, llama.cpp GGUF.
- Bot currently runs locally — needs cloud deployment for production use.

## Next Milestone

**Milestone**: Deploy bot container to the cloud so the system runs fully headless (vLLM on droplet + bot in a managed container service).
