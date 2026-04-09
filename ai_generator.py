import json
import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = (
    "You are a network data expert. Analyze the schema and sample rows from this "
    "BGP network dataset. Generate {n} new realistic rows that follow the same "
    "patterns, value ranges, and distributions. Return ONLY a JSON array of objects "
    "where each key matches the column headers exactly. Do not include any explanation "
    "or markdown."
)


def _build_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env file."
        )
    return anthropic.Anthropic(api_key=api_key)


def generate_rows(schema_prompt: str, num_rows: int, retry: bool = True) -> list[dict]:
    """Call Claude to generate synthetic rows. Retries once on malformed JSON."""
    client = _build_client()
    system = SYSTEM_PROMPT.format(n=num_rows)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": schema_prompt}],
        )
    except anthropic.APIError as exc:
        raise RuntimeError(f"Claude API error: {exc}") from exc

    raw_text = message.content[0].text.strip()

    # Strip markdown fences if Claude wraps the response
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
            "Claude returned malformed JSON after two attempts. "
            "Please try again."
        )

    if not isinstance(rows, list):
        raise RuntimeError("Expected a JSON array from Claude, got something else.")

    return rows
