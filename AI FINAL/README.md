# Campus Dining Demand & Waste Control Tower

Campus Dining Demand & Waste Control Tower is a local AI-agent app for campus dining managers. It uses recent sales, inventory, weather, and campus-event context to create a draft prep plan that reduces overproduction without creating a shortage. It is an institutional operations tool—not a personal meal planner, recipe generator, or consumer menu recommender.

The app is intentionally safe by default: it creates a recommendation only. It does not place orders, change inventory, or publish a menu. A dining manager must review the plan before it is used.

## Run locally

Requirements: Python 3.11+.

```bash
git clone https://github.com/Elaine1658/Final-Project.git
cd "Final-Project/AI FINAL"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8010
```

For the course dry run, keep any local `.env` file outside the cloned repository, one level above `Final-Project`. The submitted app runs in deterministic offline mode, so an API key is not required.

Open http://localhost:8010 in a browser and click **Create tomorrow's plan**.

The app runs in deterministic offline mode and does not require an API key. The included `.env.example` lists the supported course key names for a future live-agent mode. If a key is used, the app looks for `.env` in this folder first and then in the parent folder.

## What is included

- `data/dining.db`: small test dataset with sales, inventory, and campus context.
- `mcp_server/server.py`: MCP server exposing dining data tools.
- `backend/agents.py`: five-role planning team with structured outputs.
- `frontend/index.html`: self-contained dashboard served by FastAPI.
- `output/`: smoke-test and run evidence files.

The dashboard also supports what-if scenarios: change weather and expected attendance, rerun the plan, compare projected waste with the historical average, and approve a draft locally. Approval records a manager decision only; it does not place an order or mutate inventory.

## MCP smoke test

```bash
python output/mcp_client_smoke.py
```

This starts the stdio MCP server, initializes a client, lists the tools, and calls the dining-data tools against the included test database.

## Safety boundary

The system may recommend prep quantities, but it cannot purchase food, alter inventory, or publish a final plan. It flags expired ingredients, low-confidence demand, and plans that would leave projected coverage below 90%. A human must approve any final plan.
