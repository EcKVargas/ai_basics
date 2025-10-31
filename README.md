# Build Effective Agents — Training Workspace

This repository contains a collection of small training projects and examples for building tool-enabled agents and MCP (Model Context Protocol) integrations. It's designed as a hands-on workspace to teach developers how to:

- Register and expose functions/tools via a local MCP server.
- Route LLM prompts to tools (function-calling) and post-process tool outputs.
- Debug networked tool flows (SSE / streamable-http) and handle API edge cases.

This README gives quick setup, run, and troubleshooting steps tailored to the workspace layout.

## Repo layout

- `01_generic_training/` — small examples showing basic tool call flows.
- `02_dlm_specific_tools/` — DLM-specific tool schemas and usage examples.
- `03_mcp_training/` — MCP server, tools, orchestrators, and test harnesses. This is the main folder used in the training exercises.
- `mcp-server-demo/` — a minimal demo server showing MCP integrations.
- `py310env/`, `venv/` — virtual environments (not checked in).

## Quick start (Windows)

1. Create or activate a Python virtual environment (recommended):

```powershell
# Create once
python -m venv py310env

# Activate (PowerShell)
py310env\Scripts\Activate.ps1

# Activate (cmd.exe)
py310env\Scripts\activate.bat
```

2. Install requirements (if `requirements.txt` exists) or install packages used during training:

```powershell
pip install -r requirements.txt
# or
pip install httpx requests gen-ai-hub mcp
```

3. Run the MCP training server (from `03_mcp_training`):

```powershell
# From repo root
py310env\Scripts\python.exe 03_mcp_training\server.py
# or use fastmcp if you prefer the CLI wrapper
fastmcp run 03_mcp_training/server.py:mcp --transport streamable-http
```

4. Start the orchestrator (interactive):

```powershell
py310env\Scripts\python.exe 03_mcp_training\ai_cockpit_orchestrator.py
# Type questions at the prompt, e.g. "Show ADL overview (status, availability, program/landscape)."
```

5. Run unit-like test helpers/example scripts:

```powershell
py310env\Scripts\python.exe 03_mcp_training\test_cockpit_get_view_by_sid_abap.py
```

## Files of interest (03_mcp_training)

- `server.py` — the local MCP server exposing tools like `search_system_flexi`, `cockpit_get_view_by_sid`.
- `cockpit_utils.py` — helper functions that call the SLIM Flexi API and the Cockpit provider.
- `ai_cockpit_orchestrator.py` — example orchestrator that routes user prompts, calls the appropriate tool, and composes LLM responses.
- `test_*` scripts — quick harnesses for invoking tool functions manually.

## Best practices & tips

- Use HTTPS cert verification in production. Many demo scripts set `verify=False` for convenience; replace with `certifi.where()` or your corporate CA path.
- Prefer port >1024 when running local servers to avoid admin rights issues.
- When debugging: print the raw tool call payloads, validated schema, and save raw API responses to files (see `DEBUG_COCKPIT_SAVE` env var in `server.py`).
- The GenAI Hub proxy client may require a configured deployment; check your `proxy_client.deployments` and `select_deployment()` if you get `get_current_deployment() is None` errors.

## Git/GitHub checklist

Before pushing:

- Add a `.gitignore` (see `.gitignore.template` below).
- Remove or keep virtual env folders out of the repo. Commit `requirements.txt` if you're sharing the environment.

Basic `.gitignore` lines to add:

```
venv/
py310env/
__pycache__/
*.pyc
*.env
cockpit_*.json
```

To create the first commit and push:

```powershell
git init
git add .
git commit -m "Initial training workspace"
# create GitHub repo and then
git remote add origin <your-repo-url>
git branch -M main
git push -u origin main
```

## Troubleshooting common issues

- "Already running asyncio in this thread" — avoid calling `asyncio.run()` from inside an existing running loop (use `await` or run in a separate process). Tools that start their own event loop (fastmcp dev) can collide.
- `AttributeError: 'NoneType' object has no attribute 'additional_request_body_kwargs'` — usually means the GenAI Hub proxy has no current deployment selected. Select one via `proxy_client.select_deployment(id)` or set env var used by your proxy (see code comments).
- `invalid_function_parameters` — ensure function schemas include `required` arrays that contain all properties expected by the proxy validator, or remove `required` if not necessary.

## Next steps / exercises

- Add a real unit test (pytest) for `get_system_cockpit2` using recorded sample responses (fixture JSON).
- Replace `verify=False` calls with `certifi.where()` and test against your corporate CA.
- Make `ai_cockpit_orchestrator` reuse a single MCP session across multiple queries for performance.

---

If you'd like, I can also:

- Add a `requirements.txt` capturing the environment used in this workspace.
- Create a `.github/workflows/ci.yml` to run a small smoke test on push.
- Create a cleaner `.gitignore` in the repo root.

Which of these would you like me to add next?
