# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

MIRIX is a Multi-Agent Personal Assistant with an Advanced Memory System. It features six specialized memory components (Core, Episodic, Semantic, Procedural, Resource, Knowledge Vault) managed by dedicated agents, screen activity tracking, and privacy-first design with local data storage.

## Development Commands

### Backend Development
```bash
# Create and activate virtual environment
python -m venv mirix_env
source mirix_env/bin/activate  # On Windows: mirix_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the main server (port 47283)
python main.py

# Alternative with custom host/port
python main.py --host 0.0.0.0 --port 8000
```

### Frontend Development (React/Electron)
```bash
cd frontend

# Install dependencies
npm install

# Start React development server
npm start

# Run Electron app in development
npm run electron-dev

# Build production version
npm run build

# Package Electron app
npm run electron-pack
```

### MCP SSE Service
```bash
# Install MCP SSE specific dependencies
pip install -r requirements-mcp-sse.txt

# Run MCP SSE service (port 8080)
cd mcp_sse_service
python -m mirix.server.mcp_sse_server
```

### Docker Deployment
```bash
# Start all services with Docker Compose
docker-compose up -d

# Start individual services
docker-compose up postgres redis mirix-backend
docker-compose up mirix-frontend mirix-mcp-sse

# Development environment
docker-compose -f docker-compose.dev.yml up

# View logs
docker-compose logs -f mirix-backend
```

### Code Quality
```bash
# Run linting (if using pyproject.toml configuration)
black --check .
isort --check-only .
flake8

# Format code
black .
isort .

# Run tests
pytest
```

## Architecture

### Core Components

- **`mirix/`**: Main Python package containing all core functionality
  - **`agent/`**: Multi-agent system with specialized memory agents
    - `AgentWrapper`: Main interface for agent interactions
    - Memory agents: `EpisodicMemoryAgent`, `SemanticMemoryAgent`, `CoreMemoryAgent`, etc.
  - **`server/`**: FastAPI server implementation
  - **`client/`**: Client interfaces (`LocalClient`)
  - **`schemas/`**: Pydantic schemas for data validation
  - **`database/`**: ORM models and database management
  - **`functions/`**: Tool and function implementations
  - **`llm_api/`**: LLM provider integrations (OpenAI, Anthropic, Google)

- **`frontend/`**: React/Electron desktop application
- **`mcp_sse_service/`**: MCP (Model Context Protocol) over SSE implementation
- **`docs/`**: API documentation and guides

### Memory System Architecture

The system uses six specialized memory agents:
1. **Core Memory**: Essential facts and preferences
2. **Episodic Memory**: Specific events and experiences
3. **Semantic Memory**: General knowledge and concepts
4. **Procedural Memory**: Skills and how-to knowledge
5. **Resource Memory**: File and document management
6. **Knowledge Vault**: Structured information storage

### Data Storage

- **PostgreSQL**: Primary database with pgvector for embeddings
- **Redis**: Session management and caching
- **Local Files**: Configuration, logs, and user data

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://mirix:mirix123@localhost:5432/mirix
REDIS_URL=redis://:redis123@localhost:6379/0

# API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_AI_API_KEY=your_google_key

# Server Configuration
HOST=0.0.0.0
PORT=47283
LOG_LEVEL=INFO
```

### Agent Configuration
- Main config: `mirix/configs/mirix.yaml`
- Agent-specific configs available for different models
- Default model: `gemini-2.5-flash-lite`

## Key Services and Ports

- **Backend API**: http://10.157.152.40:47283
- **Frontend UI**: http://localhost:18001 (Docker) / http://localhost:3000 (dev)
- **MCP SSE Service**: http://localhost:18002 (Docker) / http://localhost:8080 (dev)
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6380 (Docker) / localhost:6379 (local)

## Development Workflow

### Git Workflow
The project uses a structured Git workflow with:
- Conventional commit messages (feat/fix/docs/style/refactor/test/chore)
- PowerShell scripts in `scripts/` for workflow automation
- Pre-configured commit message templates

### Branch Strategy
- Main development: `develop-mcp-server`
- Feature branches: `feature/feature-name`
- Bug fixes: `fix/bug-description`

### Testing
- Test files located in `tests/`
- Run with: `pytest`
- Test configuration in `pyproject.toml`

## SDK Usage

The project provides a Python SDK for easy integration:

```python
from mirix import Mirix

# Initialize with API key
memory_agent = Mirix(api_key="your-google-api-key")

# Add memories
memory_agent.add("Important information to remember")

# Chat with memory context
response = memory_agent.chat("What did I tell you about...?")
```

## Common Operations

### Initialize Database
```bash
python init_db.py
```

### Reset Database
```bash
python scripts/reset_database.py
```

### Debug Tools
```bash
# Debug memory system
python debug_resource_memory.py

# Debug user organization
python debug_user_org.py

# Diagnose server
python diagnose_server.py
```

## Platform-Specific Notes

### Windows
- Use PowerShell scripts in `scripts/` directory
- Electron builds create NSIS installers

### macOS
- Electron builds create DMG files
- Backend bundled as executable

### Linux
- Electron builds create AppImage files
- Standard Python virtual environment workflow