import marimo

__generated_with = "0.23.14"
app = marimo.App(
    width="full",
    app_title="The Expansion, Audited — an Investment Review",
)


@app.cell
def _():
    import datetime as dt
    import duckdb
    import marimo as mo
    import numpy as np
    import plotly.graph_objects as go
    import polars as pl

    from pathlib import Path
    from plotly.subplots import make_subplots

    ROOT = Path(__file__).resolve().parent.parent.parent
    DATA = ROOT / "data"

    # ---- shared declutter style (see analysis_workbook.py for rationale) ---
    INK = "#404040"
    MUTED = "#BFBFBF"
    ACCENT = "#2E5EAA"
    ACCENT_LIGHT = "#9DB8E6"
    WARN = "#B44646"
    PLOT = dict(
        template = "plotly_white",
        height = 400,
        margin = dict(
            l = 64,
            r = 36,
            t = 72,
            b = 52,
        ),
        font = dict(
            color = INK,
            size = 12.5,
        ),
    )
    AXIS_X = dict(
        showgrid = False,
        zeroline = False,
        showline = True,
        linecolor = "#D9D9D9",
        ticks = "outside",
        tickcolor = "#D9D9D9",
    )
    AXIS_Y = dict(
        showgrid = False,
        zeroline = False,
        showline = False,
        ticks = "",
        nticks = 5,
    )

    def style(
        fig,
        title = None,
        showlegend = False,
        n_subplot_titles = 0,
        right_margin = 36,
    ):
        fig.update_layout(
            showlegend = showlegend,
            legend = dict(
                orientation = "h",
                yanchor = "bottom",
                y = 1.0,
                xanchor = "right",
                x = 1.0,
                bgcolor = "rgba(0,0,0,0)",
                title_text = "",
            ),
            **PLOT,
        )
        fig.update_layout(margin = dict(r = right_margin))
        if title:
            fig.update_layout(
                title = dict(
                    text = title,
                    x = 0,
                    xanchor = "left",
                    pad = dict(l = PLOT["margin"]["l"]),
                    font = dict(size = 15),
                ),
            )
        for _i in range(n_subplot_titles):
            fig.layout.annotations[_i].font = dict(
                size = 13.5,
                color = INK,
            )
        fig.update_xaxes(**AXIS_X)
        fig.update_yaxes(**AXIS_Y)
        return fig

    def hide_value_axis(
        fig,
        axis,
        row = None,
        col = None,
        title = None,
    ):
        _update = fig.update_yaxes if axis == "y" else fig.update_xaxes
        _update(
            showticklabels = False,
            showline = False,
            ticks = "",
            title_text = title,
            title_font = dict(
                size = 11.5,
                color = MUTED,
            ),
            row = row,
            col = col,
        )
        return fig

    def caption(text):
        return mo.md(f"<div style='color:#7A7A7A; font-size:0.92em; padding:2px 24px 18px 64px;'><em>{text}</em></div>")

    def takeaway(
        fig,
        text,
        x = 0.02,
        y = 0.98,
        row = None,
        col = None,
        color = ACCENT,
        anchor = "left",
    ):
        fig.add_annotation(
            text = text,
            x = x,
            y = y,
            xref = "x domain",
            yref = "y domain",
            xanchor = anchor,
            yanchor = "top",
            showarrow = False,
            align = anchor,
            font = dict(
                color = color,
                size = 12.5,
            ),
            row = row,
            col = col,
        )
        return fig

    return (
        ACCENT,
        ACCENT_LIGHT,
        DATA,
        MUTED,
        WARN,
        caption,
        dt,
        duckdb,
        go,
        hide_value_axis,
        make_subplots,
        mo,
        np,
        pl,
        style,
        takeaway,
    )


@app.cell
def _(mo):
    mo.md(r"""
    # The expansion, audited: was the owner's big bet worth it?

    On **November 1, 2026**, after twenty-two months of retained earnings
    had crossed his €52,000 threshold, the owner made the classic
    small-business move: he spent **€14,000** on fit-out, hired his
    **first employee** (a clerk on an eight-hour shift), extended opening
    hours to **07:00–21:00**, and deepened the shelves by 20%. Ex ante it
    was the reasonable thing to do — a year and a half of proof, a growing
    neighborhood, December coming.

    This notebook audits that decision against the one thing no real
    business ever gets: the same three years **without** the expansion
    (`3y_no_expansion`, the CRN twin in which the threshold never
    triggers). The verdict is brutal, specific, and — because the twin
    shares every random draw — exact.
    """)
    return


