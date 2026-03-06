from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from .citation import Citation

QueryMode = Literal[
    "question_answer",
    "mcq",
    "case_study",
    "long_academic",
    "symptoms_to_disorder",
    "disorder_to_symptoms",
    "treatment_approach",
]


class QueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)
    mode: QueryMode = "question_answer"
    kb_ids: list[UUID] | None = None  # None = search all accessible KBs
    include_citations: bool = True
    stream: bool = False


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    query_mode: QueryMode
    kb_ids_searched: list[str] = []
    retrieval_count: int = 0
    was_blocked: bool = False
    query_id: str | None = None


class MCQRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=500)
    count: int = Field(default=5, ge=1, le=20)
    kb_ids: list[UUID] | None = None
    difficulty: Literal["beginner", "intermediate", "advanced"] = "intermediate"


class MCQOption(BaseModel):
    label: str
    text: str
    is_correct: bool


class MCQItem(BaseModel):
    question: str
    options: list[MCQOption]
    explanation: str
    citations: list[Citation] = []


class MCQResponse(BaseModel):
    topic: str
    items: list[MCQItem]
    kb_ids_searched: list[str] = []


class CaseRequest(BaseModel):
    disorder: str | None = None
    symptoms: list[str] | None = None
    scenario_context: str | None = None
    kb_ids: list[UUID] | None = None


class CaseResponse(BaseModel):
    case_description: str
    presenting_symptoms: list[str]
    differential_diagnosis: str
    treatment_considerations: str
    citations: list[Citation] = []
