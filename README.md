# CircuitPilot 🚀

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![KiCad](https://img.shields.io/badge/KiCad-314CB6?style=for-the-badge&logo=kicad&logoColor=white)](https://www.kicad.org/)
[![atopile](https://img.shields.io/badge/atopile-000000?style=for-the-badge&logo=python&logoColor=white)](https://atopile.io/)

**CircuitPilot** is an AI-Enabled Real-Time PCB Design Copilot.

Unlike typical chatbots, CircuitPilot directly edits a real, DRC-checked KiCad project through the same engine a human PCB designer uses, using the new KiCad 9 IPC API and `atopile` for declarative circuit constraints.

## System Architecture

```mermaid
flowchart TD
    subgraph Browser ["Browser (frontend/)"]
        ChatPanel["Chat Panel\n(commands)"]
        BoardCanvas["KiCanvas\n(live-reloading)"]
        ActivityFeed["Activity Feed\n(tool-call trace)"]
    end
    
    subgraph Backend ["Backend (backend/app) - FastAPI"]
        Orchestrator["Orchestrator\n(Planner + Agent Core)"]
        
        SchematicAgent["Schematic Agent\n(ato_tools)"]
        LayoutAgent["Layout Agent\n(kicad_tools)"]
        RoutingAgent["Routing Agent\n(routing_tools)"]
        VerificationAgent["Verification Agent\n(verification_tools)"]
        ManufacturingAgent["Manufacturing Agent\n(export_tools)"]
        
        Orchestrator --> SchematicAgent
        Orchestrator --> LayoutAgent
        Orchestrator --> RoutingAgent
        RoutingAgent --> VerificationAgent
        VerificationAgent --> ManufacturingAgent
        
        SchematicAgent --> atopile["atopile compiler"]
        LayoutAgent --> KiCadIPC["KiCad IPC API\n(kicad-python)"]
        RoutingAgent --> KiCadIPC
        RoutingAgent --> AutoRouter["Freerouting / OrthoRoute"]
        
        Store["Project Store\n(git-backed workspace)"]
    end
    
    subgraph KiCadHost ["KiCad Host"]
        KiCadInstance["Headless KiCad 9.x\n(IPC API server enabled)"]
    end
    
    ChatPanel -- "WebSocket" --> Orchestrator
    Orchestrator -- "file_changed" --> BoardCanvas
    Orchestrator -- "events" --> ActivityFeed
    
    atopile --> Store
    KiCadIPC --> Store
    KiCadIPC <--> KiCadInstance
```

## Features

- **Schematic Copilot**: Natural language translation into `atopile` `.ato` code for schematic generation.
- **Layout Copilot**: Auto-placement heuristics and manual layout adjustments via AI.
- **Routing Copilot**: Deep integration with external autorouters like Freerouting or OrthoRoute and KiCad interactive router.
- **Manufacturing Export**: Automated DFM checks and one-click Gerber/BOM/CPL generation.

## Getting Started

Run the full stack via Docker Compose:
```bash
docker-compose up --build
```
Open `http://localhost:5173` to view the UI.
