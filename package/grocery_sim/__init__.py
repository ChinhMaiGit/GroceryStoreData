"""grocery_sim — a standalone structural microsimulation of a neighborhood
grocery store, usable as a library.

    from grocery_sim import GroceryStoreSimulation

    sim = GroceryStoreSimulation()
    sim.setup(settings)      # validate a settings dict (see settings.py)
    sim.simulate()           # run phases 1-3 + the recording layer + export
    sim.data()               # in-memory tables (SimulationData)
    sim.db()                 # a duckdb connection over the same tables
    sim.erd()                # a Mermaid ER diagram string
    sim.describe()           # a business-case brief: a fictional owner
                              # narrating this run's real events and results
    sim.settings              # the resolved settings dict
    sim.create_analysis(path)  # a scaffolded marimo notebook

This package is extracted from, and mirrors, the `datagen/` implementation
behind the project's own generated cases (data/scenarios/, cases/). Each
module here implements one design document (documents/PHASE1..5_DETAILS.md)
or one cross-cutting concern:

    keys.py        the randomness discipline: master seed, keyed streams, tokens
    params.py      every parameter dict — the single source of truth
    phase1.py      the world at t = 0 (P1): locations, customers, the owner's MILP
    phase2.py      the script of the year (P2): calendar, weather, paths, events
    world.py       the World class assembling phases 1-2, plus the P5 panel flow
    phase3.py      the daily market loop (P3) + the P5 finance/expansion layer
    recording.py   the recording layer (P3 §20): how the books get dirty
    export.py      writes one run's visible/ and hidden/ split
    validate.py    the self-validation suite
    scenarios.py   the original named single-arm scenario registry (reference)
    events.py      the composer: settings.events/potential_investment -> a
                   scenario spec, generalizing scenarios.py to arbitrary,
                   independently dated, combinable events
    settings.py    the settings schema: defaults, merging, validation
    schema.py      a heuristic ER diagram over one run's exported tables
    persona.py     a reproducible fictional owner identity (cosmetic only)
    describe.py    the business-case brief generator, narrating a run's
                   real settings and results through that persona
    analysis.py    a scaffolded marimo notebook generator
    simulation.py  GroceryStoreSimulation — the public class

Known limitations of this first pass (see each module's own docstring for
detail): potential_investment.more_store (a second physical location) is
excluded entirely, not just disabled; basic.year only supports 1 or 3;
basic.year_start relabels exported dates but does not re-derive day-of-week
alignment for the target year (see events.py).
"""

from .simulation import GroceryStoreSimulation, SimulationData, ValidationError

__all__ = [
    "GroceryStoreSimulation",
    "SimulationData",
    "ValidationError",
]
