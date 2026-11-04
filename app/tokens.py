"""Token estimation when the provider does not report usage (about 4 characters per token)."""


def estimate_tokens(text: str) -> int:
    return max(1, round(len(text) / 4))
