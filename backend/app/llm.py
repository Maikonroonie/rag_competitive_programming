from __future__ import annotations

from openai import APIError, OpenAI

from .config import settings
from .models import ChatMessage, Mode, RetrievedDoc

_PLACEHOLDER_KEYS = {"", "sk-...", "sk-your-key-here", "not-needed"}


# llm configured?
def _llm_configured() -> bool:
    if settings.openai_base_url:
        return True
    key = settings.openai_api_key.strip()
    if not key or key in _PLACEHOLDER_KEYS or key.endswith("..."):
        return False
    return True


# openai client or none
def _client() -> OpenAI | None:
    if not _llm_configured():
        return None
    kwargs: dict = {"api_key": settings.openai_api_key or "not-needed"}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return OpenAI(**kwargs)


# call llm
def generate_answer(
    system_prompt: str,
    history: list[ChatMessage],
    user_message: str,
    mode: Mode,
    code_unlocked: bool,
    retrieved: list[RetrievedDoc],
) -> str:
    client = _client()
    if client is None:
        return _demo_answer(mode, code_unlocked, retrieved)

    messages = [{"role": "system", "content": system_prompt}]
    messages += [{"role": m.role, "content": m.content} for m in history[-10:]]
    messages.append({"role": "user", "content": user_message})

    try:
        completion = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.4,
            max_tokens=1200,
        )
        return completion.choices[0].message.content or ""
    except APIError as err:
        return _demo_answer(
            mode,
            code_unlocked,
            retrieved,
            prefix=f"**LLM request failed ({err.__class__.__name__}).** Check `backend/.env`.\n",
        )


# fallback without llm
def _demo_answer(
    mode: Mode,
    code_unlocked: bool,
    retrieved: list[RetrievedDoc],
    prefix: str = "",
) -> str:
    lines = [
        prefix,
        "**[DEMO MODE — no LLM configured]**",
        "Set a real `OPENAI_API_KEY` or `OPENAI_BASE_URL` in `backend/.env` to get full responses.",
        "",
        f"Active state: **{mode.value}**, code {'UNLOCKED' if code_unlocked else 'LOCKED'}.",
    ]
    if retrieved:
        lines.append("\nTop matches from the knowledge base:")
        for d in retrieved:
            lines.append(f"- **{d.title}** ({d.kind}, score {d.score:.2f})")
        best = retrieved[0]
        lines.append(f"\nBest match excerpt:\n> {best.snippet[:400]}")
    else:
        lines.append("\nKnowledge base returned no results — run `python ingest.py`.")
    return "\n".join(line for line in lines if line != "")
