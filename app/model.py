"""
Mock emotion classification model.
실제 환경에서는 transformers 등 실제 모델로 교체하면 됩니다.
예: AutoModelForSequenceClassification + AutoTokenizer (HuggingFace)
"""

import random
from typing import List, Dict

# 지원하는 감정 레이블
LABELS = ["joy", "sadness", "anger", "fear", "surprise", "neutral"]

MODEL_NAME = "mock-emotion-classifier"
MODEL_VERSION = "1.0.0"
MAX_INPUT_LENGTH = 512


class EmotionClassifier:
    def __init__(self):
        self._loaded = False

    def load(self):
        """
        모델 로딩 시뮬레이션.
        실제라면: self.tokenizer = AutoTokenizer.from_pretrained(...)
                  self.model = AutoModelForSequenceClassification.from_pretrained(...)
        """
        print(f"[Model] Loading {MODEL_NAME} v{MODEL_VERSION} ...")
        self._loaded = True
        print("[Model] Model loaded successfully.")

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def predict(self, text: str) -> Dict:
        """단일 텍스트 감정 분류"""
        if not self._loaded:
            raise RuntimeError("Model is not loaded.")

        scores = self._mock_inference(text)
        predicted_label = max(scores, key=scores.get)

        return {
            "text": text,
            "predicted_label": predicted_label,
            "confidence": round(scores[predicted_label], 4),
            "all_scores": [
                {"label": label, "score": round(score, 4)}
                for label, score in sorted(scores.items(), key=lambda x: -x[1])
            ],
        }

    def predict_batch(self, texts: List[str]) -> List[Dict]:
        """배치 텍스트 감정 분류"""
        return [self.predict(text) for text in texts]

    def _mock_inference(self, text: str) -> Dict[str, float]:
        """
        Mock 추론 로직.
        텍스트 키워드 기반으로 간단히 점수를 조정합니다.
        """
        seed = sum(ord(c) for c in text)
        rng = random.Random(seed)

        raw = {label: rng.random() for label in LABELS}

        # 간단한 키워드 힌트
        text_lower = text.lower()
        hints = {
            "joy":      ["happy", "great", "love", "excited", "wonderful", "기쁘", "행복"],
            "sadness":  ["sad", "cry", "miss", "lonely", "슬프", "그리워"],
            "anger":    ["angry", "hate", "furious", "annoying", "화나", "짜증"],
            "fear":     ["scared", "afraid", "worried", "terrified", "무서", "걱정"],
            "surprise": ["wow", "amazing", "unexpected", "놀라", "신기"],
        }
        for label, keywords in hints.items():
            if any(kw in text_lower for kw in keywords):
                raw[label] *= 3.0

        # Softmax 정규화
        total = sum(raw.values())
        return {label: score / total for label, score in raw.items()}


# 앱 전역에서 공유할 싱글턴 인스턴스
classifier = EmotionClassifier()
