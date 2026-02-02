# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenPoke is a multi-agent AI customer support assistant for Ultrahuman Ring devices. It uses an **interaction/execution agent split**:
- **Interaction Agent**: Conversational interface that understands user intent and routes to execution agents
- **Execution Agents**: Task-specific agents (battery troubleshooting, email drafting, FAQ search, reminders)

Backend uses FastAPI with Gemini 2.0-Flash (via OpenRouter). Frontend is Next.js 14. Gmail integration via Composio SDK.

## Development Commands

### Backend (server/)
```bash
# Install dependencies
pip install -r server/requirements.txt

# Run dev server with auto-reload (port 8001)
python -m server.server --reload

# Production server
python -m uvicorn server.app:app --host 0.0.0.0 --port 8001
```

### Frontend (web/)
```bash
# Install dependencies
npm install --prefix web

# Dev server (port 3000)
npm run dev --prefix web

# Build
npm run build --prefix web

# Lint
npm run lint --prefix web
```

Both servers must run concurrently for full functionality.

## Architecture

```
server/
├── agents/
│   ├── interaction_agent/     # Primary conversational agent
│   │   ├── system_prompt.md   # 250-line behavioral prompt
│   │   ├── agent.py           # Prompt building
│   │   ├── runtime.py         # LLM execution
│   │   └── tools.py           # Tool registry
│   └── execution_agent/       # Task execution engine
│       ├── system_prompt.md   # Task-focused prompt template
│       ├── tools/             # Tool implementations
│       │   ├── gmail.py       # Email operations (Composio)
│       │   ├── triggers.py    # Reminder/scheduling system
│       │   ├── faq_search.py  # Knowledge base lookup
│       │   └── ultrahuman/    # Device-specific tools
│       └── batch_manager.py   # Batch processing
├── routes/                    # FastAPI endpoints (/api/v1)
├── services/                  # Business logic (conversation, gmail, triggers)
├── models/                    # Pydantic request/response models
└── data/                      # Runtime data (git-ignored)

web/
├── app/
│   ├── page.tsx              # Main chat UI
│   └── api/                  # Next.js API routes (proxy to backend)
└── components/               # React components
```

## Request Flow

1. User message → `POST /api/v1/chat/send`
2. Interaction Agent processes with system prompt + conversation history
3. If tool call needed → routes to Execution Agent
4. Execution Agent runs tools (gmail, battery troubleshoot, FAQ, triggers)
5. Response flows back through Interaction Agent to user

## Environment Variables

Required in `.env` (copy from `.env.example`):
- `OPENROUTER_API_KEY` - LLM access
- `COMPOSIO_API_KEY` + `COMPOSIO_GMAIL_AUTH_CONFIG_ID` - Gmail integration
- `ULTRAHUMAN_PARTNER_API_KEY` - Device support API

## Key Behavioral Notes

The Interaction Agent system prompt (`server/agents/interaction_agent/system_prompt.md`) contains critical behavioral rules:
- Assess user sentiment before responding
- Route battery issues directly to `ultrahuman_battery_troubleshoot` tool
- Avoid phrases like "authorization issues", "API issues", "Is there anything else I can help with?"
- Match user tone; avoid overly formal or apologetic responses
