"""Business Data Generator — the package behind generate_dataset.py.

Each module implements one design document (documents/PHASE1..3_DETAILS.md)
or one cross-cutting concern:

    keys.py       the randomness discipline: master seed, keyed streams, tokens
    params.py     every parameter dict — the single source of truth
    phase1.py     the world at t = 0 (P1): locations, customers, the owner's MILP
    phase2.py     the script of the year (P2): calendar, weather, paths, events
    world.py      the World class assembling phases 1-2 for the daily loop
    phase3.py     the play, performed (P3): the daily market loop + refunds
    recording.py  the recording layer (P3 section 20): how the books get dirty
    export.py     writes one arm's visible/ and hidden/ split
    validate.py   the self-validation suite (full for baseline, structural
                  plus fingerprint for scenario arms)

Every arm — the baseline included — lands under data/scenarios/<name>/, with
visible/ (the analyst's dataset) and hidden/ (the answer key). Reproducible
end to end from MASTER_SEED.
"""
