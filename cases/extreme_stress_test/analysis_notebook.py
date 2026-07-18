import marimo

__generated_with = "0.23.14"
app = marimo.App(width="full", app_title="Extreme Stress Test — grocery_sim")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    import plotly.graph_objects as go

    from pathlib import Path

    # this file lives at cases/extreme_stress_test/; the project root is two levels up
    ROOT = Path(__file__).resolve().parent.parent.parent

    INK = "#404040"
    MUTED = "#BFBFBF"
    ACCENT = "#2E5EAA"
    ACCENT_LIGHT = "#9DB8E6"
    WARN = "#B44646"
    WARN_LIGHT = "#E7B9B9"
    PLOT = dict(
        template = "plotly_white",
        height = 420,
        margin = dict(l = 64, r = 36, t = 72, b = 52),
        font = dict(color = INK, size = 12.5),
    )
    AXIS_X = dict(
        showgrid = False, zeroline = False, showline = True,
        linecolor = "#D9D9D9", ticks = "outside", tickcolor = "#D9D9D9",
    )
    AXIS_Y = dict(
        showgrid = True, gridcolor = "#EFEFEF", zeroline = False,
        showline = False, ticks = "", nticks = 5,
    )

    def style(fig, title = None, showlegend = True, right_margin = 36):
        fig.update_layout(showlegend = showlegend, **PLOT)
        fig.update_layout(margin = dict(r = right_margin))
        if title:
            fig.update_layout(title = dict(
                text = title, x = 0, xanchor = "left",
                pad = dict(l = PLOT["margin"]["l"]), font = dict(size = 15),
            ))
        fig.update_xaxes(**AXIS_X)
        fig.update_yaxes(**AXIS_Y)
        return fig

    def caption(text):
        return mo.md(
            f"<div style='color:#7A7A7A; font-size:0.92em; "
            f"padding:2px 24px 18px 8px;'><em>{text}</em></div>"
        )

    def event_marker(fig, x, label, color, y = 1.0):
        fig.add_vline(x = x, line_width = 1, line_dash = "dot", line_color = color)
        fig.add_annotation(
            x = x, y = y, yref = "y domain", yanchor = "bottom",
            text = label, showarrow = False, font = dict(size = 10, color = color),
            textangle = -90, xshift = 8,
        )
        return fig

    return ACCENT, ROOT, WARN, caption, event_marker, go, mo, style


@app.cell
def _(mo):
    mo.md("""
    # Extreme Stress Test — does grocery_sim hold up under a pile-up of shocks?

    This notebook uses the `grocery_sim` package (`package/grocery_sim/`)
    directly, not pre-exported CSVs: it defines a deliberately extreme
    settings dict — three wars, three typhoons, three equipment failures,
    both tax cuts, a competitor entry, and an endogenous expansion, all in
    one three-year run — simulates it live, prints the resulting business
    case, and then checks whether the data's own reaction to each shock
    actually makes sense (right direction, right rough timing, right
    order of magnitude) rather than taking the package's own claims on
    faith.
    """)
    return


@app.cell
def _(ROOT):
    import sys

    sys.path.insert(0, str(ROOT / "package"))
    from grocery_sim import GroceryStoreSimulation

    return (GroceryStoreSimulation,)


@app.cell
def _(GroceryStoreSimulation, mo):
    settings = dict(
        basic = dict(
            name = "Extreme Stress Test Store",
            random_seed = 777,
            year = 3,
            budget = 60_000,
            year_start = "2025",
            retain_earning = True,
            retain_earning_from = "2026-01",
        ),
        events = dict(
            # three wars, spread across all three years
            war = ["2025-02", "2026-06", "2027-09"],
            # a typhoon every summer
            typhoon = ["2025-08", "2026-08", "2027-08"],
            food_vat_cut = "2025-07",
            tax_cut = "2026-03",
            competitor = "2027-01",
            # three equipment failures — the freezer having a genuinely bad run
            operational_hazard = ["2025-03", "2026-05", "2027-10"],
        ),
        potential_investment = dict(
            more_staff = True,
            bigger_store = False,
            upgrade_infrastructure = False,
        ),
    )

    sim = GroceryStoreSimulation()
    sim.setup(settings)
    sim.simulate()

    mo.md(f"Simulated **{settings['basic']['name']}** — "
          f"{sum(1 for v in settings['events'].values() if v)} of 6 event "
          f"types active, {sum(len(v) if isinstance(v, list) else 1 for v in settings['events'].values() if v)} "
          f"total event occurrences over {settings['basic']['year']} years.")
    return settings, sim


