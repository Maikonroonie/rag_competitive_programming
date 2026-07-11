from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import ast_analyzer, llm, prompts
from .models import ChatRequest, ChatResponse, Mode
from .rag import get_store

app = FastAPI(title="Competitive Programming Copilot", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# health check
@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


# main chat pipeline
@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    analysis = ast_analyzer.analyze_code(req.user_code) if req.user_code.strip() else None

    query_parts = [req.user_query, req.task_context]
    if analysis is not None:
        query_parts.append(ast_analyzer.code_to_search_text(analysis, req.user_code))
    search_query = "\n".join(p for p in query_parts if p.strip())

    retrieved = get_store().search(search_query, code_unlocked=req.code_unlocked)

    system_prompt = prompts.build_system_prompt(
        mode=req.current_mode,
        code_unlocked=req.code_unlocked,
        retrieved=retrieved,
        analysis=analysis,
        task_context=req.task_context,
    )

    user_message = req.user_query
    if req.user_code.strip():
        user_message += f"\n\nMój kod:\n```\n{req.user_code}\n```"

    answer = llm.generate_answer(
        system_prompt=system_prompt,
        history=req.history,
        user_message=user_message,
        mode=req.current_mode,
        code_unlocked=req.code_unlocked,
        retrieved=retrieved,
    )

    return ChatResponse(
        response=answer,
        mode=req.current_mode,
        code_unlocked=req.code_unlocked,
        retrieved=retrieved,
        code_analysis=analysis,
    )
