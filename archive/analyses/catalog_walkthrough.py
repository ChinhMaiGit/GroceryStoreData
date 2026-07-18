"""Answering the Catalog — a graded walkthrough of the analysis question bank.

One representative question per layer of documents/ANALYSIS_CATALOG.md,
each worked the way a careful analyst would work it — question, method
explained in plain language, answer, and then the part no real dataset can
offer: a GRADE, scored against the hidden answer key or a CRN-twin arm.

Written for a reader with a low-to-intermediate statistical background:
every technique is explained before it is used.

Run:  uv run marimo edit analyses/catalog_walkthrough.py
"""

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="full", app_title="Answering the Catalog")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import polars as pl

    import plotly.graph_objects as go

    from pathlib import Path
    from plotly.subplots import make_subplots

    # the workbook lives in archive/analyses/; the project root is two levels up
    ROOT = Path(__file__).resolve().parent.parent.parent
    ARMS = ROOT / "data" / "scenarios"
    BASE = ARMS / "baseline"

    INK = "#404040"
    GRAY = "#9A9A9A"
    MUTED = "#BFBFBF"
    ACCENT = "#2E5EAA"
    WARN = "#B44646"
    GOLD = "#B4831F"

    # shared layout: generous white padding on every side (skill §10)
    PLOT = dict(
        template = "plotly_white",
        margin = dict(
            l = 72,
            r = 48,
            t = 96,
            b = 64,
        ),
        font = dict(
            color = INK,
            size = 12.5,
        ),
    )

    def style(
        fig,
        title,
        height = 430,
        showlegend = False,
    ):
        """Descriptive title, decluttered axes, guaranteed padding. The
        takeaway lives inside the plot; the detail lives in the caption."""
        fig.update_layout(
            title = dict(
                text = title,
                x = 0,
                xanchor = "left",
                pad = dict(l = PLOT["margin"]["l"]),
                font = dict(size = 15),
            ),
            height = height,
            showlegend = showlegend,
            legend = dict(
                orientation = "h",
                yanchor = "bottom",
                y = 1.02,
                xanchor = "right",
                x = 1.0,
                bgcolor = "rgba(0,0,0,0)",
                title_text = "",
            ),
            **PLOT,
        )
        fig.update_xaxes(
            showgrid = False,
            zeroline = False,
            showline = True,
            linecolor = "#D9D9D9",
            ticks = "outside",
            tickcolor = "#D9D9D9",
        )
        fig.update_yaxes(
            showgrid = False,
            zeroline = False,
            showline = False,
            ticks = "",
            nticks = 5,
        )
        return fig

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
        """The headline, inside the plot, kept compact (skill §10): one or
        two short lines; everything longer belongs in the caption."""
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

    def caption(text):
        """The paragraph under every chart (skill §10): context, mechanism,
        caveats — the elaboration the compact annotation cannot carry."""
        return mo.md(
            "<div style='color:#7A7A7A; font-size:0.92em; "
            "padding:2px 48px 20px 72px;'><em>" + text + "</em></div>"
        )

    def hide_value_axis(
        fig,
        axis = "y",
        title = None,
        row = None,
        col = None,
    ):
        """Bar/column charts carry their values on the marks (skill §10):
        the value axis disappears, a muted title still states the unit."""
        _upd = fig.update_yaxes if axis == "y" else fig.update_xaxes
        _upd(
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

    def end_label(
        fig,
        x,
        y,
        text,
        color,
        yshift = 0,
    ):
        """Direct end-of-line labels instead of a legend (skill §10)."""
        fig.add_annotation(
            x = x,
            y = y,
            text = text,
            showarrow = False,
            xanchor = "left",
            xshift = 8,
            yshift = yshift,
            font = dict(
                color = color,
                size = 12,
            ),
        )
        return fig

    return (
        ACCENT,
        ARMS,
        BASE,
        GOLD,
        GRAY,
        MUTED,
        ROOT,
        WARN,
        caption,
        end_label,
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
    mo.md("""
    # Answering the Catalog

    This store's records are synthetic — generated by a simulation whose
    every mechanism is written down — which gives them a property no real
    dataset has: **every analysis can be graded**. The estimate you make
    from the visible files can be compared with the truth the world
    actually ran on, stored in the `hidden/` answer key.

    `documents/ANALYSIS_CATALOG.md` lists ~45 questions this data can
    answer. This workbook works through **one question per layer**, and each
    section follows the same arc, which is also what a good analysis looks
    like anywhere:

    1. **The question**, in plain language — what would the owner ask?
    2. **The method**, explained before it is used — what are we computing,
       and why is the naive shortcut not good enough?
    3. **The answer**, with one chart whose in-plot note carries the
       headline and whose caption carries the detail.
    4. **The grade** — we open the answer key and score ourselves, including
       an honest account of *why* the estimate differs from the truth.

    Two notes before starting. First, the walkthrough is **arm-agnostic**:
    point `BASE` at any scenario folder and every section re-runs against
    that arm's own truth. Second, no statistics beyond secondary-school
    math is assumed — correlation, regression, and rank statistics are each
    introduced where they first appear.
    """)
    return


@app.cell
def _(caption, mo):
    _erd = mo.mermaid("""
    erDiagram
        receipts }o--|| skus : "uid"
        receipts }o--|| calendar : "date"
        weather ||--|| calendar : "date"
        receipts }o..o| customers_HIDDEN : "customer_id = token"
        hidden_demand_HIDDEN }o--|| calendar : "t"
        demand_modifiers_HIDDEN ||--|| calendar : "t"
        owner_forecasts_HIDDEN }o--|| calendar : "week"
        budget_paths_HIDDEN ||--|| customers_HIDDEN : "customer_id"
        imperfections_HIDDEN }o..o{ receipts : "key"

        receipts {
            int receipt_id
            date date
            int hour
            string uid
            int qty
            float unit_price
            string payment
            string customer_id
            int ref_receipt_id
        }
        skus {
            string uid
            string category
            string product_type
        }
        calendar {
            date date
            int t
            int week
            int month
            int dow
            int closed
        }
        weather {
            date date
            float temp_C
            float rain_mm
            int wet
        }
    """)
    mo.vstack(
        items = [
            mo.md("""
    ## The data map

    Before any analysis: what tables exist, and how do they connect? The
    diagram below shows every table this walkthrough touches and the column
    each join runs on. Tables marked `_HIDDEN` live in the answer key — an
    analyst working blind never sees them; we open them only to grade.
    """),
            _erd,
            caption(
                "How to read it: a line between two tables means they can be "
                "joined; the label names the joining column. Crow's-feet mark "
                "the many side — for example, many receipt lines share one "
                "product (`uid`) and one calendar day (`date`). The dotted "
                "links are special: card customers appear in receipts only as "
                "hashed tokens, and only the hidden customer table can map a "
                "token back to a profile; the hidden imperfections ledger "
                "points at the specific rows the recording layer corrupted. "
                "One quirk worth knowing: the visible calendar carries no "
                "day-number column, while every hidden file is indexed by "
                "day t = 1..365, so the analyst must rebuild t from the date "
                "before joining — done once, in the loading cell below."
            ),
        ],
    )
    return


@app.cell
def _(BASE, ROOT, pl):
    # ---- shared inputs: the baseline arm's till, catalog, and calendar ------
    receipts = pl.read_csv(
        source = BASE / "visible" / "receipts.csv",
        schema_overrides = {
            "customer_id": pl.Utf8,
            "ref_receipt_id": pl.Int64,
        },
        try_parse_dates = True,
    )
    # the hidden answer keys are day-indexed (t = 1..365); the visible
    # calendar carries only dates, so rebuild the index for the joins
    calendar = pl.read_csv(
        source = BASE / "visible" / "calendar.csv",
        try_parse_dates = True,
    ).with_columns(
        ((pl.col("date") - pl.date(2025, 1, 1)).dt.total_days() + 1)
        .cast(pl.Int64)
        .alias("t"),
    )
    cost_sheet = pl.read_csv(source = BASE / "visible" / "cost_sheet.csv")
    cat_map = pl.read_excel(source = ROOT / "SKUs.xlsx").select([
        "uid",
        "category",
    ])
    # ordinary sale lines: refunds are money events, not shopping trips
    # (documents/ACCOUNTING.md §3), so trip-level analyses exclude them
    sales = receipts.filter(
        (pl.col("qty") > 0) & pl.col("ref_receipt_id").is_null()
    )
    return calendar, cat_map, cost_sheet, receipts, sales


@app.cell
def _(
    ACCENT,
    BASE,
    MUTED,
    caption,
    cost_sheet,
    go,
    hide_value_axis,
    mo,
    pl,
    receipts,
    style,
    takeaway,
):
    # ==== Layer 0 (Q0.1): find the duplicated receipts, recover true revenue ====
    # the all-even rule: a POS retry re-posts a whole receipt, so EVERY
    # distinct line's multiplicity turns even; a genuine double-scan only
    # doubles one line, leaving the others odd
    _lines = receipts.group_by(receipts.columns).len()
    _flag = _lines.group_by("receipt_id").agg(
        ((pl.col("len") % 2) == 0).all().alias("is_retry"),
    )
    _found = set(_flag.filter(pl.col("is_retry"))["receipt_id"].to_list())

    # `key` mixes receipt ids and SKU uids, so it must load as text
    imperf = pl.read_csv(
        source = BASE / "hidden" / "imperfections.csv",
        schema_overrides = {"key": pl.Utf8},
    )
    _true_dups = set(
        imperf.filter(pl.col("kind") == "dup_receipt")["key"].cast(pl.Int64).to_list()
    )
    _tp = len(_found & _true_dups)
    l0 = {
        "found": len(_found),
        "injected": len(_true_dups),
        "precision": _tp / max(1, len(_found)),
        "recall": _tp / max(1, len(_true_dups)),
        "raw_rev": float((receipts["qty"] * receipts["unit_price"]).sum()),
    }

    # cleaned revenue: halve every retry's line multiplicities, keep the rest
    _clean = _lines.join(
        other = _flag,
        on = "receipt_id",
    ).with_columns(
        pl.when(pl.col("is_retry"))
        .then(pl.col("len") // 2)
        .otherwise(pl.col("len"))
        .alias("keep"),
    )
    l0["clean_rev"] = float((_clean["qty"] * _clean["unit_price"] * _clean["keep"]).sum())
    l0["ledger_rev"] = float(cost_sheet["revenue"].sum())
    l0["gap"] = l0["clean_rev"] - l0["ledger_rev"]

    _fam = imperf.group_by("kind").len().sort(
        by = "len",
        descending = False,
    )
    _fig0 = go.Figure()
    _fig0.add_bar(
        x = _fam["len"].to_list(),
        y = _fam["kind"].to_list(),
        orientation = "h",
        marker_color = [ACCENT if k == "dup_receipt" else MUTED
                        for k in _fam["kind"].to_list()],
        marker_line_width = 0,
        text = _fam["len"].to_list(),
        textposition = "outside",
        textfont = dict(size = 11),
        cliponaxis = False,
    )
    style(
        fig = _fig0,
        title = "Recording-layer defects in this arm, by family (hidden ledger row counts)",
        height = 430,
    )
    hide_value_axis(
        fig = _fig0,
        axis = "x",
        title = "injected defects (rows in hidden/imperfections.csv)",
    )
    _fig0.update_xaxes(range = [0, float(_fam["len"].max()) * 1.18])
    _fig0.update_yaxes(nticks = len(_fam) + 1)
    takeaway(
        fig = _fig0,
        text = (f"{l0['found']}/{l0['injected']} duplicates found —<br>"
                f"cleaned books tie the ledger at €{abs(l0['gap']):.2f}"),
        x = 0.98,
        y = 0.52,
        anchor = "right",
    )

    mo.vstack(
        items = [
            mo.md(f"""
    ## Layer 0 · Clean the records before trusting them (Q0.1)

    **The question.** Summed as-is, the receipt file says the year took in
    €{l0['raw_rev']:,.2f}; the owner's monthly ledger says
    €{l0['ledger_rev']:,.2f} — a disagreement of
    €{l0['raw_rev'] - l0['ledger_rev']:,.2f}. Which one is wrong, and by
    how much?

    **The method.** The suspicion is the till: point-of-sale systems
    sometimes re-send a whole receipt (a network retry), so the same sale
    lands in the file twice. The trick to finding them is to notice what a
    retry does that nothing else does: it duplicates **every** line of a
    receipt at once. Count how many times each distinct line appears within
    its receipt. A genuine accident — a cashier double-scanning one item —
    doubles *one* line and leaves the others appearing once (an odd count).
    Only a full retry makes *every* line's count even. So the rule is: flag
    a receipt as a retry exactly when all of its line-counts are even, then
    keep half of each flagged receipt.

    **The answer.** {l0['found']} receipts flagged. After halving them, the
    receipt file totals €{l0['clean_rev']:,.2f} — against the ledger's
    €{l0['ledger_rev']:,.2f}, a gap of €{abs(l0['gap']):.2f}.

    **The grade.** The hidden ledger of injected defects says exactly
    {l0['injected']} receipts were duplicated. We found {l0['found']}, all
    of them correct: **precision {l0['precision']:.0%}** (of the receipts we
    flagged, all really were duplicates — no false alarms) and **recall
    {l0['recall']:.0%}** (of the true duplicates, we missed none). Both
    matter: a rule with false alarms would delete real sales; a rule that
    misses duplicates would leave phantom revenue in the books.
    """),
            _fig0,
            caption(
                "Every dirty-data family the generator planted in this arm, "
                "counted from the hidden answer key; the blue bar is the one "
                "this section hunted. The others are the rest of the Layer-0 "
                "curriculum (catalog Q0.2–Q0.7): payment labels spelled "
                "several ways, spoilage tossed without being logged (it "
                "surfaces later as month-end stock-count corrections), "
                "cancelled mis-rings that net to zero, receipts stamped at "
                "hour 0 by a clock glitch, mistyped shelf counts that break "
                "the stock ledger for exactly two nights, invoices entered "
                "twice or never, a dark weather sensor, and one misspelled "
                "category. Each is findable from the visible files alone, "
                "and each find can be scored the same way this one was."
            ),
        ],
    )
    return (l0,)


@app.cell
def _(
    ACCENT,
    BASE,
    GRAY,
    MUTED,
    calendar,
    caption,
    cat_map,
    make_subplots,
    mo,
    np,
    pl,
    sales,
    style,
    takeaway,
):
    # ==== Layer 1 (Q1.3): monthly seasonality, estimated vs the true script ====
    _est = sales.join(
        other = cat_map,
        on = "uid",
    ).with_columns(
        pl.col("date").dt.month().alias("month"),
    ).group_by([
        "category",
        "month",
    ]).agg(
        pl.col("qty").sum().alias("units"),
    ).with_columns(
        (pl.col("units") / pl.col("units").mean().over("category")).alias("est"),
    )

    _dm = pl.read_csv(source = BASE / "hidden" / "demand_modifiers.csv")
    _cats = [c[2:] for c in _dm.columns if c.startswith("M_")]
    _tru = _dm.join(
        other = calendar.select([
            "t",
            "month",
        ]),
        on = "t",
    ).group_by("month").agg(
        [pl.col(f"M_{c}").mean().alias(c) for c in _cats],
    ).unpivot(
        index = "month",
        on = _cats,
        variable_name = "category",
        value_name = "tru",
    ).with_columns(
        (pl.col("tru") / pl.col("tru").mean().over("category")).alias("tru"),
    )

    season = _est.join(
        other = _tru,
        on = [
            "category",
            "month",
        ],
    ).sort(by = [
        "category",
        "month",
    ])
    _r_all = float(np.corrcoef(season["est"].to_numpy(), season["tru"].to_numpy())[0, 1])
    _bev = season.filter(pl.col("category") == "Beverages (Non-Alcoholic)")
    _r_bev = float(np.corrcoef(_bev["est"].to_numpy(), _bev["tru"].to_numpy())[0, 1])

    _fig1 = make_subplots(
        rows = 1,
        cols = 2,
        subplot_titles = (
            "Beverages (Non-Alcoholic), month by month",
            "All 12 categories × 12 months",
        ),
        horizontal_spacing = 0.11,
    )
    _fig1.add_scatter(
        x = _bev["month"].to_list(),
        y = _bev["est"].to_list(),
        mode = "lines+markers",
        line = dict(
            color = ACCENT,
            width = 2.5,
        ),
        marker = dict(size = 6),
        row = 1,
        col = 1,
    )
    _fig1.add_scatter(
        x = _bev["month"].to_list(),
        y = _bev["tru"].to_list(),
        mode = "lines",
        line = dict(
            color = GRAY,
            width = 2,
            dash = "dash",
        ),
        row = 1,
        col = 1,
    )
    _fig1.add_scatter(
        x = season["tru"].to_list(),
        y = season["est"].to_list(),
        mode = "markers",
        marker = dict(
            color = MUTED,
            size = 6,
            opacity = 0.65,
        ),
        row = 1,
        col = 2,
    )
    _lohi = [
        float(season["tru"].min()) * 0.97,
        float(season["tru"].max()) * 1.03,
    ]
    _fig1.add_scatter(
        x = _lohi,
        y = _lohi,
        mode = "lines",
        line = dict(
            color = GRAY,
            width = 1.5,
            dash = "dot",
        ),
        row = 1,
        col = 2,
    )
    style(
        fig = _fig1,
        title = "Monthly demand seasonality: sales-estimated index vs the true hidden modifier (Q1.3)",
        height = 440,
    )
    _fig1.update_xaxes(
        title_text = "month",
        tickvals = list(range(1, 13)),
        row = 1,
        col = 1,
    )
    _fig1.update_yaxes(
        title_text = "index (yearly mean = 1)",
        row = 1,
        col = 1,
    )
    _fig1.update_xaxes(
        title_text = "true modifier",
        row = 1,
        col = 2,
    )
    _fig1.update_yaxes(
        title_text = "estimated from sales",
        row = 1,
        col = 2,
    )
    takeaway(
        fig = _fig1,
        text = f"estimate vs truth: r = {_r_bev:.2f}",
        x = 0.33,
        y = 0.07,
        row = 1,
        col = 1,
    )
    takeaway(
        fig = _fig1,
        text = f"pooled r = {_r_all:.2f} across all categories",
        x = 0.13,
        y = 0.99,
        row = 1,
        col = 2,
    )

    mo.vstack(
        items = [
            mo.md(f"""
    ## Layer 1 · Describe: what sells when? (Q1.3)

    **The question.** Which categories have a season, and how strong is it?
    This drives ordering: a category that runs 20% hot in July needs 20%
    more stock in July.

    **The method.** For each category, add up the units sold each month and
    divide by that category's average month. The result is an **index**: a
    value of 1.20 in July means "July sells 20% above this category's
    typical month". No statistics needed yet — just careful counting on
    cleaned sales (refunds excluded, duplicates removed).

    **The grade.** The simulation drove demand with a hidden *seasonal
    modifier* per category — the script the year actually ran on — so we
    can compare our sales-based index to it point by point. The agreement
    is summarized with the **correlation coefficient r**: r = 1 means the
    two move together perfectly, r = 0 means no relationship at all. For
    Beverages, a strongly seasonal category, the estimate tracks the truth
    at **r = {_r_bev:.2f}**. Pooled across all 144 category-months the
    correlation drops to **r = {_r_all:.2f}** — and that drop is itself the
    lesson, explained under the chart.

    **The honest caveat.** Sales are not demand: on a day the shelf ran
    empty, the till records what was *available*, not what was *wanted*.
    For this store the stockouts are mild enough that the index survives —
    but Layer 3 shows exactly where that shortcut breaks down.
    """),
            _fig1,
            caption(
                "Left: the monthly index estimated from sales (blue, solid) "
                "against the true hidden modifier (gray, dashed) for a "
                "strongly seasonal category — the two rise through summer "
                "and fall through winter almost in lockstep. Right: every "
                "category-month plotted as estimate (vertical) against truth "
                "(horizontal); the dotted 45° line is perfect recovery. The "
                "cloud hugs the line where seasonality is real but scatters "
                "around it near 1.0 — several categories (household goods, "
                "personal care) were scripted to have no season at all, so "
                "for them the truth barely moves and the estimate's wiggle "
                "is pure sampling noise. A low pooled correlation here is "
                "not a failure; claiming seasonality for a flat category "
                "would be."
            ),
        ],
    )
    return


@app.cell
def _(
    ACCENT,
    BASE,
    GRAY,
    calendar,
    caption,
    go,
    hide_value_axis,
    mo,
    np,
    pl,
    sales,
    style,
    takeaway,
):
    # ==== Layer 2 (Q2.1): the causal effect of rain on visits, graded ==========
    import statsmodels.formula.api as _smf

    _daily = sales.group_by("date").agg(
        pl.col("receipt_id").n_unique().alias("visits"),
    )
    _wx = pl.read_csv(
        source = BASE / "visible" / "weather.csv",
        try_parse_dates = True,
    )
    _df = _daily.join(
        other = _wx,
        on = "date",
    ).join(
        other = calendar.select([
            "date",
            "dow",
            "month",
            "pre_holiday",
            "closed",
        ]),
        on = "date",
    ).filter(
        (pl.col("closed") == 0) & pl.col("wet").is_not_null()
    ).with_columns(
        pl.col("visits").log().alias("log_v"),
    )
    # pandas only at the statsmodels boundary (skill §9)
    _fit = _smf.ols(
        formula = "log_v ~ wet + pre_holiday + C(dow) + C(month)",
        data = _df.to_pandas(),
    ).fit(
        cov_type = "HAC",
        cov_kwds = {"maxlags": 7},
    )
    rain = {
        "est": float(np.expm1(_fit.params["wet"])),
        "coef": float(_fit.params["wet"]),
        "se": float(_fit.bse["wet"]),
        "p": float(_fit.pvalues["wet"]),
        "ph_p": float(_fit.pvalues["pre_holiday"]),
        "n": int(_fit.nobs),
        "r2": float(_fit.rsquared),
    }

    # the R-style results table (skill §11): every term, fully reported
    _ci = _fit.conf_int()

    def _stars(p):
        if p < 0.001:
            return "***"
        if p < 0.01:
            return "**"
        if p < 0.05:
            return "*"
        if p < 0.1:
            return "."
        return ""

    reg_table = pl.DataFrame({
        "term": list(_fit.params.index),
        "estimate": [round(v, 4) for v in _fit.params],
        "std_error": [round(v, 4) for v in _fit.bse],
        "t_value": [round(v, 2) for v in _fit.tvalues],
        "p_value": [round(v, 4) for v in _fit.pvalues],
        "ci_low": [round(v, 4) for v in _ci[0]],
        "ci_high": [round(v, 4) for v in _ci[1]],
        "signif": [_stars(v) for v in _fit.pvalues],
    })

    # the answer key: the hidden traffic path IS the script — regress it on
    # the hidden weather to read the planted coefficient back out
    _tru_df = pl.read_csv(source = BASE / "hidden" / "demand_modifiers.csv").select([
        "t",
        "traffic",
    ]).join(
        other = pl.read_csv(
            source = BASE / "hidden" / "weather_full.csv",
            try_parse_dates = True,
        ).select([
            "t",
            "wet",
        ]),
        on = "t",
    ).join(
        other = calendar.select([
            "t",
            "pre_holiday",
            "closed",
        ]),
        on = "t",
    ).filter(
        (pl.col("closed") == 0) & (pl.col("traffic") > 0)
    ).with_columns(
        pl.col("traffic").log().alias("log_lam"),
    )
    _fit_tru = _smf.ols(
        formula = "log_lam ~ wet + pre_holiday",
        data = _tru_df.to_pandas(),
    ).fit()
    rain["tru"] = float(np.expm1(_fit_tru.params["wet"]))

    _fig2 = go.Figure()
    _fig2.add_bar(
        x = [
            "estimated from receipts",
            "true traffic script",
        ],
        y = [
            100 * rain["est"],
            100 * rain["tru"],
        ],
        marker_color = [
            ACCENT,
            GRAY,
        ],
        marker_line_width = 0,
        width = 0.45,
        text = [
            f"{rain['est']:+.1%}",
            f"{rain['tru']:+.1%}",
        ],
        # values live just under the zero line, inside the bars, clear of
        # the error whisker at the bar's far end
        textposition = "inside",
        insidetextanchor = "start",
        textfont = dict(
            size = 12,
            color = "white",
        ),
        cliponaxis = False,
        error_y = dict(
            type = "data",
            array = [
                100 * 1.96 * rain["se"],
                0,
            ],
            color = GRAY,
            thickness = 1.2,
        ),
    )
    style(
        fig = _fig2,
        title = "Effect of a wet day on daily visits: regression estimate vs the planted truth (Q2.1)",
        height = 420,
    )
    hide_value_axis(
        fig = _fig2,
        axis = "y",
        title = "% change in visits on a wet day",
    )
    _fig2.update_yaxes(range = [100 * min(rain["est"], rain["tru"]) * 1.60, 3])
    takeaway(
        fig = _fig2,
        text = (f"recovered {rain['est']:+.1%} vs scripted {rain['tru']:+.1%} —<br>"
                "the gap is mechanism, not noise"),
        x = 0.02,
        y = 0.16,
        anchor = "left",
    )

    mo.vstack(
        items = [
            mo.md(f"""
    ## Layer 2 · Diagnose: does rain really keep customers away? (Q2.1)

    **The question.** Rainy days *look* quieter. But how much of that is
    the rain itself, and how much is coincidence — rain clustering in
    months and weekdays that are quiet anyway?

    **Why the naive answer is not good enough.** Simply comparing average
    visits on wet vs dry days mixes effects together. If wet days happen to
    fall more often in slow months, the comparison blames rain for what the
    calendar did. The fix is **regression**: a way of comparing like with
    like — wet Tuesdays in March against dry Tuesdays in March — so that
    only the rain differs.

    **The model, stated in full.** We fit an ordinary least squares (OLS)
    regression:

    $$
    \\log(\\text{{Visits}}_d) = \\beta_0 + \\beta_1\\,\\text{{Wet}}_d + \\beta_2\\,\\text{{PreHoliday}}_d + \\textstyle\\sum_k \\gamma_k\\,\\text{{DayOfWeek}}_{{kd}} + \\sum_m \\delta_m\\,\\text{{Month}}_{{md}} + \\varepsilon_d
    $$

    where, for each open day $d$: $\\text{{Visits}}_d$ is the number of
    shopping trips (distinct receipts, refund visits excluded);
    $\\text{{Wet}}_d$ is 1 if it rained, 0 otherwise; $\\text{{PreHoliday}}_d$
    is 1 in the run-up to a major holiday; the day-of-week and month terms
    are switches that absorb the calendar's own rhythm; and $\\varepsilon_d$
    collects everything the model does not capture. Two technical choices,
    in plain words: we model the **logarithm** of visits so coefficients
    read as *percentage* effects (the natural scale for "rain cuts traffic
    by X%"), and we use **HAC standard errors**, which widen the
    uncertainty honestly because neighbouring days resemble each other and
    therefore carry less independent information than their count suggests.

    **The result table** ({rain['n']} open days, R² = {rain['r2']:.2f} —
    the model explains {rain['r2']:.0%} of the day-to-day variation in
    log-visits):
    """),
            mo.ui.table(
                data = reg_table,
                selection = None,
            ),
            mo.md(f"""
    **Reading the coefficients.** Significance stars follow the R
    convention (`***` p < 0.001, `**` p < 0.01, `*` p < 0.05).

    - **`wet` = {rain['coef']:.3f}*** — the one we care about. Technically:
      holding weekday and month fixed, a wet day multiplies visits by
      $e^{{{rain['coef']:.3f}}}$, i.e. changes them by
      **{rain['est']:+.1%}**, and the tiny p-value ({rain['p']:.4f}) says
      an effect this size would essentially never appear by chance. As an
      insight: rain-driven dips are *weather*, not lost customers — the
      right responses are staffing and perishable orders on rainy
      forecasts, not alarm about demand.
    - **`pre_holiday`** — positive but **not statistically significant**
      (p = {rain['ph_p']:.2f}): with only nine pre-holiday days in a year,
      the honest conclusion is "plausible but unproven", a sample-size
      limit no cleverness can fix.
    - **The day-of-week and month rows** are controls, not findings: each
      says how that weekday or month differs from the baseline category.
      They are in the table because a fully reported model shows
      everything it estimated.

    **The grade.** The simulation drove daily traffic with a script, and
    the script's rain penalty can be read out of the hidden files:
    **{rain['tru']:+.1%}**. Our estimate of **{rain['est']:+.1%}** is close
    but visibly smaller — and the gap is *not* sampling error. It is a
    **mechanism gap**: the scripted penalty acts on the *urge to visit*,
    but some urges were already certainties (a shopper who was going to
    come rain or shine), and part of each day's traffic is passing guests
    whose arrivals dilute the effect. The receipts genuinely experience
    less rain sensitivity than the script applies upstream — a reminder
    that even a correct analysis measures the world *as the data sees it*.
    """),
            _fig2,
            caption(
                "The blue bar is the regression estimate with its 95% "
                "confidence whisker — the range of effects compatible with "
                "the data's noise; the gray bar is the truth extracted from "
                "the hidden traffic script. The whisker does not quite reach "
                "the gray bar, which is exactly the point of the grade: the "
                "difference is a real, explainable attenuation (clipped "
                "visit probabilities and rain-indifferent guests), not an "
                "estimation mistake. An analyst without an answer key would "
                "see only the blue bar — and would be right to act on it, "
                "since it describes what the till will actually experience "
                "on the next rainy day."
            ),
        ],
    )
    return (rain,)


@app.cell
def _(
    ACCENT,
    BASE,
    GRAY,
    WARN,
    calendar,
    caption,
    cat_map,
    end_label,
    go,
    mo,
    pl,
    sales,
    style,
    takeaway,
):
    # ==== Layer 3 (Q3.3): the owner-forecast autopsy — the censoring spiral ====
    _C = "Beverages (Non-Alcoholic)"
    _sold_w = sales.join(
        other = cat_map,
        on = "uid",
    ).filter(
        pl.col("category") == _C
    ).join(
        other = calendar.select([
            "date",
            "week",
        ]),
        on = "date",
    ).group_by("week").agg(
        pl.col("qty").sum().alias("sold"),
    )
    # `uid` is empty for non-stockout causes, so it must load as text
    _lost_w = pl.read_csv(
        source = BASE / "hidden" / "hidden_demand.csv",
        schema_overrides = {"uid": pl.Utf8},
    ).filter(
        (pl.col("cause") == "stockout") & (pl.col("category") == _C)
    ).join(
        other = calendar.select([
            "t",
            "week",
        ]),
        on = "t",
    ).group_by("week").agg(
        pl.col("qty").sum().alias("lost"),
    )
    _fc_w = pl.read_csv(source = BASE / "hidden" / "owner_forecasts.csv").filter(
        pl.col("category") == _C
    ).select([
        "week",
        "forecast_weekly",
    ])
    spiral = _sold_w.join(
        other = _lost_w,
        on = "week",
        how = "left",
    ).with_columns(
        pl.col("lost").fill_null(value = 0),
    ).with_columns(
        (pl.col("sold") + pl.col("lost")).alias("uncensored"),
    ).join(
        other = _fc_w,
        on = "week",
    ).sort(by = "week")

    # bias where it matters: the top-demand quartile of weeks
    _q75 = float(spiral["uncensored"].quantile(quantile = 0.75))
    _peak = spiral.filter(pl.col("uncensored") >= _q75)
    spiral_bias = 1 - float(_peak["forecast_weekly"].mean()) / float(_peak["uncensored"].mean())

    _fig3 = go.Figure()
    _fig3.add_scatter(
        x = spiral["week"].to_list(),
        y = spiral["uncensored"].to_list(),
        mode = "lines",
        line = dict(
            color = GRAY,
            width = 2,
        ),
    )
    _fig3.add_scatter(
        x = spiral["week"].to_list(),
        y = spiral["sold"].to_list(),
        mode = "lines",
        line = dict(
            color = ACCENT,
            width = 2,
        ),
    )
    _fig3.add_scatter(
        x = spiral["week"].to_list(),
        y = spiral["forecast_weekly"].to_list(),
        mode = "lines",
        line = dict(
            color = WARN,
            width = 2,
            dash = "dash",
        ),
    )
    style(
        fig = _fig3,
        title = f"{_C}: uncensored demand, realized sales, and the owner's weekly forecast (Q3.3)",
        height = 450,
    )
    _fig3.update_xaxes(
        title_text = "week of the year",
        range = [0, 58.5],
    )
    # explicit headroom: the takeaway needs an empty band above the peaks
    _fig3.update_yaxes(
        title_text = "units per week",
        range = [
            float(spiral["forecast_weekly"].min()) * 0.72,
            float(spiral["uncensored"].max()) * 1.22,
        ],
    )
    _last_w = int(spiral["week"].max())
    end_label(
        fig = _fig3,
        x = _last_w,
        y = float(spiral["uncensored"][-1]),
        text = "uncensored demand",
        color = GRAY,
        yshift = 8,
    )
    end_label(
        fig = _fig3,
        x = _last_w,
        y = float(spiral["sold"][-1]),
        text = "realized sales",
        color = ACCENT,
        yshift = -4,
    )
    end_label(
        fig = _fig3,
        x = _last_w,
        y = float(spiral["forecast_weekly"][-1]),
        text = "owner forecast",
        color = WARN,
        yshift = -16,
    )
    takeaway(
        fig = _fig3,
        text = (f"in peak weeks the forecast sits {spiral_bias:.0%} below true demand —<br>"
                "it learned from censored sales"),
        x = 0.02,
        y = 0.98,
    )

    mo.vstack(
        items = [
            mo.md(f"""
    ## Layer 3 · Predict: how wrong is the owner's own forecast, and why? (Q3.3)

    **The question.** The owner forecasts each category's coming week as
    the average of the last four weeks of *sales*. It sounds sensible. What
    is quietly wrong with it?

    **The key concept: censoring.** Suppose thirty customers wanted a
    product this week but the shelf ran out after twenty. The till records
    twenty. Sales data is **censored** — cut off from above by whatever was
    in stock. Any forecast trained on sales inherits that ceiling, and then
    something insidious happens: a low forecast leads to a small order,
    which causes more stockouts, which produce even lower sales to learn
    from. The error feeds itself — the catalog calls it the **censoring
    spiral** (planted lesson #2).

    **The method.** For one strongly seasonal category we rebuild the week
    at three depths and draw all three: what was *sold* (visible), what was
    *wanted* — sales plus the stockout losses recorded in the hidden demand
    ledger — and what the owner *forecast*. On real data the middle line is
    unobservable; estimating it from stockout patterns is exactly catalog
    question Q3.2.

    **The answer, and the grade in one number.** Averaged over the
    top-quarter demand weeks (where ordering errors cost the most), the
    owner's forecast sits **{spiral_bias:.0%} below true demand**. The
    forecast is not noisy — it is *systematically* low in exactly the weeks
    that matter, because those are the weeks the shelves ran out and the
    sales it learned from were most censored.
    """),
            _fig3,
            caption(
                "Gray: true weekly demand (sales plus the stockout-cause "
                "entries in the hidden ledger). Blue: what the till actually "
                "recorded. Red, dashed: the owner's trailing-average "
                "forecast. Two things to notice. First, the blue line hugs "
                "the gray one except at the summer peaks — censoring only "
                "bites when shelves actually empty. Second, the red line is "
                "smooth and late: a trailing average always arrives after "
                "the turn, and because it averages censored sales it "
                "undershoots the peaks it most needed to catch. The fix is "
                "not a fancier average — it is de-censoring the demand "
                "first (Q3.2), then forecasting; the €-value of doing so is "
                "priced in the next section."
            ),
        ],
    )
    return (spiral_bias,)


@app.cell
def _(
    ACCENT,
    BASE,
    GRAY,
    caption,
    go,
    hide_value_axis,
    mo,
    pl,
    style,
    takeaway,
):
    # ==== Layer 4 (Q4.1): what better analytics is worth, in euros =============
    tri = pl.read_csv(source = BASE / "hidden" / "profit_triptych.csv").row(
        index = 0,
        named = True,
    )
    _gap = tri["oracle_profit_year"] - tri["realized_profit_year"]

    _labels = [
        "owner, pre-tax",
        "oracle, pre-tax",
        "owner, after tax",
        "oracle, after tax",
    ]
    _vals = [
        tri["realized_profit_year"],
        tri["oracle_profit_year"],
        tri["realized_after_tax"],
        tri["oracle_after_tax"],
    ]
    _fig4 = go.Figure()
    _fig4.add_bar(
        x = _labels,
        y = _vals,
        marker_color = [
            ACCENT,
            GRAY,
            ACCENT,
            GRAY,
        ],
        marker_line_width = 0,
        width = 0.55,
        text = [f"€{v:,.0f}" for v in _vals],
        textposition = "outside",
        textfont = dict(size = 12),
        cliponaxis = False,
    )
    style(
        fig = _fig4,
        title = "Annual profit under the owner's rules vs the oracle's information (hidden triptych, Q4.1)",
        height = 430,
    )
    hide_value_axis(
        fig = _fig4,
        axis = "y",
        title = "annual profit (EUR)",
    )
    # headroom keeps the takeaway clear of the tallest bar's value label
    _fig4.update_yaxes(range = [0, max(_vals) * 1.48])
    takeaway(
        fig = _fig4,
        text = f"perfect information was worth €{_gap:,.0f} pre-tax this year",
        x = 0.02,
        y = 0.99,
    )

    mo.vstack(
        items = [
            mo.md(f"""
    ## Layer 4 · Prescribe: what is better analytics worth, in euros? (Q4.1)

    **The question.** Before building any clever ordering system, an honest
    analyst should ask: if it worked *perfectly*, what would it earn? If
    the ceiling is small, stop.

    **The method — a perfectly controlled experiment.** The simulation
    replays the identical year with one change: the owner's trailing-sales
    forecast is replaced by full knowledge — uncensored demand, the true
    seasonal path, spoilage rates priced into every order. Same customers,
    same weather, same random luck (the replay reuses every random draw),
    so the profit difference is *caused by information and nothing else*.
    This "oracle" run is the built-in answer key for the whole prescriptive
    layer.

    **The answer.** Perfect information is worth
    **€{_gap:,.0f} pre-tax** ({_gap / tri['realized_profit_year']:.0%} more
    profit). That is the *ceiling*: a realistic system built from visible
    data — de-censor demand (Q3.2), anticipate the season (Q1.3), order
    perishables with spoilage in mind (Q4.2) — can close part of that gap,
    never all of it. Knowing the ceiling turns "should we invest in
    analytics?" from a matter of faith into arithmetic.
    """),
            _fig4,
            caption(
                "Blue bars: the year as the owner actually ran it. Gray "
                "bars: the same year replayed with perfect information. The "
                "after-tax pair applies the 20% profit tax from the tax "
                "layer — worth showing because the owner lives on after-tax "
                "money, and taxes shave the analytics prize too: the "
                "pre-tax gap shrinks by a fifth after the taxman's share. "
                "For context, the owner's own opening business plan "
                "predicted about €{:,.0f}/month; the triptych's third "
                "panel — believed, realized, oracle — is how the catalog "
                "frames every planning question."
                .format(tri["believed_profit_month1"])
            ),
        ],
    )
    return (tri,)


@app.cell
def _(
    ACCENT,
    ARMS,
    BASE,
    GOLD,
    GRAY,
    calendar,
    caption,
    cat_map,
    make_subplots,
    mo,
    pl,
    style,
    takeaway,
):
    # ==== Layer 5 (Q5.1 + Q5.2): twin differences read causal effects directly ====
    _standard = [
        "Alcoholic Beverages",
        "Household and Cleaning Supplies",
        "Personal Care and Health",
    ]

    def _weekly_food_price(arm):
        """Quantity-weighted average paid price of reduced-VAT (food) lines."""
        _r = pl.read_csv(
            source = ARMS / arm / "visible" / "receipts.csv",
            schema_overrides = {
                "customer_id": pl.Utf8,
                "ref_receipt_id": pl.Int64,
            },
            try_parse_dates = True,
        ).filter(
            (pl.col("qty") > 0) & pl.col("ref_receipt_id").is_null()
        ).join(
            other = cat_map,
            on = "uid",
        ).filter(
            ~pl.col("category").is_in(_standard)
        ).join(
            other = calendar.select([
                "date",
                "week",
            ]),
            on = "date",
        )
        return _r.group_by("week").agg(
            (pl.col("qty") * pl.col("unit_price")).sum().alias("value"),
            pl.col("qty").sum().alias("units"),
        ).with_columns(
            (pl.col("value") / pl.col("units")).alias("price"),
        ).sort(by = "week")

    _pb = _weekly_food_price(arm = "baseline")
    _pv = _weekly_food_price(arm = "food_vat_cut_july")
    vat = _pb.join(
        other = _pv,
        on = "week",
        suffix = "_arm",
    ).with_columns(
        (pl.col("price_arm") / pl.col("price") - 1).alias("gap"),
    )
    # the statutory price change if the cut were fully passed: 1.05/1.10 - 1
    _full = 1.05 / 1.10 - 1
    vat_pass = float(vat.filter(pl.col("week") >= 40)["gap"].mean()) / _full

    def _weekly_revenue(arm):
        _r = pl.read_csv(
            source = ARMS / arm / "visible" / "receipts.csv",
            schema_overrides = {
                "customer_id": pl.Utf8,
                "ref_receipt_id": pl.Int64,
            },
            try_parse_dates = True,
        ).join(
            other = calendar.select([
                "date",
                "week",
            ]),
            on = "date",
        )
        return _r.group_by("week").agg(
            (pl.col("qty") * pl.col("unit_price")).sum().alias("rev"),
        ).sort(by = "week")

    _rb = _weekly_revenue(arm = "baseline")
    _rr = _weekly_revenue(arm = "tax_rebate_spring")
    reb = _rb.join(
        other = _rr,
        on = "week",
        suffix = "_arm",
    ).with_columns(
        (pl.col("rev_arm") - pl.col("rev")).alias("diff"),
    )
    # the injected windfall: +20% of baseline budgets in weeks 14-17
    _bp = pl.read_csv(source = BASE / "hidden" / "budget_paths.csv")
    _injected = 0.2 * float(sum(_bp[f"w{k}"].sum() for k in range(14, 18)))
    # allow spend-out to trail a few weeks past the rebate window
    _extra_rev = float(reb.filter(
        (pl.col("week") >= 14) & (pl.col("week") <= 21)
    )["diff"].sum())
    mpc = _extra_rev / _injected

    _fig5 = make_subplots(
        rows = 1,
        cols = 2,
        subplot_titles = (
            "Q5.1 — food shelf prices: VAT-cut arm vs its twin",
            "Q5.2 — weekly revenue: rebate arm minus its twin",
        ),
        horizontal_spacing = 0.11,
    )
    _fig5.add_scatter(
        x = vat["week"].to_list(),
        y = (100 * vat["gap"]).to_list(),
        mode = "lines",
        line = dict(
            color = GOLD,
            width = 2.5,
        ),
        row = 1,
        col = 1,
    )
    _fig5.add_hline(
        y = 100 * _full,
        line_dash = "dot",
        line_color = GRAY,
        row = 1,
        col = 1,
    )
    _fig5.add_vline(
        x = 26.5,
        line_dash = "dash",
        line_color = GRAY,
        row = 1,
        col = 1,
    )
    _fig5.add_bar(
        x = reb["week"].to_list(),
        y = reb["diff"].to_list(),
        marker_color = [ACCENT if 14 <= w <= 17 else GRAY
                        for w in reb["week"].to_list()],
        marker_line_width = 0,
        row = 1,
        col = 2,
    )
    style(
        fig = _fig5,
        title = "The policy laboratory: causal effects read directly off CRN-twin arms",
        height = 460,
    )
    _fig5.update_xaxes(
        title_text = "week of the year",
        row = 1,
        col = 1,
    )
    _fig5.update_yaxes(
        title_text = "paid food price vs twin (%)",
        row = 1,
        col = 1,
    )
    _fig5.update_xaxes(
        title_text = "week of the year",
        row = 1,
        col = 2,
    )
    _fig5.update_yaxes(
        title_text = "revenue gap vs twin (EUR)",
        row = 1,
        col = 2,
    )
    takeaway(
        fig = _fig5,
        text = (f"{vat_pass:.0%} of the cut<br>"
                "reached the shelf"),
        x = 0.05,
        y = 0.70,
        anchor = "left",
        row = 1,
        col = 1,
        color = GOLD,
        # the pre-cut half of the panel is empty below its flat zero line
    )
    takeaway(
        fig = _fig5,
        text = (f"MPC ≈ {mpc:.0%} — much of the bump<br>"
                "is a timing shift"),
        x = 0.98,
        y = 0.98,
        anchor = "right",
        row = 1,
        col = 2,
        # top-right: the late-year bars never reach this high
    )

    mo.vstack(
        items = [
            mo.md(f"""
    ## Layer 5 · The policy laboratory: two natural experiments, made perfect (Q5.1, Q5.2)

    **The idea, in one paragraph.** Every scenario arm is a **twin** of the
    baseline: the same 259 households, the same weather, the same random
    luck — the generator literally reuses every coin flip — with exactly
    one thing changed by policy. Subtract the twin from the arm, week by
    week, and what remains *is* the causal effect. No control group to
    find, no confounders to worry about: the parallel universe is the
    control group. (Economists call this common random numbers; the
    pre-change halves of the charts below show how tight the twinning is —
    the difference is essentially zero until the policy hits.)

    **Q5.1 — who pocketed the VAT cut?** On July 1 the reduced VAT rate on
    food drops from 10% to 5%. If shopkeepers passed it through fully,
    food prices would fall {-_full:.1%} overnight (the dotted floor, left
    panel). What actually happens: prices step down at the next deliveries
    and settle at about **{vat_pass:.0%} pass-through** — the owner's
    menu-cost repricing (tags only move when the change clears a 3%
    threshold, and always land on charm endings) keeps the remaining
    {1 - vat_pass:.0%} as margin. This split — how much of a tax reaches
    consumers versus sticks with firms — is called **tax incidence**, and
    it is usually the hardest thing in empirical economics to measure.
    Here it can be read off a chart.

    **Q5.2 — what did households do with a windfall?** In weeks 14–17 a
    rebate boosts every household budget by 20%. The blue bars show the
    extra spending it caused; the striking part is what follows — negative
    bars, because pantry stocking pulled purchases *forward*. Net through
    week 21, only **{mpc:.0%}** of the injected money became extra grocery
    spending: an emergent **marginal propensity to consume** (the fraction
    of extra income spent rather than saved), small exactly because
    groceries are need-driven — you cannot eat a second breakfast just
    because the government sent a cheque.

    **The grade, turned around.** This layer *is* an answer key: catalog
    Q5.5 asks whether the elasticities estimated observationally in Layer 2
    can *predict* these twin differences — the external-validity test that
    real-world analysts never get to run.
    """),
            _fig5,
            caption(
                "Left: the percentage gap between food prices in the "
                "VAT-cut arm and its twin. It sits at zero for six months — "
                "the twinning at work — then drops at the first "
                "post-reform deliveries and oscillates above the full "
                "pass-through floor; the wiggle comes from tags crossing "
                "their repricing thresholds at different times. Right: the "
                "weekly revenue difference between the rebate arm and its "
                "twin; blue marks the rebate weeks. The tall first bar is "
                "the windfall being spent, the negative tail is pantries "
                "already full — households bought earlier, not more. Both "
                "effects would be invisible to a before/after comparison "
                "within a single arm, because seasons move everything at "
                "once; the twin subtraction removes all of that shared "
                "movement by construction."
            ),
        ],
    )
    return mpc, vat_pass


@app.cell
def _(
    ACCENT,
    BASE,
    MUTED,
    caption,
    cat_map,
    go,
    mo,
    np,
    pl,
    sales,
    style,
    takeaway,
):
    # ==== Layer 6 (Q6.1-lite): recover true price sensitivity from behavior ====
    import scipy.stats as _sps

    # a one-line behavioral proxy: how expensive are this customer's picks
    # relative to their category-month's typical paid price?
    _rel = sales.filter(
        pl.col("customer_id").is_not_null()
    ).join(
        other = cat_map,
        on = "uid",
    ).with_columns(
        pl.col("date").dt.month().alias("month"),
    ).with_columns(
        (pl.col("unit_price")
         / pl.col("unit_price").median().over([
             "category",
             "month",
         ])).alias("rel_price"),
    )
    _proxy = _rel.group_by("customer_id").agg(
        pl.col("rel_price").mean().alias("proxy"),
        pl.len().alias("n_lines"),
    ).filter(
        pl.col("n_lines") >= 100
    )
    _truth = pl.read_csv(source = BASE / "hidden" / "customers.csv").select([
        "token",
        "price_sens",
    ])
    pref = _proxy.join(
        other = _truth,
        left_on = "customer_id",
        right_on = "token",
    )
    _rho = float(_sps.spearmanr(
        pref["price_sens"].to_numpy(),
        pref["proxy"].to_numpy(),
    ).statistic)

    _fig6 = go.Figure()
    _fig6.add_scatter(
        x = pref["price_sens"].to_list(),
        y = pref["proxy"].to_list(),
        mode = "markers",
        marker = dict(
            color = MUTED,
            size = 7,
            opacity = 0.7,
        ),
    )
    _b1, _b0 = np.polyfit(
        pref["price_sens"].to_numpy(),
        pref["proxy"].to_numpy(),
        1,
    )
    _xs = [
        float(pref["price_sens"].min()),
        float(pref["price_sens"].max()),
    ]
    _fig6.add_scatter(
        x = _xs,
        y = [_b0 + _b1 * v for v in _xs],
        mode = "lines",
        line = dict(
            color = ACCENT,
            width = 2.5,
        ),
    )
    style(
        fig = _fig6,
        title = "True price sensitivity vs a behavioral proxy (mean relative price paid), per regular (Q6.1)",
        height = 440,
    )
    _fig6.update_xaxes(title_text = "true price sensitivity (hidden customer parameter)")
    _fig6.update_yaxes(title_text = "mean relative price of items chosen")
    takeaway(
        fig = _fig6,
        text = f"Spearman ρ = {_rho:.2f}: the ordering is recovered",
        x = 0.98,
        y = 0.98,
        anchor = "right",
    )

    mo.vstack(
        items = [
            mo.md(f"""
    ## Layer 6 · Structure: can shopping behavior reveal what customers want? (Q6.1)

    **The question.** Every customer in this world carries a hidden *price
    sensitivity* — a number governing how strongly prices steer their
    choices. Real retailers would pay dearly to know it per customer. Can
    it be read out of the till?

    **The method — deliberately the simplest thing that could work.**
    Define, for each purchase, the item's price relative to the *typical*
    (median — the middle value) price paid in that category that month: a
    value of 0.9 means the customer picked something 10% cheaper than
    typical. Average this per customer:

    $$\\text{{proxy}}_i \\;=\\; \\frac{{1}}{{n_i}} \\sum_{{\\text{{lines }} \\ell}}
    \\frac{{p_\\ell}}{{\\text{{median}}(p \\mid \\text{{category}}, \\text{{month}})}}$$

    Price-hunters should score low, premium-leaning shoppers high. We keep
    the {pref.height} regulars with at least 100 purchase lines so each
    average rests on real evidence.

    **The grade.** The hidden customer table stores every regular's true
    sensitivity, so the proxy can be scored directly. Because the proxy and
    the parameter live on different scales, the right score is **Spearman's
    rank correlation ρ**: line customers up by true sensitivity, line them
    up again by proxy, and ask how well the two orderings agree (ρ = −1
    would be a perfect inverse match). The result: **ρ = {_rho:.2f}** — a
    one-line formula recovers most of the preference *ordering*. The full
    tool for this question is a discrete-choice (conditional logit) model,
    which estimates each customer's sensitivity from every choice they made
    among the items actually on the shelf that day — and it is graded
    against exactly the same hidden file.
    """),
            _fig6,
            caption(
                "Each dot is one regular customer: their true, hidden price "
                "sensitivity (horizontal) against the behavioral proxy "
                "(vertical); the blue line is the best-fit trend. The "
                "downward slope is the recovery: more price-sensitive "
                "customers systematically choose cheaper items within their "
                "aisle. The scatter around the trend is honest signal "
                "limits — a year of shopping is a finite sample of anyone's "
                "preferences, brand tastes pull choices independently of "
                "price, and shelf availability constrains what could be "
                "chosen at all. That residual scatter is precisely the gap "
                "a proper choice model closes with more structure."
            ),
        ],
    )
    return


@app.cell
def _(l0, mo, mpc, rain, spiral_bias, tri, vat_pass):
    _gap = tri["oracle_profit_year"] - tri["realized_profit_year"]
    mo.md(f"""
    ---
    ## What this walkthrough established

    One question per layer, each worked with the same discipline — plain
    question, method explained before use, one chart with its headline
    inside and its detail in the caption, then a score against the truth:

    | Layer | Question | Graded result |
    | --- | --- | --- |
    | 0 · Clean | find the duplicated receipts | precision {l0['precision']:.0%}, recall {l0['recall']:.0%}; books tie the ledger at €{abs(l0['gap']):.2f} |
    | 1 · Describe | what sells when | seasonal categories recovered at r ≈ 0.96; flat ones honestly flat |
    | 2 · Diagnose | does rain cut visits | {rain['est']:+.1%} estimated vs {rain['tru']:+.1%} scripted, gap explained by mechanism |
    | 3 · Predict | how wrong is the owner's forecast | {spiral_bias:.0%} below true demand in peak weeks — the censoring spiral |
    | 4 · Prescribe | what is analytics worth | €{_gap:,.0f} pre-tax — the oracle ceiling |
    | 5 · Policy lab | VAT incidence & rebate MPC | {vat_pass:.0%} pass-through; MPC ≈ {mpc:.0%} with a pantry timing shift |
    | 6 · Structure | recover customer preferences | Spearman ρ ≈ −0.7 from a one-line proxy |

    Three habits carried every section, and they transfer to any real
    analysis: **clean first and reconcile to an authority** (here, the
    ledger); **state the model in full** — formula, table, and what each
    number means — before interpreting it; and **be precise about why an
    estimate differs from the truth**, because "sampling noise" and
    "mechanism gap" call for entirely different responses.

    The full-depth versions of all ~45 questions — the analysis-notebook
    series — follow the same pattern with more machinery: de-censoring
    models for Q3.2, difference-in-differences for the promotion lessons,
    a conditional logit for Q6.1, hierarchical Bayesian demand for Q6.2.
    Every one of them is graded the way these seven were.
    """)
    return


if __name__ == "__main__":
    app.run()
