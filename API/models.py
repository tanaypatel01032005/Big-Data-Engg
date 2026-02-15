from pydantic import BaseModel
from typing import List, Optional

class SemanticMatch(BaseModel):
    acc_no: int
    field: str
    text: str
    similarity: float

class SemanticResponse(BaseModel):
    results: List[SemanticMatch]
    final_threshold: float
    threshold_reduced: bool

class ModelInfo(BaseModel):
    model_name: str
    vector_dimension: int
    default_threshold: float
