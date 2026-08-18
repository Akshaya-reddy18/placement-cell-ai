import hashlib
import json
import os
import re
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI


def get_gemini_llm(model_name: str = None, temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    model = model_name or os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=temperature,
    )


def extract_json_text(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 1)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()

    first_object = cleaned.find("{")
    first_array = cleaned.find("[")
    if first_object == -1 and first_array == -1:
        return cleaned

    starts = [index for index in [first_object, first_array] if index != -1]
    start = min(starts)
    end = max(cleaned.rfind("}"), cleaned.rfind("]"))
    if end > start:
        return cleaned[start : end + 1]
    return cleaned[start:]


def safe_json_loads(text: str, default: Any) -> Any:
    try:
        return json.loads(extract_json_text(text))
    except Exception:
        return default


def call_gemini_json(prompt: str, default: Any, temperature: float = 0.0) -> Any:
    configured_model = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    models_to_try = [configured_model, "gemini-flash-latest", "gemini-2.5-flash-lite", "gemini-2.5-flash"]
    seen = set()
    unique_models = [m for m in models_to_try if not (m in seen or seen.add(m))]

    for model_name in unique_models:
        try:
            llm = get_gemini_llm(model_name=model_name, temperature=temperature)
            response = llm.invoke(prompt)
            result = safe_json_loads(response.content, None)
            if result is not None:
                return result
        except Exception:
            continue
    return default


def call_gemini_text(prompt: str, default: str = "", temperature: float = 0.0) -> str:
    configured_model = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    models_to_try = [configured_model, "gemini-flash-latest", "gemini-2.5-flash-lite", "gemini-2.5-flash"]
    seen = set()
    unique_models = [m for m in models_to_try if not (m in seen or seen.add(m))]

    for model_name in unique_models:
        try:
            llm = get_gemini_llm(model_name=model_name, temperature=temperature)
            response = llm.invoke(prompt)
            if response and response.content and response.content.strip():
                return response.content.strip()
        except Exception:
            continue
    return default


def simple_tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_+#.]+", text.lower())


def stable_embedding(text: str, dimensions: int = 64) -> list[float]:
    vector = [0.0] * dimensions
    for token in simple_tokens(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        vector[index] += 1.0

    norm = sum(value * value for value in vector) ** 0.5
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def safe_cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0

    length = min(len(left), len(right))
    left = left[:length]
    right = right[:length]

    dot = sum(a * b for a, b in zip(left, right))
    left_norm = sum(a * a for a in left) ** 0.5
    right_norm = sum(b * b for b in right) ** 0.5
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
