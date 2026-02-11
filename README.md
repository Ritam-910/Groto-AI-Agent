# 🤖 AI Agent with Tools

A powerful, local AI agent featuring real-time web search, calculator, time tools, and a modern UI. This project combines a **FastAPI** backend with a sleek **Vanilla JS** frontend, powered by **Ollama** for local LLM inference.

## 🚀 Key Features

*   **Smart Brain**: Powered by **Phi-3** (fast & capable) 
*   **Integrated Tools**:
    *   🌍 **Web Search**: Real-time results via DuckDuckGo (privacy-focused).
    *   ⏰ **Time**: Accurate local time with timezone awareness.
    *   🧮 **Calculator**: Precise mathematical operations.
*   **Modern Interface**: Beautiful, dark-mode Glassmorphism UI using Vanilla CSS.
*   **Privacy-First**: Runs entirely locally on your machine.

## 🛠️ Installation & Setup

### Prerequisites

1.  **Docker Desktop** (Recommended) OR **Python 3.11+** & **Node.js** (optional for dev).
2.  **Ollama**: [Download here](https://ollama.com) if running manually.

---

### Option 1: Docker (Recommended)

Run the entire stack with a single command. This handles the backend, frontend, and Ollama service.

1.  **Start the containers**:
    ```bash
    docker-compose up -d
    ```
    *This starts the Backend on port `8000` and Ollama on `11434`.*

2.  **Initialize the Model** (One-time setup):
    The Ollama container starts empty. You must pull the model inside it:
    ```bash
    docker exec -it ai_agent_ollama ollama pull phi3:latest
    ```

3.  **Access the App**:
    Open `frontend/index.html` in your browser.

---

### Option 2: Manual Setup (Windows)

1.  **Install Dependencies**:
    ```bash
    pip install -r backend/requirements.txt
    ```

2.  **Pull the Model**:
    Ensure Ollama is installed locally and run:
    ```bash
    ollama pull phi3:latest
    ```

3.  **Start the Backend**:
    Double-click `start-backend.bat` or run:
    ```bash
    cd backend
    python -m uvicorn main:app --reload
    ```

4.  **Start the Frontend**:
    Double-click `start-frontend.bat` or open `frontend/index.html`.

## 💡 Usage

**Just ask naturally!** The agent automatically decides when to use tools.

*   "Search for the latest AI news" → Triggers Web Search
*   "What time is it in Tokyo?" → Triggers Time Tool
*   "Calculate 15% of 850" → Triggers Calculator
*   "Explain quantum entanglement" → Uses internal knowledge

## ⚙️ Configuration

To switch models (e.g., to Llama 3), edit `backend/main.py`:

```python
agent = AIAgent(
    model="phi3:latest",     
    # model="llama3:latest",
    ...
)
```

## 📂 Project Structure

*   `backend/`: FastAPI application, agent logic (LangChain/Ollama), and tools.
*   `frontend/`: Static HTML/CSS/JS interface.
*   `docker-compose.yml`: Container orchestration.

---
*Built with FastAPI, Ollama, and Love.*
