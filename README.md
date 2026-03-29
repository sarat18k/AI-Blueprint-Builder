# A2A Startup Builder

An autonomous multi-agent system that takes a single startup idea and produces a complete startup blueprint — market research, competitor analysis, PRD, system architecture, MVP code, go-to-market strategy, investor pitch deck, and exportable documents.

Built on **Google's Agent-to-Agent (A2A) protocol**, with real-time streaming via SSE.

![Pipeline](https://img.shields.io/badge/agents-8-blue) ![Protocol](https://img.shields.io/badge/protocol-A2A-green) ![Python](https://img.shields.io/badge/python-3.11%2B-blue) ![License](https://img.shields.io/badge/license-MIT-blue)

---

## How It Works

Submit a startup idea. Eight specialized AI agents collaborate in sequence:

```
Market Research → Competitor Analysis → [Product Requirements ∥ GTM Strategy] → System Architecture → MVP Code → Pitch Deck → Document Export
```

Each agent uses the model best suited for its task. Results stream in real time as each agent completes.

---

## Agents

| Agent | Model (Premium) | Output |
|---|---|---|
| Market Research | Perplexity Sonar Pro | Market size, trends, target audience |
| Competitor Analysis | Claude Opus 4 | Competitors, SWOT, positioning |
| Product Requirements | Claude Opus 4 | PRD, personas, MVP features, timeline |
| Go-to-Market Strategy | GPT-4.1 | Messaging, launch plan, pricing tiers |
| System Architecture | Claude Sonnet 4 | Tech stack, services, system design |
| MVP Code Generation | Claude Sonnet 4 | Full project scaffold with working code |
| Investor Pitch Deck | Gemini 2.5 Pro | 10-slide deck, financials, investor FAQ |
| Document Export | Local | `.docx` startup plan + `.pptx` pitch deck |

Switch between **Standard** (fast, cost-effective) and **Premium** (best quality) tiers from the UI.

---

## Stack

- **Backend:** Python 3.11+, FastAPI, uvicorn
- **LLM routing:** [OpenRouter](https://openrouter.ai) — routes to Perplexity, Claude, GPT-4, Gemini
- **Protocol:** Google A2A (Agent Cards, Task lifecycle, SSE streaming)
- **Documents:** `python-docx`, `python-pptx`
- **Storage:** SQLite (run history), local filesystem (document downloads)
- **Frontend:** Vanilla JS, SSE

---

## Quickstart

### 1. Clone & install

```bash
git clone https://github.com/your-username/A2A-startup-builder.git
cd A2A-startup-builder
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and add your OpenRouter API key
```

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

Get a free API key at [openrouter.ai/keys](https://openrouter.ai/keys).

### 3. Run

```bash
python run.py
```

Open [http://localhost:8000](http://localhost:8000).

---

## API

### A2A Discovery

| Endpoint | Description |
|---|---|
| `GET /.well-known/agent.json` | Master agent card |
| `GET /agents` | List all agents with models and descriptions |
| `GET /agents/{name}/agent.json` | Individual agent card |

### Pipeline

| Endpoint | Description |
|---|---|
| `POST /api/run` | Start a pipeline run (returns SSE stream) |
| `GET /api/tier` | Get current model tier |
| `POST /api/tier` | Switch model tier (`standard` \| `premium`) |

### History & Downloads

| Endpoint | Description |
|---|---|
| `GET /api/history` | List past runs |
| `GET /api/history/{id}` | Get full run results |
| `GET /api/download/{file_id}` | Download `.docx` or `.pptx` |

### SSE Event Types

```
pipeline_start  — agents list with models
agent_start     — agent began processing
agent_done      — agent completed with data and elapsed time
agent_error     — agent failed with error message
pipeline_done   — all agents finished, full results
error           — pipeline-level error
```

---

## Project Structure

```
A2A-startup-builder/
├── run.py                   # Entry point
├── requirements.txt
├── .env.example
├── server/
│   ├── main.py              # FastAPI app, routes, SSE
│   ├── orchestrator.py      # Pipeline execution
│   ├── llm.py               # OpenRouter client, model tiers
│   ├── a2a_protocol.py      # A2A protocol models (Pydantic)
│   ├── documents.py         # .docx and .pptx generation
│   ├── history.py           # SQLite run history
│   └── agents/
│       ├── base.py          # Abstract base agent
│       ├── research.py
│       ├── analysis.py
│       ├── product.py
│       ├── architect.py
│       ├── code.py
│       ├── marketing.py
│       ├── pitch.py
│       └── document.py
├── static/
│   ├── index.html           # Main UI
│   ├── history.html         # Run history UI
│   ├── styles.css
│   └── format.js            # Output formatting
└── data/
    ├── history.db           # SQLite database (gitignored)
    └── downloads/           # Generated files (gitignored)
```

---

## Model Tiers

| | Standard | Premium |
|---|---|---|
| Market Research | Perplexity Sonar Pro | Perplexity Sonar Pro |
| Competitor Analysis | Claude Sonnet 4 | Claude Opus 4 |
| Product Requirements | Claude Sonnet 4 | Claude Opus 4 |
| System Architecture | Claude Sonnet 4 | Claude Sonnet 4 |
| MVP Code | Claude Sonnet 4 | Claude Sonnet 4 |
| GTM Strategy | GPT-4.1 | GPT-4.1 |
| Pitch Deck | Gemini 2.5 Flash | Gemini 2.5 Pro |
| Documents | Local | Local |

Switch tiers without restarting the server — the tier button in the UI updates all agents instantly.

---

## License

[MIT](LICENSE)
