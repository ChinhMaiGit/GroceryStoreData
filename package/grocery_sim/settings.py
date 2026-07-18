"""The settings schema: defaults, merging, and validation for
GroceryStoreSimulation.setup(settings).

Kept deliberately separate from simulation.py so the contract — what a
settings dict must look like, and every way it can be invalid — is readable
in one place.
"""

from __future__ import annotations

import datetime as dt

DEFAULTS = {
    "basic": {
        "name": "My Grocery Store",
        "random_seed": 20260712,
        "year": 1,
        "budget": 60_000,
        "year_start": "2025",
        "retain_earning": False,   # meaningless below basic.year == 3
        "retain_earning_from": None,     # None -> defaults to formalize_month (P5 §4)
    },
    "events": {
        "tax_cut": None,
        "tax_raise": None,
        "food_vat_cut": None,
        "typhoon": None,
        "competitor": None,
        "operational_hazard": None,
        "war": None,
    },
    "potential_investment": {
        "more_staff": True,
        "bigger_store": False,
        "upgrade_infrastructure": False,
    },
}

_PHASE5_ONLY_EVENTS = ("competitor", "operational_hazard")

# these six accept a list of dates to make the same event happen more than
# once. war/typhoon/food_vat_cut/tax_cut/tax_raise ride World's own
# events_add/weather_edit/vat_schedule/revenue_tax_schedule lists;
# operational_hazard (the freezer failure) is a self-contained, transient
# window (loss + a capped-capacity recovery period) that phase3.py loops
# over explicitly. `competitor` stays single-date: it is a permanent regime
# change once triggered (a ramp that never resets), and stacking a second
# entry on top of an already-suppressed customer base is a real calibration
# decision (how do two competitors' effects compound?), not a mechanical
# repeat.
_MULTI_OK_EVENTS = (
    "war", "typhoon", "food_vat_cut", "tax_cut", "tax_raise", "operational_hazard",
)


class SettingsError(ValueError):
    """Raised by validate() — always with a message naming the exact field."""


def _deep_merge(defaults: dict, override: dict) -> dict:
    out = dict(defaults)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _parse_month(label: str, field: str) -> dt.date:
    try:
        parts = label.split("-")
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 1
        return dt.date(year, month, 1)
    except (ValueError, AttributeError, IndexError) as exc:
        raise SettingsError(
            f"{field}: {label!r} is not a 'YYYY' or 'YYYY-MM' label"
        ) from exc


def resolve(user_settings: dict | None) -> dict:
    """Merge user_settings over DEFAULTS (missing keys/sections are fine —
    unknown top-level or leaf keys are not, to catch typos early) and
    validate. Returns the fully-resolved settings dict."""
    user_settings = user_settings or {}
    unknown_sections = set(user_settings) - set(DEFAULTS)
    if unknown_sections:
        raise SettingsError(f"unknown settings section(s): {sorted(unknown_sections)}")
    for section, keys in user_settings.items():
        unknown_keys = set(keys) - set(DEFAULTS[section])
        if unknown_keys:
            raise SettingsError(
                f"settings[{section!r}]: unknown key(s) {sorted(unknown_keys)}"
            )
    resolved = _deep_merge(DEFAULTS, user_settings)
    _validate(resolved)
    return resolved


def _validate(s: dict) -> None:
    basic = s["basic"]
    events = s["events"]

    if not isinstance(basic["name"], str) or not basic["name"].strip():
        raise SettingsError("basic.name must be a non-empty string")

    if basic["year"] not in (1, 3):
        raise SettingsError(
            "basic.year must be 1 or 3 — the Phase 5 three-year arc "
            "(holidays, panel churn, the expansion, the scripted year-two/"
            "year-three events) is hand-calibrated to exactly three years; "
            "arbitrary horizons are not yet supported"
        )

    if not isinstance(basic["random_seed"], int):
        raise SettingsError("basic.random_seed must be an int")

    if basic["budget"] <= 0:
        raise SettingsError("basic.budget must be positive")

    year_start = _parse_month(basic["year_start"], "basic.year_start")

    if basic["retain_earning"] and basic["year"] != 3:
        raise SettingsError(
            "basic.retain_earning requires basic.year == 3 — retained "
            "earnings and the expansion decision are Phase 5 mechanisms"
        )
    if basic["retain_earning_from"] is not None:
        rf = _parse_month(basic["retain_earning_from"], "basic.retain_earning_from")
        if rf < year_start:
            raise SettingsError("basic.retain_earning_from is before basic.year_start")

    story_end = dt.date(year_start.year + basic["year"], year_start.month, 1)

    for name, value in events.items():
        if value is None:
            continue
        if name in _PHASE5_ONLY_EVENTS and basic["year"] != 3:
            raise SettingsError(
                f"events.{name} requires basic.year == 3 — it is a Phase 5 "
                f"mechanism (it only exists on the three-year horizon)"
            )
        if isinstance(value, list):
            if name not in _MULTI_OK_EVENTS:
                raise SettingsError(
                    f"events.{name} takes a single date, not a list — it is "
                    f"a Phase 5 single-fire mechanism"
                )
            labels = value
            if not labels:
                raise SettingsError(f"events.{name} is an empty list")
            if len(set(labels)) != len(labels):
                raise SettingsError(f"events.{name} has a duplicate date in {labels}")
        else:
            labels = [value]

        for label in labels:
            ev_date = _parse_month(label, f"events.{name}")
            if ev_date < year_start:
                raise SettingsError(f"events.{name} ({label}) is before basic.year_start")
            if ev_date >= story_end:
                raise SettingsError(
                    f"events.{name} ({label}) falls after the story ends "
                    f"({basic['year']} year(s) from {basic['year_start']})"
                )

    # bigger_store / upgrade_infrastructure need no validation of their own:
    # like more_staff, they are plain booleans consumed by events.py's
    # composer, which already no-ops them outside basic.year == 3.
