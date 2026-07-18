"""The business-case brief generator.

Two rules govern everything here, both from documents/CASE_WRITING_GUIDE.md:

1. **The epistemic firewall.** The brief is written entirely inside the
   owner's own information set: something they could have observed (a bill
   they paid, a shop opening down the street, their own year-end revenue),
   never a mechanism (a modifier, a defection parameter, a hidden true
   cause). Every number that appears is rounded the way an owner would
   actually round it in their head — never the simulator's own
   floating-point precision.

2. **Every trait is load-bearing.** `persona.py` invents cosmetic identity
   only (a name, a gender/pronoun, a town, a prior career). Every actual
   story beat here — which events happened, what they cost, whether an
   investment paid for itself, even the records caveats in the intake
   interview — is derived from this run's own settings and its own real
   exported tables, never invented. Two runs with different seeds get two
   genuinely different owners telling two genuinely different, true stories.

The "misguide": real small businesses often fixate on the most visible
cause of a bad year (a competitor opening, a supply shock) when the actual
dominant driver is something quieter (a capital decision, a lease term).
`simulation.py`'s `describe()` grounds this honestly rather than asserting
it: it silently runs one counterfactual twin (same settings and seed, the
most salient blamed event removed) and passes this module a `misguide`
dict reporting whether removing that event would actually have recovered
most of the shortfall. This module never prints that computation's number
— it only uses it to decide how hedged the owner's closing conviction reads.
"""

from __future__ import annotations

import itertools

import pandas as pd

from .params import PHASE5

_EVENT_LINES = {
    "war": "a sudden jump in wholesale costs, reported as coming from a "
           "conflict-driven supply squeeze reaching almost every shelf",
    "typhoon": "a short, severe storm that kept customers home for a few days "
               "and roughed up the fresh and seafood deliveries that week",
    "food_vat_cut": "a government tax cut on food, announced ahead of time, "
                     "that eventually showed up in some of the shelf prices",
    "tax_cut": "a broader tax cut on non-food goods, announced ahead of time",
    "tax_raise": "a new government levy on shop revenue, announced ahead of time",
    "competitor": "a discount grocer opening a short walk away",
    "operational_hazard": "an overnight equipment failure",
}

# short noun-phrase per misguide-eligible event, for slots (like "the
# questions") where the full _EVENT_LINES clause would read as a run-on —
# only needs entries for pick_misguide_candidate's three possible events
_EVENT_SHORT_LABEL = {
    "war": "the cost spike",
    "competitor": "the competitor",
    "operational_hazard": "the equipment failure",
}

_INVESTMENT_LINES = {
    "more_staff": "hired my first employee and extended the opening hours",
    "bigger_store": "rebuilt the shelving for deeper stock",
    "upgrade_infrastructure": "put in a better freezer and cold-chain setup",
}

_INVESTMENT_CATALOG_Q = {
    "more_staff": "Was hiring worth it?",
    "bigger_store": "Did the extra shelf space actually pay for itself?",
    "upgrade_infrastructure": "Did the freezer upgrade actually cut my losses?",
}

# table name -> a one-line, owner-plausible description of what it holds.
# only tables actually present in `tables.keys()` are ever listed, so this
# stays correct even if the export changes which tables it writes.
_DATA_DESCRIPTIONS = {
    "receipts": "every till line: date, hour, product, quantity, unit price, "
                "payment type; card payments carry a stable but anonymized "
                "customer code; voided lines and refunds reference the "
                "original line",
    "price_history": "every shelf-tag change, per product",
    "promotions": "markdown campaigns: dates, depth, category",
    "procurement": "supplier invoice lines: order/delivery/posted dates, "
                   "quantity, unit cost",
    "inventory_eod": "end-of-day book stock per product",
    "write_offs": "everything binned, with a reason",
    "cost_sheet": "the monthly ledger, authoritative for money: revenue, "
                  "procurement, rent, wages, utilities, VAT remitted, "
                  "capital spend, tax payments",
    "tax_statement": "the annual filings",
    "calendar": "the trading calendar",
    "weather": "the shop's own temperature and rainfall log",
    "locations": "the site-scouting notes from before opening",
}


def _investment_capex() -> dict:
    fin = PHASE5["finance"]
    return {
        "more_staff": fin["expansion_capex"],
        "bigger_store": fin["shelf_capex"],
        "upgrade_infrastructure": fin["infra_capex"],
    }


