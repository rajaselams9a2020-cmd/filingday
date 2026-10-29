
from app.config import Settings
from app.llm.fake import FakeProvider
from app.llm.openai_compat import OpenAICompatProvider


def build_provider(settings: Settings):
    if settings.llm_provider == "fake":
        primary = FakeProvider(model=settings.llm_model)

    elif settings.llm_provider == "openai_compat":
        primary = OpenAICompatProvider(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
            backoff_base_seconds=settings.llm_backoff_base_seconds,
        )

    else:
        raise ValueError(
            f"Unsupported LLM provider: {settings.llm_provider}"
        )

    if not settings.llm_fallback_model:
        return primary

    fallback = OpenAICompatProvider(
        base_url=settings.llm_fallback_base_url or settings.llm_base_url,
        api_key=settings.llm_fallback_api_key or settings.llm_api_key,
        model=settings.llm_fallback_model,
        timeout_seconds=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
        backoff_base_seconds=settings.llm_backoff_base_seconds,
    )

    from app.llm.fallback import FallbackProvider

    return FallbackProvider(primary, fallback)
