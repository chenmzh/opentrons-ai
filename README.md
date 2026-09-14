# Opentrons AI

A repository for building AI-assisted control of an Opentrons OT-2 liquid-handling robot.

## Current status

The repository contains contributor instructions and setup notes. Robot-control code, an OpenAI integration, and automated tests have not been implemented yet.

The USB Ethernet configuration and previously successful OT-2 health check are recorded in [NOTES.md](NOTES.md). Those notes are historical observations, not a live connectivity check.

## Working with an AI agent

Start with [AGENTS.md](AGENTS.md). It defines how to develop, validate, and report work in this repository. [OpenAI integration guidance](docs/openai-guidance.md) records the model guidance used to prepare these instructions.

## Implementation direction

1. Add read-only robot health and state inspection.
2. Add protocol generation, validation, and simulation with explicit deck and pipette configuration.
3. Add execution and run monitoring for authorized protocols, including recovery from interrupted requests.

Keep model orchestration separate from robot transport. Store reusable protocols in `protocols/`, implementation in `src/`, and tests in `tests/` when those components are added.

## Development

No installation or runtime commands exist yet. For documentation changes, inspect the diff and run `git diff --check`. Keep credentials in local environment configuration; `.gitignore` excludes `.env` files and generated run output.
