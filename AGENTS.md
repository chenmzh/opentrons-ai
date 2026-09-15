# Repository Guidelines

## Project Structure & Module Organization

This project is for AI-assisted control of an Opentrons OT-2. The foundation dashboard supports observation, hardware inventory, accounts, and optional pictures. Read `README.md` for scope and `NOTES.md` for recorded network configuration. Use:

- `src/` for production code, grouped by feature or package.
- `frontend/` for the React/TypeScript UI; keep all interface strings in `src/i18n.ts` with Chinese and English entries.
- `tests/` for automated tests that mirror the `src/` hierarchy.
- `protocols/` for versioned Opentrons protocols and `assets/` for labware definitions.
- `docs/` for design notes and user-facing documentation.

Do not commit generated outputs, caches, virtual environments, credentials, or large experimental datasets. Add them to `.gitignore` instead.

## Build, Test, and Development Commands

`make setup` installs dashboard dependencies; `make build` builds the frontend; `make run` serves loopback HTTP. See `docs/dashboard.md` for admin creation and HTTPS team access. `make test` runs mocked backend tests; `make test-ui` runs Playwright; `make lint` checks Ruff and Prettier. Protocol-specific tests remain separate. Use `git diff --check` for patch whitespace.

## Coding Style & Naming Conventions

Prefer Python with four-space indentation, `snake_case` functions/modules, and `PascalCase` classes; use two spaces for YAML/JSON. Separate model orchestration, protocol validation, and robot transport. Specify units explicitly, such as `volume_ul`.

## AI Agent Workflow

Apply the [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model), reviewed 2026-09-14:

- Complete authorized work; resolve routine choices from context and avoid repeated permission requests.
- Prepare reviewable results before asking questions that block completion.
- Audit instruction files for conflicts. User instructions override skill guidelines; identify and quote any skill rule causing a pause.
- Report outcomes, verification, and remaining blockers concisely.
- Delegate only when explicitly requested; keep robot execution under one controller.

For future OpenAI integration, consult `docs/openai-guidance.md`. These instructions do not configure the agent's model or implement a runtime.

## Robot Control

Treat recorded health checks as historical. Verify current robot state before execution. Use the user's authorized protocol and confirmed deck configuration; do not invent labware, pipettes, or volumes. Validate and simulate protocols before physical execution. After an ambiguous timeout, inspect run state before retrying a command that could repeat liquid handling.

Use camera images only for operator assistance and optional run records. Do not use images or capture failures to drive planning, validation, approval, or robot-control decisions. Automated vision feedback is deferred; camera availability must not gate execution.

## Testing Guidelines

Use meaningful regression tests for behavior changes, especially validation and transport errors. Name Python tests `test_<feature>.py`; mock robot access in unit tests. Mark hardware tests explicitly. Match checks to the change and avoid redundant testing for documentation edits. No coverage threshold is configured.

## Commit & Pull Request Guidelines

Use imperative Conventional Commit subjects, such as `feat: add protocol validation`. PRs should describe behavior, verification, relevant issues, and hardware impacts. Never claim a robot run succeeded without observed results.
