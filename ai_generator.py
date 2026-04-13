import json
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-4-26b-a4b-it:free",
    "qwen/qwen3-coder:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-3-27b-it:free",
]

SYSTEM_PROMPT = (
    "You are a network data expert. Generate {n} new realistic rows for this "
    "BGP network dataset. Follow the same patterns, value ranges, and distributions. "
    "Do NOT duplicate existing entries. "
    "IMPORTANT: Output ONLY a valid JSON array. No thinking, no explanation, no markdown. "
    "Start your response with [ and end with ]."
)


def _get_api_key() -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Add it to your .env file."
        )
    return api_key


def _call_api(api_key: str, model: str, system: str, user_content: str) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "max_tokens": 4096,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
    }

    response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    data = response.json()

    if not response.ok or "error" in data:
        err = data.get("error", {})
        msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
        raise RuntimeError(f"[{model}] {msg}")

    return data


def generate_rows(schema_prompt: str, num_rows: int, retry: bool = True):
    """Try multiple free models until one works. Returns (rows, model_name)."""
    api_key = _get_api_key()
    system = SYSTEM_PROMPT.format(n=num_rows)

    last_error = None
    for i, model in enumerate(MODELS):
        try:
            print(f"[NetGen AI] Trying model: {model}")
            data = _call_api(api_key, model, system, schema_prompt)
            used_model = data.get("model", model)
            print(f"[NetGen AI] Success with: {used_model}")
            break
        except RuntimeError as exc:
            last_error = exc
            print(f"[NetGen AI] {model} failed: {exc}")
            if i < len(MODELS) - 1:
                time.sleep(0.5)
            continue
    else:
        raise RuntimeError(
            "All AI models are temporarily unavailable. Please try again in a minute."
        )

    raw_text = data["choices"][0]["message"]["content"].strip()
    print(f"[NetGen AI] Raw response (first 500 chars): {raw_text[:500]}")
    rows = _extract_json_array(raw_text)

    if rows is None:
        print(f"[NetGen AI] Failed to parse JSON from response")
        if retry:
            return generate_rows(schema_prompt, num_rows, retry=False)
        raise RuntimeError(
            "AI returned malformed JSON after two attempts. "
            "Please try again."
        )

    return rows, used_model


def _extract_json_array(text: str):
    """Extract a JSON array from AI response, handling extra text and formatting."""
    import re

    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    # Remove markdown code fences
    text = re.sub(r"```(?:json)?\s*", "", text).strip()

    # Try parsing the whole text first
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Try to find a JSON array within the text using bracket matching
    start = text.find("[")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "[":
                depth += 1
            elif text[i] == "]":
                depth -= 1
                if depth == 0:
                    try:
                        result = json.loads(text[start:i + 1])
                        if isinstance(result, list):
                            return result
                    except json.JSONDecodeError:
                        break

    return None
