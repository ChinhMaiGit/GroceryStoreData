"""Business Data Generator — the package behind generate_dataset.py.

Each module implements one design document (documents/PHASE1..5_DETAILS.md)
or one cross-cutting concern:

    keys.py       the randomness discipline: master seed, keyed streams, tokens
    params.py     every parameter dict — the single source of truth
    phase1.py     the world at t = 0 (P1): locations, customers, the owner's MILP
    phase2.py     the script of the year (P2): calendar, weather, paths, events
                  — generated in per-year keyed blocks on the P5 horizon
    world.py      the World class assembling phases 1-2 for the daily loop,
                  plus the P5 panel flow and the discounter's defection paths
    phase3.py     the play, performed (P3): the daily market loop + refunds,
                  plus the P5 finance layer (draws, retained earnings, the
                  expansion, January tax) and the year-two/three scripts
    recording.py  the recording layer (P3 section 20): how the books get dirty,
                  run per calendar-year binder on the P5 horizon
    export.py     writes one arm's visible/ and hidden/ split
    validate.py   the self-validation suite (full for baseline, structural
                  plus fingerprint for scenario arms, plus the P5 battery —
                  year-one byte identity, panel accounting, the RE ledger)

Every arm — the baseline included — lands under data/scenarios/<name>/, with
visible/ (the analyst's dataset) and hidden/ (the answer key). The three-year
arc (P5) ships as the arms prefixed 3y_. Reproducible end to end from
MASTER_SEED.
"""
