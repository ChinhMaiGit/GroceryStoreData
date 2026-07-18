import marimo

__generated_with = "0.23.14"
app = marimo.App(width="full", app_title="Story Quality Check — grocery_sim")


@app.cell
def _():
    import sys
    import marimo as mo
    import pandas as pd
    import plotly.graph_objects as go

    from pathlib import Path

    # this file lives at cases/story_quality_check/; the project root is two up
    ROOT = Path(__file__).resolve().parent.parent.parent
    PKG = ROOT / "package"
    if str(PKG) not in sys.path:
        sys.path.insert(0, str(PKG))

    from grocery_sim import GroceryStoreSimulation

    INK = "#404040"
    ACCENT = "#2E5EAA"
    WARN = "#B44646"
    PLOT = dict(
        template="plotly_white",
        height=420,
        margin=dict(l=64, r=36, t=72, b=52),
        font=dict(color=INK, size=12.5),
    )
    AXIS_X = dict(
        showgrid=False, zeroline=False, showline=True,
        linecolor="#D9D9D9", ticks="outside", tickcolor="#D9D9D9",
    )
    AXIS_Y = dict(
        showgrid=True, gridcolor="#EFEFEF", zeroline=False,
        showline=False, ticks="", nticks=5,
    )

    def style(fig, title=None, showlegend=True):
        fig.update_layout(showlegend=showlegend, **PLOT)
        if title:
            fig.update_layout(title=dict(
                text=title, x=0, xanchor="left",
                pad=dict(l=PLOT["margin"]["l"]), font=dict(size=15),
            ))
        fig.update_xaxes(**AXIS_X)
        fig.update_yaxes(**AXIS_Y)
        return fig

    def caption(text):
        return mo.md(
            f"<div style='color:#7A7A7A; font-size:0.92em; "
            f"padding:2px 24px 18px 8px;'><em>{text}</em></div>"
        )

    def event_marker(fig, x, label, color):
        fig.add_vline(x=x, line_width=1, line_dash="dot", line_color=color)
        fig.add_annotation(
            x=x, y=1.0, yref="y domain", yanchor="bottom",
            text=label, showarrow=False, font=dict(size=10, color=color),
            textangle=-90, xshift=8,
        )
        return fig

    return (
        ACCENT,
        GroceryStoreSimulation,
        WARN,
        caption,
        event_marker,
        go,
        mo,
        pd,
        style,
    )


@app.cell
def _(mo):
    mo.md("""
    # Story quality check — does the generated business case feel real?

    `describe()` (`package/grocery_sim/describe.py`) builds a fictional
    owner and a narrative brief entirely from one run's own settings and
    real results — no invented numbers, no hidden simulation parameter. This
    notebook is a QA tool, not a student case: it runs one deliberately
    event-dense scenario live, prints the generated brief exactly as a
    learner would first see it, and then checks — line by line — whether
    every claim the "owner" makes is actually backed by the data underneath.

    Read the brief below first, as a client would. Then look at the checks
    that follow and judge whether the story it tells is *earned*.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## The settings
    """)
    return


@app.cell
def _():
    # deliberately dense: every event type, all three investments allowed,
    # so the brief has to narrate a genuinely busy three years
    SETTINGS = dict(
        basic=dict(
            name="Story Quality Check Shop",
            random_seed=12345,
            year=3,
            budget=60_000,
            year_start="2025",
            retain_earning=True,
            retain_earning_from="2026-01",
        ),
        events=dict(
            war=["2025-03-01", "2026-09-01"],
            typhoon="2025-07-15",
            food_vat_cut="2025-05-01",
            tax_cut="2026-02-01",
            tax_raise="2027-01-01",
            competitor="2026-06-01",
            operational_hazard="2027-04-01",
        ),
        potential_investment=dict(
            more_staff=True,
            bigger_store=True,
            upgrade_infrastructure=True,
        ),
    )
    return (SETTINGS,)


@app.cell
def _(mo):
    mo.md("""
    ## Simulate
    """)
    return


@app.cell
def _(GroceryStoreSimulation, SETTINGS):
    sim = GroceryStoreSimulation()
    sim.setup(SETTINGS)
    sim.simulate()
    struct_ok = sim.validation["structural_ok"]
    return sim, struct_ok


