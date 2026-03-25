from pydantic import BaseModel, Field
from typing import List, Optional


# --- Request Models ---

class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=512, description="Input text for emotion classification")

    model_config = {
        "json_schema_extra": {
            "examples": [{"text": "I am so happy today!"}]
        }
    }


class BatchPredictRequest(BaseModel):
    texts: List[str] = Field(..., min_items=1, max_items=16, description="List of texts to classify")


# --- Response Models ---

class EmotionScore(BaseModel):
    label: str
    score: float = Field(..., ge=0.0, le=1.0)


class PredictResponse(BaseModel):
    text: str
    predicted_label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    all_scores: List[EmotionScore]


class BatchPredictResponse(BaseModel):
    results: List[PredictResponse]
    total: int


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str


class ModelInfoResponse(BaseModel):
    model_name: str
    version: str
    labels: List[str]
    max_input_length: int
    description: Optional[str] = None
