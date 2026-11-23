# SPDX-License-Identifier: Apache-2.0
"""Strict, offline-only identities for the Holographic v7 live witness.

A revision-shaped string is not proof of deployment, signer identity, or
correct source bytes. These predicates only reject syntactically invalid
values before any release witness can label an observation LIVE.
"""
from __future__ import annotations

import re

_SHA40 = re.compile(r"[0-9a-f]{40}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


def is_sha40(value: object) -> bool:
    """Allow only the canonical lower-case 40-digit hexadecimal Git revision."""
    return type(value) is str and _SHA40.fullmatch(value) is not None


def is_sha256(value: object) -> bool:
    """Allow only a canonical lower-case 64-digit SHA-256 digest."""
    return type(value) is str and _SHA256.fullmatch(value) is not None
