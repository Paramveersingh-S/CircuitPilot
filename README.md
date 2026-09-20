# CircuitPilot

![CircuitPilot Screenshot](file:///C:/Users/Paramveer/.gemini/antigravity-ide/brain/b18b75ad-0be2-47be-86ee-8594d1be00b7/.user_uploaded/media_1789894996804.png)

CircuitPilot is an **Enterprise-grade, AI-driven PCB Design Copilot**. It allows hardware engineers to rapidly prototype and synthesize physical KiCad boards through natural language interaction.

## ✨ Features
- **AI-Powered Design:** Uses Groq-powered LLMs to understand complex electrical requirements.
- **Native PCB Synthesis:** Dynamically generates real, valid `.kicad_pcb` files instantly on the fly without relying on slow or broken third-party compilers.
- **Interactive UI:** A premium, glassmorphism-inspired dark mode interface that feels responsive and alive.
- **Real-Time Viewer:** Integrates KiCanvas to render newly generated hardware designs directly in your browser.

## 🚀 Getting Started

### Prerequisites
- Node.js
- Python 3.11+

### Installation

1. **Start the Frontend:**
```bash
cd frontend
npm install
npm run dev
```

2. **Start the Backend:**
```bash
cd backend
.\venv311\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

## 🛠️ Architecture
- **Frontend:** React, TypeScript, Vite, Vanilla CSS
- **Backend:** FastAPI, Uvicorn, LiteLLM (Groq)
- **Hardware Integration:** Native Python KiCad Generator, KiCanvas
