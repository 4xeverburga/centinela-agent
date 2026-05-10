# Documentation Index

This file is the entry point for agents and contributors looking for project context, current state, logbook history, and input/output artifacts.

## Current State

- [Project status](status.md)
- [README](../README.md)

## Logbook Index

| Date | Entry | Summary |
|---|---|---|
| 2026-04-28 | [Entry 1](logbooks/2026-04-28.md#1-documentation-navigation-and-artifact-partitioning-2026-04-28) | Added documentation index and partitioned artifacts into external inputs and co-created outputs. |
| 2026-07-15 | [Entry 1](logbooks/2026-07-15.md#entry-1-full-mvp-implementation-phases-19) | Full MVP implementation — domain, ports, services, SQLite, Telegram, image pipeline, LLM, worker, HITL, report, composition root. |
| 2026-05-08 | [Entry 1](logbooks/2026-05-08.md#entry-1-vllm-deployment-and-end-to-end-bot-launch) | vLLM nightly deployed on MI300X, Gemma 4 31B serving, Telegram bot running end-to-end. |
| 2026-05-08 | [Entry 2](logbooks/2026-05-08.md#entry-2-containerfilebot-and-documentation-update) | Containerfile.bot added, README/status/AGENTS.md updated. |
| 2026-05-10 | [Entry 1](logbooks/2026-05-10.md#entry-1--schema-refactor-inspections_queue-composite-pk-preprocessing-at-ingest) | Schema refactor: queue → inspections_queue, move preprocessing to ingest, fix HITL callback bug, capture photo captions. |

## Artifacts

| Folder | Purpose |
|---|---|
| [artifacts/in/](artifacts/in/) | External input files such as SOWs, briefs, requirements, reference exports, or source materials. |
| [artifacts/out/](artifacts/out/) | Output files co-created with AI agents; artifact type should be clear from the filename and content. |

## Documentation Conventions

- Use `docs/logbooks/YYYY-MM-DD.md` for daily project history.
- Add each important logbook entry to the Logbook Index table above.
- Place external source materials in `docs/artifacts/in/`.
- Place agent co-created deliverables in `docs/artifacts/out/`.
- Let filenames and file content identify the artifact format and purpose instead of creating methodology-specific folders.
