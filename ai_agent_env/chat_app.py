"""
FastAPI web server for the Panchangam chat agent.

Run from this directory (so ./data resolves correctly):
  uvicorn chat_app:app --reload --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool

from llama_index.core.base.response.schema import StreamingResponse as LIStreamingResponse

from local_panchangam_agent import setup_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = await run_in_threadpool(setup_agent)
    app.state.query_engine = engine
    yield


app = FastAPI(title="Panchangam Chat", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=16000)


class ChatResponse(BaseModel):
    reply: str


def _sync_full_reply(message: str) -> str:
    engine = app.state.query_engine
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Agent not initialized. Add PDFs under ./data and restart.",
        )
    response = engine.query(message)
    return str(response)


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return CHAT_HTML


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    reply = await run_in_threadpool(_sync_full_reply, req.message)
    return ChatResponse(reply=reply)


def _sse_token_chunks(message: str):
    engine = app.state.query_engine
    if engine is None:
        err = json.dumps({"error": "Agent not initialized. Add PDFs under ./data and restart."})
        yield f"data: {err}\n\n"
        return
    response = engine.query(message)
    if isinstance(response, LIStreamingResponse) and response.response_gen is not None:
        for chunk in response.response_gen:
            yield f"data: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"
    else:
        text = str(response)
        yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        iterate_in_threadpool(_sse_token_chunks(req.message)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


CHAT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Panchangam Chat</title>
  <style>
    :root {
      --bg: #0f1419;
      --surface: #1a2332;
      --text: #e8eaed;
      --muted: #8b9cb3;
      --accent: #c9a227;
      --border: #2d3a4d;
    }
    * { box-sizing: border-box; }
    body {
      font-family: "Georgia", "Times New Roman", serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      padding: 1rem 1.25rem;
      border-bottom: 1px solid var(--border);
      background: var(--surface);
    }
    header h1 {
      margin: 0;
      font-size: 1.25rem;
      font-weight: 600;
      color: var(--accent);
    }
    header p { margin: 0.35rem 0 0; font-size: 0.85rem; color: var(--muted); }
    #log {
      flex: 1;
      overflow-y: auto;
      padding: 1rem 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }
    .msg {
      max-width: 52rem;
      padding: 0.65rem 0.9rem;
      border-radius: 8px;
      line-height: 1.5;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .msg.user {
      align-self: flex-end;
      background: var(--surface);
      border: 1px solid var(--border);
    }
    .msg.assistant {
      align-self: flex-start;
      background: #16202e;
      border: 1px solid var(--border);
    }
    .msg.assistant.streaming { opacity: 0.95; }
    form {
      display: flex;
      gap: 0.5rem;
      padding: 1rem 1.25rem;
      border-top: 1px solid var(--border);
      background: var(--surface);
    }
    textarea {
      flex: 1;
      min-height: 2.75rem;
      max-height: 8rem;
      resize: vertical;
      padding: 0.6rem 0.75rem;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text);
      font: inherit;
    }
    button {
      padding: 0.6rem 1.1rem;
      border-radius: 8px;
      border: 1px solid var(--accent);
      background: transparent;
      color: var(--accent);
      font: inherit;
      cursor: pointer;
      align-self: flex-end;
    }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    button:not(:disabled):hover { background: rgba(201, 162, 39, 0.12); }
  </style>
</head>
<body>
  <header>
    <h1>Panchangam agent</h1>
    <p>Telugu astrology Q&A from your indexed PDF. Streaming replies.</p>
  </header>
  <div id="log" aria-live="polite"></div>
  <form id="f">
    <textarea id="q" rows="2" placeholder="Ask in Telugu, English, or Manglish…" autocomplete="off"></textarea>
    <button type="submit" id="send">Send</button>
  </form>
  <script>
    const log = document.getElementById("log");
    const form = document.getElementById("f");
    const input = document.getElementById("q");
    const send = document.getElementById("send");

    function addMsg(role, text, streaming) {
      const div = document.createElement("div");
      div.className = "msg " + role + (streaming ? " streaming" : "");
      div.textContent = text;
      log.appendChild(div);
      log.scrollTop = log.scrollHeight;
      return div;
    }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const message = input.value.trim();
      if (!message) return;
      input.value = "";
      send.disabled = true;
      addMsg("user", message);
      const assistantEl = addMsg("assistant", "", true);

      try {
        const res = await fetch("/api/chat/stream", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message }),
        });
        if (!res.ok) {
          assistantEl.textContent = "Error: " + res.status + " " + res.statusText;
          assistantEl.classList.remove("streaming");
          return;
        }
        const reader = res.body.getReader();
        const dec = new TextDecoder();
        let buf = "";
        let full = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += dec.decode(value, { stream: true });
          const lines = buf.split("\\n");
          buf = lines.pop() || "";
          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const data = line.slice(6).trim();
            if (data === "[DONE]") continue;
            try {
              const j = JSON.parse(data);
              if (j.error) {
                assistantEl.textContent = j.error;
                assistantEl.classList.remove("streaming");
                return;
              }
              if (j.text) {
                full += j.text;
                assistantEl.textContent = full;
                log.scrollTop = log.scrollHeight;
              }
            } catch (_) {}
          }
        }
      } catch (err) {
        assistantEl.textContent = "Network error: " + err;
      } finally {
        assistantEl.classList.remove("streaming");
        send.disabled = false;
        input.focus();
      }
    });
  </script>
</body>
</html>
"""