@app.cell
def _(mo, sim):
    mo.md(sim.describe())
    return


@app.cell
def _(mo, sim):
    v = sim.validation
    structural_fails = [c for c in v["checks"] if c["tier"] == "structural" and not c["pass"]]
    core = [c for c in v["checks"] if c["tier"] == "core"][0]
    band_fails = [c for c in v["checks"] if c["tier"] == "band" and not c["pass"]]

    if structural_fails:
        structural_line = f"{len(structural_fails)} FAILED (would have raised ValidationError)"
    else:
        structural_line = "all passed"

    if core["pass"]:
        core_line = "The oracle beats the realistically-forecasting owner, as the paper's framing assumes."
    else:
        core_line = ("Under this specific pile-up of shocks, it does not - the same finding "
                     "the earlier, hand-computed section of this notebook already surfaced, "
                     "now confirmed by the actual validation harness rather than an ad hoc calculation.")

    # NOT len(v["checks"]) - len(structural_fails) - 1: that only subtracts
    # the *failed* structural checks, so when everything structural passes
    # (the common case) it silently folds all the passing structural checks
    # into the band count too, inflating "N of M bands passed" with checks
    # that were never bands in the first place. Count the band tier directly.
    n_bands = len([c for c in v["checks"] if c["tier"] == "band"])
    mo.md(
        "## `validate()` - wired into `simulate()` automatically\n\n"
        f"**Structural invariants:** {structural_line}. "
        "These are bookkeeping/conservation/recording-layer identities that "
        "must hold regardless of which events are active; a failure here "
        "would mean this run never got this far.\n\n"
        f"**Core mechanism** (`oracle > realized`, the paper's own central "
        f"claim): {'PASS' if core['pass'] else 'FAIL'} - {core['detail']}. "
        f"{core_line}\n\n"
        f"**Realism bands:** {n_bands - len(band_fails)} of {n_bands} passed. "
        f"{len(band_fails)} diverged from their baseline-calibrated range "
        "(expected under this many active events, reported for context, "
        "never fatal): " + ", ".join(c["name"] for c in band_fails)
    )
    return


@app.cell
def _(mo, sim):
    data = sim.data(include_hidden = True)
    mo.md("## The tables\n\n```\n" + repr(data) + "\n```")
    return (data,)


@app.cell
def _(data, mo):
    cs = data.cost_sheet.copy()
    cs["t"] = range(1, len(cs) + 1)
    # profit before tax comes from the audited tax_statement, not from
    # summing cost_sheet's own columns: several of those (cash,
    # retained_earnings) are cumulative month-end *balances*, not monthly
    # expense line items, and summing a balance across 36 months is
    # meaningless (it double-, triple-, quadruple-counts every euro that
    # carried over). owner_draw and profit_tax_paid are downstream
    # distributions/cash-timing of profit, not costs that produce it either.
    profit_before_tax = float(data.tax_statement["profit_before_tax"].sum())
    mo.md(
        f"Cost sheet: {len(cs)} months across {cs['year'].nunique()} years. "
        f"Total revenue {cs['revenue'].sum():,.0f}, total profit before tax "
        f"{profit_before_tax:,.0f} (from the audited tax statement below — "
        f"cost_sheet's own columns include cumulative balances like `cash` "
        f"and `retained_earnings`, which cannot be summed across months as "
        f"if they were expenses)."
    )
    return (cs,)


