"""Stage 6: produce a corrected answer that changes only the stale claims.

The model only writes a short replacement for each stale passage. Code splices the
replacements into the original text by character offset, so everything else stays
word for word, and adds the citation markers and "(could not verify)" flags itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from pydantic import BaseModel

from app import config, llm
from app.models import AnswerEdit, Citation, ClaimResult, Evidence, Rewrite
from app.pipeline.metrics import MetricsCollector
from app.prompts import load_prompt, neutralise_tag

COULD_NOT_VERIFY = " (could not verify)"
OUT_OF_DATE = " (out of date)"
FLAGGED_VERDICTS = ("unverified", "error")
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
_CITATION_MARKER = re.compile(r"\[\d+\]")


class Replacement(BaseModel):
    claim_id: str
    replacement: str


class RewriteOutput(BaseModel):
    replacements: list[Replacement]


@dataclass
class _Change:
    result: ClaimResult
    kind: str  # "stale" or "flag"


def _valid_span(answer: str, result: ClaimResult) -> bool:
    span = result.claim.span
    return bool(span) and 0 <= span[0] < span[1] <= len(answer)


def _numbers(text: str) -> set[str]:
    return {match.replace(",", "") for match in _NUMBER.findall(text)}


def validate_replacement(before: str, replacement: str, current_value: str) -> bool:
    """Accept only a drop-in replacement that states the current value and nothing new."""
    text = replacement.strip()
    if not text or "\n" in text or text == before.strip():
        return False
    if _CITATION_MARKER.search(text):
        return False
    if len(text) > max(3 * len(before), len(before) + len(current_value) + 40):
        return False
    new_numbers = _numbers(text)
    value_numbers = _numbers(current_value)
    # No numbers may appear that neither the original nor the current value contains.
    if not new_numbers <= _numbers(before) | value_numbers:
        return False
    # If the current value has numbers, the replacement has to use at least one.
    return not value_numbers or bool(new_numbers & value_numbers)


def best_source(result: ClaimResult) -> Evidence | None:
    """The source to cite for a correction: the heaviest one that contradicts the claim."""
    contradicting = [item for item in result.evidence if item.stance == "contradicts"]
    return max(contradicting, key=lambda item: item.weight, default=None)


def _changes(answer: str, results: list[ClaimResult]) -> tuple[list[_Change], list[_Change]]:
    """Split the changes into ones placed in the text and ones that become end notes."""
    changes = []
    for result in results:
        if result.verdict == "stale":
            changes.append(_Change(result, "stale"))
        elif result.verdict in FLAGGED_VERDICTS and result.claim.category != "static":
            changes.append(_Change(result, "flag"))

    placed = sorted(
        (change for change in changes if _valid_span(answer, change.result)),
        key=lambda change: change.result.claim.span,
    )
    notes = [change for change in changes if not _valid_span(answer, change.result)]
    kept: list[_Change] = []
    last_end = -1
    for change in placed:
        start, end = change.result.claim.span
        if start < last_end:
            # Overlapping passages can't both be edited in place.
            notes.append(change)
        else:
            kept.append(change)
            last_end = end
    # Notes follow the answer's order; claims with no place in the text go last.
    notes.sort(
        key=lambda change: (0, change.result.claim.span[0])
        if _valid_span(answer, change.result)
        else (1, 0)
    )
    return kept, notes


def build_rewrite(
    answer: str, results: list[ClaimResult], replacements: dict[str, str]
) -> Rewrite:
    placed, notes = _changes(answer, results)
    citations: dict[str, Citation] = {}

    def cite(result: ClaimResult) -> int | None:
        source = best_source(result)
        if source is None:
            return None
        if source.url not in citations:
            citations[source.url] = Citation(
                number=len(citations) + 1,
                url=source.url,
                title=source.title,
                domain=source.domain,
                published_date=source.published_date,
            )
        return citations[source.url].number

    edits: list[AnswerEdit] = []
    for change in placed:
        result = change.result
        start, end = result.claim.span
        before = answer[start:end]
        citation = None
        if change.kind == "flag":
            kind, after = "flag", before + COULD_NOT_VERIFY
        elif result.current_value:
            citation = cite(result)
            replacement = replacements.get(result.claim.id)
            if replacement is None:
                replacement = f"{before} (now {result.current_value})"
            # Don't double the sentence's full stop when the passage ends just before it.
            if replacement.endswith(".") and answer[end : end + 1] == ".":
                replacement = replacement[:-1]
            kind, after = "replace", replacement
        else:
            citation = cite(result)
            kind, after = "flag", before + OUT_OF_DATE
        if citation is not None:
            after += f" [{citation}]"
        edits.append(AnswerEdit(
            claim_id=result.claim.id, kind=kind, start=start, end=end,
            before=before, after=after, citation=citation,
        ))

    for change in notes:
        result = change.result
        citation = None
        if change.kind == "flag":
            text = f"Could not verify: {result.claim.text}"
        elif result.current_value:
            citation = cite(result)
            text = f"Out of date: {result.claim.text} Sources now say: {result.current_value}."
        else:
            citation = cite(result)
            text = f"Out of date: {result.claim.text}"
        if citation is not None:
            text += f" [{citation}]"
        edits.append(AnswerEdit(
            claim_id=result.claim.id, kind="note", start=None, end=None,
            before="", after=text, citation=citation,
        ))

    pieces = []
    cursor = 0
    for edit in edits:
        if edit.kind == "note":
            continue
        pieces += [answer[cursor : edit.start], edit.after]
        cursor = edit.end
    pieces.append(answer[cursor:])
    corrected = "".join(pieces)
    note_lines = [edit.after for edit in edits if edit.kind == "note"]
    if note_lines:
        corrected = corrected.rstrip() + "\n\n" + "\n".join(note_lines)

    return Rewrite(
        corrected_answer=corrected, edits=edits, citations=list(citations.values())
    )


def build_messages(answer: str, targets: list[ClaimResult], check_date: date) -> list[dict]:
    parts = [
        f"Today's date: {check_date.isoformat()}",
        f"<answer>\n{neutralise_tag(answer, 'answer')}\n</answer>",
    ]
    for result in targets:
        start, end = result.claim.span
        fields = "\n".join([
            f"original: {answer[start:end]}",
            f"claim: {result.claim.text}",
            f"current value: {result.current_value}",
        ])
        body = neutralise_tag(neutralise_tag(fields, "passage"), "answer")
        parts.append(f'<passage id="{result.claim.id}">\n{body}\n</passage>')
    return [
        {"role": "system", "content": load_prompt("rewrite")},
        {"role": "user", "content": "\n\n".join(parts)},
    ]


async def rewrite_answer(
    answer: str, results: list[ClaimResult], check_date: date, metrics: MetricsCollector
) -> Rewrite:
    """Write the corrected answer. Model problems fall back to plain "(now X)" edits."""
    targets = [
        result
        for result in results
        if result.verdict == "stale" and result.current_value and _valid_span(answer, result)
    ]
    replacements: dict[str, str] = {}
    if targets:
        settings = config.get_settings()
        try:
            response = await metrics.chat(
                "rewrite",
                build_messages(answer, targets, check_date),
                settings.model_strong,
                settings.fallbacks_strong_list,
                json_schema=RewriteOutput,
            )
        except llm.LLMError:
            response = None
        if response is not None:
            by_id = {result.claim.id: result for result in targets}
            for item in response.parsed.replacements:
                result = by_id.get(item.claim_id)
                if result is None or item.claim_id in replacements:
                    continue
                start, end = result.claim.span
                if validate_replacement(answer[start:end], item.replacement, result.current_value):
                    replacements[item.claim_id] = item.replacement.strip()
    return build_rewrite(answer, results, replacements)
