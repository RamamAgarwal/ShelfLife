"""Stage 4: have the strong model record what each source says about a claim.

The model only reports stances. Scoring happens in score.py. Each stance has to be
backed by a quote that really appears in the source, or it doesn't count.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from typing import Literal

from pydantic import BaseModel

from app import config
from app.models import CheckContext, Claim, LLMCallInfo, Stance
from app.pipeline.metrics import MetricsCollector, call_info
from app.prompts import load_prompt, neutralise_tag
from app.search import SearchResult

_ELLIPSIS = re.compile(r"\.{3,}|…")


class EvidenceJudgement(BaseModel):
    id: str
    stance: Stance
    quote: str | None = None


class AdjudicationOutput(BaseModel):
    judgements: list[EvidenceJudgement]
    current_value: str | None = None
    claimed_value: str | None = None
    change_type: Literal[
        "value_changed", "superseded", "deprecated", "discontinued", "renamed", "no_change",
        "unclear",
    ] | None = None
    context_note: str | None = None
    explanation: str = ""


@dataclass(frozen=True)
class Judgement:
    stance: Stance
    quote: str | None


@dataclass
class Adjudication:
    judgements: dict[str, Judgement]
    current_value: str | None
    explanation: str
    call: LLMCallInfo | None = None
    claimed_value: str | None = None
    change_type: str | None = None
    context_note: str | None = None


def evidence_id(index: int) -> str:
    return f"E{index + 1}"


async def adjudicate_claim(
    claim: Claim,
    sources: list[SearchResult],
    check_date: date,
    answer_date: date | None,
    metrics: MetricsCollector,
    context: CheckContext | None = None,
) -> Adjudication:
    settings = config.get_settings()
    result = await metrics.chat(
        "adjudicate",
        build_messages(claim, sources, check_date, answer_date, context),
        settings.model_strong,
        settings.fallbacks_strong_list,
        json_schema=AdjudicationOutput,
    )
    adjudication = validate_output(result.parsed, sources, claim.text)
    adjudication.call = call_info(result)
    return adjudication


def evidence_hash(claim: Claim, sources: list[SearchResult]) -> str:
    """Fingerprint the evidence so that new evidence can never hit an old cache entry."""
    payload = [
        claim.text,
        [[item.url, str(item.published_date), item.snippet] for item in sources],
    ]
    return hashlib.sha256(json.dumps(payload).encode()).hexdigest()[:16]


def build_messages(
    claim: Claim,
    sources: list[SearchResult],
    check_date: date,
    answer_date: date | None,
    context: CheckContext | None = None,
) -> list[dict]:
    parts = [
        f"Today's date: {check_date.isoformat()}",
        f"Evidence set: {evidence_hash(claim, sources)}",
    ]
    if answer_date:
        parts.append(f"The claim was written on {answer_date.isoformat()}.")
    if context and not context.is_empty():
        lines = neutralise_tag("\n".join(context.lines()), "context")
        parts.append(
            f"<context>\n{lines}\n</context>\n"
            "The answer was written for this context. If the claim may be true in general "
            "but not for this context, say so in `context_note`."
        )
    parts.append(f"<claim>\n{neutralise_tag(claim.text, 'claim')}\n</claim>")
    for index, source in enumerate(sources):
        parts.append(_evidence_block(evidence_id(index), source))
    return [
        {"role": "system", "content": load_prompt("adjudicate")},
        {"role": "user", "content": "\n\n".join(parts)},
    ]


def _evidence_block(identifier: str, source: SearchResult) -> str:
    published = source.published_date.isoformat() if source.published_date else "unknown"
    fields = [
        f"title: {source.title}",
        f"domain: {source.domain}",
        f"published: {published}",
        f"snippet: {source.snippet[: config.MAX_SNIPPET_CHARS]}",
    ]
    body = neutralise_tag("\n".join(fields), "evidence")
    return f'<evidence id="{identifier}">\n{body}\n</evidence>'


def validate_output(
    output: AdjudicationOutput, sources: list[SearchResult], claim_text: str | None = None
) -> Adjudication:
    """Keep only judgements that match a supplied source and quote it accurately."""
    snippets = {evidence_id(index): source.snippet for index, source in enumerate(sources)}
    judgements: dict[str, Judgement] = {}
    for item in output.judgements:
        if item.id not in snippets or item.id in judgements:
            continue
        quote = verified_quote(item.quote, snippets[item.id])
        if item.stance == "irrelevant" or quote is None:
            judgements[item.id] = Judgement("irrelevant", None)
        else:
            judgements[item.id] = Judgement(item.stance, quote)

    for identifier in snippets:
        judgements.setdefault(identifier, Judgement("irrelevant", None))

    has_backing = any(item.stance != "irrelevant" for item in judgements.values())
    current_value = (output.current_value or "").strip() or None
    # The old value has to come from the claim itself, not from the model's memory.
    claimed = (output.claimed_value or "").strip() or None
    if claimed and not (claim_text and _comparable(claimed) in _comparable(claim_text)):
        claimed = None
    return Adjudication(
        judgements=judgements,
        current_value=current_value if has_backing else None,
        explanation=output.explanation.strip(),
        claimed_value=claimed,
        change_type=output.change_type if has_backing else None,
        context_note=(output.context_note or "").strip()[:200] or None,
    )


def verified_quote(quote: str | None, snippet: str) -> str | None:
    """Return the quote, limited in length, if its words really appear in the snippet.

    Case, punctuation and spacing are ignored, and "..." may join separate passages.
    """
    if not quote or not quote.strip():
        return None
    trimmed = " ".join(quote.split()[: config.MAX_QUOTE_WORDS])
    passages = [_comparable(part) for part in _ELLIPSIS.split(trimmed)]
    passages = [passage for passage in passages if passage]
    if not passages:
        return None
    haystack = f" {_comparable(snippet)} "
    return trimmed if all(f" {passage} " in haystack for passage in passages) else None


def _comparable(text: str) -> str:
    normalised = unicodedata.normalize("NFKC", text).casefold()
    # Keep decimals and prices such as "$1,000.50" intact as a single token.
    normalised = re.sub(r"(?<=\d)[.,](?=\d)", "", normalised)
    return " ".join(re.sub(r"[^\w\s$€£¥%]", " ", normalised).split())
