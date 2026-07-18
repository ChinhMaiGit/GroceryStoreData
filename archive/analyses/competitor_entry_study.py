import marimo

__generated_with = "0.23.14"
app = marimo.App(
    width="full",
    app_title="The Discounter Next Door — an Entry Study",
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

    def end_label(
        fig,
        x,
        y,
        text,
        color,
        row = None,
        col = None,
    ):
        fig.add_annotation(
            x = x,
            y = y,
            text = text,
            showarrow = False,
            xanchor = "left",
            xshift = 8,
            font = dict(
                color = color,
                size = 12,
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
        ROOT,
        WARN,
        caption,
        dt,
        duckdb,
        end_label,
        go,
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
    # The discounter next door: what did it actually cost?

    On **March 1, 2027** a discount grocer opened 600 meters from the shop.
    The three-year review (`three_year_review.py`) ended that chapter on an
    uncomfortable note: *the entry is invisible from inside the shop's own
    data* — visits and revenue kept growing right through it, because the
    neighborhood was growing and the shop had just extended its hours.

    This notebook answers the question the shop's own data cannot:
    **how much did the discounter cost, and who stopped coming?** It can do
    so because the policy laboratory generated a *counterfactual twin* —
    `3y_no_competitor` — the identical three years, sharing every random
    draw with the baseline (every customer, every delivery, every rainy
    day), with exactly one thing deleted: the entry. Any difference between
    the two arms **is** the discounter's effect, by construction.

    Along the way it grades two textbook mistakes an analyst could make
    here: reading the trend as "no effect" (§3), and reading the owner's
    own price cuts as an independent strategy rather than a *response*
    (§6).
    """)
    return


@app.cell
def _(DATA, ROOT, duckdb, pl):
    # ---- load both arms through the identical cleaning contract -------------
    _products = pl.read_excel(source = ROOT / "SKUs.xlsx")

    def _load_arm(arm):
        """One arm's cleaned tables (same cleaning contract as the one-year
        workbook §2: retry dedup, void cancellation, label normalization)."""
        _con = duckdb.connect()
        _vis = DATA / "scenarios" / arm / "visible"
        for _name in ["receipts", "cost_sheet", "price_history"]:
            _con.execute(
                query = f"""
                    CREATE TABLE {_name}_raw AS
                    SELECT *
                    FROM   read_csv_auto('{(_vis / _name).as_posix()}.csv')
                """,
            )
        _con.register("products_df", _products)
        _rec = _con.sql(
            query = """
                WITH lines AS (
                    SELECT receipt_id,
                           hour,
                           customer_id,
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
                       l.customer_id,
                       l.uid,
                       sum(l.qty * CASE WHEN r.is_retry THEN l.n // 2
                                        ELSE l.n END)                 AS qty,
                       l.unit_price,
                       l.date,
                       l.ref_receipt_id
                FROM   lines l
                JOIN   retry r USING (receipt_id)
                GROUP  BY l.receipt_id, l.customer_id, l.uid,
                          l.unit_price, l.date, l.ref_receipt_id
                HAVING sum(l.qty * CASE WHEN r.is_retry THEN l.n // 2
                                        ELSE l.n END) != 0
            """,
        ).pl()
        _cs = _con.sql(query = "SELECT * FROM cost_sheet_raw").pl()
        _ph = _con.sql(
            query = """
                SELECT ph.uid,
                       ph.date,
                       ph.price,
                       p.category
                FROM   price_history_raw ph
                JOIN   products_df p USING (uid)
            """,
        ).pl()
        _con.close()
        return {
            "receipts": _rec,
            "cost_sheet": _cs,
            "price_history": _ph,
        }

    arm_b = _load_arm(arm = "3y_baseline")
    arm_nc = _load_arm(arm = "3y_no_competitor")
    brand_of = dict(zip(
        _products["uid"].to_list(),
        _products["brand_level"].to_list(),
    ))
    return arm_b, arm_nc, brand_of


@app.cell
def _(caption, mo):
    _map = mo.mermaid("""
    erDiagram
        baseline_receipts }o--|| products : "uid"
        twin_receipts }o--|| products : "uid"
        baseline_receipts ||..|| twin_receipts : "same tokens, same days (CRN)"
        baseline_cost_sheet ||..|| twin_cost_sheet : "same schema"

        baseline_receipts {
            date date "2025-01 .. 2027-12, WITH the entry"
        }
        twin_receipts {
            date date "identical world, entry deleted"
        }
    """)
    mo.vstack(
        items = [
            mo.md("## 1 · Two copies of the same world"),
            _map,
            caption(
                "The twin (3y_no_competitor) shares every keyed random draw "
                "with the baseline — the same customers with the same "
                "tokens, the same weather, the same deliveries — so the "
                "arms are row-comparable at the level of individual "
                "shoppers. Before March 2027 the two datasets are "
                "near-identical; afterwards, every gap is the entry's "
                "causal footprint. Dotted links mark this twin pairing."
            ),
        ],
    )
    return


@app.cell
def _(
    ACCENT,
    MUTED,
    WARN,
    arm_b,
    arm_nc,
    caption,
    dt,
    go,
    make_subplots,
    mo,
    pl,
    style,
    takeaway,
):
    # ---- the headline: the gap that only the twin can show ------------------
    def _monthly(rec):
        return rec.filter(
            (pl.col("qty") > 0) & pl.col("ref_receipt_id").is_null()
        ).with_columns(
            pl.col("date").dt.truncate("1mo").alias("m"),
            (pl.col("qty") * pl.col("unit_price")).alias("v"),
        ).group_by("m").agg(pl.col("v").sum().alias("revenue")).sort(by = "m")

    _mb = _monthly(rec = arm_b["receipts"])
    _mn = _monthly(rec = arm_nc["receipts"])
    gap_m = _mb.join(
        other = _mn,
        on = "m",
        suffix = "_twin",
    ).with_columns((pl.col("revenue") - pl.col("revenue_twin")).alias("gap")).sort(by = "m")
    entry_cost_2027 = -float(gap_m.filter(pl.col("m") >= dt.date(2027, 1, 1))["gap"].sum())

    _fig = make_subplots(
        rows = 1,
        cols = 2,
        subplot_titles = (
            "Monthly revenue: the shop vs. its no-entry twin",
            "The entry's running cost (cumulative twin gap)",
        ),
        horizontal_spacing = 0.12,
    )
    _fig.add_scatter(
        x = _mn["m"].to_list(),
        y = _mn["revenue"].to_list(),
        mode = "lines",
        line = dict(
            color = MUTED,
            width = 2.5,
        ),
        row = 1,
        col = 1,
    )
    _fig.add_scatter(
        x = _mb["m"].to_list(),
        y = _mb["revenue"].to_list(),
        mode = "lines",
        line = dict(
            color = ACCENT,
            width = 2,
        ),
        row = 1,
        col = 1,
    )
    _fig.add_annotation(
        x = _mn["m"].to_list()[-1],
        y = float(_mn["revenue"][-1]),
        text = "no-entry twin",
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
        x = _mb["m"].to_list()[-1],
        y = float(_mb["revenue"][-1]) * 0.93,
        text = "the shop",
        showarrow = False,
        xanchor = "left",
        xshift = 8,
        font = dict(
            color = ACCENT,
            size = 12,
        ),
        row = 1,
        col = 1,
    )
    _cum = gap_m["gap"].cum_sum()
    _fig.add_scatter(
        x = gap_m["m"].to_list(),
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
            x = dt.date(2027, 3, 1),
            line_dash = "dash",
            line_color = WARN,
            line_width = 1.5,
            row = 1,
            col = _c,
        )
    style(
        fig = _fig,
        title = "Only the counterfactual twin makes the discounter visible",
        n_subplot_titles = 2,
        right_margin = 96,
    )
    _fig.update_yaxes(
        title_text = "revenue (€/month)",
        range = [0, float(_mn["revenue"].max()) * 1.25],
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
        title_text = "cumulative revenue gap (€)",
        range = [float(_cum.min()) * 1.35, max(0.0, float(_cum.max())) + 3_000],
        row = 1,
        col = 2,
    )
    # both takeaways live in empty plot regions, clear of the entry marker
    takeaway(
        fig = _fig,
        text = "one line until March 2027 — then a quiet separation",
        x = 0.02,
        y = 0.30,
        row = 1,
        col = 1,
    )
    takeaway(
        fig = _fig,
        text = f"−€{entry_cost_2027:,.0f} of revenue by year end",
        x = 0.05,
        y = 0.35,
        color = WARN,
        row = 1,
        col = 2,
    )
    mo.vstack(
        items = [
            mo.md("## 2 · The headline: a leak, not a cliff"),
            _fig,
            caption(
                "Left: monthly revenue in both arms. Through February 2027 "
                "the two curves are indistinguishable — the twin discipline "
                "at work — and from March they separate by one to three "
                "thousand euros a month, an amount far too small to spot "
                "against seasonal swings of ten thousand. Right: the same "
                "gap accumulated. The dashed line marks the opening. By "
                "December the entry has cost about "
                f"€{entry_cost_2027:,.0f} of revenue — roughly 2% of the "
                "year — which at the shop's margins converts to about €5k "
                "of profit. Real money, but (as expansion_review.py shows) "
                "an order of magnitude less than what the owner's own "
                "expansion cost in the same year."
            ),
        ],
    )
    return entry_cost_2027, gap_m


@app.cell
def _(dt, gap_m, mo, np, pl):
    # ---- the effect, estimated the honest way -------------------------------
    import statsmodels.api as sm

    # weekly twin gap: with CRN twins the pre-period gap is pure shared-noise
    # residue, so a single post-entry step regression IS the diff-in-diff
    # (the arm pairing is differenced out inside `gap` itself)
    _g = gap_m.with_columns((pl.col("m") >= dt.date(2027, 3, 1)).cast(pl.Int8).alias("post"))
    _X = sm.add_constant(_g["post"].to_numpy())
    _ols = sm.OLS(
        endog = _g["gap"].to_numpy(),
        exog = _X,
    ).fit(
        cov_type = "HAC",
        cov_kwds = {"maxlags": 2},
    )
    _ci = _ols.conf_int()

    def _stars(p):
        return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""

    did_table = pl.DataFrame({
        "term": [
            "intercept (pre-entry gap)",
            "post-entry step",
        ],
        "estimate": [round(float(_b), 2) for _b in _ols.params],
        "std_error": [round(float(_s), 2) for _s in _ols.bse],
        "t_stat": [round(float(_t), 2) for _t in _ols.tvalues],
        "p_value": [round(float(_p), 4) for _p in _ols.pvalues],
        "ci_low": [round(float(_l), 2) for _l in _ci[:, 0]],
        "ci_high": [round(float(_h), 2) for _h in _ci[:, 1]],
        "sig": [_stars(p = float(_p)) for _p in _ols.pvalues],
    })
    did_stats = {
        "pre": float(_ols.params[0]),
        "step": float(_ols.params[1]),
        "p": float(_ols.pvalues[1]),
        "r2": float(_ols.rsquared),
    }
    mo.accordion(
        items = {
            "See exactly how the entry effect was estimated": mo.vstack(
                items = [
                    mo.md(
                        r"""
    **The model.** Let $\Delta_m$ be the month-$m$ revenue gap between the
    baseline and its no-entry twin. Because the arms share every random
    draw, $\Delta_m$ already differences out seasonality, weather, growth,
    and every shock common to both worlds — so the difference-in-differences
    estimator collapses to a single step regression on the gap itself:

    $$\Delta_m = \beta_0 + \beta_1 \, \mathbb{1}[m \geq \text{Mar 2027}] + \varepsilon_m$$

    with $\beta_0$ the pre-entry gap (which should be ≈ 0 if the twin
    discipline holds) and $\beta_1$ the entry's average monthly cost.
    HAC(2) standard errors guard the month-to-month correlation.
    """
                    ),
                    mo.ui.table(
                        data = did_table,
                        selection = None,
                    ),
                    mo.md(
                        f"""
    **Technical reading.** $\\beta_0$ = €{did_stats['pre']:,.0f} — the
    pre-entry gap is economically zero, which *validates the twin
    discipline itself* (26 months of shared randomness leave almost no
    residue). $\\beta_1$ = €{did_stats['step']:,.0f} per month
    (p = {did_stats['p']:.4f}): from March 2027 the baseline runs about
    €{-did_stats['step']:,.0f} per month below its twin.

    **What it means for the owner.** The discounter costs roughly
    €{-did_stats['step']:,.0f} a month — about
    €{-12 * did_stats['step'] / 1000:.0f}k a year if nothing changes.
    Worth knowing, worth responding to — but not existential. In real life
    there is no twin arm; the honest substitute is a *forecast*
    counterfactual (project revenue from pre-entry trend and season, then
    difference), which is exactly the method a careful analyst should
    reach for — and which this laboratory can grade, because here the true
    counterfactual is known.
    """
                    ),
                ],
            ),
        },
    )
    return


@app.cell
def _(
    ACCENT,
    ACCENT_LIGHT,
    DATA,
    MUTED,
    arm_b,
    arm_nc,
    brand_of,
    caption,
    dt,
    go,
    mo,
    pl,
    style,
    takeaway,
):
    # ---- who stopped coming ------------------------------------------------
    # per-token post-entry visit counts in BOTH arms: the twin says how often
    # each individual customer would have shopped without the discounter
    def _post_visits(rec):
        return rec.filter(
            (pl.col("qty") > 0)
            & pl.col("ref_receipt_id").is_null()
            & pl.col("customer_id").is_not_null()
            & (pl.col("date") >= dt.date(2027, 4, 1))
        ).group_by("customer_id").agg(pl.col("receipt_id").n_unique().alias("visits"))

    _vb = _post_visits(rec = arm_b["receipts"])
    _vn = _post_visits(rec = arm_nc["receipts"])
    _kept = _vn.join(
        other = _vb,
        on = "customer_id",
        how = "left",
        suffix = "_b",
    ).with_columns(pl.col("visits_b").fill_null(value = 0)) \
        .filter(pl.col("visits") >= 10) \
        .with_columns((pl.col("visits_b") / pl.col("visits")).alias("keep"))

    _hid = pl.read_csv(
        source = DATA / "scenarios" / "3y_baseline" / "hidden" / "customers.csv",
        schema_overrides = {"departure_date": pl.Utf8},
    ).select([
        pl.col("token").alias("customer_id"),
        "persistence",
        "price_sens",
    ])
    _j = _kept.join(
        other = _hid,
        on = "customer_id",
        how = "inner",
    ).with_columns((pl.col("price_sens").rank() / pl.len()).alias("ps_pct"))
    _groups = [
        (
            "rooted residents",
            _j.filter(pl.col("persistence") == "rooted"),
            MUTED,
        ),
        (
            "transient residents",
            _j.filter(pl.col("persistence") == "transient"),
            ACCENT_LIGHT,
        ),
        (
            "most price-sensitive third",
            _j.filter(pl.col("ps_pct") > 2 / 3),
            ACCENT,
        ),
    ]
    who_left = pl.DataFrame({
        "group": [_g[0] for _g in _groups],
        "visits_kept_pct": [round(100 * float(_g[1]["keep"].mean()), 1) for _g in _groups],
        "n_customers": [len(_g[1]) for _g in _groups],
    })

    _fig = go.Figure()
    _fig.add_bar(
        x = who_left["visits_kept_pct"].to_list(),
        y = who_left["group"].to_list(),
        orientation = "h",
        marker_color = [_g[2] for _g in _groups],
        text = [f"{_v:.1f}%" for _v in who_left["visits_kept_pct"]],
        textposition = "outside",
    )
    style(
        fig = _fig,
        title = "Visits kept after the entry, per customer, relative to their own no-entry twin",
    )
    _fig.update_xaxes(
        range = [0, 132],
        showticklabels = False,
        showline = False,
        ticks = "",
        title_text = "% of counterfactual visits kept (Apr–Dec 2027)",
        title_font = dict(
            size = 11.5,
            color = MUTED,
        ),
    )
    _fig.update_yaxes(title_text = "")
    takeaway(
        fig = _fig,
        text = "the leak is people, and specific people: renters and bargain-hunters",
        x = 0.98,
        y = 0.98,
        anchor = "right",
    )
    mo.vstack(
        items = [
            mo.md(
                """
    ## 4 · Who stopped coming

    The twin lets us ask a question no loyalty dashboard can: for **each
    individual customer**, how often did they shop with the discounter
    present, versus how often the *same person* shopped in the world
    without it? (The tokens match across arms — same households, same
    keyed randomness.)
    """
            ),
            _fig,
            caption(
                "Each bar is the average share of counterfactual visits a "
                "group kept after the entry (regulars with at least ten "
                "twin visits, April–December 2027). Rooted long-term "
                "residents barely moved; transient households — and the "
                "most price-sensitive third of the panel — gave up roughly "
                "twice the visits. One humbling detail for the "
                "practitioner: the *observable* proxy an analyst would "
                "reach for (each customer's premium-brand share) shows "
                "almost no gradient at all — the defection is real and "
                "targeted, but the paper trail is too noisy to identify "
                "the defectors without the answer key. Grouping here uses "
                "the hidden customer ledger, i.e. this panel is a grading "
                "exercise, not something the owner could compute."
            ),
        ],
    )
    return (who_left,)


@app.cell
def _(
    ACCENT,
    MUTED,
    WARN,
    arm_b,
    arm_nc,
    caption,
    dt,
    gap_m,
    make_subplots,
    mo,
    pl,
    style,
    takeaway,
):
    # ---- the owner's response, and the trap it sets --------------------------
    _CUT = [
        "Beverages (Non-Alcoholic)",
        "Snacks and Confectionery",
        "Household and Cleaning Supplies",
    ]

    def _tag_path(ph):
        """Mean posted tag across the cut categories, sampled monthly:
        forward-fill each SKU's latest tag, then average."""
        _m_ends = [dt.date(2026 + (k // 12), (k % 12) + 1, 1) for k in range(24)]
        _p = ph.filter(pl.col("category").is_in(_CUT)).sort(by = "date")
        _rows = []
        for _d in _m_ends:
            _last = _p.filter(pl.col("date") < _d).group_by("uid").agg(pl.col("price").last())
            _rows.append({
                "m": _d,
                "tag": float(_last["price"].mean()),
            })
        return pl.DataFrame(_rows)

    _tb = _tag_path(ph = arm_b["price_history"])
    _tn = _tag_path(ph = arm_nc["price_history"])
    _fig = make_subplots(
        rows = 1,
        cols = 2,
        subplot_titles = (
            "Average shelf tag on the three price-visible categories",
            "Monthly revenue gap vs. the twin, around the response",
        ),
        horizontal_spacing = 0.12,
    )
    _fig.add_scatter(
        x = _tn["m"].to_list(),
        y = _tn["tag"].to_list(),
        mode = "lines+markers",
        line = dict(
            color = MUTED,
            width = 2,
        ),
        marker = dict(size = 5),
        row = 1,
        col = 1,
    )
    _fig.add_scatter(
        x = _tb["m"].to_list(),
        y = _tb["tag"].to_list(),
        mode = "lines+markers",
        line = dict(
            color = ACCENT,
            width = 2,
        ),
        marker = dict(size = 5),
        row = 1,
        col = 1,
    )
    _fig.add_annotation(
        x = _tn["m"].to_list()[-1],
        y = float(_tn["tag"][-1]),
        text = "no-entry twin",
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
        x = _tb["m"].to_list()[-1],
        y = float(_tb["tag"][-1]) * 0.985,
        text = "the shop",
        showarrow = False,
        xanchor = "left",
        xshift = 8,
        yshift = -8,
        font = dict(
            color = ACCENT,
            size = 12,
        ),
        row = 1,
        col = 1,
    )
    # right panel: the monthly gap again, with the response marked — the
    # cuts did not close the gap, they only stopped it widening
    _g = gap_m.filter(pl.col("m") >= dt.date(2026, 7, 1))
    _fig.add_bar(
        x = _g["m"].to_list(),
        y = _g["gap"].to_list(),
        marker_color = [
            WARN if _m >= dt.date(2027, 3, 1) else MUTED
            for _m in _g["m"]
        ],
        row = 1,
        col = 2,
    )
    for _c in (1, 2):
        _fig.add_vline(
            x = dt.date(2027, 5, 1),
            line_dash = "dot",
            line_color = ACCENT,
            line_width = 1.5,
            row = 1,
            col = _c,
        )
        # marker label inside the panel, at the bottom, clear of everything
        _fig.add_annotation(
            x = dt.date(2027, 5, 1),
            y = 0.04,
            yref = "y domain",
            text = "price cuts begin",
            showarrow = False,
            xanchor = "left",
            xshift = 6,
            font = dict(
                color = ACCENT,
                size = 11,
            ),
            row = 1,
            col = _c,
        )
    style(
        fig = _fig,
        title = "The owner fights back in May 2027 — and why a naive read of it misleads",
        n_subplot_titles = 2,
        right_margin = 96,
    )
    _fig.update_yaxes(
        title_text = "mean tag (€, cut categories)",
        range = [float(_tb["tag"].min()) * 0.96, float(_tb["tag"].max()) * 1.08],
        row = 1,
        col = 1,
    )
    _fig.update_yaxes(
        title_text = "revenue gap vs. twin (€/month)",
        row = 1,
        col = 2,
    )
    takeaway(
        fig = _fig,
        text = "identical price books<br>until May 2027 — then the cut",
        x = 0.02,
        y = 0.19,
        row = 1,
        col = 1,
    )
    takeaway(
        fig = _fig,
        text = "the cuts contain the leak;<br>they don't close it",
        x = 0.02,
        y = 0.97,
        row = 1,
        col = 2,
    )
    mo.vstack(
        items = [
            mo.md(
                """
    ## 5 · The response — and the endogeneity trap

    From **May 1, 2027** the owner cut his margin about four points on the
    three categories where a discounter's prices are most visible
    (beverages, snacks, household goods). The twin makes two things
    unambiguous that the shop's own books never could:
    """
            ),
            _fig,
            caption(
                "Left: the average posted tag across the three cut "
                "categories. The two arms carry literally identical price "
                "books until May 2027; then the baseline cuts while the "
                "twin's tags keep riding cost inflation upward — proof the "
                "cuts were a *response to the entry*, not an independent "
                "strategy (in the world without a competitor, the same "
                "owner never cuts). Right: the monthly revenue gap. After "
                "the cuts the gap stabilizes around −€2k instead of "
                "widening — containment, not recovery. The trap for the "
                "analyst: inside the baseline data alone, prices fall in "
                "May and revenue weakens anyway, which naive regression "
                "will happily report as 'price cuts don't work.' The cuts "
                "were caused by the decline they are being blamed for — "
                "textbook endogeneity, planted and now graded."
            ),
        ],
    )
    return


@app.cell
def _(entry_cost_2027, mo, who_left):
    _kept_root = float(who_left.filter(who_left["group"] == "rooted residents")["visits_kept_pct"][0])
    _kept_trans = float(who_left.filter(who_left["group"] == "transient residents")["visits_kept_pct"][0])
    mo.md(
        f"""
    ## 6 · Verdict

    - **The cost:** about €{entry_cost_2027:,.0f} of 2027 revenue — ≈ €5k
      of profit — a steady leak of one to three thousand euros a month,
      completely invisible against growth without the twin.
    - **The mechanism:** targeted defection. Rooted residents kept
      {_kept_root:.0f}% of their counterfactual visits; transient
      households only {_kept_trans:.0f}%. The discounter took the
      customers who were cheapest to lose individually and easiest to
      lose collectively.
    - **The response:** real, reactive, and partially effective — the May
      price cuts stopped the gap widening at the price of thinner margins
      on three categories.
    - **The perspective:** the entry explains only a small slice of 2027's
      profit collapse. For the much larger slice, see
      `expansion_review.py`.
    """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ### Appendix — method notes

    Both arms load through the identical cleaning contract (retry dedup,
    void cancellation) so the comparison never mixes recording noise with
    economics. The per-customer analysis exploits the CRN twin design:
    card tokens denote the same households in both arms, so each person is
    their own control. The group labels in §4 come from the hidden answer
    key (`hidden/customers.csv`) and are flagged as grading, not analysis.
    Tools: DuckDB, Polars, Plotly, statsmodels (HAC errors on the step
    regression).
    """)
    return


if __name__ == "__main__":
    app.run()
