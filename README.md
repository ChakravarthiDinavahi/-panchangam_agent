# Panchangam agent

Local RAG agent over Telugu panchangam and related documents using [LlamaIndex](https://www.llamaindex.ai/), [Ollama](https://ollama.com/) (Qwen3), and Hugging Face embeddings (`BAAI/bge-m3`). Optional **FastAPI** web UI for chat in the browser.

## Prerequisites

- **Python** 3.10 or newer
- **[Ollama](https://ollama.com/download)** installed and running
- Enough disk/RAM for the embedding model (first run downloads weights)

## 1. Install Ollama and the chat model

Install Ollama, then pull the model the script uses:

```bash
ollama pull qwen3:8b
```

Keep the Ollama app or `ollama serve` running while you use the agent.

## 2. Python environment

From the repository root:

```bash
python3 -m venv ai_agent_env
source ai_agent_env/bin/activate   # Windows: ai_agent_env\Scripts\activate
pip install --upgrade pip
pip install -r ai_agent_env/requirements.txt
```

## 3. Data files (PDF and text)

Put documents in a folder named **`data`** next to where you run the app:

- If you run **from the repo root**, you can use a top-level **`data/`** directory (if you point `PDF_PATH` there) or keep everything under **`ai_agent_env/data/`** as in this repo.
- If you **`cd ai_agent_env`**, use **`ai_agent_env/data/`**.

The agent loads **all supported files** under `./data` via LlamaIndex `SimpleDirectoryReader` (see `PDF_PATH` in `local_panchangam_agent.py`). Typical formats include PDFs (for example `panchangam2026.pdf`) and plain text. This repository includes **`ai_agent_env/data/sandhyavandanam.txt`** as reference text for Sandhyavandanam-related questions.

Add your own PDFs locally if you need the full panchangam; large PDFs are not always committed to git.

## 4. Run the agent (CLI)

**Recommended (from `ai_agent_env`, uses `ai_agent_env/data/`):**

```bash
source ai_agent_env/bin/activate
cd ai_agent_env
python local_panchangam_agent.py
```

**From repo root:**

```bash
source ai_agent_env/bin/activate
python ai_agent_env/local_panchangam_agent.py
```

Ensure your current working directory matches where `./data` should resolve, or adjust `PDF_PATH` in code.

At the prompt, ask in Telugu, English, or transliterated Telugu (Manglish). Type **`exit`** or **`quit`** to stop.

## 5. Web UI (FastAPI)

Run the API and embedded chat page from **`ai_agent_env`** so `./data` resolves correctly:

```bash
source ai_agent_env/bin/activate
cd ai_agent_env
python -m uvicorn chat_app:app --reload --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000** in a browser. The UI streams replies; **`POST /api/chat`** returns a full JSON reply, and **`POST /api/chat/stream`** streams Server-Sent Events for custom clients.

## Configuration

In `ai_agent_env/local_panchangam_agent.py` you can change:

- **`PDF_PATH`** — directory of documents (default `./data`)
- **`Settings.llm`** — Ollama model name (default `qwen3:8b`)
- **`HuggingFaceEmbedding(model_name=...)`** — embedding model (default `BAAI/bge-m3`)

## Troubleshooting

- **`Connection refused` to Ollama** — Start Ollama and confirm `ollama list` shows `qwen3:8b`.
- **First run is slow** — Hugging Face will download `bge-m3`; subsequent runs are faster.
- **Empty or missing data** — Ensure `./data` exists from your current working directory and contains files before starting.
