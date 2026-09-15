# Opentrons AI

A repository for building AI-assisted control of an Opentrons OT-2 liquid-handling robot.

## Motor music experiment and research report

The [research article (中文)](docs/research/ot2-motor-music-paper.zh.md)
documents two completed pitch-range and rhythm experiments on one OT-2,
including methods, results, uncertainty and references. The
[reproducibility guide](docs/research/README.md) provides reviewed numerical
evidence, offline acoustic analysis, and commands to build figures and an HTML/PDF
article. Original microphone recordings and runtime logs remain local.

Three [complete song arrangements](docs/ot2-music-full-arrangements.md) have
direct Python launchers, with local `--dry-run` and robot `--simulate-only` modes.
Set `OT2_URL` and `OT2_EXPECTED_NAME` locally before hardware use.
They precompose phrase directions inside a bounded X interval and preserve Z
after homing. Music execution is separate from the dashboard.

## Current status

The first dashboard milestone is implemented: Chinese/English switching,
authenticated team accounts, OT-2 status, hardware import/catalog approval,
and optional camera pictures. See the [console guide](docs/dashboard.md)
for installation, local/LAN access, and limitations. AI experiment planning,
simulation, and execution are not connected to the dashboard yet.

The separate [OT-2 home and 100 mm circle protocol](docs/ot2-circle-test.md)
and its offline regression tests are also present; it is not exposed through
the dashboard.

Set `OT2_URL` locally for your robot; connection details are not distributed. [NOTES.md](NOTES.md) records historical outcomes, not a live connectivity check.

Still-image capture has been verified on the robot. See [the camera method](docs/ot2-camera.md) for tested curl commands and local picture locations.

## Working with an AI agent

The [system and interface design](docs/system-design.md) specifies the full roadmap for the shared lab dashboard, natural-language experiment workflow, validation, and recipe automation. The observation/catalog foundation is implemented; execution stages remain planned. Images are for operator reference and records, not automated decisions.

Start with [AGENTS.md](AGENTS.md). It defines how to develop, validate, and report work in this repository. [OpenAI integration guidance](docs/openai-guidance.md) records the model guidance used to prepare these instructions.

## Implementation direction

1. Available: robot status, bilingual dashboard, team accounts, hardware catalog, and snapshots.
2. Add protocol generation, validation, and simulation with explicit deck and pipette configuration.
3. Add execution and run monitoring for authorized protocols, including recovery from interrupted requests.

Keep model orchestration separate from robot transport. Backend code is in `src/opentrons_ai/`, React UI in `frontend/`, reusable protocols in `protocols/`, and backend tests in `tests/`.

## Development

### Local robot configuration

Copy `.env.example` to `.env`, replace the example endpoint and expected robot
name locally, then load it into the shell before hardware use:

```bash
set -a
. ./.env
set +a
```

The dashboard shows a disconnected robot when `OT2_URL` is absent. Music
execution additionally requires `OT2_EXPECTED_NAME` to match the calibrated
robot. A music `--dry-run` needs neither variable. Actual device identifiers,
network settings and run identifiers are excluded from the published files;
`.env`, `.local/`, and `runs/` remain local.

### Installation

```bash
make setup
make build
.venv/bin/python -m opentrons_ai create-admin --username admin
make run
```

Open `http://127.0.0.1:8080`. The interface defaults to Chinese; use **中文 / EN**
in the header to switch. Team access requires HTTPS; see [setup details](docs/dashboard.md).
Run `make test`, `make lint`, and `make test-ui` for dashboard checks.

The [circle test instructions](docs/ot2-circle-test.md) describe robot-side
simulation and execution. Run offline checks with
`python3 -m unittest discover -s tests -p test_circle_protocol.py -v`; no host Opentrons SDK is needed
for these tests. For documentation changes, inspect the diff and run
`git diff --check`. Keep credentials in local environment configuration;
`.gitignore` excludes `.env` files and generated run output.
