# Agent Harness

A minimal coding-agent loop built from scratch in Python — no LangChain, no framework.
Swap models with a `.env` change (Gemini or Groq). Harness features (limits, tracing, evals, sandbox) in progress.

## How it works

The LLM never executes anything — it only *requests* a tool call. This code runs the
function locally and feeds the result back, looping until the model returns plain text.

Tools: `read_file`, `list_files`, `search_files`, `edit_file`, `run_tests`.

Bad tool calls don't crash the run. Unknown tool names, wrong arguments (checked against
the real function signature) and runtime errors are all turned into error text the model
reads and retries from.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`.env`:

```
GROQ_API_KEY=...
GEMINI_API_KEY=...

LLM_PROVIDER=groq                # groq | gemini
LLM_MODEL=openai/gpt-oss-120b    # optional
```

## Run

```bash
python main.py
```

The task is hardcoded in `main.py` and edits `example.py` + its test as a fixture —
reset those between runs, otherwise the task is already done and the agent wanders.

## Layout

```
agent/
  loop.py            agent loop + safe tool execution
  tools.py           tool functions and their schemas
  types.py           ToolCall, LLMResponse, ToolSpec
  providers/         LLMProvider interface, Gemini + Groq adapters, get_provider()
```

## Known gaps

No iteration limit (the loop can spin), no token/cost budget, no sandbox (tools hit the
real filesystem), no trace of a run beyond stdout, no evals, and provider rate limits
still crash the run.
