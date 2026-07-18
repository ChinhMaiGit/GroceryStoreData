"""A first-pass business-case brief, built entirely from `settings` — never
from simulated results — which is what keeps it honest about the epistemic
firewall in documents/CASE_WRITING_GUIDE.md: the brief may only describe
what the owner could have observed (an event happening, a decision made),
never a mechanism (a modifier, a defection parameter) and never a number
more precise than an owner would carry in his head. Because this generator
only reads settings, not the run's own tables, that firewall holds by
construction.

This is a template, not the full CASE_WRITING_GUIDE apparatus (no persona
bank, no brand/town generation, no instructor-appendix split yet) — it gives
a usable narrative skeleton for a run's own settings, meant to be edited by
hand into a full case, the way a case writer would start from an outline.
"""

from __future__ import annotations

_EVENT_LINES = {
    "war": "a sudden jump in wholesale costs, reported as coming from a "
           "conflict-driven supply squeeze reaching almost every shelf",
    "typhoon": "a short, severe storm that kept customers home for a few days "
               "and roughed up the fresh and seafood deliveries that week",
    "food_vat_cut": "a government tax cut on food, announced ahead of time, "
                     "that eventually showed up in some of the shelf prices",
    "tax_cut": "a broader tax cut on non-food goods, announced ahead of time",
    "competitor": "a discount grocer opening a short walk away",
    "operational_hazard": "an overnight equipment failure that wrote off a "
                           "chunk of the frozen and chilled stock in one go",
}

_INVESTMENT_LINES = {
    "more_staff": "taking on extra help and longer opening hours once the "
                   "shop could clearly afford it",
}


def build_brief(settings: dict) -> str:
    b, ev, inv = settings["basic"], settings["events"], settings["potential_investment"]
    name = b["name"]
    years = b["year"]
    lines = []

    lines.append(f"# {name} — Business Case Brief")
    lines.append("")
    span = "one year" if years == 1 else f"{years} years"
    lines.append(
        f"{name} is a small neighborhood grocery store. The owner opened "
        f"with {_round_money(b['budget'])} in starting capital and "
        f"has now been trading for {span}."
    )
    lines.append("")

    # war/typhoon/food_vat_cut/tax_cut/operational_hazard may each carry a
    # list of dates (repeated occurrences); flatten to one (key, date) pair
    # per occurrence before sorting chronologically.
    active_events = []
    for k, v in ev.items():
        if v is None:
            continue
        dates = v if isinstance(v, list) else [v]
        active_events.extend((k, d) for d in dates)

    if active_events:
        lines.append("## What happened along the way")
        lines.append("")
        seen = set()
        for key, _date in sorted(active_events, key = lambda kv: kv[1]):
            sentence = _EVENT_LINES.get(key, f"an event ('{key}')")
            again = " again" if key in seen else ""
            lines.append(f"- Around {_date}, {sentence}{again}.")
            seen.add(key)
        lines.append("")

    if years == 3 and inv.get("more_staff"):
        lines.append("## Growing the business")
        lines.append("")
        lines.append(f"- {_INVESTMENT_LINES['more_staff'].capitalize()}.")
        lines.append("")

    lines.append("## The ask")
    lines.append("")
    lines.append(
        "The owner has handed over the shop's records — till receipts, "
        "supplier invoices, and the monthly ledger — and wants an honest "
        "read of how the business is actually doing, and what, if "
        "anything, should change."
    )
    lines.append("")
    lines.append(
        "*(Generated from settings only — no simulated result appears in "
        "this brief. Edit freely; this is a starting outline, not a "
        "finished case.)*"
    )
    return "\n".join(lines)


def _round_money(x: float) -> str:
    """An owner-plausible rounding, per CASE_WRITING_GUIDE.md's rule that no
    number in the brief should carry more precision than an owner would
    actually carry in his head."""
    if x >= 10_000:
        return f"about {round(x / 1000) * 1000:,.0f} euros"
    return f"about {round(x / 100) * 100:,.0f} euros"
