"""grocery_sim's own addition: a reproducible, fictional owner identity for
the case brief (describe.py).

Per documents/CASE_WRITING_GUIDE.md's own rule, invented details here are
cosmetic identity only — a name, an age, a prior career, a fictional town
and street (never a real place) — never a substitute for narrative content.
Every actual story beat in the brief is derived from what really happened
in the run (see describe.py); this module only answers "who is telling the
story and where."
"""

from __future__ import annotations

# gender is a persona trait, not a narrative one: it exists only to pick a
# name from the right list and the matching pronoun set, so the brief reads
# like it is about one consistent person. describe.py never varies the
# actual story — events, costs, results — by gender.
FIRST_NAMES_MALE = [
    "Henrik", "Mikael", "Lars", "Oskar",
    "Anders", "Nils", "Erik", "Johan",
]
FIRST_NAMES_FEMALE = [
    "Astrid", "Ingrid", "Freya", "Sigrid",
    "Liv", "Karin", "Marit", "Solveig",
]
PRONOUNS = {
    "male": {"subject": "he", "object": "him", "possessive": "his"},
    "female": {"subject": "she", "object": "her", "possessive": "her"},
}
LAST_NAMES = [
    "Malm", "Berglund", "Solheim", "Kvist", "Lindqvist", "Aas",
    "Holm", "Vinter", "Dahl", "Fjeld", "Strand", "Nygard",
]
TOWNS = [
    "Lindaker", "Bjornvik", "Kastholm", "Solby", "Grankil",
    "Vidnes", "Almstad", "Tjornby", "Ravnhaug", "Bakkeby",
]
STREETS = [
    "Kastanjegatan", "Bjorkvagen", "Furugatan", "Lindallen",
    "Granstigen", "Almtorget", "Ekbacken", "Ronnvagen",
]
PRIOR_EMPLOYERS = [
    "Fylkia", "Nordmart", "Solvik Handel", "Ostrand Group",
    "Kornmagasinet", "Torvik and Co", "Bryggeriet Dagligvarer",
]

_AGE_RANGE = (34, 58)
_PRIOR_YEARS_RANGE = (8, 26)


def generate_persona(rng) -> dict:
    """rng: a numpy Generator, already keyed off the run's own random_seed
    (see simulation.py) so the same seed always produces the same owner."""
    gender = "male" if rng.integers(2) == 0 else "female"
    names = FIRST_NAMES_MALE if gender == "male" else FIRST_NAMES_FEMALE
    first = names[rng.integers(len(names))]
    last = LAST_NAMES[rng.integers(len(LAST_NAMES))]
    return {
        "owner_name": f"{first} {last}",
        "gender": gender,
        "pronoun": PRONOUNS[gender],
        "age": int(rng.integers(_AGE_RANGE[0], _AGE_RANGE[1] + 1)),
        "prior_years": int(rng.integers(_PRIOR_YEARS_RANGE[0], _PRIOR_YEARS_RANGE[1] + 1)),
        "prior_employer": PRIOR_EMPLOYERS[rng.integers(len(PRIOR_EMPLOYERS))],
        "town": TOWNS[rng.integers(len(TOWNS))],
        "street": STREETS[rng.integers(len(STREETS))],
    }