def _decompose_capex(total: float, allowed: list[str]) -> list[str]:
    """Which investment(s) account for a month's capex total — matched
    exactly against each investment's own calibrated constant, since two
    investments firing in the same month simply sum. All three constants
    (14,000 / 6,000 / 5,000) and their pairwise/triple sums are distinct,
    so an exact match is never ambiguous."""
    consts = _investment_capex()
    candidates = [k for k in allowed if k in consts]
    for r in range(1, len(candidates) + 1):
        for combo in itertools.combinations(candidates, r):
            if abs(sum(consts[c] for c in combo) - total) < 1.0:
                return list(combo)
    return []


def _round_money(x: float) -> str:
    """An owner-plausible rounding: no number in the brief should carry
    more precision than an owner would actually carry in their head.
    Below 1,000 this rounds to the nearest 10 rather than the nearest
    100 — coarser than that would routinely collapse a genuine ~10-15%
    rent step (typically a few hundred euros) into the same displayed
    figure on both sides of a "from X to Y" comparison."""
    x = abs(x)
    if x >= 10_000:
        step = 1000
    elif x >= 1_000:
        step = 100
    else:
        step = 10
    return f"about {round(x / step) * step:,.0f} euros"


def _round_pct(x: float) -> str:
    return f"{round(x * 100):.0f} percent"


def _cap_first(s: str) -> str:
    """Capitalize only the first character, leaving the rest untouched —
    str.capitalize() also lowercases the rest, which mangles a mid-sentence
    "I" (as in "...on top of the stock I lost")."""
    return s[:1].upper() + s[1:] if s else s


def _result_phrase(result: float) -> str:
    return (
        "a loss" if result < -500
        else "almost exactly nothing" if abs(result) <= 500
        else "a real profit"
    )


def pick_misguide_candidate(events: dict) -> str | None:
    """The most visible, most emotionally salient active event — the one a
    real owner would fixate on, whether or not the data agrees. Priority:
    a competitor (impossible to ignore, walks past the window), then the
    most recent war shock, then the most recent operational hazard."""
    if events.get("competitor"):
        return "competitor"
    for key in ("war", "operational_hazard"):
        val = events.get(key)
        if val:
            return key
    return None


def _active_events(ev: dict) -> list[tuple[str, str]]:
    out = []
    for k, v in ev.items():
        if v is None:
            continue
        dates = v if isinstance(v, list) else [v]
        out.extend((k, d) for d in dates)
    return out


def _investment_dates(cs, allowed_investments: list[str]) -> dict[str, str]:
    capex_rows = cs[cs["capex"] > 0] if "capex" in cs.columns else cs.iloc[0:0]
    out: dict[str, str] = {}
    for _, row in capex_rows.iterrows():
        fired = _decompose_capex(float(row["capex"]), allowed_investments)
        label = f"{int(row['year'])}-{int(row['month']):02d}" if "year" in row else f"month {int(row['month'])}"
        for name in fired:
            out[name] = label
    return out


def _event_sentence(key: str, date: str, cs) -> str:
    """The bare clause describing one event (no "Around DATE," prefix, no
    trailing period) — shared by the top-level timeline and the per-year
    intake narrative, so the two never drift out of sync."""
    sentence = _EVENT_LINES.get(key, f"an event ('{key}')")
    if key == "operational_hazard":
        # owner-knowable exactly: they paid the repair invoice themself.
        # date is in the story's own year_start-relative labeling, matched
        # directly against cost_sheet's year/month (subject to the same
        # year_start caveat as the rest of the package — see events.py's
        # module docstring).
        event_year, event_month = int(date[:4]), int(date[5:7])
        month_repairs = cs[(cs["year"] == event_year) & (cs["month"] == event_month)] \
            if "year" in cs.columns else cs.iloc[0:0]
        repair_cost = float(month_repairs["repairs"].iloc[0]) \
            if len(month_repairs) and "repairs" in cs.columns else 0.0
        if repair_cost > 0:
            sentence = (f"{sentence} that cost me {_round_money(repair_cost)} "
                        f"to fix, on top of the stock I lost")
    return sentence


def _event_beat(key: str, date: str, cs) -> str:
    return f"Around {date}, {_event_sentence(key, date, cs)}."


