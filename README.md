# Deep Research Agent 🧠

![Deep Research Agent](https://via.placeholder.com/1200x600/0E0F14/CBA45D?text=Deep+Research+Agent+Preview)

A next-generation AI research assistant that automates web searching, content analysis, and intelligence report generation. Powered by **FastAPI**, **React**, and **Groq (Llama 3.3)**.

## ✨ Features

-   **Autonomous Research**: Takes a topic, searches the web, and scrapes top sources.
-   **Deep Analysis**: Synthesizes information into a structured, professional intelligence report.
-   **High-Speed Inference**: Utilizes Groq's LPU for near-instant analysis.
-   **Premium UI**: A "Deep Night" interface with Aurora effects, glassmorphism, and editorial typography.
-   **Export Ready**: One-click copy for reports.

## 🤖 Supported Models & Providers

This agent supports multiple AI providers, allowing for flexibility and privacy.

1.  **Groq (Default)**: Uses `llama-3.3-70b` for ultra-fast inference. Requires a Groq API Key.
2.  **OpenAI**: Uses `gpt-4o`. Requires an OpenAI API Key.
3.  **Anthropic**: Uses `claude-3-opus`. Requires an Anthropic API Key.
4.  **Custom / Local**: Connect to any OpenAI-compatible API (e.g., **Ollama**, **LM Studio**, **vLLM**).
    -   Select "Custom" in settings.
    -   Enter Base URL (e.g., `http://localhost:11434/v1`).
    -   Enter Model Name (e.g., `mistral`, `llama3`).

## 🚀 Quick Start

### Prerequisites
-   Python 3.10+
-   Node.js 18+
-   [Groq API Key](https://console.groq.com/) (or key for your preferred provider)

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt

# (Optional) Create .env file for default keys
cp .env.example .env
```
Start the server:
```bash
python main.py
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) (or the port shown in terminal).

## 🛠 Tech Stack

-   **Backend**: Python, FastAPI, Trafilatura (Scraping), DuckDuckGo Search
-   **AI Engine**: Llama 3.3 70B via Groq
-   **Frontend**: React, Vite, Tailwind CSS v3, Framer Motion

## 📄 License

MIT © 2026