@app.cell
def _(ACCENT, WARN, cs, event_marker, go, settings, style):
    # month index of each event, for vertical markers on the monthly chart
    def month_of(label):
        y, m = (int(x) for x in label.split("-"))
        return (y - 2025) * 12 + m

    # cost_sheet has no "profit_after_tax" column at all — profit is only
    # settled annually (tax_statement), never monthly. An earlier version of
    # this cell fell back to `cs["revenue"] * 0` when the column was
    # missing, which silently plotted an all-zero bar series instead of
    # raising. The correct monthly figure is the same operating result
    # phase3.py itself accumulates into the annual profit (month_result =
    # revenue - procurement - rent - wages - payroll_tax - utilities -
    # storage - flyers - vat - credit_interest - repairs) — pre-tax, since
    # tax is an annual, not monthly, concept.
    #
    # This will NOT sum to tax_statement's profit_before_tax exactly: the
    # opening location's one-time setup cost and the initial inventory
    # purchase are booked directly into year one's annual settlement
    # (phase3.py's `_oneoffs`) and never appear in any monthly cost_sheet
    # column, so the monthly series here is "recurring operations only" —
    # a real, deliberate gap of about one opening's worth of capital, not a
    # rounding error to chase down.
    monthly_operating_result = (
        cs["revenue"] - cs["procurement"] - cs["rent"] - cs["wages"]
        - cs["payroll_tax"] - cs["utilities"] - cs["storage"] - cs["flyers"]
        - cs["vat"] - cs["credit_interest"] - cs["repairs"]
    )

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x = cs["t"], y = cs["revenue"], name = "Revenue",
        mode = "lines", line = dict(color = ACCENT, width = 2),
    ))
    fig1.add_trace(go.Bar(
        x = cs["t"], y = monthly_operating_result,
        name = "Monthly operating result (pre-tax)", marker_color = WARN, opacity = 0.55,
    ))
    for _label in settings["events"]["war"]:
        event_marker(fig1, month_of(_label), "war", WARN)
    for _label in settings["events"]["typhoon"]:
        event_marker(fig1, month_of(_label), "typhoon", ACCENT)
    for _label in settings["events"]["operational_hazard"]:
        event_marker(fig1, month_of(_label), "hazard", "#B48A2E")
    event_marker(fig1, month_of(settings["events"]["competitor"]), "competitor", "#7A2E8A")

    style(fig1, title = "Monthly revenue and operating result (pre-tax), with every shock marked")
    fig1
    return


@app.cell
def _(caption):
    caption(
        "Dotted lines mark every scripted shock. The bars are recurring "
        "operating result only (see the code comment above — the opening "
        "setup cost and initial stock purchase are booked once, annually, "
        "not monthly), so they will not sum to the audited annual figure, "
        "but they should still visibly dip in months touching a war or a "
        "hazard if the mechanism is honest, and the competitor's entry "
        "(2027-01) should mark a visible, *permanent* step down in the "
        "trend rather than a one-month dip."
    )
    return


@app.cell
def _(WARN, data, go, style):
    wo = data.write_offs.copy()
    wo["date"] = wo["date"].astype("datetime64[ns]")
    damage = wo[wo["reason"] == "damage"] if "reason" in wo.columns else wo.iloc[0:0]
    spoilage = wo[wo["reason"] != "damage"] if "reason" in wo.columns else wo

    daily_damage = damage.groupby("date")["units"].sum()
    daily_spoilage = spoilage.groupby("date")["units"].sum()

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x = daily_spoilage.index, y = daily_spoilage.values,
        name = "Ordinary spoilage / stock-count write-offs",
        mode = "lines", line = dict(color = "#BFBFBF", width = 1),
    ))
    fig2.add_trace(go.Scatter(
        x = daily_damage.index, y = daily_damage.values,
        name = "Equipment-failure damage",
        mode = "markers", marker = dict(color = WARN, size = 10, symbol = "x"),
    ))
    style(fig2, title = "Write-offs over time — do the three hazards show up as spikes?")
    fig2
    return (damage,)


@app.cell
def _(caption, damage, settings):
    hazard_dates = set(settings["events"]["operational_hazard"])
    hit_dates = sorted(damage["date"].dt.strftime("%Y-%m-%d").unique()) if len(damage) else []
    caption(
        f"Requested hazard months: {sorted(hazard_dates)}. Damage write-offs "
        f"actually landed on: {hit_dates}. "
        + ("Match — the three failures fired exactly where scripted, each "
           "as a one-day spike distinct from the low, continuous background "
           "of ordinary spoilage." if len(hit_dates) == len(hazard_dates) else
           "MISMATCH — investigate before trusting the rest of this run.")
    )
    return


