# Contributing to CircuitPilot

First off, thank you for considering contributing to CircuitPilot! It's people like you that make open source tools powerful and accessible.

## Project Structure
CircuitPilot has a dual-layer architecture:
- **`backend/`**: A Python/FastAPI server that acts as the orchestrator. It uses `LiteLLM` to talk to AI models (the "Planner" and "Critic") and includes a custom Force-Directed Python physics engine to layout the PCBs and route tracks, outputting a `.kicad_pcb` file.
- **`frontend/`**: A React/Vite/TypeScript frontend that provides the chat interface and the KiCanvas-based board viewer.

## Local Setup
To run the full stack locally:

### 1. Backend
```bash
cd backend
python -m venv venv311
# Windows: .\venv311\Scripts\Activate.ps1
# Mac/Linux: source venv311/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
Make sure you copy `.env.example` to `.env` and provide an API key (like `OPENAI_API_KEY`) so the LLM pipeline works.

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```

## Pull Request Process

1. **Fork the repo** and create your branch from `main`.
2. **Make your changes**. 
3. **Ensure it builds**: We don't enforce strict formatting right now, but your code *must* compile. The GitHub Actions CI pipeline will run `npm run build` for the frontend and check Python syntax for the backend.
4. **Create a Pull Request**: Use the provided PR template. Fill it out completely with context on what you are fixing or adding.
5. **Code Review**: A maintainer will review your code. Once approved and the CI is green, it will be merged!

## Code Guidelines
- Keep things simple.
- If you modify the PCB Generator physics (`backend/app/agent/tools/native_generator.py`), please attach a screenshot in your PR showing that the output board still routes properly.
- Be respectful and kind in issues and PRs.