@app.cell
def _(DATA, duckdb, pl):
    # ---- load both arms' books and tills ------------------------------------
    def _load_arm(arm):
        _con = duckdb.connect()
        _vis = DATA / "scenarios" / arm / "visible"
        for _name in ["receipts", "cost_sheet", "tax_statement", "inventory_eod"]:
            _con.execute(
                query = f"""
                    CREATE TABLE {_name}_raw AS
                    SELECT *
                    FROM   read_csv_auto('{(_vis / _name).as_posix()}.csv')
                """,
            )
        # cleaned till (retry dedup + void cancellation), enough for revenue
        # and hour-of-day work; the ledger needs no cleaning by contract
        _rec = _con.sql(
            query = """
                WITH lines AS (
                    SELECT receipt_id,
                           hour,
                           uid,
                           qty,
                           unit_price,
                           date,
                           ref_receipt_id,
                           count(*) AS n
                    FROM   receipts_raw
                    GROUP  BY ALL
                ),
                retry AS (
                    SELECT receipt_id,
                           bool_and(n % 2 = 0) AS is_retry
                    FROM   lines
                    GROUP  BY receipt_id
                )
                SELECT l.receipt_id,
                       CASE WHEN l.hour = 0 THEN NULL ELSE l.hour END AS hour,
                       l.uid,
                       sum(l.qty * CASE WHEN r.is_retry THEN l.n // 2
                                        ELSE l.n END)                 AS qty,
                       l.unit_price,
                       l.date,
                       l.ref_receipt_id
                FROM   lines l
                JOIN   retry r USING (receipt_id)
                GROUP  BY l.receipt_id, l.hour, l.uid,
                          l.unit_price, l.date, l.ref_receipt_id
                HAVING sum(l.qty * CASE WHEN r.is_retry THEN l.n // 2
                                        ELSE l.n END) != 0
            """,
        ).pl()
        _out = {
            "receipts": _rec,
            "cost_sheet": _con.sql(query = "SELECT * FROM cost_sheet_raw ORDER BY year, month").pl(),
            "tax": _con.sql(query = "SELECT * FROM tax_statement_raw ORDER BY year").pl(),
            "oos": _con.sql(
                query = """
                    SELECT date_trunc('month', date)              AS m,
                           avg(CASE WHEN on_hand <= 0 THEN 1.0
                                    ELSE 0.0 END)                 AS oos
                    FROM   inventory_eod_raw
                    GROUP  BY 1
                    ORDER  BY 1
                """,
            ).pl(),
        }
        _con.close()
        return _out

    arm_b = _load_arm(arm = "3y_baseline")
    arm_ne = _load_arm(arm = "3y_no_expansion")
    return arm_b, arm_ne


