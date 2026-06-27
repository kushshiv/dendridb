from uuid import UUID

from pydantic import BaseModel, Field

from dendridb.api.schemas.memory_record import MemoryRecordResponse
from dendridb.ranking.hybrid import RankingWeights


class RecallWeights(BaseModel):
    similarity: float = Field(default=0.5, ge=0.0)
    recency: float = Field(default=0.2, ge=0.0)
    salience: float = Field(default=0.2, ge=0.0)
    association: float = Field(default=0.1, ge=0.0)

    def to_ranking_weights(self) -> RankingWeights:
        return RankingWeights(
            similarity=self.similarity,
            recency=self.recency,
            salience=self.salience,
            association=self.association,
        )


class RecallRequest(BaseModel):
    namespace: str = Field(..., min_length=1, max_length=255)
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    candidate_limit: int = Field(default=100, ge=1, le=500)
    context_memory_id: UUID | None = None
    weights: RecallWeights = Field(default_factory=RecallWeights)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)


class RecallExplanation(BaseModel):
    summary: str
    factors: dict[str, float]
    contributions: dict[str, float]
    weights: RecallWeights


class RecallMemoryResult(MemoryRecordResponse):
    score: float = 0.0
    explanation: RecallExplanation | None = None


def build_recall_memory_result(
    record,
    *,
    score: float,
    explanation: RecallExplanation,
) -> RecallMemoryResult:
    base = MemoryRecordResponse.model_validate(record)
    return RecallMemoryResult.model_construct(
        **base.model_dump(),
        score=score,
        explanation=explanation,
    )


class RecallResponse(BaseModel):
    query: str
    namespace: str
    items: list[RecallMemoryResult]
    total_candidates: int


class ReindexRequest(BaseModel):
    namespace: str = Field(..., min_length=1, max_length=255)
    limit: int = Field(default=500, ge=1, le=5000)


class ReindexResponse(BaseModel):
    namespace: str
    updated: int
