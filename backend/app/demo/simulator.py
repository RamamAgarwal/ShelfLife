"""Simulated Bifrost, Tavily and web pages for demo mode and tests.

Every company, product and figure here is invented, so no real-world fact is
stored in the code. The simulator answers the real pipeline's requests, so demo
mode exercises the same code paths as a live run without keys or credits.
"""

from __future__ import annotations

import asyncio
import json
import random
import re
from datetime import date, timedelta
from typing import Any

import httpx


def ago(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


# --- scenarios ------------------------------------------------------------------

CLOUD_QUESTION = "Which cloud host is cheapest for a 10-person startup in India, and how do I deploy to it?"
CLOUD_ANSWER = (
    "For a 10-person startup, Nimbus Cloud is the cheapest option. Nimbus Cloud's Starter plan "
    "costs $20 per seat per month, while Stratus Cloud charges $25 per seat per month. For 10 "
    "seats, Nimbus Cloud costs $200 a month, saving you $50 a month compared with Stratus Cloud. "
    "Nimbus Cloud is available in India. To deploy, call nimbus.deploy(app) from the Nimbus SDK."
)

FACTS_QUESTION = "How much does Acme Cloud cost, and who runs Acme?"
FACTS_ANSWER = (
    "Acme Cloud costs $10 per month on the Starter plan. The latest Acme SDK is version 3.2. "
    "Bo Lee is the CEO of Acme. Acme has 40 million users. Acme was founded in 1999 in Oslo. "
    "The Orbit feature is still in beta. The Data Act requires Acme to keep records for 5 years. "
    "Acme's spring sale is still running."
)

VAULT_QUESTION = "How many users can an Acme Vault workspace have, and what does it cost?"
VAULT_ANSWERS = [
    {"app": "Sales assistant", "answer": "Acme Vault supports up to 10,000 users per workspace and costs $12 per user per month."},
    {"app": "Support assistant", "answer": "Acme Vault supports up to 5,000 users per workspace and costs $12 per user per month."},
    {"app": "Docs assistant", "answer": "Acme Vault supports up to 8,000 users per workspace and costs $15 per user per month."},
]

SCENARIOS = [
    {
        "id": "cloud",
        "label": "Cloud recommendation",
        "description": "A recommendation built on prices, a calculation, a hidden assumption, an API call and availability.",
        "question": CLOUD_QUESTION,
        "answer": CLOUD_ANSWER,
        "context": {"country": "india"},
    },
    {
        "id": "facts",
        "label": "Product facts",
        "description": "Every kind of verdict: stale, uncertain, fresh, unverified and couldn't check.",
        "question": FACTS_QUESTION,
        "answer": FACTS_ANSWER,
        "context": None,
    },
    {
        "id": "compare",
        "label": "Three assistants disagree",
        "description": "The same question answered differently by a sales, support and docs assistant.",
        "question": VAULT_QUESTION,
        "answers": VAULT_ANSWERS,
    },
]


def claim(ref, kind, text, source, category, queries=(), entities=("Acme",), **extra):
    return {
        "ref": ref, "kind": kind, "text": text, "source_text": source, "span": None,
        "category": category, "entities": list(entities), "time_sensitive": category != "static",
        "search_queries": list(queries), "official_domains": extra.pop("official", []), **extra,
    }


CLOUD_EXTRACTION = [
    claim("r1", "recommendation", "Nimbus Cloud is the cheapest option for a 10-person startup.",
          "Nimbus Cloud is the cheapest option", "pricing", entities=("Nimbus Cloud",),
          depends_on=["r2", "r3", "r4", "r5", "r8"]),
    claim("r2", "fact", "Nimbus Cloud's Starter plan costs $20 per seat per month.",
          "Nimbus Cloud's Starter plan costs $20 per seat per month", "pricing",
          ["Nimbus Cloud Starter plan price"], ("Nimbus Cloud", "Nimbus"), number=20, official=["nimbus.example"]),
    claim("r3", "fact", "Stratus Cloud charges $25 per seat per month.",
          "Stratus Cloud charges $25 per seat per month", "pricing",
          ["Stratus Cloud price per seat"], ("Stratus Cloud", "Stratus"), number=25),
    claim("r4", "calculation", "For 10 seats, Nimbus Cloud costs $200 a month.",
          "Nimbus Cloud costs $200 a month", "pricing", entities=("Nimbus Cloud",),
          depends_on=["r2"], formula="{r2} * 10", number=200),
    claim("r5", "calculation", "Choosing Nimbus Cloud saves $50 a month compared with Stratus Cloud.",
          "saving you $50 a month", "pricing", entities=("Nimbus Cloud",),
          depends_on=["r2", "r3"], formula="({r3} - {r2}) * 10", number=50),
    claim("r6", "availability", "Nimbus Cloud is available in India.",
          "Nimbus Cloud is available in India", "product_status",
          ["Nimbus Cloud regions"], ("Nimbus Cloud", "Nimbus")),
    claim("r7", "api_usage", "nimbus.deploy(app) is the current way to deploy with the Nimbus SDK.",
          "call nimbus.deploy(app)", "version_api", ["Nimbus SDK deploy method"], ("Nimbus SDK", "Nimbus")),
    claim("r8", "assumption", "Nimbus Cloud's Starter plan allows at least 10 seats.", "",
          "product_status", ["Nimbus Cloud Starter plan seat limit"], ("Nimbus Cloud", "Nimbus"), number=10),
]

FACTS_EXTRACTION = [
    claim("f1", "fact", "Acme Cloud costs $10 per month on the Starter plan.",
          "Acme Cloud costs $10 per month on the Starter plan", "pricing", ["Acme Cloud price"],
          ("Acme Cloud", "Acme"), number=10),
    claim("f2", "fact", "The latest Acme SDK is version 3.2.", "The latest Acme SDK is version 3.2",
          "version_api", ["Acme SDK latest version"], number=3.2),
    claim("f3", "fact", "Bo Lee is the CEO of Acme.", "Bo Lee is the CEO of Acme", "leadership_role", ["Acme CEO"]),
    claim("f4", "fact", "Acme has 40 million users.", "Acme has 40 million users", "statistic",
          ["Acme number of users"], number=40),
    claim("f5", "fact", "Acme was founded in 1999 in Oslo.", "Acme was founded in 1999 in Oslo", "static"),
    claim("f6", "fact", "Acme's Orbit feature is still in beta.", "The Orbit feature is still in beta",
          "product_status", ["Acme Orbit beta"]),
    claim("f7", "fact", "The Data Act requires Acme to keep records for 5 years.",
          "The Data Act requires Acme to keep records for 5 years", "law_regulation",
          ["Data Act record keeping period"], number=5),
    claim("f8", "fact", "Acme's spring sale is still running.", "Acme's spring sale is still running",
          "event_status", ["Acme spring sale"]),
]


def vault_extraction(answer: str) -> list[dict]:
    users = re.search(r"up to ([\d,]+) users", answer)
    price = re.search(r"\$(\d+) per user", answer)
    claims = []
    if users:
        claims.append(claim("v1", "fact", f"Acme Vault supports up to {users.group(1)} users per workspace.",
                            f"Acme Vault supports up to {users.group(1)} users per workspace", "version_api",
                            ["Acme Vault users per workspace limit"], ("Acme Vault", "Acme"),
                            number=float(users.group(1).replace(",", ""))))
    if price:
        claims.append(claim("v2", "fact", f"Acme Vault costs ${price.group(1)} per user per month.",
                            f"costs ${price.group(1)} per user per month", "pricing",
                            ["Acme Vault price per user"], ("Acme Vault", "Acme"), number=float(price.group(1))))
    return claims


def result(url, content, days, title="Page", score=0.9):
    return {"title": title, "url": url, "content": content, "score": score,
            "published_date": ago(days) if days is not None else None,
            "favicon": None}


def search_results() -> dict[str, list[dict]]:
    return {
        "Nimbus Cloud Starter plan price": [
            result("https://nimbus.example/pricing", "Pricing", 3, "Nimbus Cloud pricing", 0.95),
            result("https://technews.example/nimbus-price", "Nimbus Cloud raises its Starter plan to $28 per seat per month, effective this quarter.", 10, "Nimbus raises prices", 0.9),
            result("https://dailycloud.example/nimbus", "Nimbus Cloud raises its Starter plan to $28 per seat per month, effective this quarter!", 9, "Nimbus price rise", 0.85),
            result("https://oldblog.example/cheap-clouds", "Nimbus Cloud's Starter plan costs $20 per seat per month.", 400, "Cheapest clouds", 0.5),
        ],
        "Stratus Cloud price per seat": [
            result("https://stratus.example/pricing", "Stratus Cloud costs $25 per seat per month on every plan.", 6, "Stratus pricing"),
        ],
        "Nimbus Cloud regions": [
            result("https://nimbus.example/regions", "Nimbus Cloud regions: Mumbai (India), Singapore and Frankfurt.", 25, "Regions"),
        ],
        "Nimbus SDK deploy method": [
            result("https://nimbus.example/docs/changelog", "SDK 4.0: nimbus.deploy() is deprecated. Use nimbus.deployments.create(app) instead.", 15, "SDK changelog"),
        ],
        "Nimbus Cloud Starter plan seat limit": [
            result("https://nimbus.example/plans", "The Starter plan supports up to 5 seats. Teams of 6 or more need the Team plan.", 30, "Plans"),
        ],
        "Acme Cloud price": [
            result("https://acme.example/pricing", "The Acme Cloud Starter plan now costs $25 per month.", 4, "Acme pricing", 0.95),
            result("https://www.reuters.com/acme-price", "Acme raised its Starter plan to $25 per month this year.", 30, "Acme raises price", 0.9),
            result("https://oldblog.example/acme", "Acme Cloud costs $10 per month on the Starter plan.", 700, "Old post", 0.5),
        ],
        "Acme SDK latest version": [result("https://acme.example/sdk", "The latest Acme SDK is version 3.2.", 210, "SDK releases")],
        "Acme CEO": [
            result("https://acme.example/about", "Bo Lee is the chief executive of Acme.", 12, "About Acme", 0.95),
            result("https://techcrunch.com/acme", "Acme CEO Bo Lee spoke at the conference.", 40, "Acme at the conference", 0.9),
        ],
        "Acme number of users": [result("https://reddit.com/r/acme/1", "I heard Acme has 40 million users.", None, "Forum thread")],
        "Acme Orbit beta": [result("https://acme.example/orbit", "Orbit overview.", 5, "Orbit")],
        "Data Act record keeping period": [result("https://justice.gov/data-act", "The Data Act requires companies to keep records for 5 years.", 90, "Data Act")],
        "Acme spring sale": [result("https://acme.example/sale", "The Acme spring sale is running now.", 39, "Spring sale")],
        "Acme Vault users per workspace limit": [result("https://acme.example/vault/limits", "Each Acme Vault workspace supports up to 8,000 users.", 12, "Vault limits")],
        "Acme Vault price per user": [result("https://acme.example/vault/pricing", "Acme Vault costs $15 per user per month.", 8, "Vault pricing")],
    }


FULL_PAGES = {
    "https://nimbus.example/pricing": "Nimbus Cloud Starter plan: $28 per seat per month, up to 5 seats. Team plan: $35 per seat per month.",
}

# What a link check finds at each address: status, redirect target, page text.
LINK_PAGES: dict[str, tuple[int, str | None, str]] = {
    "https://nimbus.example/pricing": (200, None, FULL_PAGES["https://nimbus.example/pricing"]),
    "https://technews.example/nimbus-price": (404, None, "Not found"),
    "https://dailycloud.example/nimbus": (301, "https://dailycloud.example/archive/nimbus", ""),
    "https://dailycloud.example/archive/nimbus": (200, None, "Archive: Nimbus Cloud raises its Starter plan to $28 per seat per month, effective this quarter!"),
    "https://oldblog.example/cheap-clouds": (410, None, "Gone"),
    "https://nimbus.example/docs/changelog": (200, None, "SDK 5.0 release notes. See the migration guide."),
}


def one(eid, stance, quote):
    return {"id": eid, "stance": stance, "quote": quote}


def adjudicate(claim_text: str, context: str) -> Any:
    text = claim_text
    if "Nimbus Cloud's Starter plan costs" in text:
        return {"judgements": [one("E1", "contradicts", "Nimbus Cloud Starter plan: $28 per seat per month"),
                               one("E2", "contradicts", "raises its Starter plan to $28 per seat per month"),
                               one("E3", "contradicts", "raises its Starter plan to $28 per seat per month"),
                               one("E4", "supports", "Nimbus Cloud's Starter plan costs $20 per seat per month")],
                "current_value": "$28 per seat per month", "claimed_value": "$20 per seat per month",
                "change_type": "value_changed", "explanation": "The official pricing page and the news now list $28 per seat."}
    if "Stratus Cloud charges" in text:
        return {"judgements": [one("E1", "supports", "Stratus Cloud costs $25 per seat per month")],
                "current_value": "$25 per seat per month", "change_type": "no_change",
                "explanation": "Stratus's pricing page still lists $25 per seat."}
    if "available in" in text and "Nimbus" in text:
        note = "No Brazil region is listed." if "Brazil" in context else None
        return {"judgements": [one("E1", "supports", "Nimbus Cloud regions: Mumbai (India)")],
                "current_value": "Available in India (Mumbai region)", "context_note": note,
                "explanation": "Nimbus lists a Mumbai region."}
    if "nimbus.deploy" in text:
        return {"judgements": [one("E1", "contradicts", "nimbus.deploy() is deprecated. Use nimbus.deployments.create(app) instead")],
                "current_value": "nimbus.deployments.create(app)", "claimed_value": "nimbus.deploy(app)",
                "change_type": "deprecated", "explanation": "The SDK changelog deprecates nimbus.deploy()."}
    if "at least 10 seats" in text:
        return {"judgements": [one("E1", "contradicts", "The Starter plan supports up to 5 seats")],
                "current_value": "Up to 5 seats", "claimed_value": "at least 10 seats",
                "change_type": "value_changed", "explanation": "The Starter plan is capped at 5 seats."}
    if "Acme Cloud costs" in text:
        return {"judgements": [one("E1", "contradicts", "Starter plan now costs $25 per month"),
                               one("E2", "contradicts", "raised its Starter plan to $25 per month"),
                               one("E3", "supports", "Acme Cloud costs $10 per month")],
                "current_value": "$25 per month", "claimed_value": "$10 per month",
                "change_type": "value_changed", "explanation": "Current sources list a higher Starter price."}
    if "Acme SDK" in text:
        return {"judgements": [one("E1", "supports", "latest Acme SDK is version 3.2")],
                "current_value": "Version 3.2", "explanation": "The only source agrees, but it is several months old."}
    if "CEO" in text:
        return {"judgements": [one("E1", "supports", "Bo Lee is the chief executive of Acme"),
                               one("E2", "supports", "Acme CEO Bo Lee")],
                "current_value": "Bo Lee", "explanation": "The company site and trade press agree."}
    if "40 million" in text:
        return {"judgements": [one("E1", "supports", "Acme has 40 million users")],
                "current_value": "40 million", "explanation": "Only a forum post mentions this."}
    if "Orbit" in text:
        return "this is not valid JSON"
    if "Data Act" in text:
        return {"judgements": [one("E1", "supports", "requires companies to keep records for 5 years")],
                "current_value": "5 years", "explanation": "The government source confirms the period."}
    if "spring sale" in text:
        return {"judgements": [one("E1", "supports", "The Acme spring sale is running now")],
                "current_value": "Running", "explanation": "The sale page says it is running."}
    if "users per workspace" in text:
        match = re.search(r"up to ([\d,]+) users", text)
        stated = match.group(1) if match else ""
        if stated == "8,000":
            return {"judgements": [one("E1", "supports", "supports up to 8,000 users")],
                    "current_value": "8,000 users", "explanation": "The limits page lists 8,000 users."}
        return {"judgements": [one("E1", "contradicts", "supports up to 8,000 users")],
                "current_value": "8,000 users", "claimed_value": f"{stated} users",
                "change_type": "value_changed", "explanation": "The limits page lists 8,000 users."}
    if "Acme Vault costs" in text:
        if "$15" in text:
            return {"judgements": [one("E1", "supports", "Acme Vault costs $15 per user per month")],
                    "current_value": "$15 per user per month", "explanation": "The pricing page agrees."}
        return {"judgements": [one("E1", "contradicts", "Acme Vault costs $15 per user per month")],
                "current_value": "$15 per user per month", "claimed_value": re.search(r"\$\d+ per user per month", text).group(),
                "change_type": "value_changed", "explanation": "The pricing page lists $15."}
    return {"judgements": [], "current_value": None, "explanation": "The demo has no sources for this claim."}


def extraction_for(answer: str) -> list[dict]:
    if "Nimbus Cloud" in answer:
        return CLOUD_EXTRACTION
    if "Acme Vault" in answer:
        return vault_extraction(answer)
    if "Acme Cloud costs" in answer:
        return FACTS_EXTRACTION
    return []


def generated_answer(question: str) -> str:
    lowered = question.lower()
    if any(word in lowered for word in ("cloud host", "nimbus", "deploy")):
        return CLOUD_ANSWER
    if "vault" in lowered:
        return VAULT_ANSWERS[0]["answer"]
    return FACTS_ANSWER


_NUMBER = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def rewrite_passage(original: str, current: str) -> str:
    if "cheapest option" in original:
        return "Stratus Cloud is now the cheaper option, at $25 per seat per month"
    if current.startswith("-") and _NUMBER.search(original):
        return f"costing you ${current.lstrip('-$')} more a month"
    old_number = _NUMBER.search(original)
    new_number = _NUMBER.search(current)
    if old_number and new_number and "seat" not in current.lower()[:3]:
        return original[: old_number.start()] + new_number.group() + original[old_number.end():]
    code = re.search(r"[\w.]+\(\w*\)", original)
    if code and "(" in current:
        return original[: code.start()] + current + original[code.end():]
    return current


def decision_reply() -> dict:
    return {
        "holds": "no",
        "revised": "Stratus Cloud is now the cheaper option for a 10-person startup, at $25 per seat per month.",
        "reason": "Nimbus Cloud's Starter plan now costs $28 per seat and allows only 5 seats.",
    }


# --- the transport ------------------------------------------------------------


class Simulator:
    """An httpx handler that plays Bifrost, Tavily and the web."""

    def __init__(self, latency: tuple[float, float] = (0.15, 0.5)) -> None:
        self.latency = latency
        self.cache: set[tuple] = set()
        self.spend = 0.0
        self.credits = 0
        self.searches = search_results()

    async def __call__(self, request: httpx.Request) -> httpx.Response:
        if self.latency[1] > 0:
            await asyncio.sleep(random.uniform(*self.latency))
        url = str(request.url).split("?")[0]
        path = request.url.path
        if request.url.host == "api.tavily.com":
            return self._tavily(path, request)
        if url in LINK_PAGES or request.url.host.endswith(".example"):
            return self._web(url)
        return self._bifrost(path, request)

    def _web(self, url: str) -> httpx.Response:
        # Pages without a link fixture still say what their search result said.
        snippets = [item["content"] for items in search_results().values() for item in items if item["url"] == url]
        status, location, text = LINK_PAGES.get(url, (200, None, " ".join(snippets) or "A page in the demo web."))
        headers = {"location": location} if location else {}
        return httpx.Response(status, headers=headers, text=text)

    def _tavily(self, path: str, request: httpx.Request) -> httpx.Response:
        if path == "/usage":
            return httpx.Response(200, json={"key": {"usage": self.credits, "limit": 1000}})
        body = json.loads(request.content)
        if path == "/extract":
            results = [{"url": u, "raw_content": FULL_PAGES[u]} for u in body["urls"] if u in FULL_PAGES]
            self.credits += 1 if results else 0
            return httpx.Response(200, json={"results": results, "usage": {"credits": 1 if results else 0}})
        query = re.sub(r" (India|Brazil|[A-Z][a-z]+ [A-Z][a-z]+)$", "", body["query"])
        found = self.searches.get(query) or self.searches.get(body["query"], [])
        self.credits += 1
        return httpx.Response(200, json={"results": found, "usage": {"credits": 1}})

    def _bifrost(self, path: str, request: httpx.Request) -> httpx.Response:
        if path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        if path == "/api/session/is-auth-enabled":
            return httpx.Response(200, json={"inference_auth_enforced": False})
        if path == "/api/governance/virtual-keys/quota":
            return httpx.Response(200, json={"virtual_key_name": "shelflife-demo", "is_active": True,
                                             "budgets": [{"max_limit": 5.0, "current_usage": round(self.spend, 4), "reset_duration": "1M"}]})
        if path.startswith("/api/plugins"):
            return httpx.Response(200, json={"plugins": [{"name": "semantic_cache", "enabled": True}]})
        body = json.loads(request.content)
        messages = body["messages"]
        full = "\n".join(message["content"] for message in messages)
        last = messages[-1]["content"]
        context = (re.search(r"<context>\n(.*?)\n</context>", full, re.S) or [None, ""])[1] or ""

        if "<passage" in full:
            passages = re.findall(r'<passage id="(c\d+)">\noriginal: (.*?)\nclaim: .*?\ncurrent value: (.*?)\n</passage>', full, re.S)
            reply: Any = {"replacements": [{"claim_id": cid, "replacement": rewrite_passage(original, current)}
                                           for cid, original, current in passages]}
        elif "<recommendation>" in full:
            reply = decision_reply()
        elif (match := re.search(r"<claim>\n(.*?)\n</claim>", full, re.S)):
            reply = adjudicate(match.group(1), context)
        elif "<answer>" in last:
            answer = re.search(r"<answer>\n(.*?)\n</answer>", last, re.S).group(1)
            reply = {"claims": extraction_for(answer)}
        else:
            question = re.search(r"<question>\n(.*?)\n</question>", full, re.S)
            reply = generated_answer(question.group(1) if question else last)
        content = reply if isinstance(reply, str) else json.dumps(reply)

        provider, model = body["model"].split("/", 1)
        cache_key = request.headers.get("x-bf-cache-key")
        fingerprint = (cache_key, body["model"], full)
        if cache_key and fingerprint in self.cache:
            return self._completion(content, {"provider": provider, "model": model},
                                    {"cache_hit": True, "hit_type": "direct"}, cost=None)
        if cache_key:
            self.cache.add(fingerprint)
        routing = {"provider": provider, "model": model}
        # Runs with the cache off stand in for a broken primary provider.
        if not cache_key and body.get("fallbacks"):
            fallback_provider, fallback_model = body["fallbacks"][0].split("/", 1)
            routing = {"provider": fallback_provider, "model": fallback_model, "is_fallback": True,
                       "primary_provider": provider, "primary_model": model}
        self.spend += 0.00042
        return self._completion(content, routing, {"cache_hit": False}, cost=0.00042)

    @staticmethod
    def _completion(content: str, routing: dict, cache: dict, cost: float | None) -> httpx.Response:
        usage = {"prompt_tokens": 820, "completion_tokens": 90, "total_tokens": 910}
        if cost is not None:
            usage["cost"] = {"total_cost": cost}
        return httpx.Response(200, json={
            "choices": [{"message": {"role": "assistant", "content": content}}],
            "usage": usage,
            "extra_fields": {"routing_info": routing, "cache_debug": cache},
        })