@app.cell
def _(arm_b, arm_ne, caption, mo, pl):
    # ---- the bet, stated in the owner's own numbers --------------------------
    _b = arm_b["tax"]
    _n = arm_ne["tax"]
    bet = _b.select([
        "year",
        pl.col("profit_before_tax").round(0).alias("with_expansion"),
    ]).join(
        other = _n.select([
            "year",
            pl.col("profit_before_tax").round(0).alias("without_expansion"),
        ]),
        on = "year",
    ).with_columns(
        (pl.col("with_expansion") - pl.col("without_expansion")).alias("the_bet_cost"),
    )
    op_cost = -float(bet["the_bet_cost"].sum())
    _capex = float(arm_b["cost_sheet"]["capex"].sum())
    full_cost = op_cost + _capex
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 1 · The bet, in three lines of the tax statement

    Both worlds file identical 2025 returns (the expansion hadn't happened
    yet in either). Then they diverge:
    """
            ),
            mo.ui.table(
                data = bet,
                selection = None,
            ),
            caption(
                f"Annual profit before tax, € — identical 2025s are the CRN "
                f"twin discipline showing its work. The expansion drags 2026 "
                f"by its last two months and then costs a full year in "
                f"2027. Operating shortfall over the bet's fourteen months: "
                f"€{op_cost:,.0f}; add the €{_capex:,.0f} fit-out (capex, "
                f"never expensed) and the bet's total cash cost is about "
                f"€{full_cost:,.0f}. For scale: the discounter that opened "
                f"in March 2027 cost about €5k over the same period "
                f"(competitor_entry_study.py)."
            ),
        ],
    )
    return bet, full_cost, op_cost


@app.cell
def _(
    ACCENT,
    MUTED,
    WARN,
    arm_b,
    arm_ne,
    caption,
    dt,
    go,
    make_subplots,
    mo,
    op_cost,
    pl,
    style,
    takeaway,
):
    # ---- the running total of the bet ----------------------------------------
    def _monthly_result(cs):
        """The month's operating result from the ledger columns — the same
        arithmetic the RE ledger retains from (ACCOUNTING §7.1)."""
        return cs.select([
            pl.date(pl.col("year"), pl.col("month"), 1).alias("m"),
            (pl.col("revenue") - pl.col("procurement") - pl.col("rent")
             - pl.col("wages") - pl.col("payroll_tax") - pl.col("utilities")
             - pl.col("storage") - pl.col("flyers") - pl.col("vat")
             - pl.col("credit_interest") - pl.col("repairs")).alias("result"),
        ])

    _rb = _monthly_result(cs = arm_b["cost_sheet"])
    _rn = _monthly_result(cs = arm_ne["cost_sheet"])
    _j = _rb.join(
        other = _rn,
        on = "m",
        suffix = "_ne",
    ).sort(by = "m").with_columns(
        (pl.col("result") - pl.col("result_ne")).alias("diff"),
    )
    # the capex leaves cash on Nov 1, 2026 — put it in the running total
    _j = _j.with_columns(
        (pl.col("diff") - pl.when(pl.col("m") == dt.date(2026, 11, 1))
            .then(float(arm_b["cost_sheet"]["capex"].sum()))
            .otherwise(0.0)).alias("diff_cash"),
    )
    _cum = _j["diff_cash"].cum_sum()

    _fig = make_subplots(
        rows = 1,
        cols = 2,
        subplot_titles = (
            "Monthly operating result, both worlds",
            "The bet's running total (incl. the €14k fit-out)",
        ),
        horizontal_spacing = 0.12,
    )
    _fig.add_scatter(
        x = _rn["m"].to_list(),
        y = _rn["result"].to_list(),
        mode = "lines",
        line = dict(
            color = MUTED,
            width = 2.5,
        ),
        row = 1,
        col = 1,
    )
    _fig.add_scatter(
        x = _rb["m"].to_list(),
        y = _rb["result"].to_list(),
        mode = "lines",
        line = dict(
            color = ACCENT,
            width = 2,
        ),
        row = 1,
        col = 1,
    )
    _fig.add_annotation(
        x = _rn["m"].to_list()[-1],
        y = float(_rn["result"][-1]),
        text = "no expansion",
        showarrow = False,
        xanchor = "left",
        xshift = 8,
        font = dict(
            color = "#9A9A9A",
            size = 12,
        ),
        row = 1,
        col = 1,
    )
    _fig.add_annotation(
        x = _rb["m"].to_list()[-1],
        y = float(_rb["result"][-1]),
        text = "the shop",
        showarrow = False,
        xanchor = "left",
        xshift = 8,
        yshift = -10,
        font = dict(
            color = ACCENT,
            size = 12,
        ),
        row = 1,
        col = 1,
    )
    _fig.add_scatter(
        x = _j["m"].to_list(),
        y = _cum.to_list(),
        mode = "lines",
        line = dict(
            color = WARN,
            width = 2.5,
        ),
        row = 1,
        col = 2,
    )
    for _c in (1, 2):
        _fig.add_vline(
            x = dt.date(2026, 11, 1),
            line_dash = "dash",
            line_color = WARN,
            line_width = 1.5,
            row = 1,
            col = _c,
        )
        # marker label inside the panel, at the bottom, clear of the titles
        _fig.add_annotation(
            x = dt.date(2026, 11, 1),
            y = 0.04,
            yref = "y domain",
            text = "expansion",
            showarrow = False,
            xanchor = "right",
            xshift = -6,
            font = dict(
                color = WARN,
                size = 11,
            ),
            row = 1,
            col = _c,
        )
    style(
        fig = _fig,
        title = "Fourteen months of the expansion, next to the world that skipped it",
        n_subplot_titles = 2,
        right_margin = 96,
    )
    _fig.update_yaxes(
        title_text = "operating result (€/month)",
        range = [
            min(float(_rb["result"].min()), 0.0) * 1.15,
            float(_rn["result"].max()) * 1.4,
        ],
        row = 1,
        col = 1,
    )
    # keep the date axis from stretching past the data to fit the end labels
    _fig.update_xaxes(
        range = [
            dt.date(2024, 12, 1),
            dt.date(2028, 4, 1),
        ],
        row = 1,
        col = 1,
    )
    _fig.update_yaxes(
        title_text = "cumulative difference (€)",
        range = [float(_cum.min()) * 1.3, 8_000],
        row = 1,
        col = 2,
    )
    takeaway(
        fig = _fig,
        text = "after November 2026 the blue line lives €4–7k/month below its twin",
        x = 0.02,
        y = 0.99,
        row = 1,
        col = 1,
    )
    takeaway(
        fig = _fig,
        text = f"−€{op_cost + float(arm_b['cost_sheet']['capex'].sum()):,.0f}<br>and still falling at the data's edge",
        x = 0.04,
        y = 0.40,
        color = WARN,
        row = 1,
        col = 2,
    )
    mo.vstack(
        items = [
            mo.md("## 2 · The running total"),
            _fig,
            caption(
                "Left: the month's operating result (revenue minus all "
                "ledger costs) in both worlds. The curves are identical "
                "until November 2026; afterwards the expanded shop runs "
                "persistently lower — the gap is the clerk's wages plus "
                "payroll tax, minus whatever the longer day and deeper "
                "shelves earn back. Right: the same gap accumulated, with "
                "the €14,000 fit-out charged at the start. There is no "
                "inflection: the bet loses money at a steady rate, and "
                "nothing in the trend suggests year four would look "
                "different — the monthly loss is structural (a fixed wage "
                "bill against a variable-margin trickle), not a ramp-up "
                "cost."
            ),
        ],
    )
    return


@app.cell
def _(
    ACCENT,
    MUTED,
    arm_b,
    arm_ne,
    caption,
    dt,
    hide_value_axis,
    make_subplots,
    mo,
    pl,
    style,
    takeaway,
):
    # ---- what the money actually bought --------------------------------------
    _b_rec = arm_b["receipts"].filter(
        (pl.col("qty") > 0)
        & pl.col("ref_receipt_id").is_null()
        & (pl.col("date") >= dt.date(2026, 11, 1))
    ).with_columns((pl.col("qty") * pl.col("unit_price")).alias("v"))
    ext_rev = float(_b_rec.filter(pl.col("hour").is_in([7, 20]))["v"].sum())
    ext_share = ext_rev / float(_b_rec["v"].sum())

    _ob = arm_b["oos"].filter(pl.col("m") >= dt.date(2026, 1, 1))
    _on = arm_ne["oos"].filter(pl.col("m") >= dt.date(2026, 1, 1))
    _fig = make_subplots(
        rows = 1,
        cols = 2,
        subplot_titles = (
            "Revenue rung up in the new hours (07h and 20h)",
            "Empty-shelf rate, with and without the deeper shelves",
        ),
        horizontal_spacing = 0.12,
    )
    _ext_m = _b_rec.filter(pl.col("hour").is_in([7, 20])).with_columns(
        pl.col("date").dt.truncate("1mo").alias("m"),
    ).group_by("m").agg(pl.col("v").sum().alias("rev")).sort(by = "m")
    _fig.add_bar(
        x = _ext_m["m"].to_list(),
        y = _ext_m["rev"].to_list(),
        marker_color = ACCENT,
        # the value axis is hidden below, so each column carries its number
        text = [f"{_v / 1000:.1f}k" for _v in _ext_m["rev"]],
        textposition = "outside",
        textfont = dict(size = 10.5),
        row = 1,
        col = 1,
    )
    _fig.add_scatter(
        x = _on["m"].to_list(),
        y = (100 * _on["oos"]).to_list(),
        mode = "lines+markers",
        line = dict(
            color = MUTED,
            width = 2,
        ),
        marker = dict(size = 5),
        row = 1,
        col = 2,
    )
    _fig.add_scatter(
        x = _ob["m"].to_list(),
        y = (100 * _ob["oos"]).to_list(),
        mode = "lines+markers",
        line = dict(
            color = ACCENT,
            width = 2,
        ),
        marker = dict(size = 5),
        row = 1,
        col = 2,
    )
    _fig.add_annotation(
        x = _on["m"].to_list()[-1],
        y = float(100 * _on["oos"][-1]),
        text = "no expansion",
        showarrow = False,
        xanchor = "left",
        xshift = 8,
        font = dict(
            color = "#9A9A9A",
            size = 12,
        ),
        row = 1,
        col = 2,
    )
    _fig.add_annotation(
        x = _ob["m"].to_list()[-1],
        y = float(100 * _ob["oos"][-1]),
        text = "the shop",
        showarrow = False,
        xanchor = "left",
        xshift = 8,
        font = dict(
            color = ACCENT,
            size = 12,
        ),
        row = 1,
        col = 2,
    )
    _fig.add_vline(
        x = dt.date(2026, 11, 1),
        line_dash = "dash",
        line_color = MUTED,
        line_width = 1,
        row = 1,
        col = 2,
    )
    style(
        fig = _fig,
        title = "The expansion did deliver — just not enough to pay for itself",
        n_subplot_titles = 2,
        right_margin = 96,
    )
    _fig.update_yaxes(
        range = [0, float(_ext_m["rev"].max()) * 1.35],
        row = 1,
        col = 1,
    )
    hide_value_axis(
        fig = _fig,
        axis = "y",
        row = 1,
        col = 1,
        title = "extended-hours revenue (€/month)",
    )
    _fig.update_yaxes(
        title_text = "% of SKU-days out of stock",
        range = [0, float(100 * _on["oos"].max()) * 1.35],
        row = 1,
        col = 2,
    )
    takeaway(
        fig = _fig,
        text = f"€{ext_rev / 1000:,.0f}k rung up at 7am and 8pm — {ext_share:.0%} of post-expansion revenue",
        x = 0.02,
        y = 0.99,
        row = 1,
        col = 1,
    )
    takeaway(
        fig = _fig,
        text = "empty shelves nearly halve once the shelves deepen",
        x = 0.02,
        y = 0.99,
        row = 1,
        col = 2,
    )
    mo.vstack(
        items = [
            mo.md(
                """
    ## 3 · What the money bought

    A fair audit lists the benefits before the verdict — and they are
    real:
    """
            ),
            _fig,
            caption(
                "Left: money the till rings up in hours that simply did "
                "not exist before the expansion (the 7am and 8pm hours). "
                "Right: the share of product-days with an empty shelf, in "
                "both worlds — the deeper shelves cut stockouts by "
                "roughly four percentage points, which is recovered "
                "demand and happier regulars. The problem is arithmetic, "
                "not direction: the new hours are the day's quietest, so "
                "their revenue converts to roughly 18 cents of margin per "
                "euro, and the deeper shelves buy extra stock that partly "
                "rots (the twin comparison shows procurement rising by "
                "more than revenue). Against a fixed wage bill of "
                "€4–5k a month, the earn-back never comes close."
            ),
        ],
    )
    return ext_rev, ext_share


@app.cell
def _(
    MUTED,
    WARN,
    arm_b,
    arm_ne,
    caption,
    go,
    hide_value_axis,
    mo,
    op_cost,
    pl,
    style,
    takeaway,
):
    # ---- the decomposition: where the money went ------------------------------
    _cols = [
        ("revenue", "extra revenue", +1),
        ("procurement", "extra stock bought", -1),
        ("wages", "clerk's wages", -1),
        ("payroll_tax", "payroll tax", -1),
        ("utilities", "longer-day utilities", -1),
        ("storage", "storage", -1),
        ("vat", "net VAT", -1),
    ]
    _b = arm_b["cost_sheet"]
    _n = arm_ne["cost_sheet"]
    _rows = []
    for _c, _lbl, _sign in _cols:
        _d = float(_b[_c].sum() - _n[_c].sum())
        _rows.append({
            "component": _lbl,
            "effect": -_d if _sign < 0 else _d,
        })
    _rows.append({
        "component": "fit-out capex",
        "effect": -float(_b["capex"].sum()),
    })
    decomp = pl.DataFrame(_rows).sort(by = "effect")
    _fig = go.Figure()
    _fig.add_bar(
        x = decomp["effect"].to_list(),
        y = decomp["component"].to_list(),
        orientation = "h",
        marker_color = [
            WARN if _v < 0 else "#5B8C5A"
            for _v in decomp["effect"]
        ],
        text = [f"{_v:+,.0f}" for _v in decomp["effect"]],
        textposition = "outside",
    )
    style(
        fig = _fig,
        title = "Every euro of the bet, decomposed (baseline minus no-expansion twin, Nov 2026 – Dec 2027)",
    )
    hide_value_axis(
        fig = _fig,
        axis = "x",
        title = "effect on the owner's money (€, + earns / − costs)",
    )
    # the shared style caps y ticks at five, which would drop every other
    # category label on this eight-bar chart — restore them all
    _fig.update_yaxes(
        title_text = "",
        nticks = len(decomp) + 1,
    )
    _fig.update_xaxes(range = [
        float(decomp["effect"].min()) * 1.25,
        float(decomp["effect"].max()) * 1.6,
    ])
    takeaway(
        fig = _fig,
        text = "labor is four-fifths of the damage — and the deeper<br>shelf bought more stock than it sold",
        x = 0.97,
        y = 0.42,
        anchor = "right",
    )
    mo.vstack(
        items = [
            mo.md("## 4 · Where the money went"),
            _fig,
            caption(
                "Each bar is the twin difference in one ledger line over "
                "the expansion's lifetime, signed from the owner's "
                "pocket. The two structural findings: (1) wages plus "
                "payroll tax dwarf everything else — a legal-wage "
                "employee against an 18% gross margin needs to *create* "
                "roughly five euros of revenue for every euro he costs, "
                "and the quiet morning hours create nowhere near that; "
                "(2) the 'extra revenue' bar is smaller than the 'extra "
                "stock bought' bar — deeper shelves cut stockouts, but "
                "on perishables the unsold depth spoils, so the gross "
                "margin on the expansion's own revenue is negative "
                "before labor even enters. The sum of the bars is the "
                f"bet's total: about −€{op_cost + float(_b['capex'].sum()):,.0f}."
            ),
        ],
    )
    return (decomp,)


@app.cell
def _(arm_ne, bet, full_cost, mo, pl):
    _p27_ne = float(bet.filter(pl.col("year") == 2027)["without_expansion"][0])
    _p27_b = float(bet.filter(pl.col("year") == 2027)["with_expansion"][0])
    mo.md(
        f"""
    ## 5 · Verdict — and the renew-or-close question, answered

    **Was the expansion worth it?** No. Total cost ≈
    **€{full_cost:,.0f}** over fourteen months (operating shortfall plus
    fit-out), with no ramp-up story in the trend: the loss is a fixed
    wage bill on a thin-margin business.

    **Was it a stupid decision?** That is the more interesting question,
    and the honest answer is no — it was the *normal* decision. The owner
    followed the classic playbook: prove the concept, retain earnings,
    reinvest when the threshold is crossed. What the playbook missed is
    arithmetic peculiar to groceries: at an 18% gross margin, one
    legal-wage employee must generate about €25k of *new revenue per
    year* just to break even, and a shop this size has no lever that
    large. The twin quantifies what intuition alone could not.

    **The three-year review asked: renew the lease, or close?** This
    notebook answers it. Without the expansion, 2027 — discounter, rent
    step, wage inflation and all — would have earned
    **€{_p27_ne:,.0f}** before tax. With it, the same year earned
    €{_p27_b:,.0f}. The shop's problem is not the location, not the
    lease, and not the competitor: it is a payroll line that the margin
    structure cannot carry. The books' recommendation for 2028 writes
    itself: **renew the lease, reverse the expansion** — return to
    owner-only hours (or keep the hours and staff them himself), keep
    the deeper shelves only for the non-perishable categories where
    depth doesn't rot.
    """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ### Appendix — method notes

    The comparison arm (`3y_no_expansion`) is the identical world with the
    expansion threshold set to infinity: same customers, same weather,
    same discounter, same contracts — every difference in this notebook
    is the expansion's causal effect by construction. Ledger figures come
    from `cost_sheet.csv` (which needs no cleaning by the accounting
    contract); till figures pass through the standard retry/void
    cleaning. No answer-key files were used: unlike the churn and entry
    studies, this audit is entirely computable from the two visible
    folders — the laboratory's gift here is the twin itself, not the
    grading.
    """)
    return


if __name__ == "__main__":
    app.run()