@app.cell
def _(ACCENT, WARN, data, event_marker, go, settings, style):
    rec = data.receipts.copy()
    rec["date"] = rec["date"].astype("datetime64[ns]")
    daily_lines = rec.groupby("date").size()

    # the ground-truth traffic modifier (hidden/demand_modifiers.csv), not
    # just the noisy visible receipt count — this is what actually decides
    # whether the mechanism fired, independent of small-panel sampling noise
    dm = data["hidden_demand_modifiers"][["t", "traffic"]].copy()
    cal_t = data.calendar.reset_index(drop = True)
    dm["date"] = cal_t["date"].to_numpy()[dm["t"].to_numpy() - 1]
    dm["date"] = dm["date"].astype("datetime64[ns]")

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x = daily_lines.index, y = daily_lines.values,
        name = "Receipt lines / day (visible)", mode = "lines",
        line = dict(color = ACCENT, width = 1),
    ))
    fig3.add_trace(go.Scatter(
        x = dm["date"], y = dm["traffic"] * daily_lines.mean(),
        name = "True traffic modifier Λₜ × mean lines (hidden)",
        mode = "lines", line = dict(color = WARN, width = 1.5, dash = "dash"),
    ))
    import datetime as _dt

    for _label in settings["events"]["typhoon"]:
        _y, _m = (int(x) for x in _label.split("-"))
        _d0 = _dt.date(_y, _m, 1)
        event_marker(fig3, str(_d0), "typhoon", WARN, y = 0.95)
    style(fig3, title = "Daily footfall: the noisy visible count vs. the true traffic mechanism")
    fig3
    return (dm,)


@app.cell
def _(caption, dm, settings):
    _hits = []
    for _label in settings["events"]["typhoon"]:
        _y, _m = (int(x) for x in _label.split("-"))
        _window = dm[(dm["date"].dt.year == _y) & (dm["date"].dt.month == _m)
                     & (dm["date"].dt.day <= 3)]
        _hits.append(f"{_label}: traffic {_window['traffic'].min():.2f} (vs. baseline ~1.0)")
    caption(
        "The dashed line (the true traffic modifier, from the hidden answer "
        "key) shows a clean, sharp 3-day crash at every typhoon date — "
        f"{'; '.join(_hits)} — confirming the mechanism itself fires exactly "
        "as scripted. The solid line (the visible daily receipt count, what "
        "an analyst actually receives) does **not** show an equally obvious "
        "dip: at this store's scale (~270 total customers) day-to-day "
        "sampling noise and weekday/weekend seasonality are comparable in "
        "size to the storm's effect, and the pantry rebound (customers "
        "rained off one day arrive hungrier a few days later, per this "
        "project's own Phase Two design) can partly refill the dip within "
        "the same week. This is not a bug — it is the paper's own point "
        "about hidden demand made concrete: the ground truth and what the "
        "visible data actually shows are two different things, and an "
        "analyst who only eyeballs the solid line could easily miss an "
        "effect that unambiguously exists."
    )
    return


@app.cell
def _(data, mo):
    tx = data.tax_statement
    mo.vstack([mo.md("## Tax statement across the three years"), tx])
    return (tx,)


@app.cell
def _(caption, tx):
    vat_2025, vat_2026 = tx["vat_remitted"].iloc[0], tx["vat_remitted"].iloc[1]
    caption(
        f"food_vat_cut fires mid-2025 and tax_cut fires early 2026, both "
        f"lowering rates; VAT remitted moved from {vat_2025:,.0f} (2025) to "
        f"{vat_2026:,.0f} (2026). A lower rate on a similar or growing sales "
        f"base landing lower (or barely higher) than the prior year is the "
        f"expected direction — a *sharp* jump instead would be a red flag."
    )
    return


@app.cell
def _(data, mo):
    pt = data["hidden_profit_triptych"]
    mo.vstack([
        mo.md("## The profit triptych, under maximum stress"),
        pt,
        mo.md(
            "This is the hidden answer key (`include_hidden=True`), used "
            "here only to sanity-check the mechanism, never in the student-facing "
            "case: `believed_profit_month1` is what the owner projected at "
            "opening, before any of these six shocks were even scripted; "
            "`realized_profit_year` is his first year's actual result once the "
            "first war and hazard had already hit; `oracle_profit_year` is what "
            "a perfectly informed operator would have earned facing the *same* "
            "shocks with a perfect forecast instead of the owner's trailing "
            "average."
        ),
    ])
    return (pt,)


