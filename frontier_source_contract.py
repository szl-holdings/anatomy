# SPDX-License-Identifier: Apache-2.0
"""Validate typed frontier source receipts without fetching or hydrating content.

Git sources bind candidates to an exact commit/path. Public research sources
bind each candidate to its canonical metadata capture, then bind the declared
provider receipt to the sorted aggregate of those captures. These are different
identities; a metadata digest must never be presented as a Git revision.

The bounded metadata projection follows szl-second-brain's public_research/v1
contract. Captures are public HTTPS observations, not independent attestations,
and grant no content, training, promotion, or execution authority.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote, urlencode

GIT_REVISION = "git-sha1"
METADATA_REVISION = "metadata-capture-sha256"
_HEX_40 = re.compile(r"^[0-9a-f]{40}$")
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_DOI = re.compile(r"^10\.\d{4,9}/[A-Za-z0-9._;()/:-]{1,180}$")
_ARXIV_VERSION = re.compile(r"^\d{4}\.\d{4,5}v[1-9]\d{0,2}$")
_SECRET = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----|"
    r"\b(?:sk-|gh[pousr]_|hf_)[A-Za-z0-9_-]{24,}\b|\bAKIA[0-9A-Z]{16}\b"
)
_AUTHENTICATION = "PUBLIC_HTTPS_METADATA_NOT_INDEPENDENT_ATTESTATION"
_METADATA_KEYS = {
    "provider", "identifier", "canonical_url", "title", "authors", "published",
    "updated", "categories", "licence_urls", "metadata_licence", "full_text_licence",
}


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(f"frontier source {reason}")


def _revision(kind: Any, revision: Any) -> None:
    pattern = {GIT_REVISION: _HEX_40, METADATA_REVISION: _HEX_64}.get(str(kind))
    _require(pattern is not None and isinstance(revision, str) and bool(pattern.fullmatch(revision)),
             "revision kind or exact digest is invalid")


def validate_source_revision(source: dict[str, Any]) -> None:
    kind = source.get("revision_kind", GIT_REVISION)
    _revision(kind, source.get("revision"))
    if kind == GIT_REVISION:
        _require(not str(source.get("repository", "")).startswith("public-metadata/")
                 and source.get("parser") != "public_research_metadata",
                 "metadata receipt is mislabeled as Git")


def _timestamp(value: Any) -> datetime:
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        _require(stamp.tzinfo is not None and stamp.utcoffset() == timezone.utc.utcoffset(stamp),
                 "research timestamp must be UTC")
        return stamp
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValueError("frontier source research timestamp is invalid") from exc


def _clean_text(value: Any) -> None:
    _require(isinstance(value, str), "metadata field is not text")
    _require(not _SECRET.search(value), "secret-like metadata is rejected")
    cleaned = " ".join(re.sub(r"<[^>]{0,512}>", " ", value).split())
    _require(value == cleaned and 0 < len(value) <= 240
             and all(ord(char) >= 32 and ord(char) != 127 for char in value),
             "metadata field is not bounded sanitized text")


def _validate_provenance(provenance: Any, now: datetime) -> dict[str, Any]:
    _require(isinstance(provenance, dict), "research provenance is missing")
    metadata = provenance.get("metadata")
    _require(isinstance(metadata, dict) and set(metadata) == _METADATA_KEYS,
             "metadata projection is unsupported")
    _require(len(_canonical(metadata)) <= 256 * 1024
             and len(_canonical(provenance)) <= 2 * 1024 * 1024,
             "research capture exceeds byte bound")
    _require(provenance.get("capture_sha256") == _digest(metadata),
             "research capture digest mismatch")
    provider, identifier = provenance.get("provider"), provenance.get("identifier")
    _require(isinstance(provider, str) and provider in {"crossref", "arxiv"}
             and isinstance(identifier, str),
             "research provider or identifier is invalid")
    _require(metadata["provider"] == provider and metadata["identifier"] == identifier,
             "research provider identity mismatch")
    _require(metadata["full_text_licence"] == "NOT_INFERRED",
             "full-text licence was inferred")
    for key, bound in (("authors", 32), ("categories", 12), ("licence_urls", 8)):
        values = metadata[key]
        _require(isinstance(values, list) and len(values) <= bound, "metadata count exceeds bound")
        for value in values:
            _clean_text(value)
    _clean_text(metadata["title"])
    if provider == "arxiv":
        _require(bool(_ARXIV_VERSION.fullmatch(identifier)), "arXiv identifier is not version pinned")
        _require(metadata["canonical_url"] == "https://arxiv.org/abs/" + identifier
                 and metadata["metadata_licence"] == "CC0-1.0",
                 "arXiv canonical URL or metadata licence changed")
        _timestamp(metadata["published"])
        _timestamp(metadata["updated"])
        allowed_requests = {
            "https://export.arxiv.org/api/query?" + urlencode({"id_list": value, "max_results": 1})
            for value in (identifier, identifier.split("v")[0])
        }
    else:
        _require(bool(_DOI.fullmatch(identifier)) and identifier == identifier.lower(),
                 "Crossref DOI is not canonical")
        _require(metadata["canonical_url"] == "https://doi.org/" + identifier
                 and metadata["metadata_licence"] == "NOT_DECLARED_BY_RESPONSE"
                 and metadata["updated"] is None,
                 "Crossref canonical URL, licence, or revision changed")
        publication = metadata["published"]
        if publication is not None:
            _require(isinstance(publication, str)
                     and bool(re.fullmatch(r"\d{4}(?:-\d{2})?(?:-\d{2})?", publication)),
                     "Crossref publication date is malformed")
            fields = [int(field) for field in publication.split("-")]
            try:
                datetime(fields[0], fields[1] if len(fields) > 1 else 1,
                         fields[2] if len(fields) > 2 else 1)
            except ValueError as exc:
                raise ValueError("frontier source Crossref publication date is invalid") from exc
        allowed_requests = {"https://api.crossref.org/works/" + quote(identifier, safe="")}
    _require(isinstance(provenance.get("request_url"), str)
             and provenance["request_url"] in allowed_requests, "research request origin mismatch")
    response_bytes = provenance.get("response_bytes")
    _require(bool(_HEX_64.fullmatch(str(provenance.get("response_sha256", ""))))
             and type(response_bytes) is int and 0 < response_bytes <= 256 * 1024,
             "research response receipt is invalid")
    age = (now - _timestamp(provenance.get("observed_at"))).total_seconds()
    _require(-300 <= age <= 180 * 86400, "research capture is future dated or stale")
    _require(provenance.get("source_authentication") == _AUTHENTICATION,
             "research authentication claim is unsupported")
    return metadata


class FrontierSourceBindings:
    """Resolve typed candidate bindings and verify provider aggregate receipts."""

    def __init__(self, sources: list[dict[str, Any]]) -> None:
        self._now = datetime.now(timezone.utc)
        self._sources: dict[str, dict[str, Any]] = {}
        self._metadata: dict[str, list[dict[str, Any]]] = {}
        self._captures: set[str] = set()
        for source in sources:
            if source.get("revision_kind", GIT_REVISION) != METADATA_REVISION:
                continue
            repository = source["repository"]
            _require(repository in {"public-metadata/arxiv", "public-metadata/crossref"}
                     and repository not in self._sources
                     and source.get("parser") == "public_research_metadata"
                     and source.get("path") == "data/public-research-metadata.v1.json",
                     "research manifest binding is invalid or duplicated")
            self._sources[repository] = source
            self._metadata[repository] = []

    def binding_for(self, row: dict[str, Any]) -> tuple[str, str, str]:
        kind = row.get("source_revision_kind", GIT_REVISION)
        revision = row.get("source_revision")
        _revision(kind, revision)
        repository, path = str(row.get("source_repository") or ""), str(row.get("source_path") or "")
        if kind == GIT_REVISION:
            _require(not repository.startswith("public-metadata/")
                     and row.get("source_kind") != "research-metadata",
                     "metadata candidate is mislabeled as Git")
            return repository, revision, path
        _require(row.get("source_kind") == "research-metadata"
                 and row.get("admission") == "DISCOVERED_REVIEW_REQUIRED",
                 "research candidate admission changed")
        provenance = row.get("provenance")
        metadata = _validate_provenance(provenance, self._now)
        _require(repository == f"public-metadata/{provenance['provider']}"
                 and path == provenance["identifier"] and revision == provenance["capture_sha256"],
                 "research candidate binding mismatch")
        _require(repository in self._sources, "research provider has no declared source receipt")
        _require(revision not in self._captures, "research capture is duplicated")
        self._captures.add(revision)
        self._metadata[repository].append(metadata)
        source = self._sources[repository]
        return repository, source["revision"], source["path"]

    def verify(self) -> None:
        for repository, source in self._sources.items():
            metadata = sorted(self._metadata[repository],
                              key=lambda item: (item["provider"], item["identifier"], _digest(item)))
            measured = _digest(metadata)
            _require(bool(metadata) and source["revision"] == measured
                     and source["content_sha256"] == measured
                     and source["candidate_count"] == len(metadata),
                     "research aggregate receipt binding mismatch")


def metadata_handle_identity(row: dict[str, Any]) -> dict[str, Any]:
    """Retain the explicit revision type and bounded, already validated identity."""
    if row.get("source_revision_kind", GIT_REVISION) != METADATA_REVISION:
        return {}
    provenance = row["provenance"]
    metadata = provenance["metadata"]
    return {
        "revisionKind": METADATA_REVISION,
        "sourceIdentity": {
            "provider": provenance["provider"],
            "identifier": provenance["identifier"],
            "canonicalUrl": metadata["canonical_url"],
            "observedAt": provenance["observed_at"],
            "metadataLicence": metadata["metadata_licence"],
            "fullTextLicence": "NOT_INFERRED",
            "sourceAuthentication": provenance["source_authentication"],
        },
    }
