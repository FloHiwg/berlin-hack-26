# Voice Project

Phase 1 is a terminal-based insurance claims intake agent. It uses Gemini Live in text mode, follows a declarative YAML playbook, updates structured claim state through function calls, and persists each session to local JSON files.

## Requirements

- Python 3.11+
- `uv`
- Gemini API key

## Setup

Install dependencies with `uv`:

```bash
uv sync --extra dev
```

Create your local environment file:

```bash
cp .env.example .env
```

Then set:

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3.1-flash-live-preview
GEMINI_TEXT_MODEL=gemini-2.5-flash
GEMINI_API_VERSION=v1alpha
```

## Run

Start the Phase 1 text-mode intake agent:

```bash
uv run python app/main.py --text-mode
```

The agent prints a session ID, greets the customer, asks one question at a time, and saves progress after each structured state update.

By default, `--transport auto` tries the Gemini Live model first, then falls back to `GEMINI_TEXT_MODEL` with the regular Gemini text API if Live rejects the session during setup. This keeps the Phase 1 terminal workflow testable even when the preview Live API returns setup-time `1008` or `1011` errors.

Force one transport when debugging:

```bash
uv run python app/main.py --text-mode --transport live
uv run python app/main.py --text-mode --transport generate-content
```

## Eval Transcript Mode

You can replay a prepared conversation file with one user turn per line:

```bash
uv run python app/main.py --text-mode --eval-transcript path/to/transcript.txt
```

## Storage

Runtime files are written to:

```text
storage/sessions/<session_id>.jsonl
storage/sessions/<session_id>_claim.json
```

The JSONL file stores the transcript and tool events. The claim JSON file stores the latest structured claim state and is overwritten after each `update_claim_state` call.

## Tests

Run the local playbook/state tests:

```bash
uv run pytest
```

## Project Layout

```text
app/
  main.py
  agent/
    prompts.py
    schemas.py
    session.py
    tools.py
  claims/
    claim_state.py
    playbook.yaml
    playbook_engine.py
tests/
  test_playbook_engine.py
```
