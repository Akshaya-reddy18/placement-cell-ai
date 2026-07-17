import hashlib
import json
import os
import re
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI


def get_gemini_llm(temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
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
    try:
        llm = get_gemini_llm(temperature=temperature)
        response = llm.invoke(prompt)
        return safe_json_loads(response.content, default)
    except Exception:
        return default


def call_gemini_text(prompt: str, default: str = "", temperature: float = 0.0) -> str:
    try:
        llm = get_gemini_llm(temperature=temperature)
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception:
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
