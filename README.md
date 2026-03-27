# Panchangam agent

Local RAG agent over a Telugu panchangam PDF using [LlamaIndex](https://www.llamaindex.ai/), [Ollama](https://ollama.com/) (Qwen3), and Hugging Face embeddings (`BAAI/bge-m3`).

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
pip install llama-index llama-index-llms-ollama llama-index-embeddings-huggingface
```

## 3. Panchangam PDF

Put your PDF (for example `panchangam2026.pdf`) in a folder named **`data`** next to where you run the script:

- If you run the script **from the repo root**, use the top-level **`data/`** directory.
- If you `cd ai_agent_env` and run it there, use **`ai_agent_env/data/`**.

The script reads every file under `./data` (see `PDF_PATH` in `local_panchangam_agent.py`).

## 4. Run the agent

**Recommended (repo root, uses `data/` at the project root):**

```bash
source ai_agent_env/bin/activate
python ai_agent_env/local_panchangam_agent.py
```

**Alternative (from `ai_agent_env`, uses `ai_agent_env/data/`):**

```bash
source ai_agent_env/bin/activate
cd ai_agent_env
python local_panchangam_agent.py
```

At the prompt, ask in Telugu, English, or transliterated Telugu (Manglish). Type **`exit`** or **`quit`** to stop.

## Configuration

In `ai_agent_env/local_panchangam_agent.py` you can change:

- **`PDF_PATH`** — directory of PDFs (default `./data`)
- **`Settings.llm`** — Ollama model name (default `qwen3:8b`)
- **`HuggingFaceEmbedding(model_name=...)`** — embedding model (default `BAAI/bge-m3`)

## Troubleshooting

- **`Connection refused` to Ollama** — Start Ollama and confirm `ollama list` shows `qwen3:8b`.
- **First run is slow** — Hugging Face will download `bge-m3`; subsequent runs are faster.
- **Empty or missing data** — Ensure `./data` exists from your current working directory and contains the PDF before starting.
