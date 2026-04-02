# ARK IDE v3.0 — Autonomous Software Development Platform

> **Build software by describing what you want.** ARK IDE is an autonomous agent pipeline that plans, builds, tests, and deploys software from natural language goals.

![ARK IDE](https://img.shields.io/badge/ARK%20IDE-v3.0-6366f1?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-18.2-61DAFB?style=flat-square&logo=react)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python)

---

## 🧠 What is ARK IDE?

ARK IDE is a platform powered by a 5-agent autonomous pipeline. You describe what you want to build in natural language — the agents handle everything:

```
User Goal → ORCHESTRATOR
              ↓
          🧠 PLANNER   — Decomposes goal into structured task tree
              ↓
          🔨 BUILDER   — Generates code in isolated E2B sandbox
              ↓
          🧪 TESTER    — Writes & runs tests, validates coverage
              ↓  (if tests fail → back to BUILDER, max 3 iterations)
          🚀 DEPLOYER  — Builds Docker image, generates preview URL
              ↓
          👁️ MONITOR   — Health checks, log watching
```

---

## 🏗️ Architecture

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI + Python 3.10+, async/await throughout |
| **Database** | MongoDB (Motor async driver) |
| **Frontend** | React 18 + TailwindCSS + shadcn/ui |
| **Sandbox** | E2B.dev — isolated code execution environments |
| **LLM** | OpenAI GPT-4o |
| **Streaming** | Server-Sent Events (SSE) for real-time pipeline updates |
| **Deploy** | Local preview (iframe) + Railway/Fly.io cloud deploy |

### Backend Structure

```
backend/
├── server.py                    # FastAPI app, CORS, router registration
├── database.py                  # MongoDB Motor async connection
├── requirements.txt
├── .env.example
├── models/
│   └── session.py               # Pydantic v2: Project, Task, TaskTree, TestResult, DeployInfo
├── routers/
│   ├── health.py                # GET /health
│   └── projects.py              # Full CRUD + pipeline trigger + SSE stream
└── lib/
    ├── streaming/sse.py         # SSEManager — pub/sub event broadcasting
    ├── multi_agent/
    │   └── orchestrator.py      # 5-agent pipeline orchestrator
    ├── workflows/
    │   └── pipeline.py          # Pipeline state machine
    ├── sandbox/
    │   └── e2b_client.py        # E2B.dev sandbox integration
    ├── runtime/
    │   └── executor.py          # Task execution engine
    ├── deploy/
    │   └── deployer.py          # Deployment management
    ├── guardrails/
    │   └── command_filter.py    # Dangerous command blocking
    ├── tools/
    │   └── file_tools.py        # File manipulation helpers
    ├── summary/
    │   └── summarizer.py        # OpenAI-powered summarization
    ├── diff/
    │   └── differ.py            # File diff utilities
    └── utils/
        └── retry.py             # Exponential backoff retry
```

### Frontend Structure

```
frontend/src/
├── App.jsx                      # Main app shell, routing, toast system
├── index.js / index.css         # Entry point + Tailwind base
├── api/
│   └── ark.js                   # Full API client class
├── hooks/
│   └── useSSE.js                # SSE hook with auto-reconnect (max 5 retries)
└── components/ark/
    ├── GoalInput.jsx             # Natural language project creation form
    ├── PipelineView.jsx          # 5-stage animated pipeline visualizer
    ├── EventLog.jsx              # Real-time SSE event stream, color-coded by agent
    ├── FileExplorer.jsx          # File tree + syntax-highlighted code viewer
    ├── TestResults.jsx           # Pass/fail/skip breakdown + coverage metrics
    ├── DeployPanel.jsx           # Live URL card + build metadata
    └── ProjectList.jsx           # Project sidebar with status badges
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB (local or Atlas)
- OpenAI API key
- E2B API key (get one at [e2b.dev](https://e2b.dev))

### Option 1: Docker Compose (Recommended)

```bash
# Clone and enter the project
cd /a0/usr/workdir/ark-ide

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Start everything
docker-compose up --build
```

Services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MongoDB**: localhost:27017

### Option 2: Manual Setup

#### Backend

```bash
cd /a0/usr/workdir/ark-ide/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your keys

# Start the server
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend

```bash
cd /a0/usr/workdir/ark-ide/frontend

# Install dependencies
npm install

# Start development server
npm start
# → http://localhost:3000
```

---

## ⚙️ Configuration

Create `backend/.env` from the example:

```env
# MongoDB
MONGODB_URL=mongodb://localhost:27017
DB_NAME=ark_ide

# OpenAI — Required for all agents
OPENAI_API_KEY=sk-...

# E2B — Required for sandbox code execution
E2B_API_KEY=e2b_...

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/projects` | Create project with goal |
| `GET` | `/api/projects` | List all projects |
| `GET` | `/api/projects/{id}` | Get project details |
| `POST` | `/api/projects/{id}/run` | Start pipeline |
| `GET` | `/api/projects/{id}/stream` | **SSE** real-time event stream |
| `GET` | `/api/projects/{id}/files` | Get generated file manifest |
| `GET` | `/api/projects/{id}/tests` | Get test results |
| `GET` | `/api/projects/{id}/deploy` | Get deploy info |
| `POST` | `/api/projects/{id}/approve` | Approve dangerous action |
| `DELETE` | `/api/projects/{id}` | Delete project |
| `GET` | `/health` | Health check |

### SSE Event Schema

All real-time events follow this schema:

```json
{
  "event_type": "pipeline_start|agent_start|agent_complete|task_start|task_complete|task_failed|test_results|deploy_complete|pipeline_complete|error",
  "agent": "planner|builder|tester|deployer|monitor",
  "stage": 1,
  "message": "Human readable message",
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## 🎨 Dashboard Layout

```
┌─────────────────┬──────────────────────┬─────────────────┐
│  Project List   │   Live Agent Feed    │  Code Preview   │
│  (Sidebar)      │   (SSE Stream)       │  (File Tree +   │
│                 │                      │   iframe)       │
│  Goal Input     ├──────────────────────┤                 │
│                 │   Test Results       │  Deploy Panel   │
│  Pipeline       │   (Pass/Fail/Cov)    │                 │
│  Visualizer     │                      │                 │
│  (5 stages)     │                      │                 │
└─────────────────┴──────────────────────┴─────────────────┘
```

### Pipeline Stage Colors

| Agent | Color | Stage |
|-------|-------|-------|
| 🧠 Planner | Purple | 1 |
| 🔨 Builder | Blue | 2 |
| 🧪 Tester | Yellow | 3 |
| 🚀 Deployer | Green | 4 |
| 👁️ Monitor | Gray | 5 |

---

## 🔒 Safety & Guardrails

ARK IDE includes a command filter that:
- **Blocks** dangerous commands (rm -rf /, fork bombs, credential theft)
- **Flags** commands requiring approval (npm publish, git push, cloud deletes)
- **Limits** pipeline iterations to `MAX_ITERATIONS=3` to prevent infinite loops
- **Caps** agent steps at `MAX_STEPS=10` per agent

---

## 🧪 Development

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=. --cov-report=html

# Frontend tests
cd frontend
npm test
```

### Syntax Validation

```bash
# Validate all Python files
find backend -name "*.py" | xargs python -m py_compile && echo "All OK"
```

### API Documentation

Interactive Swagger UI available at: http://localhost:8000/docs
ReDoc available at: http://localhost:8000/redoc

---

## 📦 Production Build

```bash
# Build frontend
cd frontend && npm run build

# Serve with nginx or:
npx serve -s build -l 3000

# Run backend in production mode
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🗺️ Roadmap

- [ ] GitHub integration (push generated code to repo)
- [ ] Multi-language support (Go, Rust, Java)
- [ ] Team collaboration (shared projects)
- [ ] Custom agent plugins
- [ ] Persistent sandbox sessions
- [ ] Cost tracking per pipeline run

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with ❤️ by ARK Intelligence — Powered by GPT-4o + E2B Sandboxes*
