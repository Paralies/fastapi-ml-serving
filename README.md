# fastapi-ml-serving

FastAPI 기반 ML 모델 서빙 실습 애플리케이션.
텍스트 감정 분류 API를 제공하며, GitHub Actions CI/CD를 통해 Harbor 레지스트리로 이미지를 빌드·푸시하고 EKS에 자동 배포합니다.

---

## 📁 프로젝트 구조

```
fastapi-ml-serving/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI 앱 진입점, 엔드포인트 정의
│   ├── schemas.py        # Pydantic 요청/응답 모델
│   └── model.py          # 감정 분류 모델 로직 (Mock)
├── manifests/
│   ├── deployment.yaml       # K8s Deployment (앱 + Fluentd 사이드카)
│   ├── service.yaml          # K8s Service (ClusterIP)
│   └── configmap-fluentd.yaml  # Fluentd 설정
├── .github/
│   └── workflows/
│       └── ci-cd.yml     # GitHub Actions CI/CD 파이프라인
├── Dockerfile            # Multi-stage 빌드
├── requirements.txt
└── README.md
```

---

## 🚀 API 엔드포인트

| Method | Path | 설명 |
|---|---|---|
| `GET` | `/health` | 서버 및 모델 상태 확인 |
| `GET` | `/model/info` | 모델 메타데이터 조회 |
| `POST` | `/predict` | 단일 텍스트 감정 분류 |
| `POST` | `/predict/batch` | 최대 16개 텍스트 일괄 분류 |
| `DELETE` | `/model/reset` | 모델 재로딩 |

지원 감정 레이블: `joy` · `sadness` · `anger` · `fear` · `surprise` · `neutral`

---

## 🛠️ 로컬 실행

### 일반 실행

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Swagger UI: http://localhost:8000/docs

### Docker 실행

```bash
docker build -t fastapi-ml-serving .
docker run -p 8000:8000 fastapi-ml-serving
```

---

## 🔄 CI/CD 파이프라인

### 흐름

```
Push to main
    │
    ├─ [ci]  이미지 빌드 → Harbor Push (short SHA 태그 + latest)
    │         └─ PR이면 여기서 종료
    │
    └─ [cd]  EKS 배포 (push / workflow_dispatch 이벤트만)
              ├─ ConfigMap apply  (Fluentd 설정)
              ├─ Deployment apply (이미지 태그 sed 치환 후 apply)
              ├─ Service apply
              └─ rollout status 대기 (최대 300초)
```

### 트리거

| 이벤트 | ci job | cd job |
|---|---|---|
| `push` to main | ✅ | ✅ |
| `pull_request` to main | ✅ | ❌ |
| `workflow_dispatch` | ✅ | ✅ |

### GitHub Settings 등록 항목

**Variables** (`Settings > Secrets and variables > Actions > Variables`)

| 키 | 예시 값 |
|---|---|
| `HARBOR_REGISTRY` | `harbor.example.com` |
| `HARBOR_PROJECT` | `skala` |
| `IMAGE_NAME` | `fastapi-ml-serving` |
| `AWS_REGION` | `ap-northeast-2` |
| `EKS_CLUSTER_NAME` | `my-eks-cluster` |
| `K8S_NAMESPACE` | `skala3-ai1` |

**Secrets** (`Settings > Secrets and variables > Actions > Secrets`)

| 키 | 설명 |
|---|---|
| `HARBOR_USERNAME` | Harbor Robot Account 이름 (`robot$이름`) |
| `HARBOR_PASSWORD` | Harbor Robot Account 토큰 |
| `AWS_ACCESS_KEY_ID` | EKS 접근용 IAM Access Key |
| `AWS_SECRET_ACCESS_KEY` | EKS 접근용 IAM Secret Key |

---

## ☸️ Kubernetes 구성

### Deployment

- **Namespace:** `skala3-ai1`
- **Replicas:** 2
- **이미지 태그:** CI에서 `FULL_IMAGE_PLACEHOLDER`를 short SHA로 `sed` 치환
- **Harbor 프로젝트:** Public 설정 → `imagePullSecrets` 불필요

#### Pod 내부 구조

```
Pod
├── [컨테이너] fastapi-ml-serving   ← 앱 서버 :8000
│       └── /var/log/app/ 로그 write (emptyDir 공유)
└── [사이드카] fluentd              ← /var/log/app/*.log tail → stdout
```

#### 헬스체크

`/health` 엔드포인트를 liveness / readiness probe로 활용합니다.

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 15
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

### Service

- **Type:** `ClusterIP`
- **Port:** `80` → `8000` (targetPort)

### Fluentd 사이드카

앱 컨테이너와 `emptyDir` 볼륨을 공유하여 로그를 수집합니다.
`configmap-fluentd.yaml`에 정의된 설정을 `/fluentd/etc/fluent.conf`로 마운트합니다.

현재는 `stdout` 출력이며, 운영 환경에서는 아래처럼 교체 가능합니다.

```
stdout → Elasticsearch / S3 / CloudWatch 등
```

---

## 🐳 Dockerfile

Multi-stage 빌드로 이미지 크기를 최소화합니다.

```
Stage 1 (builder): pip install → /install
Stage 2 (runtime): /install 복사 + 소스 복사 + appuser로 실행
```

---

## 💡 실제 모델로 교체하기

현재 `app/model.py`는 Mock 추론 로직입니다.
HuggingFace 모델로 교체하려면 `load()`와 `_mock_inference()` 두 메서드만 수정하면 됩니다.

```python
# load()
self.tokenizer = AutoTokenizer.from_pretrained("model-name")
self.model = AutoModelForSequenceClassification.from_pretrained("model-name")

# _mock_inference() → 실제 추론으로 교체
inputs = self.tokenizer(text, return_tensors="pt", truncation=True)
outputs = self.model(**inputs)
scores = torch.softmax(outputs.logits, dim=-1)
```

`requirements.txt`에 `transformers`, `torch` 추가 후 Dockerfile 재빌드하면 됩니다.
