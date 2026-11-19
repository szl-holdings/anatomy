# SPDX-License-Identifier: Apache-2.0
"""Bounded, source-attributed historical mathematics for the Living Anatomy.

This is an original educational *metadata and example* atlas. It never scrapes
manuscript text at runtime, deciphers a museum object, promotes an SZL conjecture,
executes external code, or infers historical influence from a modern analogy.
All ten calculations operate on immutable synthetic/illustrative examples using
stdlib integers and Fraction. "Exact" qualifies arithmetic only, never history.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from fractions import Fraction
from typing import Any
from urllib.parse import urlsplit

SCHEMA = "szl.anatomy.ancient-math-atlas/v1"
PAPERS_SHA = "39c228dc3a29c6cfd831d43be6a8531e718692ac"
KHIPU_SHA = "5a6a3843008906051e7b3289767078cd04d26ac3"
LEAN_SHA = "80e35f859801d80fce7cf81e4d9b0c8bdf91cfea"
PAPERS_URL = (
    f"https://github.com/szl-holdings/szl-papers/blob/{PAPERS_SHA}/"
    "MATH_RUNTIME_EXECUTION_MATRIX.md"
)
KHIPU_URL = (
    f"https://github.com/szl-holdings/szl-khipu/blob/{KHIPU_SHA}/"
    "docs/KHIPU_NUMERICAL_INSPIRATION.md"
)
PROOF_URL = (
    f"https://github.com/szl-holdings/lutar-lean/blob/{LEAN_SHA}/"
    "Lutar/Uniqueness/TheoremU.lean"
)

# Public-source references, NOT copied manuscript corpus, OCR, private holdings,
# new historical attribution, independent third-party verification, or training.
# A citation means "reference for historical context", not "archive permission".
RECORDS: tuple[dict[str, str], ...] = (
    {
        "id": "rhind-unit-fractions",
        "tradition": "Ancient Egypt",
        "artifact": "Rhind Mathematical Papyrus; 2/n table",
        "title": "Distinct unit fractions",
        "formula": "2/7 = 1/4 + 1/28",
        "example": "2/7 and 1/4 + 1/28 (exact rational equality)",
        "historical_url": "https://www.open.edu/openlearn/science-maths-technology/mathematics-statistics/egyptian-mathematics/content-section-1.1.1",
        "math_url": "https://en.wikisource.org/wiki/Page:The_Rhind_Mathematical_Papyrus,_Volume_I.pdf/40",
        "status": "HISTORICAL_METHOD_MODERN_NOTATION",
        "limit": "A modern Fraction check is not a transcription, and does not validate all Rhind tables.",
        "szl_link": PAPERS_URL,
        "analogy": "Exact fractions as a reproducible witness; no new SZL theorem.",
    },
    {
        "id": "rhind-doubling",
        "tradition": "Ancient Egypt",
        "artifact": "Rhind Mathematical Papyrus; doubling multiplication",
        "title": "Doubling and binary decomposition",
        "formula": "41 * 59 = (32 + 8 + 1) * 59 = 2419",
        "example": "Integer product 41 by 59, using 32 + 8 + 1",
        "historical_url": "https://mathshistory.st-andrews.ac.uk/HistTopics/Egyptian_papyri/",
        "math_url": "https://mathshistory.st-andrews.ac.uk/HistTopics/Egyptian_papyri/",
        "status": "HISTORICAL_METHOD_MODERN_NOTATION",
        "limit": "Binary notation is modern explanatory notation; no claim of an ancient binary computer.",
        "szl_link": PAPERS_URL,
        "analogy": "Deterministic decomposition resembles reproducible computation, not proof ancestry.",
    },
    {
        "id": "moscow-frustum",
        "tradition": "Ancient Egypt",
        "artifact": "Moscow Mathematical Papyrus, problem 14",
        "title": "Volume of a square-pyramid frustum",
        "formula": "V = h * (a^2 + a*b + b^2) / 3",
        "example": "a=2, b=4, h=6; V=56",
        "historical_url": "https://mathworld.wolfram.com/MoscowMathematicalPapyrus.html",
        "math_url": "https://mathworld.wolfram.com/MoscowMathematicalPapyrus.html",
        "status": "HISTORICAL_METHOD_MODERN_NOTATION",
        "limit": "Applies to a right square-pyramid frustum, not every truncated solid.",
        "szl_link": PAPERS_URL,
        "analogy": "Exact geometric witness, not a newly formalized Lean declaration.",
    },
    {
        "id": "euclid-i47",
        "tradition": "Ancient Greece",
        "artifact": "Euclid, Elements, Book I, Proposition 47",
        "title": "Right-triangle square areas",
        "formula": "a^2 + b^2 = c^2 (right angle required)",
        "example": "a=3, b=4, c=5; 9 + 16 = 25",
        "historical_url": "https://www.euclids-elements.org/elements/books/bookI/propositions/propI47/",
        "math_url": "https://www.claymath.org/euclid_index/",
        "status": "HISTORICAL_PROPOSITION_MODERN_NOTATION",
        "limit": "A 3-4-5 test is not Euclid's complete geometrical proof.",
        "szl_link": PAPERS_URL,
        "analogy": "Formal proof and a finite executable test are different evidence tiers.",
    },
    {
        "id": "euclid-vii2",
        "tradition": "Ancient Greece",
        "artifact": "Euclid, Elements, Book VII, Proposition 2",
        "title": "Greatest common measure",
        "formula": "gcd(a,b) = gcd(b, a mod b) (modern equivalent)",
        "example": "gcd(1071, 462) = 21",
        "historical_url": "https://www.claymath.org/euclid_index/fundamentals-of-number-theory/?chapter=2",
        "math_url": "https://www.claymath.org/euclid_index/",
        "status": "HISTORICAL_PROPOSITION_MODERN_NOTATION",
        "limit": "Euclid describes repeated subtraction; modulo syntax is a modern equivalent.",
        "szl_link": PAPERS_URL,
        "analogy": "Algorithm termination on this finite input is not a new historic theorem.",
    },
    {
        "id": "dresden-venus-cycle",
        "tradition": "Maya Codices",
        "artifact": "Dresden Maya Codex, Venus tables (pp. 24, 46-50)",
        "title": "Venus and solar-calendar commensuration",
        "formula": "5 * 584 days = 8 * 365 days = 2920 days",
        "example": "Five table-cycle periods and eight 365-day years",
        "historical_url": "https://www.slub-dresden.de/en/explore/manuscripts/the-dresden-maya-codex/content",
        "math_url": "https://www.famsi.org/mayawriting/codices/dresden.html",
        "status": "HISTORICAL_CALENDAR_TABLE_MODERN_NOTATION",
        "limit": "584 days is a calendrical approximation, not a claim of exact orbital mechanics or prophecy.",
        "szl_link": PAPERS_URL,
        "analogy": "Period coordination offers a numerical illustration, not historical evidence of modern time-series AI.",
    },
    {
        "id": "maya-long-count",
        "tradition": "Maya Codices",
        "artifact": "Maya Long Count time-position convention (codex context)",
        "title": "Long Count mixed-radix day count",
        "formula": "days = 144000*b + 7200*k + 360*t + 20*u + kin",
        "example": "1.2.3.4.5 corresponds to 159565 counted days",
        "historical_url": "https://www.slub-dresden.de/en/explore/manuscripts/the-dresden-maya-codex/content",
        "math_url": "https://maya.nmai.si.edu/calendar/maya-calendar-converter",
        "status": "HISTORICAL_CALENDAR_CONVENTION_MODERN_NOTATION",
        "limit": "This is a modern numerical rendering; no individual codex glyph was deciphered here.",
        "szl_link": PAPERS_URL,
        "analogy": "Mixed-radix encoding is a mathematical comparison only, not a connection to khipu encoding.",
    },
    {
        "id": "andean-khipu-positional",
        "tradition": "Andean Khipu",
        "artifact": "Documented base-ten numeric knot registers (not a specific museum cord)",
        "title": "Decimal place-value reading",
        "formula": "N = sum(d_i * 10^i), where each known d_i is in {0,...,9}",
        "example": "Synthetic known digits (units,tens,hundreds)=(5,4,3) give 345",
        "historical_url": "https://www.nist.gov/nist-museum/standardizing-empire",
        "math_url": "https://khipukamayuq.com/khipu-datasets/",
        "status": "DOCUMENTED_NUMERIC_STRUCTURE_SYNTHETIC_EXAMPLE",
        "limit": "An unknown/broken cord is not zero. No archival identification, narrative decipherment, or community approval is inferred.",
        "szl_link": KHIPU_URL,
        "analogy": "Inspired by Andean counting; not proof that ancient khipus encoded cryptographic receipts.",
    },
    {
        "id": "andean-khipu-aggregate",
        "tradition": "Andean Khipu",
        "artifact": "Some documented khipu aggregate-cord relations (not universal)",
        "title": "Declared aggregate versus known child values",
        "formula": "T ?= sum(x_i) for an explicit complete group",
        "example": "Synthetic known values 12, 5, 8 and declared T=25",
        "historical_url": "https://github.com/khipulab/open-khipu-repository",
        "math_url": "https://khipukamayuq.com/khipu-datasets/",
        "status": "MODERN_RECONCILIATION_SYNTHETIC_EXAMPLE",
        "limit": "Agreement of numbers cannot prove archaeological meaning; missing values yield UNKNOWN, not pass.",
        "szl_link": KHIPU_URL,
        "analogy": "Modern arithmetic integrity preflight, not an ancient consensus protocol.",
    },
    {
        "id": "szl-kcrc-fingerprint",
        "tradition": "SZL Modern Research",
        "artifact": "SZL Khipu Cord Reconciliation and Challenge (KCRC-v1)",
        "title": "Modern finite-field polynomial fingerprint",
        "formula": "W_r(x) = sum(x_i * r^i) mod (2^61-1)",
        "example": "Synthetic x=(12,5,8), r=7 yields W=439",
        "historical_url": "https://www.nist.gov/nist-museum/standardizing-empire",
        "math_url": KHIPU_URL,
        "status": "MODERN_SZL_CONSTRUCTION_NOT_HISTORICAL",
        "limit": "Not used by ancient peoples; digest equality is not identity; soundness requires nonadaptive fixed references and field-uniform challenge.",
        "szl_link": KHIPU_URL,
        "analogy": "Original SZL engineering adaptation of a standard polynomial-fingerprint technique; not a locked Lean theorem.",
    },
)

_IDS = frozenset(row["id"] for row in RECORDS)
_ALLOWED_TRADITIONS = frozenset(row["tradition"] for row in RECORDS)
_REQUIRED = frozenset((
    "id", "tradition", "artifact", "title", "formula", "example",
    "historical_url", "math_url", "status", "limit", "szl_link", "analogy",
))


def _exact_example(item_id: str) -> tuple[str, str]:
    """Return exactly computed witness and independently stated expected value."""
    if item_id == "rhind-unit-fractions":
        return str(Fraction(1, 4) + Fraction(1, 28)), str(Fraction(2, 7))
    if item_id == "rhind-doubling":
        return str((32 + 8 + 1) * 59), "2419"
    if item_id == "moscow-frustum":
        return str(Fraction(6 * (2**2 + 2 * 4 + 4**2), 3)), "56"
    if item_id == "euclid-i47":
        return str(3**2 + 4**2), str(5**2)
    if item_id == "euclid-vii2":
        return str(math.gcd(1071, 462)), "21"
    if item_id == "dresden-venus-cycle":
        return str(5 * 584), str(8 * 365)
    if item_id == "maya-long-count":
        return str(1 * 144000 + 2 * 7200 + 3 * 360 + 4 * 20 + 5), "159565"
    if item_id == "andean-khipu-positional":
        digits = (5, 4, 3)  # complete synthetic registers, low place first
        return str(sum(d * 10**i for i, d in enumerate(digits))), "345"
    if item_id == "andean-khipu-aggregate":
        return str(sum((12, 5, 8))), "25"
    if item_id == "szl-kcrc-fingerprint":
        xs = (12, 5, 8)
        return str(sum(x * pow(7, i, 2**61 - 1) for i, x in enumerate(xs)) % (2**61 - 1)), "439"
    raise ValueError("unregistered formula identifier")


def _validate() -> None:
    if len(RECORDS) != 10 or len(_IDS) != len(RECORDS):
        raise ValueError("catalog count or identifiers drifted")
    if _ALLOWED_TRADITIONS != {
        "Ancient Egypt", "Ancient Greece", "Maya Codices",
        "Andean Khipu", "SZL Modern Research",
    }:
        raise ValueError("catalog tradition coverage drifted")
    for sha in (PAPERS_SHA, KHIPU_SHA, LEAN_SHA):
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError("unpinned first-party source revision")
    for record in RECORDS:
        if set(record) != _REQUIRED or any(not isinstance(v, str) or not v.strip() for v in record.values()):
            raise ValueError("incomplete record")
        if not re.fullmatch(r"[a-z0-9-]{3,64}", record["id"]):
            raise ValueError("unsafe catalog identifier")
        for key in ("historical_url", "math_url", "szl_link"):
            url = urlsplit(record[key])
            if url.scheme != "https" or not url.netloc or url.username or url.password:
                raise ValueError("invalid source link")
        if record["tradition"] == "SZL Modern Research" and record["status"] != "MODERN_SZL_CONSTRUCTION_NOT_HISTORICAL":
            raise ValueError("modern formula mislabeled as ancient")
        actual, expected = _exact_example(record["id"])
        if actual != expected:
            raise ValueError(f"exact arithmetic regression for {record['id']}")


def catalog_payload() -> dict[str, Any]:
    """Deterministic bounded metadata; no user input, mutable effects, or API reads."""
    try:
        _validate()
        basis = {"schema": SCHEMA, "source_pins": {
            "szl-papers": PAPERS_SHA,
            "szl-khipu": KHIPU_SHA,
            "lutar-lean": LEAN_SHA,
        }, "records": RECORDS}
        digest = hashlib.sha256(json.dumps(
            basis, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        examples = []
        for record in RECORDS:
            actual, expected = _exact_example(record["id"])
            examples.append({**record, "witness": {
                "status": "PASS_EXACT_ARITHMETIC",
                "observed": actual, "expected": expected,
                "kind": "FIXED_SYNTHETIC_OR_ILLUSTRATIVE",
            }})
        return {
            "schema": SCHEMA,
            "ready": True,
            "state": "CURATED_RESEARCH_EXACT_EXAMPLES",
            "evidence_state": "COMPUTED_ARITHMETIC_ONLY",
            "source_identity": "PINNED_DECLARATIONS_NOT_LIVE_VERIFIED",
            "catalog_sha256": digest,
            "records": examples,
            "record_count": len(examples),
            "traditions": sorted(_ALLOWED_TRADITIONS),
            "source_pins": basis["source_pins"],
            "authority": {
                "historical_decipherment": "NONE",
                "historic_influence_claim": "NONE",
                "lean_proof": "NOT_CLAIMED",
                "locked_proven_count_modified": False,
                "training": "NONE",
                "promotion": "NONE",
                "execution": "FIXED_LOCAL_ARITHMETIC_ONLY",
                "provider_mutation": "NONE",
                "publication": "NOT_VERIFIED_BY_THIS_ENDPOINT",
            },
            "research_context": {
                "papers": PAPERS_URL,
                "khipu": KHIPU_URL,
                "formal_proof_context": PROOF_URL,
                "lambda": "CONJECTURE_1_DISPROVED_AS_STATED_CONDITIONAL_THEOREM_U",
                "khipu_bft": "CONJECTURE_2_OPEN_CONDITIONAL_ONLY",
                "locked_proven_ids": ["F1", "F4", "F7", "F11", "F12", "F18", "F19", "F22"],
            },
            "limits": [
                "Source URLs are references, not proof that current links or publisher identities were read back.",
                "Only illustrative mathematics is executable; historical records are not ingested or deciphered.",
                "The Maya codices and Andean khipus are distinct traditions and media.",
                "No modern cryptographic mechanism is attributed to ancient communities.",
                "Computed examples do not constitute Lean proof, training evidence, or runtime release readiness.",
            ],
        }
    except (ValueError, TypeError, KeyError, OverflowError):
        return {
            "schema": SCHEMA,
            "ready": False,
            "state": "UNAVAILABLE",
            "evidence_state": "UNAVAILABLE",
            "records": [],
            "record_count": 0,
            "authority": {"execution": "NONE", "provider_mutation": "NONE"},
        }
