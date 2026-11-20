"""Stage 2: decide which claims are worth searching for."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import HALF_LIFE_DAYS
from app.models import DERIVED_KINDS, Claim


@dataclass
class TriageResult:
    to_check: list[Claim]
    not_time_sensitive: list[Claim]
    over_limit: list[Claim]
    # Calculations and recommendations: worked out from other claims, not searched.
    derived: list[Claim]


def triage(claims: list[Claim], max_claims: int) -> TriageResult:
    candidates: list[Claim] = []
    not_time_sensitive: list[Claim] = []
    derived: list[Claim] = []
    for claim in claims:
        if claim.kind in DERIVED_KINDS:
            derived.append(claim)
        elif claim.category == "static" or not claim.time_sensitive:
            not_time_sensitive.append(claim)
        else:
            candidates.append(claim)

    # sorted() is stable, so ties keep the order of the answer.
    by_urgency = sorted(candidates, key=lambda claim: HALF_LIFE_DAYS[claim.category])
    return TriageResult(
        to_check=by_urgency[:max_claims],
        not_time_sensitive=not_time_sensitive,
        over_limit=by_urgency[max_claims:],
        derived=derived,
    )
