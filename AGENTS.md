# Agent Instructions

## Project Context

- **Project**: Centinela
- **Phase**: Development
- **Description**: {Descripción breve del proyecto.}

## Team Ownership

| Role | Name | GithubHandle |
|---|---|---|
| Lead Developer and Product Owner | Ever Burga | `4xeverburga` |

> ⚠️ **Note on Secondary Owners**: Adding a Secondary Owner (`{Owner2}`) to this table is **not recommended** and should be avoided whenever possible. It should only be considered in exceptional cases such as extended vacations or medical leave, and only after explicit confirmation from the user. Under normal circumstances, the Primary Owner is the single accountable person for the scope of his role and decisions.

### Identifying the Current Developer

Before updating `docs/status.md` (especially the owner brackets `**[{Owner}]**`) or modifying the **Team Ownership** table, agents must resolve who is currently authoring the changes:

1. Run `git config user.name` to obtain the active git identity.
2. Match the resulting handle against the `GithubHandle` column above to map it to the real `Name`.
3. If no row matches, **ask the user** for their real name and GitHub handle, then add a new row to the table before assigning ownership of any task.
4. Use the resolved real `Name` (not the GitHub handle) inside `**[Name]**` brackets in `docs/status.md`.

## Documentation Rules

- Keep documentation up to date continuously.
- Documentation and input or output artifact files must live in the `docs/` folder.
- The long-form project history is maintained in `docs/logbooks/`, with one file per day using ISO date format: `docs/logbooks/YYYY-MM-DD.md`.
- Each day's logbook captures detailed entries, decisions, root causes, and verification steps for that date.
- When starting a new day, create a new file (e.g., `docs/logbooks/2026-04-15.md`). Do not append to previous days.
- `docs/index.md` is the documentation entry point and must include links to relevant logbook entries so agents can find project history quickly.
- The current execution state (pending and completed tasks) must be maintained in `docs/status.md`.
- `README.md` must reflect the current image of the project state (see [README.md Conventions](#readmemd-conventions) below).
- External input files must be stored in `docs/artifacts/in/`.
- Output files co-created with the user or AI agents must be stored in `docs/artifacts/out/`.
- Updates should be pushed to the `dev` branch first.
- Alternative: If on another branch different to dev or main, simply push to upstream or create a new branch. Then create a PR to `dev`
- Then create a PR to merge `main` into the target branch.

## Logbook Conventions (`docs/logbooks/*.md`)

- One file per day, named `YYYY-MM-DD.md`. Do not append entries to a previous day's file.
- Each entry must have a sequential number, a descriptive title, and the date.
- Include technical details: configurations, commands, IPs, endpoints, error messages.
- Code blocks must use the appropriate language identifier (```bash, ```properties, ```text, etc.).
- Record findings, root causes, and decisions — not just actions.
- Sensitive data (keys, passwords, tokens) must be redacted.

## Status Conventions (`docs/status.md`)

- Maintain three sections: **Done**, **Pending**, and **Risks / Blockers**.
- Each pending task must have an owner in brackets: `**[{Owner1}]**`.
- Use checkboxes: `- [x]` for done, `- [ ]` for pending.
- Include a **Next Milestone** section with a clear, measurable goal.
- Update the **Team Ownership** table when roles change.

## README.md Conventions

`README.md` is the primary entry point for anyone reviewing the repository. Keep it updated as the project evolves. It must include:

- **Business Justification** — why this project exists and the business problem it solves.
- **Current Infrastructure and Services Deployed** — what has been provisioned and where (cloud providers, regions, services, networking).
- **Steps to Create the Infrastructure and Resources** — how to reproduce the deployment from scratch.
- **Shortcomings** — known limitations, active blockers, and areas not yet addressed.

## Documentation Index (`docs/index.md`)

`docs/index.md` is the first place agents should inspect when searching for project context. It must include:

| Section | Content |
|---|---|
| Status | Link to `docs/status.md` |
| Logbook Index | Links to `docs/logbooks/YYYY-MM-DD.md` files with short summaries |
| Artifacts | Links to `docs/artifacts/in/` and `docs/artifacts/out/` |

Update `docs/index.md` whenever a new logbook entry or important artifact is added.

## Artifacts (`docs/artifacts/`)

Artifacts are stored by source rather than by project methodology, because not every project needs use cases, user stories, misuse cases, or diagrams:

| Subdirectory | Content |
|---|---|
| `docs/artifacts/in/` | External input files such as SOWs, briefs, requirements, reference exports, or source materials |
| `docs/artifacts/out/` | Output files co-created between the team and AI agents during the project lifecycle |

Artifact filenames should be descriptive enough to explain the format and purpose, for example `sow-modernization.md`, `finops-analysis.xlsx`, `network-diagram.puml`, or `technical-objectives.md`.

## General Rules

- Always reference related logbook entries when updating status.
- When creating new documentation, follow the existing format and structure.
- Do not remove historical entries from the logbook; only append.
- Commit messages for documentation changes must use the prefix `docs:`.

## Architecture

The codebase follows **Hexagonal Architecture (Ports & Adapters)**. The root code package lives under `src/` and is split into two top-level layers:

```
src/
├── app/                      # Application core (pure, framework-agnostic)
│   ├── domain/               # Entities, value objects, domain rules
│   ├── ports/                # Interfaces (driven & driving ports)
│   └── services/             # Use cases / application services
└── ext/                      # Adapters / external concerns
    ├── repositories/         # Persistence adapters (SQLite, etc.)
    ├── providers/            # Outbound adapters (Telegram, vLLM, etc.)
    ├── controllers/          # Inbound adapters (bot handlers, HTTP, CLI)
    └── shared/               # Cross-cutting infra (db conn, http client)

containers/                   # Container images deployed to the AMD GPU droplet (Containerfile.bot, etc.)
scripts/                      # Shell helpers (start/stop/check vLLM on droplet)
```

Rules:
- `app/` must not import from `ext/`. Dependency direction is always `ext/ → app/`.
- Interfaces/ports are defined in `app/ports/`; concrete repositories and providers implementing them live in `ext/`.
- Wiring (DI/composition root) lives outside `app/`, typically in an entrypoint module that imports from `ext/` and `config.py`.
- Vertical feature slicing is **not** adopted at this stage. If the codebase grows enough to justify it, the structure can later evolve into `src/{app,ext}/<feature>/...` without changing the dependency rules above.

## Python Conventions

- **Python version**: 3.13.0, managed with `pyenv` + `venv` for local development.
- **Dependencies**: declared in `requirements.txt` at repo root, pinned by exact version.
- **Style**: PEP 8. Format with `black` and lint with `ruff` when available.
- **No file-level docstrings**: do not add a docstring at the top of `.py` files. They harm readability for this project. Use docstrings only for non-trivial public functions/classes when they add real value.
- **No default values** in function/method/class parameter signatures. All configuration is injected explicitly by the caller, ultimately sourced from `.env` via the `config.py` module at the repo root. This keeps the composition root as the single source of truth and avoids hidden defaults scattered across the codebase.
- **Avoid `Optional` / `None` fields**: prefer explicit, non-nullable types. Only use `| None` when the domain genuinely requires the absence of a value (e.g., a field that is populated later in a lifecycle). Do not use `Optional` as a convenience to skip initialization.
- `config.py` loads `.env` (via `python-dotenv`) and exposes a typed configuration object that is passed down through constructors.
- Secrets and tokens must never be hardcoded; always read from `.env`.
