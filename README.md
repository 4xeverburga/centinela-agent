# {NOMBRE_DEL_PROYECTO}

## Business Justification

{Why this project exists and the business problem it solves.}

## Current Infrastructure and Services Deployed

{What has been provisioned and where — cloud providers, regions, services, networking.}

## Steps to Create the Infrastructure and Resources

{How to reproduce the deployment from scratch.}

## Shortcomings

{Known limitations, active blockers, and areas not yet addressed.}

## Repository Structure

```text
.
├── AGENTS.md                          # Instructions for AI agents (Copilot, etc.)
├── docs/
│   ├── index.md                       # Documentation entry point and logbook index
│   ├── logbooks/                      # Project logbook entries (one per date)
│   │   └── YYYY-MM-DD.md
│   ├── artifacts/                     # Project inputs and agent co-created outputs
│   │   ├── in/                        # External input files
│   │   └── out/                       # Output files co-created with AI agents
│   └── status.md                      # Current project execution state
└── README.md
```

## Documentation

| File / Folder | Description |
|---|---|
| [docs/index.md](docs/index.md) | Documentation entry point with links to status, artifacts, and logbook entries |
| [docs/status.md](docs/status.md) | Current execution state: completed tasks, pending items, risks, and next milestone |
| [docs/logbooks/](docs/logbooks/) | Chronological logbook entries with technical details, decisions, and findings |
| [docs/artifacts/in/](docs/artifacts/in/) | External input files such as SOWs, briefs, requirements, or source materials |
| [docs/artifacts/out/](docs/artifacts/out/) | Output files co-created with AI agents; file naming and content should describe the artifact type |