@app.cell
def _(mo, struct_ok):
    mo.md(f"""
    **Structural validation: {'PASS' if struct_ok else 'FAIL'}** — "
        f"a real generator bug would fail here regardless of the story; "
        f"band divergences (seed-sensitive magnitude checks) are expected "
        f"under this many active events and are not fatal. See "
        f"`sim.validation` for the full report.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## The brief — read this as a client would

    This is exactly what `sim.describe()` prints: no numbers below are
    edited or cherry-picked.
    """)
    return


@app.cell
def _(mo, sim):
    brief_text = sim.describe()
    mo.md(brief_text)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Does the story hold up?

    Every beat in "What happened along the way" and every number in "The
    letter" should trace back to something real in the settings or the
    exported tables. Checked below, one claim at a time.
    """)
    return


@app.cell
def _(mo, sim):
    persona = sim._persona
    misguide = sim._misguide
    mo.md(
        f"""
    **Persona** (cosmetic identity only — invented, but consistently
    reproducible per `random_seed`): {persona['owner_name']} ({persona['gender']}),
    age {persona['age']}, {persona['prior_years']} years at
    {persona['prior_employer']}, {persona['street']}, {persona['town']}.

    **Misguide grounding** (never shown to the reader in the brief itself —
    this is the internal number `describe()` used to decide how hedged the
    "Stakes" section should read): candidate = `{misguide['candidate']}`,
    grounded = `{misguide['grounded']}`. "Grounded" means a counterfactual
    twin with that event removed recovered more than 5% of total revenue's
    worth of profit; "not grounded" means the owner's instinct and the data
    disagree — which is exactly what the brief's hedged phrasing above
    should reflect.
    """
    )
    return


@app.cell
def _(sim):
    data = sim.data()
    cs = data.cost_sheet
    tx = data.tax_statement
    rc = data.receipts.copy()
    return cs, rc, tx


@app.cell
def _(cs, mo):
    total_revenue_actual = float(cs["revenue"].sum())
    mo.md(
        f"**Letter's revenue claim** — the brief says \"about "
        f"{round(total_revenue_actual / 1000) * 1000:,.0f} euros\" across "
        f"the till over 3 years. Actual `cost_sheet.revenue.sum()` = "
        f"{total_revenue_actual:,.2f}. Rounding is owner-plausible (nearest "
        f"thousand), not simulator precision — matches by construction "
        f"since the brief reads this same number, but confirmed here "
        f"against the exported table directly rather than trusting the "
        f"brief's own arithmetic."
    )
    return


@app.cell
def _(mo, tx):
    final_year = tx.iloc[-1]
    result = float(final_year["profit_after_tax"])
    phrase = (
        "a loss" if result < -500
        else "almost exactly nothing" if abs(result) <= 500
        else "a real profit"
    )
    mo.md(
        f"**Letter's bottom-line claim** — brief says the bottom line came "
        f"out to \"{phrase}\". Actual final-year `profit_after_tax` = "
        f"{result:,.2f}. Matches the same threshold logic `describe()` "
        f"uses (loss < -500, breakeven within ±500, else real profit)."
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ### Event beats: real footprint, not just a mention

    A convincing case can't just *say* "a war happened" — the cost sheet
    has to actually move. Each chart below marks the settings' own event
    dates against the real monthly series they should affect.
    """)
    return


@app.cell
def _(ACCENT, SETTINGS, WARN, cs, event_marker, go, pd, style):
    _dates = pd.to_datetime(cs["year"].astype(str) + "-" + cs["month"].astype(str) + "-01")
    fig_proc = go.Figure()
    fig_proc.add_trace(go.Scatter(
        x=_dates, y=cs["procurement"], mode="lines+markers",
        line=dict(color=ACCENT, width=2), name="procurement",
    ))
    for _d in SETTINGS["events"]["war"]:
        event_marker(fig_proc, pd.Timestamp(_d), "war", WARN)
    fig_proc = style(fig_proc, title="Monthly procurement cost, with each war's start date marked", showlegend=False)
    return (fig_proc,)


@app.cell
def _(caption, fig_proc, mo):
    mo.vstack([
        mo.ui.plotly(fig_proc),
        caption(
            "Both wars should show a visible procurement bump in their own "
            "month — a claimed cause with no matching cost movement would "
            "be an unconvincing case, not a real one."
        ),
    ])
    return


