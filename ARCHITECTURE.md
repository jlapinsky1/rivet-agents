# Rivet Agents — Architecture

Python agent service for Rivet. Runs on Render. The Rivet UI and any other channel (MCP, CLI) POST to this service.

## Cascade

```
app.py (FastAPI router)
  └── Agent (agents/*.py)           — scoped function, model, skill list
        └── Skill (skills/<name>/)  — SKILL.md + resources/
              └── resources/*.md    — ALL logic and rules (Markdown, not code)
```

## Multi-model

| Model  | When | Pattern |
|--------|------|---------|
| Haiku  | Single-pass focused tasks | All skill content pre-injected into system prompt, one API call |
| Sonnet | Tool-use loops, deep reasoning | Reserved for future agents |

## File structure

```
agents/
  job_advisor.py          — Job Advisor agent definition
skills/
  scope_clarifier/
    SKILL.md              — skill instructions
    resources/
      question-patterns.md  — per-trade question logic (edit this, not code)
runtime/
  loop.py                 — main agent loop (Haiku + Sonnet paths)
  registry.py             — agent/skill registration and loading
db/
  supabase_client.py      — Supabase service client
app.py                    — FastAPI entry point and task router
```

## Adding a new agent

1. Create `skills/<skill-name>/SKILL.md` with instructions
2. Add resource files in `skills/<skill-name>/resources/`
3. Create `agents/<name>.py`, call `register_agent()`
4. Add a task case in `app.py`

## Environment variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service role key |
