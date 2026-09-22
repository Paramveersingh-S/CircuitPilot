<div align="center">
  <img src="logo.jpg" alt="CircuitPilot Logo" width="160" style="border-radius: 24px;"/>

  <h1>CircuitPilot</h1>
  <p><strong>Expert AI-Powered PCB Design · From Prompt to Physical Board</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Frontend-React%20%7C%20Vite-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React" />
    <img src="https://img.shields.io/badge/Language-TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript" />
    <img src="https://img.shields.io/badge/Backend-Python%20%7C%20FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/AI-LiteLLM%20%7C%20Multi--Provider-FF6F00?style=for-the-badge&logo=openai&logoColor=white" alt="LiteLLM" />
    <img src="https://img.shields.io/badge/Engine-KiCad%20%7C%20Native%20Router-314CB6?style=for-the-badge&logo=kicad&logoColor=white" alt="KiCad" />
    <img src="https://img.shields.io/badge/Runtime-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  </p>
  
  <p>
    <a href="https://github.com/Paramveersingh-S/CircuitPilot/stargazers"><img src="https://img.shields.io/github/stars/Paramveersingh-S/CircuitPilot?style=social" alt="Stars Badge"/></a>
    <a href="https://github.com/Paramveersingh-S/CircuitPilot/fork"><img src="https://img.shields.io/github/forks/Paramveersingh-S/CircuitPilot?style=social" alt="Forks Badge"/></a>
    <a href="https://github.com/Paramveersingh-S/CircuitPilot/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Paramveersingh-S/CircuitPilot?style=flat-square" alt="License Badge"/></a>
    <a href="https://x.com/ParamveerS15896"><img src="https://img.shields.io/badge/Twitter-Follow-1DA1F2?logo=twitter&style=flat-square" alt="Twitter"/></a>
  </p>
</div>

<br />

## Overview

**Stop manually placing components for simple IoT boards. Let physics and AI do it in seconds.**

**CircuitPilot** is an open-source AI agent that translates natural language into production-ready KiCad PCB layouts using a multi-stage pipeline. Unlike wrappers that just output text, CircuitPilot includes a custom built **Force-Directed Physics Router** to generate expert-quality boards with 45-degree multi-layer trace routing.

👉 **[Read the Deep Dive: How the Force-Directed Physics Router Works](ARCHITECTURE.md)**

### Application

<div align="center">
  <img src="app_screenshot.png" alt="CircuitPilot Application Interface" width="860"/>
  <p><em>CircuitPilot UI — AI Chat, IPC Critic verification, real-time KiCanvas board viewer with zoom/pan controls.</em></p>
</div>

### PCB Output Example (KiCad Desktop)

<div align="center">
  <img src="pcb_output.png" alt="Force-Directed AI Generated PCB Output" width="860"/>
  <p><em>AI-generated PCB opened in KiCad — Force-Directed Net-Aware routing with 45-degree chamfers, multi-layer vias, copper ground pour, and M3 mounting holes. Generated entirely from a single text prompt.</em></p>
</div>

---

## How It Works

