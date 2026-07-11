from enum import Enum

from pydantic import BaseModel, Field


class Mode(str, Enum):
    BRAINSTORMING = "brainstorming"
    COMPLEXITY = "complexity"
    HINT = "hint"


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    user_query: str
    user_code: str = ""
    task_context: str = ""
    current_mode: Mode = Mode.BRAINSTORMING
    code_unlocked: bool = False
    history: list[ChatMessage] = Field(default_factory=list)


class RetrievedDoc(BaseModel):
    title: str
    kind: str
    score: float
    snippet: str


class CodeAnalysis(BaseModel):
    language: str = ""
    functions: list[str] = Field(default_factory=list)
    variables: list[str] = Field(default_factory=list)
    max_loop_nesting: int = 0
    loop_count: int = 0
    recursion: bool = False
    estimated_complexity: str = ""
    warnings: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    response: str
    mode: Mode
    code_unlocked: bool
    retrieved: list[RetrievedDoc] = Field(default_factory=list)
    code_analysis: CodeAnalysis | None = None
