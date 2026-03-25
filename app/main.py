from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.model import classifier, MODEL_NAME, MODEL_VERSION, LABELS, MAX_INPUT_LENGTH
from app.schemas import (
    PredictRequest,
    BatchPredictRequest,
    PredictResponse,
    BatchPredictResponse,
    HealthResponse,
    ModelInfoResponse,
)


# ── Lifespan: 앱 시작 시 모델 로드 ──────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    classifier.load()
    yield
    print("[Model] Shutting down.")


# ── FastAPI 앱 초기화 ────────────────────────────────────────────────────────
app = FastAPI(
    title="Emotion Classification API",
    description="FastAPI ML Serving 실습 — 텍스트 감정 분류 REST API",
    version=MODEL_VERSION,
    lifespan=lifespan,
)


# ── 엔드포인트 ───────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """서버 및 모델 상태 확인"""
    return HealthResponse(
        status="ok",
        model_loaded=classifier.is_loaded,
        version=MODEL_VERSION,
    )


@app.get("/model/info", response_model=ModelInfoResponse, tags=["Model"])
def model_info():
    """모델 메타데이터 조회"""
    return ModelInfoResponse(
        model_name=MODEL_NAME,
        version=MODEL_VERSION,
        labels=LABELS,
        max_input_length=MAX_INPUT_LENGTH,
        description="Mock emotion classifier for FastAPI serving practice.",
    )


@app.post("/predict", response_model=PredictResponse, tags=["Inference"])
def predict(request: PredictRequest):
    """단일 텍스트 감정 분류"""
    if not classifier.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded yet.")
    result = classifier.predict(request.text)
    return PredictResponse(**result)


@app.post("/predict/batch", response_model=BatchPredictResponse, tags=["Inference"])
def predict_batch(request: BatchPredictRequest):
    """다수 텍스트 일괄 감정 분류 (최대 16개)"""
    if not classifier.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded yet.")
    results = classifier.predict_batch(request.texts)
    return BatchPredictResponse(
        results=[PredictResponse(**r) for r in results],
        total=len(results),
    )


@app.delete("/model/reset", tags=["Model"])
def reset_model():
    """모델 재로딩 (실습용 — 운영에서는 보호 필요)"""
    classifier.load()
    return {"message": "Model reloaded successfully."}