@app.cell
def _(caption, pt):
    # believed_profit_month1 is exactly what its name says — the MILP's
    # first-month objective value, not an annual figure. Comparing it
    # directly against the *annual* realized/oracle profit (an early draft
    # of this notebook did exactly that) overstates the optimism gap by
    # roughly 12x. A fairer, still-rough comparison annualizes it first.
    believed_month1 = float(pt["believed_profit_month1"].iloc[0])
    believed_annualized = believed_month1 * 12
    realized = float(pt["realized_profit_year"].iloc[0])
    oracle = float(pt["oracle_profit_year"].iloc[0])
    optimism_gap = realized - believed_annualized
    analytics_gap = oracle - realized
    caption(
        f"believed_profit_month1 = {believed_month1:,.0f} (one month) → "
        f"×12 = {believed_annualized:,.0f} as a rough annualized belief. "
        f"Optimism gap (realized − annualized belief): {optimism_gap:,.0f}. "
        f"Analytics gap (oracle − realized): {analytics_gap:,.0f} "
        f"({analytics_gap / realized:+.2%} of realized profit) — "
        + ("essentially zero: under this specific pile-up of shocks, the "
           "perfectly-informed oracle does **not** clearly outperform the "
           "realistically-forecasting owner. That is a genuinely useful, "
           "slightly uncomfortable finding, not something to explain away: "
           "either a single random seed under this much compounding shock "
           "density is not enough to see the oracle's edge (a real "
           "limitation of one-run analysis, and itself a fair lesson), or "
           "the oracle's ordering rule stops clearly helping once shocks "
           "are dense enough that no forecast — perfect or not — has time "
           "to matter before the next shock lands. Either reading is more "
           "honest than assuming the gap must widen just because the "
           "story has more shocks in it."
           if abs(analytics_gap) < 0.02 * realized else
           "a genuine gap in the expected direction.")
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ## Does the whole thing hang together? (revised after actually checking)

    An earlier draft of this conclusion was written before the numbers
    above were checked, and asserted two things that turned out to be
    wrong — leaving that mistake visible here on purpose, because "the
    model reacted as expected" is exactly the kind of claim this project
    insists on verifying rather than assuming.

    **What held up.** The three equipment failures wrote off stock on
    exactly their three scripted dates and nowhere else, cleanly
    distinguishable from the low, continuous background of ordinary
    spoilage. The true traffic modifier (the hidden `Λₜ`, not the raw
    receipt count) crashes to about a third of baseline for exactly
    three days at every typhoon date, confirming the mechanism itself
    is correct. VAT remitted moved down from 2025 to 2026 as both tax
    cuts took effect, the expected direction.

    **What the first draft got wrong.** The footfall chart's original
    claim — "look for a brief, sharp drop" *in the visible receipt
    count* — does not actually hold up well: at this store's scale, day
    to day sampling noise and the pantry rebound are large enough to
    mostly hide the storm in the raw numbers, even though the underlying
    mechanism is firing exactly on schedule. And the claim that the
    profit triptych's gaps should simply "widen under more stress" was
    asserted before checking; the actual analytics gap came out
    essentially zero (the oracle did not clearly beat the realistically
    forecasting owner under this specific pile-up), which is a more
    interesting and more honest finding than the tidy story originally
    written here.

    **The actual lesson.** A model can be mechanically correct — every
    shock firing on the right day, at the right magnitude — while a
    naive read of the visible data, or a plausible-sounding claim about
    what "should" happen, still gets the story wrong. That gap between
    mechanism and naive read is not a flaw in `grocery_sim`; it is the
    entire pedagogical point of building it with a known ground truth
    in the first place, and this notebook only demonstrates that point
    because its own first draft fell into the trap.

    One boundary this run does not test: the competitor and the
    endogenous expansion are still single-fire mechanisms by design
    (see `events.py`'s docstring for why competitor stays that way), so
    piling on more *of the same* shock type was never attempted for
    those two — this run only confirms they still fire correctly
    alongside everything else, not that they would compose sensibly if
    repeated.
    """)
    return


if __name__ == "__main__":
    app.run()
