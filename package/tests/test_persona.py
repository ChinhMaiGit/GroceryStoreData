"""persona.py in isolation — no simulation needed, since persona generation
depends only on an rng stream, never on settings or results."""

from __future__ import annotations

import numpy as np

from grocery_sim import persona


def test_gender_and_pronoun_consistent_across_many_seeds():
    for seed in range(50):
        rng = np.random.default_rng(seed)
        p = persona.generate_persona(rng)
        assert p["gender"] in ("male", "female")
        assert p["pronoun"] == persona.PRONOUNS[p["gender"]]
        first_name = p["owner_name"].split()[0]
        names = (
            persona.FIRST_NAMES_MALE if p["gender"] == "male"
            else persona.FIRST_NAMES_FEMALE
        )
        assert first_name in names


def test_both_genders_actually_occur_across_seeds():
    genders = {
        persona.generate_persona(np.random.default_rng(s))["gender"]
        for s in range(30)
    }
    assert genders == {"male", "female"}


def test_reproducible_given_same_rng_state():
    p1 = persona.generate_persona(np.random.default_rng(7))
    p2 = persona.generate_persona(np.random.default_rng(7))
    assert p1 == p2


def test_varies_across_different_seeds():
    names = {
        persona.generate_persona(np.random.default_rng(s))["owner_name"]
        for s in range(15)
    }
    assert len(names) > 1


def test_no_name_appears_in_both_gender_lists():
    assert set(persona.FIRST_NAMES_MALE).isdisjoint(persona.FIRST_NAMES_FEMALE)
