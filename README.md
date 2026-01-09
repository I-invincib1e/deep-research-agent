# Deep Research Agent 🧠

![Deep Research Agent](https://via.placeholder.com/1200x600/0E0F14/CBA45D?text=Deep+Research+Agent+Preview)

A next-generation AI research assistant that automates web searching, content analysis, and intelligence report generation. Powered by **FastAPI**, **React**, and **Groq (Llama 3.3)**.

## ✨ Features

-   **Autonomous Research**: Takes a topic, searches the web, and scrapes top sources.
-   **Deep Analysis**: Synthesizes information into a structured, professional intelligence report.
-   **High-Speed Inference**: Utilizes Groq's LPU for near-instant analysis.
-   **Premium UI**: A "Deep Night" interface with Aurora effects, glassmorphism, and editorial typography.
-   **Export Ready**: One-click copy for reports.

## 🚀 Quick Start

### Prerequisites
-   Python 3.10+
-   Node.js 18+
-   [Groq API Key](https://console.groq.com/)

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
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
