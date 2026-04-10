import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = [
    "google/gemini-2.5-flash-lite",
]

SYSTEM_PROMPT = (
    "You are a network data expert. Analyze the schema and sample rows from this "
    "BGP network dataset. Generate {n} new realistic rows that follow the same "
    "patterns, value ranges, and distributions. The generated rows must be coherent, "
    "valid within the schema, and must NOT duplicate any existing entries. "
    "Return ONLY a JSON array of objects where each key matches the column headers "
    "exactly. Do not include any explanation or markdown."
)


def _get_api_key() -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Add it to your .env file."
        )
    return api_key


def _call_openrouter(api_key: str, model: str, system: str, user_content: str) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "max_tokens": 2048,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
    data = response.json()

    if not response.ok or "error" in data:
        err = data.get("error", {})
        msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
        raise RuntimeError(f"[{model}] {msg}")

    return data


def generate_rows(schema_prompt: str, num_rows: int, retry: bool = True) -> tuple[list[dict], str]:
    """Try multiple free models until one works. Returns (rows, model_name)."""
    api_key = _get_api_key()
    system = SYSTEM_PROMPT.format(n=num_rows)

    used_model = None
    last_error = None
    for model in MODELS:
        try:
            print(f"[NetGen AI] Trying model: {model}")
            data = _call_openrouter(api_key, model, system, schema_prompt)
            used_model = data.get("model", model)
            break
        except RuntimeError as exc:
            last_error = exc
            print(f"[NetGen AI] {model} failed: {exc}")
            continue
    else:
        raise RuntimeError(
            f"All AI models failed. Last error: {last_error}"
        )

    raw_text = data["choices"][0]["message"]["content"].strip()

    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw_text = "\n".join(lines).strip()

    try:
        rows = json.loads(raw_text)
    except json.JSONDecodeError:
        if retry:
            return generate_rows(schema_prompt, num_rows, retry=False)
        raise RuntimeError(
            "AI returned malformed JSON after two attempts. "
            "Please try again."
        )

    if not isinstance(rows, list):
        raise RuntimeError("Expected a JSON array from the AI, got something else.")

    return rows, used_model
