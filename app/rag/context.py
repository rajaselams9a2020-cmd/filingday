"""Format retrieved GST pages as context for an LLM."""


def build_context(pages: list[dict]) -> str:
    """Combine retrieved pages with source and page references."""
    if not pages:
        return "No relevant information found in the GST documents."

    sections = []

    for page in pages:
        sections.append(f"[Source: {page['source']}, Page: {page['page']}]\n{page['text']}")

    return "\n\n".join(sections)


def build_rag_messages(messages: list, context: str) -> list:
    """Add retrieved GST context to the conversation's system message."""
    rag_instruction = (
        "Answer the user's question using the GST document context below. "
        "If the context does not contain the answer, say that the document "
        "does not provide enough information. Cite the source and page number.\n\n"
        f"GST DOCUMENT CONTEXT:\n{context}"
    )

    updated_messages = [message.model_copy() for message in messages]

    for message in updated_messages:
        if message.role == "system":
            message.content += "\n\n" + rag_instruction
            return updated_messages

    from app.schemas import Message

    return [
        Message(role="system", content=rag_instruction),
        *updated_messages,
    ]
