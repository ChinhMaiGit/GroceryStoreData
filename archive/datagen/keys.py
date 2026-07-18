"""Randomness discipline (Phase 2 §13 / Phase 3 §12) and tiny POS utilities.

Every draw in the generator comes from a stream keyed by stable identity
(stream key, entity, day / receipt), so counterfactual replays are CRN-valid.
"""

from __future__ import annotations

import numpy as np

MASTER_SEED = 20260712
K_PHASE1 = 1
K_PHASE2 = 2
K_CUSTDAY = 3
K_SKUDAY = 4
K_OWNERWK = 5
K_COST = 6
K_GUEST = 7
K_DIRT = 8      # the recording layer (P3 §20) — document defects, never sim draws
K_REFUND = 9    # refunds (P3 §21) — keyed per receipt, CRN-safe across replays
K_PANEL = 10    # the panel flow (P5 §3) — persistence, churn, replacement arrivals


def rng_for(*key: int) -> np.random.Generator:
    # variadic key: positional by necessity
    return np.random.default_rng(np.random.SeedSequence([MASTER_SEED, *key]))


def token(
    kind: int,
    n: int,
) -> str:
    """Stable, non-sequential customer token (what a POS card terminal yields)."""
    return f"C{((n * 2654435761) ^ (kind * 40503)) % 2**32:08X}"


def charm(
    p,
    ending,
):
    """Shelf-price psychology: snap to the SKU's habitual ending (min 0.09)."""
    dime = np.round(a = p * 10) / 10
    off = np.where(ending == 9, 0.01, np.where(ending == 5, 0.05, 0.0))
    return np.maximum(0.09, dime - off)
