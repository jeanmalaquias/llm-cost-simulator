"""Optional token estimator — an APPROXIMATION for sizing only.

Exact token counts are provider-specific (tiktoken, the Anthropic count_tokens
endpoint, the Vertex tokenizer). This helper estimates tokens from text by a
calibrated chars-per-token ratio so you can ballpark a workload; it does NOT
claim parity. For billing-grade counts, call the provider's real tokenizer and
feed those numbers into the cost engine. Expected error band: roughly ±20% on
typical English prose, worse on code or non-English text.
"""

from __future__ import annotations

# ~4 chars/token is a common rule of thumb for English prose across BPE
# tokenizers. Override per content type for a closer estimate.
DEFAULT_CHARS_PER_TOKEN = 4.0


def estimate_tokens(text: str, chars_per_token: float = DEFAULT_CHARS_PER_TOKEN) -> int:
    """Roughly estimate the token count of ``text``. Approximation — see module docs."""
    if chars_per_token <= 0:
        raise ValueError("chars_per_token must be positive")
    if not text:
        return 0
    return max(1, round(len(text) / chars_per_token))
