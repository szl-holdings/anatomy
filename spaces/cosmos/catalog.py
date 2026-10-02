"""Anonymous, bounded Hugging Face catalog; provider stages are not app health."""
import copy
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

OWNERS = ("SZLHOLDINGS", "betterwithage")
KINDS = ("space", "model", "dataset")
TTL = 120
MAX_BYTES = 2_000_000
LIMIT = 500


def utc():
    return datetime.now(timezone.utc).isoformat()


def public_stream(owner, kind):
    params = [("author", owner), ("limit", str(LIMIT))]
    fields = ["sha", "private", "likes", "lastModified"]
    if kind == "space":
        fields += ["runtime", "sdk"]
    params += [("expand[]", field) for field in fields]
    url = "https://huggingface.co/api/" + kind + "s?" + urlencode(params)
    # urllib deliberately has no HF token discovery and no Authorization header.
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "SZL-Cosmos-public-catalog/1"})
    with urlopen(request, timeout=8) as response:
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError("response size limit")
        rows = json.loads(body)
        truncated = bool(response.headers.get("Link")) or len(rows) >= LIMIT
    if not isinstance(rows, list):
        raise ValueError("invalid catalog")
    nodes = []
    for row in rows[:LIMIT]:
        repo = row.get("id", "")
        if row.get("private") is not False or not isinstance(repo, str):
            continue
        if not re.fullmatch(re.escape(owner) + r"/[A-Za-z0-9_.-]+", repo, re.I):
            continue
        runtime = row.get("runtime") or {}
        stage = runtime.get("stage", "UNKNOWN") if kind == "space" else "NOT_APPLICABLE"
        stage = stage if isinstance(stage, str) and re.fullmatch(r"[A-Z_]{1,40}", stage) else "UNKNOWN"
        path = "spaces/" if kind == "space" else "datasets/" if kind == "dataset" else ""
        nodes.append({"id": kind + ":" + repo, "repo_id": repo, "slug": repo.split("/")[1],
                      "owner": owner, "kind": kind, "url": "https://huggingface.co/" + path + repo,
                      "runtime_stage": stage, "revision": row.get("sha"),
                      "runtime_revision": runtime.get("sha"), "modified_at": row.get("lastModified"),
                      "likes": row.get("likes", 0), "sdk": row.get("sdk"),
                      "self": repo == "betterwithage/cosmos"})
    return {"nodes": nodes, "observed_at": utc(), "truncated": truncated, "source_url": url}


class Catalog:
    def __init__(self, fetch=public_stream, clock=time.monotonic):
        self.fetch, self.clock = fetch, clock
        self.lock = threading.Lock()
        self.parts = {}
        self.errors = {}
        self.busy = False
        self.attempt = None

    def _refresh(self):
        def one(key):
            try:
                return key, self.fetch(*key), None
            except Exception:
                # Never include upstream bodies, paths, credentials or exception text.
                return key, None, "UPSTREAM_UNAVAILABLE"
        try:
            with ThreadPoolExecutor(max_workers=6) as pool:
                for key, part, error in pool.map(one, [(o, k) for o in OWNERS for k in KINDS]):
                    with self.lock:
                        if part is not None:
                            self.parts[key] = (part, self.clock())
                        self.errors[key] = error
        finally:
            with self.lock:
                self.busy = False

    def snapshot(self):
        with self.lock:
            now = self.clock()
            if not self.busy and (self.attempt is None or now - self.attempt >= TTL):
                self.busy = True
                self.attempt = now
                threading.Thread(target=self._refresh, daemon=True).start()
            nodes, sources = [], []
            for owner in OWNERS:
                for kind in KINDS:
                    key = (owner, kind)
                    part, at = self.parts.get(key, ({}, None))
                    age = round(max(0, now - at), 1) if at is not None else None
                    state = "UNAVAILABLE" if at is None else "STALE" if self.errors.get(key) or age >= TTL else "FRESH"
                    if part.get("truncated") and state == "FRESH":
                        state = "PARTIAL"
                    sources.append({"owner": owner, "kind": kind, "state": state, "age_seconds": age,
                                    "observed_at": part.get("observed_at"), "source_url": part.get("source_url"),
                                    "error": self.errors.get(key), "truncated": part.get("truncated", False)})
                    for node in part.get("nodes", []):
                        nodes.append(dict(node, observation_state=state, observed_at=part.get("observed_at")))
            states = {s["state"] for s in sources}
            state = "FRESH" if states == {"FRESH"} else "UNAVAILABLE" if not self.parts else "PARTIAL"
            return copy.deepcopy({"schema_version": 1, "state": state, "refreshing": self.busy,
                                  "served_at": utc(), "ttl_seconds": TTL, "sources": sources,
                                  "nodes": sorted(nodes, key=lambda n: n["id"]),
                                  "evidence": "Anonymous public Hugging Face metadata. RUNNING is provider stage; application health, inference, training and proof validity are not verified."})


CATALOG = Catalog()
