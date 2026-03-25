# ── Stage 1: Builder ────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# 의존성만 먼저 복사 → 레이어 캐싱 활용
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# builder 에서 설치된 패키지만 복사
COPY --from=builder /install /usr/local

# 소스 복사
COPY app/ ./app/

# 보안: root 가 아닌 전용 유저로 실행
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

# 운영: workers 수는 환경에 맞게 조정 (일반적으로 CPU코어 * 2 + 1)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