```mermaid
flowchart TD
    U(["User Prompt\n(Natural Language)"]):::user
    U --> P

    subgraph AI_PIPELINE ["AI Pipeline (3-Stage)"]
        direction TB
        P["Planner LLM\nExtracts categorized\ncomponent list"]:::llm
        P -->|"JSON: main_ics, decoupling_caps,\npassives, connectors"| C
        C["Critic LLM\nSelf-verification pass\nEnforces IPC rules"]:::critic
        C -->|"Corrected + IPC-compliant\ncomponent manifest"| R
    end

    subgraph ROUTER ["Native Python Router Engine"]
        direction TB
        R["Force-Directed\nPlacement Simulation\n(Physics-based clustering)"]:::engine
        R --> N["Net-Aware Ratsnest\nRouting\n(Shortest-first, per net)"]:::engine
        N --> T["45° Chamfered\nTrace Generator\nIPC-2152 width rules"]:::engine
        T --> G["KiCad PCB Builder\nMounting holes · GND pour\nMulti-layer vias"]:::engine
    end

    G -->|".kicad_pcb file"| WS
    WS["WebSocket Stream\nFastAPI Backend"]:::server --> KV
    KV["KiCanvas Viewer\nZoom · Pan · Download\nIn-browser PCB viewer"]:::frontend

    KV --> KD["KiCad Desktop\nFull DRC · 3D View\nGerber Export"]:::kicad

    classDef user fill:#6366f1,stroke:#4f46e5,color:#fff
    classDef llm fill:#0ea5e9,stroke:#0284c7,color:#fff
    classDef critic fill:#f59e0b,stroke:#d97706,color:#fff
    classDef engine fill:#10b981,stroke:#059669,color:#fff
    classDef server fill:#8b5cf6,stroke:#7c3aed,color:#fff
    classDef frontend fill:#334155,stroke:#475569,color:#fff
    classDef kicad fill:#1e40af,stroke:#1d4ed8,color:#fff
```

---

## Features

- **Prompt-to-PCB in seconds**: Describe any circuit in plain English, get a physical board
- **LLM Self-Verification (Critic)**: A second AI pass enforces IPC design rules before routing — adds missing decoupling caps, crystal oscillators, resistors for LEDs automatically
- **Force-Directed Physics Placement**: Components cluster organically by electrical connectivity, not rigid grids
- **Net-Aware Ratsnest Routing**: Routes shortest connections first per net, like a real EDA tool
- **IPC-2152 Trace Widths**: Power nets routed at 0.8mm, signal nets at 0.25mm automatically
- **Multi-Layer Routing**: Automatically switches between F.Cu and B.Cu with drill vias
- **DFM Edge Clearances**: 15mm margins enforced from board edge (fabrication safe)
- **Provider-Agnostic AI**: Switch between OpenAI, Gemini, Anthropic, or local Ollama via `.env`
- **Interactive KiCanvas Viewer**: Zoom, pan, and inspect the board before downloading

---

## Architecture

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, TypeScript, KiCanvas |
| Backend | Python 3.11, FastAPI, WebSockets |
| AI Layer | LiteLLM (OpenAI / Gemini / Anthropic / Ollama) |
| PCB Router | Custom Native Python Engine (Force-Directed + Net-Aware) |
| Containerization | Docker, Docker Compose |
| PCB Format | KiCad 10 `.kicad_pcb` |

---

## Quick Start (Zero Friction)

The easiest way to run CircuitPilot is via Docker. You just need an LLM API key (OpenAI, Gemini, Anthropic, etc).

```bash
git clone https://github.com/Paramveersingh-S/CircuitPilot.git
cd CircuitPilot/backend
cp .env.example .env 
# Add your OPENAI_API_KEY to .env, then run:
cd .. && docker-compose up --build
```
Then open `http://localhost:5173` in your browser!

---

## Local Development Setup

### Prerequisites

- **Node.js** (v18+)
- **Python** (v3.11+)
- An LLM API key

### 1. Configure Environment

```bash
cd backend
cp .env.example .env
# Edit .env:
# OPENAI_API_KEY=your_key
# LLM_MODEL=openai/gpt-4o          # or gemini/gemini-2.0-flash
# OPENAI_API_BASE=http://localhost:11434  # for Ollama
```

### 2. Start the Backend

```bash
cd backend
python -m venv venv311
.\venv311\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Docker (Full Stack)

```bash
docker compose up --build
```

---

## Usage

1. Navigate to `http://localhost:5173/`
2. Describe your circuit in the Chat Panel
3. Watch: **Planner** extracts components → **Critic** verifies IPC rules → **Router** generates the board
4. Use **Scroll** to zoom and **Right-click drag** to pan the board in the browser
5. Download the `.kicad_pcb` file and open in KiCad Desktop for full DRC + 3D view + Gerber export