def _records_caveats(tables) -> list[str]:
    """Honest, owner-observable imperfections — computed straight from the
    visible exported tables, never from the hidden answer key. These are
    real artifacts of the recording layer (recording.py / P3 §20), not
    invented color: an owner filing their own paperwork really would
    notice a doubled receipt or a gap in the weather log."""
    notes = []
    if "receipts" in tables.keys():
        rc = tables.receipts
        if "ref_receipt_id" in rc.columns and "qty" in rc.columns:
            void_n = int(((rc["qty"] < 0) & rc["ref_receipt_id"].isna()).sum())
            if void_n > 0:
                notes.append(
                    f"the till terminal mis-rings an item now and then — I "
                    f"void it and re-ring it, so you'll find {void_n} "
                    f"paired correction lines in the receipts over the "
                    f"whole period, nothing missing, just messy"
                )
    if "procurement" in tables.keys():
        dpr = tables.procurement
        inv_key = [c for c in ("uid", "qty", "unit_cost", "order_date", "delivery_date")
                   if c in dpr.columns]
        if len(inv_key) == 5:
            dupe_groups = dpr.groupby(inv_key).size()
            n_dupe = int((dupe_groups > 1).sum())
            if n_dupe > 0:
                plural = "duplicate" if n_dupe == 1 else "duplicates"
                notes.append(
                    f"my supplier's system has posted the same invoice twice "
                    f"before — I caught {n_dupe} such {plural} myself, but "
                    f"I'll admit I don't check every single one"
                )
        notes.append(
            "some delivery paperwork never got typed in — there were weeks "
            "I was alone and exhausted, and I paid the supplier for goods "
            "you won't find an invoice line for; my bank-account ledger is "
            "still right, I just can't always show you the paper behind it"
        )
    if "weather" in tables.keys() and "temp_C" in tables.weather.columns:
        w_null = int(tables.weather["temp_C"].isna().sum())
        if w_null > 0:
            notes.append(
                f"the little weather log I keep goes dark for a few days "
                f"now and then — {w_null} missing day(s) over the whole "
                f"period — the station on the roof is nothing fancy"
            )
    return notes