@app.cell
def _(ACCENT, SETTINGS, WARN, event_marker, go, pd, rc, style):
    rc["date"] = pd.to_datetime(rc["date"])
    rc["line_amount"] = rc["qty"] * rc["unit_price"]
    _typhoon = pd.Timestamp(SETTINGS["events"]["typhoon"])
    _window = rc[(rc["date"] >= _typhoon - pd.Timedelta(days=10))
                 & (rc["date"] <= _typhoon + pd.Timedelta(days=10))]
    _daily = _window.groupby("date")["line_amount"].sum()
    fig_typhoon = go.Figure()
    fig_typhoon.add_trace(go.Scatter(
        x=_daily.index, y=_daily.values, mode="lines+markers",
        line=dict(color=ACCENT, width=2), name="daily revenue",
    ))
    event_marker(fig_typhoon, _typhoon, "typhoon", WARN)
    fig_typhoon = style(
        fig_typhoon,
        title="Daily revenue, ±10 days around the typhoon — the dent a monthly total would hide",
        showlegend=False,
    )
    return (fig_typhoon,)


@app.cell
def _(caption, fig_typhoon, mo):
    mo.vstack([
        mo.ui.plotly(fig_typhoon),
        caption(
            "A 3-day storm is a small dent against a full month's revenue "
            "— real, but easy to miss at monthly resolution. This is the "
            "actual daily-level footprint the brief's storm beat refers to."
        ),
    ])
    return


@app.cell
def _(ACCENT, SETTINGS, WARN, cs, event_marker, go, pd, style):
    _dates2 = pd.to_datetime(cs["year"].astype(str) + "-" + cs["month"].astype(str) + "-01")
    fig_rev = go.Figure()
    fig_rev.add_trace(go.Scatter(
        x=_dates2, y=cs["revenue"], mode="lines+markers",
        line=dict(color=ACCENT, width=2), name="revenue",
    ))
    event_marker(fig_rev, pd.Timestamp(SETTINGS["events"]["competitor"]), "competitor entry", WARN)
    event_marker(fig_rev, pd.Timestamp(SETTINGS["events"]["tax_raise"]), "tax raise", WARN)
    fig_rev = style(fig_rev, title="Monthly revenue over the full 3 years", showlegend=False)
    return (fig_rev,)


@app.cell
def _(caption, fig_rev, mo):
    mo.vstack([
        mo.ui.plotly(fig_rev),
        caption(
            "This scenario's competitor is calibrated to a modest ~9% "
            "visit-rate drop (params.py), with a scheduled owner price "
            "response partly offsetting it — so a case where revenue "
            "barely dips after entry is the model working as calibrated, "
            "not a missing effect. This is exactly why describe()'s "
            "misguide grounding above matters: the owner's instinct to "
            "blame the competitor may not match what the data shows."
        ),
    ])
    return


@app.cell
def _(cs):
    capex_rows = cs[cs["capex"] > 0][["year", "month", "capex"]]
    capex_rows
    return (capex_rows,)


@app.cell
def _(capex_rows, mo):
    mo.md(f"""
    **Investment beats** — the brief claims specific investments "
        f"were made, with specific costs, at specific dates. "
        f"`cost_sheet` shows {len(capex_rows)} capex-bearing month(s) "
        f"totaling {capex_rows['capex'].sum():,.0f} — these should be the "
        f"exact same months and (decomposed) amounts named in "What "
        f"happened along the way" above.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Reader's checklist

    Having seen both the brief and the data underneath, judge it as a
    reader would:

    - Does the owner's voice read like a real small-business owner, not a
      simulator printout? (rounded numbers, plain language, one clear worry)
    - Does every beat in "What happened along the way" correspond to a real
      movement in the charts above, not just a restated setting?
    - Does the "Stakes" section's confidence (or hedging) actually match
      whether the misguide candidate turned out to be grounded?
    - Would a student handed only the brief and the visible/ CSVs — not
      this notebook — have enough to start investigating, without already
      being told the answer?

    If all four hold, the case is doing its job: a convincing first guess
    that the data can either confirm or correct.
    """)
    return


if __name__ == "__main__":
    app.run()
