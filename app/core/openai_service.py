"""OpenAI integration service for transcription, analysis, and generation."""

import logging
from typing import Any

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger("empireo.openai")

_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def transcribe_audio(file_path: str, language: str = "en") -> dict:
    """Transcribe an audio file using Whisper. Returns {text, language, duration, segments}."""
    client = get_openai_client()
    with open(file_path, "rb") as audio_file:
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language,
            response_format="verbose_json",
        )
    return {
        "text": response.text,
        "language": response.language,
        "duration": response.duration,
        "segments": [s.model_dump() for s in (response.segments or [])],
    }


async def analyze_call(transcription: str) -> dict:
    """Analyze a call transcription for sentiment, quality, and key information."""
    client = get_openai_client()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert call quality analyst for a study abroad consultancy. "
                    "Analyze the call transcription and return a JSON object with these fields:\n"
                    "- sentiment_score: float -1.0 to 1.0\n"
                    "- quality_score: float 0.0 to 10.0\n"
                    "- professionalism_score: float 0.0 to 10.0\n"
                    "- resolution_score: float 0.0 to 10.0\n"
                    "- summary: brief summary of the call\n"
                    "- topics: list of discussed topics\n"
                    "- action_items: list of follow-up actions needed\n"
                    "- flags: list of any concerns or red flags\n"
                    "- key_phrases: list of important phrases\n"
                    "- caller_intent: what the caller wanted\n"
                    "- outcome: resolved/unresolved/follow_up_needed\n"
                    "Return ONLY valid JSON."
                ),
            },
            {"role": "user", "content": transcription},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    import json

    content = response.choices[0].message.content
    tokens_used = response.usage.total_tokens if response.usage else 0
    result = json.loads(content)
    result["ai_tokens_used"] = tokens_used
    result["ai_model_used"] = "gpt-4o-mini"
    return result


async def generate_performance_summary(metrics: dict, call_analyses: list[dict]) -> dict:
    """Generate an AI performance review summary from metrics and call data."""
    client = get_openai_client()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an HR performance analyst for a study abroad consultancy. "
                    "Given employee metrics and call analysis summaries, generate a JSON review:\n"
                    "- ai_summary: 2-3 paragraph performance summary\n"
                    "- ai_strengths: list of strengths\n"
                    "- ai_improvements: list of areas for improvement\n"
                    "- ai_recommendations: list of actionable recommendations\n"
                    "- overall_score: float 0.0 to 10.0\n"
                    "Return ONLY valid JSON."
                ),
            },
            {
                "role": "user",
                "content": f"Metrics: {metrics}\n\nCall Analyses: {call_analyses}",
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    import json

    content = response.choices[0].message.content
    tokens_used = response.usage.total_tokens if response.usage else 0
    result = json.loads(content)
    result["ai_tokens_used"] = tokens_used
    result["ai_model_used"] = "gpt-4o-mini"
    return result


async def extract_document_data(text: str, document_type: str = "general") -> dict:
    """Extract structured data from document text using GPT."""
    client = get_openai_client()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    f"Extract structured data from this {document_type} document. "
                    "Return a JSON object with the extracted fields and their values. "
                    "Include a 'confidence' field (0.0-1.0) for each extracted value."
                ),
            },
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    import json

    content = response.choices[0].message.content
    tokens_used = response.usage.total_tokens if response.usage else 0
    result = json.loads(content)
    result["ai_tokens_used"] = tokens_used
    result["ai_model_used"] = "gpt-4o-mini"
    return result


async def chat_completion(
    messages: list[dict[str, str]],
    model: str = "gpt-4o-mini",
    temperature: float = 0.5,
    json_mode: bool = False,
) -> dict[str, Any]:
    """Generic chat completion wrapper. Returns {content, tokens_used, model}."""
    client = get_openai_client()
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(**kwargs)
    return {
        "content": response.choices[0].message.content,
        "tokens_used": response.usage.total_tokens if response.usage else 0,
        "model": model,
    }


async def generate_embedding(text: str, model: str = "text-embedding-3-small") -> list[float]:
    """Generate a vector embedding for the given text. Returns a list of floats (1536 dim)."""
    client = get_openai_client()
    text = text.replace("\n", " ").strip()
    if not text:
        return []
    response = await client.embeddings.create(model=model, input=[text])
    return response.data[0].embedding


async def semantic_search_candidates(query: str, model: str = "text-embedding-3-small") -> list[float]:
    """Generate query embedding for semantic search. Alias for generate_embedding."""
    return await generate_embedding(query, model)