def build_brief(
    settings: dict,
    persona: dict,
    tables,
    misguide: dict | None = None,
) -> str:
    b, ev, inv = settings["basic"], settings["events"], settings["potential_investment"]
    years = b["year"]
    shop_name = f"{persona['owner_name'].split()[-1]}'s Market"
    misguide = misguide or {"candidate": None, "grounded": None}
    pn = persona["pronoun"]

    cs = tables.cost_sheet
    tx = tables.tax_statement

    lines: list[str] = []
    lines.append(f"# {shop_name} — Engagement Brief")
    lines.append("")
    lines.append(
        f"*Client: {persona['owner_name']}, owner, {shop_name}, "
        f"{persona['street']}, {persona['town']}.*"
    )
    lines.append("")

    # ---------------------------------------------------------------- shared
    span = "one year" if years == 1 else f"{years} years"
    final_year_result = float(tx["profit_after_tax"].iloc[-1])
    total_revenue = float(cs["revenue"].sum())
    result_phrase = _result_phrase(final_year_result)
    candidate = misguide.get("candidate")

    active_events = _active_events(ev)
    allowed_investments = [k for k, v in inv.items() if v]
    investment_dates = _investment_dates(cs, allowed_investments)

    yearly_revenue = (
        cs.groupby("year")["revenue"].sum().sort_index()
        if "year" in cs.columns else None
    )

    # ---------------------------------------------------------------- letter
    lines.append("## The letter")
    lines.append("")
    lines.append("> Dear analyst,")
    lines.append(">")
    lines.append(
        f"> I'm {persona['age']}. I spent {persona['prior_years']} years "
        f"working for {persona['prior_employer']} before I opened "
        f"{shop_name} myself, on {persona['street']} in {persona['town']}, "
        f"with {_round_money(float(b['budget']))} of my own money behind "
        f"it. That was {b['year_start']}."
    )
    lines.append(">")
    if yearly_revenue is not None and len(yearly_revenue) > 1:
        first_yr_rev = float(yearly_revenue.iloc[0])
        last_yr_rev = float(yearly_revenue.iloc[-1])
        trend = (
            "our best year yet" if last_yr_rev > first_yr_rev * 1.03
            else "our worst year yet" if last_yr_rev < first_yr_rev * 0.97
            else "about where we started"
        )
        lines.append(
            f"> We started small — {_round_money(first_yr_rev)} through the "
            f"till that first year. By last year we took in "
            f"{_round_money(last_yr_rev)}, {trend}."
        )
        lines.append(">")
    if candidate:
        blame_phrase = _EVENT_LINES.get(candidate, candidate)
        lines.append(
            f"> Over {span} we have taken in {_round_money(total_revenue)} "
            f"across the till altogether, and the bottom line came out to "
            f"{result_phrase}. I think I know why: {blame_phrase}. I want "
            f"someone who isn't me to look at my numbers properly before I "
            f"decide what to do next."
        )
    else:
        lines.append(
            f"> Over {span} we have taken in {_round_money(total_revenue)} "
            f"across the till altogether, and the bottom line came out to "
            f"{result_phrase}. I want someone who isn't me to look at my "
            f"numbers properly before I decide what to do next."
        )
    lines.append(">")
    lines.append(f"> — {persona['owner_name']}")
    lines.append("")

    # ------------------------------------------------------ intake interview
    lines.append("## Intake interview notes")
    lines.append("")
    lines.append(f"*In {persona['owner_name']}'s own words.*")
    lines.append("")

    Subj = pn["subject"].capitalize()

    lines.append("**Q: Tell me about yourself and how the shop started.**")
    lines.append("")
    lines.append(
        f"{Subj}: I'm {persona['age']}. I spent {persona['prior_years']} "
        f"years working for {persona['prior_employer']} before deciding to "
        f"open my own place. I had {_round_money(float(b['budget']))} "
        f"saved, and I took a spot on {persona['street']}, in "
        f"{persona['town']}. We opened in {b['year_start']}."
    )
    lines.append("")

    lines.append("**Q: What kind of shop is it?**")
    lines.append("")
    n_sku = int(tables.price_history["uid"].nunique()) \
        if "price_history" in tables.keys() and "uid" in tables.price_history.columns else None
    card_share = None
    if "receipts" in tables.keys() and "payment" in tables.receipts.columns:
        _pay = tables.receipts["payment"]
        if len(_pay):
            card_share = float((_pay == "card").mean())
    shop_desc = "A full grocery, small format"
    if n_sku:
        shop_desc += f" — about {n_sku} products on the shelf at any time"
    lines.append(
        f"{Subj}: {shop_desc}. People come because we're close and we have "
        f"what they need — that's the whole business." +
        (f" I'd guess close to {_round_pct(card_share)} of what we take is "
         f"by card, the rest cash." if card_share else "")
    )
    lines.append("")

    lines.append("**Q: Walk me through the routine.**")
    lines.append("")
    delivery_note = ""
    if "procurement" in tables.keys() and "delivery_date" in tables.procurement.columns:
        _dd = pd.to_datetime(tables.procurement["delivery_date"])
        if len(_dd):
            weekday = _dd.dt.day_name().mode().iloc[0]
            delivery_note = f" Deliveries come every {weekday}, one truck."
    hiring_note = ""
    if "more_staff" in investment_dates:
        hiring_note = (f" Since {investment_dates['more_staff']} I've had "
                        f"an extra pair of hands and longer hours.")
    lines.append(
        f"{Subj}: Same routine most weeks.{delivery_note} I do the "
        f"shelf prices myself, only when they've genuinely drifted."
        f"{hiring_note}"
    )
    lines.append("")

    # the lease step is a fixed part of the three-year story, never a
    # settings.events toggle — narrated inside the year-3 answer below,
    # only if it actually shows up
    lease_beat = None
    if years == 3 and "year" in cs.columns:
        y2026 = cs[cs["year"] == 2026]["rent"]
        y2027 = cs[cs["year"] == 2027]["rent"]
        if len(y2026) and len(y2027) and float(y2027.iloc[0]) > float(y2026.iloc[-1]):
            before, after = float(y2026.iloc[-1]), float(y2027.iloc[0])
            pct = after / before - 1
            lease_beat = (
                "2027-01-01",
                f"my lease renewed and the rent went up {_round_pct(pct)}, "
                f"from {_round_money(before)} to {_round_money(after)} a month",
            )

    if yearly_revenue is not None and len(yearly_revenue) > 1:
        for yr in yearly_revenue.index:
            yr = int(yr)
            lines.append(f"**Q: And {yr}?**")
            lines.append("")
            # events and investments interleaved and sorted by date, so the
            # narrative follows the order things actually happened in, not
            # the settings dict's own key order
            yr_beats: list[tuple[str, str]] = [
                (d, _event_sentence(k, d, cs)) for k, d in active_events if d[:4] == str(yr)
            ]
            for name, date in investment_dates.items():
                if date[:4] == str(yr):
                    yr_beats.append((date, f"I {_INVESTMENT_LINES[name]}, paying "
                                            f"{_round_money(_investment_capex()[name])} from savings"))
            if lease_beat is not None and lease_beat[0][:4] == str(yr):
                yr_beats.append(lease_beat)
            yr_beats.sort(key=lambda x: x[0])
            beats = [sentence for _, sentence in yr_beats]
            yr_rev = float(yearly_revenue.loc[yr])
            narrative = f"{Subj}: "
            if beats:
                narrative += _cap_first("; ".join(beats)) + f". We took in {_round_money(yr_rev)} that year."
            else:
                narrative += f"A quiet year. We took in {_round_money(yr_rev)}."
            lines.append(narrative)
            lines.append("")

    lines.append("**Q: What do you think happened?**")
    lines.append("")
    if candidate:
        lines.append(
            f"{Subj}: {_cap_first(_EVENT_LINES.get(candidate, candidate))}. "
            f"I don't need a consultant to see it. That's what I want you "
            f"to check with the numbers."
        )
    else:
        lines.append(
            f"{Subj}: Honestly, no single villain. I just want to "
            f"understand the business properly."
        )
    lines.append("")

    lines.append("**Q: Anything I should know about the records before you start?**")
    lines.append("")
    caveats = _records_caveats(tables)
    if caveats:
        if len(caveats) == 1:
            lines.append(f"{Subj}: Yes — {caveats[0]}.")
        else:
            _ordinals = ["First", "Second", "Third", "Fourth", "Fifth"]
            intro = "Yes, be careful with a couple of things." if len(caveats) == 2 \
                else f"Yes, be careful with {len(caveats)} things."
            caveat_sentences = " ".join(
                f"{_ordinals[i]}, {caveats[i]}."
                for i in range(len(caveats))
            )
            lines.append(f"{Subj}: {intro} {caveat_sentences}")
    else:
        lines.append(f"{Subj}: Not really — my books are as clean as I can make them.")
    lines.append("")

    lines.append("**Q: What does a useful answer look like to you?**")
    lines.append("")
    lines.append(
        f"{Subj}: Pages I can read. A number, and how sure you are behind "
        f"it. Don't be polite about it either."
    )
    lines.append("")

    # ------------------------------------------------------------- the data
    lines.append("## The data")
    lines.append("")
    lines.append(
        f"{persona['owner_name']} hands over complete records for the full "
        f"{span}:"
    )
    lines.append("")
    lines.append("| File | What it is |")
    lines.append("|---|---|")
    for name in tables.keys():
        if name in _DATA_DESCRIPTIONS:
            lines.append(f"| `{name}` | {_DATA_DESCRIPTIONS[name]} |")
    lines.append("")

    # -------------------------------------------------------- the questions
    lines.append("## The questions")
    lines.append("")
    q = []
    q.append("Show me where the money actually goes.")
    if years == 3:
        q.append("Am I really growing, or does it just feel that way?")
    q.append("What is the shrinkage costing me, and should I be worried about theft?")
    if candidate:
        q.append(f"What did {_EVENT_SHORT_LABEL.get(candidate, candidate)} actually cost me?")
    for name in investment_dates:
        if name in _INVESTMENT_CATALOG_Q:
            q.append(_INVESTMENT_CATALOG_Q[name])
    if years == 3:
        q.append("Which customers am I losing, and who replaced them?")
        q.append("What should I expect next year to look like if nothing changes?")
    q.append("What should I actually do next?")
    for i, question in enumerate(q, start = 1):
        lines.append(f"{i}. \"{question}\"")
    lines.append("")

    # --------------------------------------------------------------- stakes
    lines.append("## Stakes")
    lines.append("")
    if candidate and misguide.get("grounded") is False:
        lines.append(
            f"{persona['owner_name']} is convinced {pn['subject']} knows "
            f"the answer. {pn['subject'].capitalize()} may be right. "
            f"{pn['subject'].capitalize()} may not be — and the difference "
            f"matters more than {pn['possessive']} confidence suggests."
        )
    elif candidate:
        lines.append(
            f"{persona['owner_name']}'s instinct points at one clear cause. "
            f"Whether the numbers agree exactly, and by how much, is the "
            f"question worth pricing precisely rather than assuming."
        )
    else:
        lines.append(
            f"{persona['owner_name']} has no single villain in mind — just "
            f"a business {pn['subject']} wants understood properly before "
            f"deciding what, if anything, to change."
        )
    lines.append("")
    lines.append(
        "*(This brief is generated from this run's own settings and its "
        "own real results — no hidden simulation parameter appears above. "
        "Edit freely; this is a starting outline, not a finished case.)*"
    )
    return "\n".join(lines)
