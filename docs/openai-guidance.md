# OpenAI Integration Guidance

Reviewed 2026-09-14 against the official [model guide](https://developers.openai.com/api/docs/guides/latest-model). This document describes a future integration; no API client is implemented.

## API configuration

The guide currently identifies `gpt-6-astra`. Make the model configurable and recheck compatibility before implementation. Use Responses for tool calling, a supported reasoning effort (not `none` or `minimal`), and omit unsupported sampling parameters including `temperature` and `top_p`.

## Application responsibilities

Tool execution remains application-owned. If asynchronous tools are adopted, correlate results with their original `call_id`.

For this project, expose narrow robot operations with validated arguments. Serialize commands affecting the robot. Keep requested actions, returned results, and run identifiers distinct so interrupted execution can be reconciled without duplicating physical actions.

## Instruction maintenance

Keep workflow instructions in the root `AGENTS.md`. Record hardware observations in `NOTES.md` with dates. Changing these documents does not change the model selected by the agent application.
