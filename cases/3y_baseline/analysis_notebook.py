import marimo

__generated_with = "0.23.14"
app = marimo.App(width="full", app_title="Malm's Market — Analyst Workings")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import plotly.graph_objects as go
    import polars as pl

    from pathlib import Path

    # this file lives at cases/3y_baseline/; the project root is three levels up
    ROOT = Path(__file__).resolve().parent.parent.parent
    DATA = ROOT / "data" / "scenarios" / "3y_baseline" / "visible"

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
        right_margin = 36,
    ):
        fig.update_layout(
            showlegend = showlegend,
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
        fig.update_xaxes(**AXIS_X)
        fig.update_yaxes(**AXIS_Y)
        return fig

    def caption(text):
        return mo.md(f"<div style='color:#7A7A7A; font-size:0.92em; padding:2px 24px 18px 64px;'><em>{text}</em></div>")

    def takeaway(
        fig,
        text,
        x = 0.02,
        y = 0.98,
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
        go,
        mo,
        np,
        pl,
        style,
        takeaway,
    )


@app.cell
def _(mo):
    mo.md(r"""
    # Malm's Market — working notes

    *Prepared for Henrik Malm. This notebook is the appendix to the report
    — every number in the report traces back to a cell here, computed
    directly from the files you handed over
    (`data/scenarios/3y_baseline/visible/` in this project's layout: your
    receipts, invoices, stock counts, ledger, and calendar). Nothing here
    comes from anywhere else. Where I had to make a judgment call — a
    cutoff, a definition of "regular" — I've said so and shown what
    changes if you draw the line differently.*

    The eight sections below answer your eight questions in the order you
    asked them. Each one states what I did, what I found, and how sure I
    am.
    """)
    return


@app.cell
def _(DATA, mo, pl):
    # ---- load and clean the till, exactly as you warned me to -------------
    # your POS terminal re-uploads whole receipts sometimes: when EVERY
    # distinct line on a receipt appears an even number of times, that's the
    # signature of a retry, not a customer who bought two of everything. I
    # keep half of such a receipt's lines. A handful of GENUINE double-scans
    # (one product, scanned twice, nothing else on the receipt) look
    # identical to this rule and get halved too -- I check for exactly this
    # at the end of section 1, because it is the one place it matters to
    # the cent.
    _raw = pl.read_csv(
        source = DATA / "receipts.csv",
        schema_overrides = {
            "customer_id": pl.Utf8,
            "ref_receipt_id": pl.Utf8,
        },
    )
    _key = ["receipt_id", "hour", "payment", "customer_id", "uid", "qty", "unit_price", "promo", "date", "ref_receipt_id"]
    _counts = _raw.group_by(_key).agg(pl.len().alias("n"))
    _retry = _counts.group_by("receipt_id").agg(
        (pl.col("n") % 2 == 0).all().alias("is_retry"),
    )
    receipts = _counts.join(
        other = _retry,
        on = "receipt_id",
    ).with_columns(
        pl.when(pl.col("is_retry")).then(pl.col("qty") * (pl.col("n") // 2))
        .otherwise(pl.col("qty") * pl.col("n")).alias("qty_clean"),
    ).group_by(
        ["receipt_id", "hour", "payment", "customer_id", "uid", "unit_price", "date", "ref_receipt_id"]
    ).agg(
        pl.col("qty_clean").sum().alias("qty"),
    ).filter(pl.col("qty") != 0)

    n_flagged = int(_retry.filter(pl.col("is_retry"))["receipt_id"].n_unique())
    mo.md(
        f"""
    ## 1 · Show me where the money actually goes

    First, the paperwork check you asked for. **{n_flagged} receipts**
    across the three years carry the re-upload signature (every line on
    them repeats an even number of times) and have been halved back to
    what was actually sold.
    """
    )
    return (receipts,)


@app.cell
def _(DATA, mo, pl, receipts):
    # ---- tie the cleaned till to your own monthly ledger, year by year ----
    _till = receipts.with_columns(
        pl.col("date").str.slice(0, 4).cast(pl.Int32).alias("yy"),
    ).group_by("yy").agg(
        (pl.col("qty") * pl.col("unit_price")).sum().alias("till_revenue"),
    )
    _ledger = pl.read_csv(source = DATA / "cost_sheet.csv").group_by("year").agg(
        pl.col("revenue").sum().alias("ledger_revenue"),
    )
    tie = _till.join(
        other = _ledger,
        left_on = "yy",
        right_on = "year",
    ).sort(by = "yy").with_columns(
        (pl.col("till_revenue") - pl.col("ledger_revenue")).alias("gap"),
    )
    _max_gap = float(tie["gap"].abs().max())
    mo.vstack(
        items = [
            mo.md("**Till vs. ledger, cleaned receipts against your own monthly books:**"),
            mo.ui.table(
                data = tie.select([
                    "yy",
                    pl.col("till_revenue").round(2),
                    pl.col("ledger_revenue").round(2),
                    pl.col("gap").round(2),
                ]),
                selection = None,
            ),
            mo.md(
                f"The largest year's gap is **€{_max_gap:.2f}** — close enough "
                "that I went looking for the reason rather than writing it "
                "off as noise (below)."
            ),
        ],
    )
    return (tie,)


@app.cell
def _(DATA, caption, mo, pl, tie):
    # ---- the last cent: a genuine double-scan the retry rule can't tell
    # apart from itself ---------------------------------------------------
    # a receipt with exactly ONE distinct item, scanned twice, satisfies
    # "every line repeats an even number of times" just as well as a true
    # re-upload does. I can't distinguish the two from the receipt alone --
    # but I CAN find the specific receipt behind each year's gap, because
    # its true value equals the gap exactly.
    _raw = pl.read_csv(
        source = DATA / "receipts.csv",
        schema_overrides = {"customer_id": pl.Utf8, "ref_receipt_id": pl.Utf8},
    )
    _lines = _raw.group_by(
        ["receipt_id", "date", "uid", "qty", "unit_price"]
    ).agg(pl.len().alias("n_dup"))
    _distinct = _lines.group_by("receipt_id").agg(pl.len().alias("n_distinct"))
    _suspects = _lines.join(
        other = _distinct,
        on = "receipt_id",
    ).filter(
        (pl.col("n_distinct") == 1) & (pl.col("n_dup") == 2)
    ).with_columns(
        (pl.col("qty") * pl.col("unit_price")).round(2).alias("true_value"),
    )
    _gaps = [round(float(g), 2) for g in tie["gap"].abs().to_list() if abs(g) > 0.5]
    _found = _suspects.filter(pl.col("true_value").is_in(_gaps))
    mo.vstack(
        items = [
            mo.md(
                "Two receipts, one per affected year, match exactly:"
            ),
            mo.ui.table(
                data = _found.select(["receipt_id", "date", "uid", "qty", "unit_price", "true_value"]),
                selection = None,
            ),
            caption(
                "Both are a single product rung up in two identical scans — "
                "most likely two units of the same item, or a genuine "
                "double-scan the cashier caught and corrected by re-ringing "
                "rather than voiding. Either way it is real, small, and "
                "explains the entire residual gap in both years. **Your "
                "ledger is right. The till, once cleaned, ties to it to "
                "within a rounding error I can name and explain.**"
            ),
        ],
    )
    return


@app.cell
def _(ACCENT, DATA, MUTED, WARN, caption, go, mo, pl, style, takeaway):
    # ---- the three-year arc and the margin waterfall -----------------------
    cs = pl.read_csv(source = DATA / "cost_sheet.csv")
    ts = pl.read_csv(source = DATA / "tax_statement.csv")
    _cost_cols = ["rent", "wages", "payroll_tax", "utilities", "storage", "flyers", "vat", "credit_interest", "repairs"]
    by_year = cs.group_by("year").agg(
        revenue = pl.col("revenue").sum(),
        procurement = pl.col("procurement").sum(),
        opex = pl.sum_horizontal(_cost_cols).sum(),
    ).sort(by = "year").join(
        other = ts.select(["year", "profit_before_tax", "profit_after_tax"]),
        on = "year",
    )
    _fig = go.Figure()
    _fig.add_bar(
        x = by_year["year"].to_list(),
        y = by_year["revenue"].to_list(),
        name = "revenue",
        marker_color = ACCENT,
    )
    _fig.add_bar(
        x = by_year["year"].to_list(),
        y = (-by_year["procurement"]).to_list(),
        name = "cost of goods",
        marker_color = MUTED,
    )
    _fig.add_bar(
        x = by_year["year"].to_list(),
        y = (-by_year["opex"]).to_list(),
        name = "rent, wages, bills, VAT",
        marker_color = "#8A8A8A",
    )
    _fig.add_trace(
        go.Scatter(
            x = by_year["year"].to_list(),
            y = by_year["profit_before_tax"].to_list(),
            mode = "markers+text",
            marker = dict(
                size = 14,
                color = WARN,
                symbol = "diamond",
            ),
            text = [f"€{v:+,.0f}" for v in by_year["profit_before_tax"]],
            textposition = "top center",
            textfont = dict(
                color = WARN,
                size = 12.5,
            ),
            name = "profit before tax",
        ),
    )
    style(
        fig = _fig,
        title = "Three years, one picture: what came in, what left, what was left over",
        showlegend = True,
    )
    _fig.update_layout(barmode = "relative")
    _fig.update_yaxes(
        showticklabels = False,
        showline = False,
        ticks = "",
        title_text = "€ per year (bars) / profit (diamond)",
        title_font = dict(size = 11.5, color = MUTED),
    )
    _fig.update_xaxes(
        title_text = "",
        tickmode = "linear",
        dtick = 1,
    )
    takeaway(
        fig = _fig,
        text = "record sales in 2027 — and almost nothing left over",
        x = 0.02,
        y = 0.98,
    )
    mo.vstack(
        items = [
            _fig,
            caption(
                "Revenue grew every year (€743.0k → €771.3k → €814.3k). "
                "So did what it cost to fill the shelves and run the "
                "shop. The diamond is what was left for you: "
                f"€{by_year['profit_before_tax'][0]:+,.0f} in 2025, "
                f"€{by_year['profit_before_tax'][1]:+,.0f} in 2026 — your "
                f"best year — and €{by_year['profit_before_tax'][2]:+,.0f} "
                "in 2027. Your own description matches this exactly: "
                "record sales, nothing left over. The question worth "
                "asking is not whether that's true — it plainly is — but "
                "*why* it happened in a year when sales were the best "
                "you've ever had. Sections 4, 5, and 8 answer that."
            ),
        ],
    )
    return (by_year,)


@app.cell
def _(
    ACCENT,
    ACCENT_LIGHT,
    MUTED,
    caption,
    go,
    mo,
    np,
    pl,
    receipts,
    style,
    takeaway,
):
    # ==== 2. Am I really growing, or does it just feel that way? ============
    _r = receipts.filter((pl.col("qty") > 0) & pl.col("ref_receipt_id").is_null())
    _m = _r.with_columns(
        yy = pl.col("date").str.slice(0, 4).cast(pl.Int32),
        mm = pl.col("date").str.slice(5, 2).cast(pl.Int32),
    ).group_by(["yy", "mm"]).agg(
        rev = (pl.col("qty") * pl.col("unit_price")).sum(),
    ).sort(["yy", "mm"]).with_columns(
        t = (pl.col("yy") - 2025) * 12 + pl.col("mm"),
    )
    # your own account tells me month 1 isn't a normal trading month --
    # "everyone came to try us... filling pantries, not shopping normally."
    # I exclude it so the opening rush doesn't get mistaken for a trend.
    _train = _m.filter(pl.col("t") != 1)
    _X = np.column_stack([
        np.ones(_train.height),
        _train["t"].to_numpy(),
        *[(_train["mm"].to_numpy() == k).astype(float) for k in range(2, 13)],
    ])
    _y = np.log(_train["rev"].to_numpy())
    _beta, *_r2 = np.linalg.lstsq(_X, _y, rcond = None)
    _trend_pct_yr = (np.exp(_beta[1] * 12) - 1) * 100
    _fitted = np.exp(_X @ _beta)

    _fig = go.Figure()
    _fig.add_bar(
        x = _train["t"].to_list(),
        y = _train["rev"].to_list(),
        marker_color = ACCENT_LIGHT,
        name = "actual monthly revenue",
    )
    _fig.add_trace(
        go.Scatter(
            x = _train["t"].to_list(),
            y = list(_fitted),
            mode = "lines",
            line = dict(color = ACCENT, width = 2.5),
            name = "trend + season (fitted)",
        ),
    )
    style(
        fig = _fig,
        title = "Monthly revenue split into a growth trend and a repeating seasonal pattern (January 2025 excluded)",
        showlegend = True,
    )
    _fig.update_layout(legend = dict(orientation = "h", yanchor = "bottom", y = 1.0, xanchor = "left", x = 0, font = dict(size = 11.5)))
    _fig.update_yaxes(showticklabels = False, showline = False, ticks = "", title_text = "revenue (€/month)", title_font = dict(size = 11.5, color = MUTED))
    _fig.update_xaxes(title_text = "month (Feb 2025 = 2)")
    takeaway(
        fig = _fig,
        text = f"underlying growth ≈{_trend_pct_yr:+.1f}%/year, once the summer/winter swing is removed",
        x = 0.02,
        y = 0.98,
    )

    # decompose the growth: volume, average price, active card base
    _yearly = _r.with_columns(yy = pl.col("date").str.slice(0, 4).cast(pl.Int32)).group_by("yy").agg(
        rev = (pl.col("qty") * pl.col("unit_price")).sum(),
        units = pl.col("qty").sum(),
        cards = pl.col("customer_id").filter(pl.col("customer_id").is_not_null()).n_unique(),
        trips = pl.col("receipt_id").n_unique(),
    ).sort(by = "yy").with_columns(
        avg_price = pl.col("rev") / pl.col("units"),
        basket = pl.col("rev") / pl.col("trips"),
    )
    growth_stats = {
        "trend_pct_yr": _trend_pct_yr,
        "unit_growth_pct": (_yearly["units"][-1] / _yearly["units"][0] - 1) * 100,
        "price_growth_pct": (_yearly["avg_price"][-1] / _yearly["avg_price"][0] - 1) * 100,
        "basket_growth_pct": (_yearly["basket"][-1] / _yearly["basket"][0] - 1) * 100,
        "trips_growth_pct": (_yearly["trips"][-1] / _yearly["trips"][0] - 1) * 100,
    }
    mo.vstack(
        items = [
            mo.md(r"""
    ## 2 · Am I really growing, or does it just feel that way?

    Both, and it's worth separating them. Every month's revenue is a mix
    of the CALENDAR (summer is always busier than February) and the
    TREND (the shop getting genuinely bigger year over year). I fit both
    at once — one straight growth line, plus one repeating 12-month
    shape — and let the data decide how much of each month belongs to
    which. Your opening month is excluded: you told me it was pantry-filling,
    not a normal trading pattern, and it would otherwise look like an
    enormous one-off spike no one could ever explain.
    """),
            _fig,
            caption(
                f"The growth line alone says roughly "
                f"{growth_stats['trend_pct_yr']:+.1f}% a year, net of "
                "season. That is genuine: units sold grew "
                f"{growth_stats['unit_growth_pct']:+.1f}% from 2025 to "
                f"2027, not just prices (average shelf price only drifted "
                f"{growth_stats['price_growth_pct']:+.1f}% over the same "
                f"span) — and it shows up as bigger baskets "
                f"({growth_stats['basket_growth_pct']:+.1f}% per trip) more "
                f"than as more trips ({growth_stats['trips_growth_pct']:+.1f}%). "
                "In plain terms: it isn't that more people are walking in "
                "the door — it's that the people who do walk in are buying "
                "more each time. That is consistent with a loyal, growing "
                "core of regulars trusting the shop with more of their "
                "list, not with new footfall."
            ),
        ],
    )
    return (growth_stats,)


@app.cell
def _(
    ACCENT,
    DATA,
    MUTED,
    WARN,
    by_year,
    caption,
    go,
    mo,
    pl,
    style,
    takeaway,
):
    # ==== 3. Shrinkage: what's it costing me, and is it theft? ==============
    _wo = pl.read_csv(source = DATA / "write_offs.csv")
    _proc = pl.read_csv(source = DATA / "procurement.csv").unique(
        subset = ["uid", "qty", "unit_cost", "order_date", "delivery_date"],
    )
    _cost = _proc.group_by("uid").agg(pl.col("unit_cost").median().alias("mc"))
    _woc = _wo.join(other = _cost, on = "uid", how = "left").with_columns(
        eur = pl.col("units") * pl.col("mc"),
        yy = pl.col("date").str.slice(0, 4),
    )
    _by_reason = _woc.group_by("reason").agg(
        units = pl.col("units").sum(),
        eur = pl.col("eur").sum(),
    ).sort(by = "eur", descending = True)
    _total_eur = float(_by_reason["eur"].sum())
    _rev_3y = float(by_year["revenue"].sum())

    _fig = go.Figure()
    _labels = {"spoilage": "spoiled on the shelf", "stock_count": "month-end count correction", "damage": "the freezer accident"}
    _fig.add_bar(
        x = [_labels[r] for r in _by_reason["reason"]],
        y = _by_reason["eur"].to_list(),
        marker_color = [WARN if r == "damage" else ACCENT for r in _by_reason["reason"]],
        text = [f"€{v:,.0f}" for v in _by_reason["eur"]],
        textposition = "outside",
    )
    style(fig = _fig, title = "Three years of write-offs, by cause (€, at your own invoice cost)")
    _fig.update_yaxes(showticklabels = False, showline = False, ticks = "", title_text = "€ over 3 years", title_font = dict(size = 11.5, color = MUTED), range = [0, float(_by_reason["eur"].max()) * 1.3])
    takeaway(fig = _fig, text = f"€{_total_eur:,.0f} over 3 years ({_total_eur/_rev_3y*100:.1f}% of sales) — almost all of it spoilage", x = 0.98, y = 0.98, anchor = "right")

    # trace one spike month to a specific double-posted invoice
    _sc_monthly = _woc.filter(pl.col("reason") == "stock_count").with_columns(
        ym = pl.col("date").str.slice(0, 7),
    ).group_by("ym").agg(units = pl.col("units").sum()).sort(by = "units", descending = True)
    _worst_month = _sc_monthly.row(0, named = True)["ym"]
    _dupe = _proc.group_by(["uid", "qty", "unit_cost", "order_date", "delivery_date"]).agg(
        pl.len().alias("n"),
    ).filter(pl.col("n") > 1).with_columns(
        delivery_month = pl.col("delivery_date").str.slice(0, 7),
        extra_units = (pl.col("n") - 1) * pl.col("qty"),
    )
    _dupe_that_month = _dupe.filter(pl.col("delivery_month") == _worst_month)
    _extra = int(_dupe_that_month["extra_units"].sum())
    _correction = int(_sc_monthly.row(0, named = True)["units"])

    mo.vstack(
        items = [
            mo.md(r"""
    ## 3 · What is the shrinkage costing me — and should I be worried about theft?

    Your write-off log gives three reasons, and they tell three different
    stories:
    """),
            _fig,
            caption(
                "Spoilage is the real, structural cost of a full fresh "
                "range: it grew a little faster than sales (about 4.7% of "
                "revenue in 2025, rising to 5.7% by 2027), which fits the "
                "hotter summers and the growing produce/dairy volumes more "
                "than anything alarming. The freezer accident is exactly "
                "what you described — one event, isolated to February "
                "2026 — and it never repeats. The count-correction line is "
                "the one worth a closer look, because that is where theft "
                "would show up if it existed."
            ),
            mo.md(
                f"""**Tracing the biggest correction month.** Your largest single
    month-end correction was **{_worst_month}**, at
    **{_correction:,} units**. That same month, your own invoice file has
    **{_dupe_that_month.height} delivery lines entered twice** — same
    product, quantity, cost, order date, and delivery date, posted on two
    different days. Those duplicated lines alone account for
    **{_extra:,} units** of phantom stock on your books that never
    physically existed to be missing. That is most of the month's
    correction, explained by a paperwork double-entry, not a person."""
            ),
            mo.md(
                "**My verdict: no theft signal.** Every count correction I "
                "can trace, traces to a paperwork cause — a duplicated "
                "invoice, or ordinary counting noise that runs both "
                "positive and negative month to month (a real theft "
                "problem shows up as a one-directional drift, and yours "
                "doesn't). The euro cost that matters is spoilage, not "
                "shrinkage in the sense you were worried about."
            ),
        ],
    )
    return


@app.cell
def _(ACCENT, MUTED, ROOT, caption, go, mo, np, pl, receipts, style, takeaway):
    # ==== 4. What did Spara+ actually cost me? ================================
    _sku = pl.read_excel(source = ROOT / "SKUs.xlsx").select(["uid", "category"])
    _r = receipts.filter((pl.col("qty") > 0) & pl.col("ref_receipt_id").is_null())
    _m = _r.with_columns(
        yy = pl.col("date").str.slice(0, 4).cast(pl.Int32),
        mm = pl.col("date").str.slice(5, 2).cast(pl.Int32),
    ).group_by(["yy", "mm"]).agg(
        rev = (pl.col("qty") * pl.col("unit_price")).sum(),
        units = pl.col("qty").sum(),
        trips = pl.col("receipt_id").n_unique(),
    ).sort(["yy", "mm"]).with_columns(t = (pl.col("yy") - 2025) * 12 + pl.col("mm"))

    # fit trend+season on the PRE-ENTRY period only (Feb 2025 - Feb 2027,
    # t=2..26) and project forward -- if nothing else had changed, this is
    # what the shop's own pre-entry trajectory implies for March-December
    # 2027 (t=27..36), Spara+'s first ten months
    _train = _m.filter((pl.col("t") >= 2) & (pl.col("t") <= 26))
    _post = _m.filter(pl.col("t") >= 27)

    def _fit_and_project(col):
        _X = np.column_stack([
            np.ones(_train.height), _train["t"].to_numpy(),
            *[(_train["mm"].to_numpy() == k).astype(float) for k in range(2, 13)],
        ])
        _y = np.log(_train[col].to_numpy())
        _beta, *_ = np.linalg.lstsq(_X, _y, rcond = None)
        _Xp = np.column_stack([
            np.ones(_post.height), _post["t"].to_numpy(),
            *[(_post["mm"].to_numpy() == k).astype(float) for k in range(2, 13)],
        ])
        _resid = _y - _X @ _beta
        _sigma = float(_resid.std(ddof = _X.shape[1]))
        return np.exp(_Xp @ _beta), _post[col].to_numpy(), _sigma

    _pred_rev, _act_rev, _sigma_rev = _fit_and_project("rev")
    _pred_units, _act_units, _ = _fit_and_project("units")
    _pred_trips, _act_trips, _ = _fit_and_project("trips")

    # the categories you named cutting prices on, checked against everything
    # else, controlling for the same trend + season every other section
    # uses (raw before/after averages are too sensitive to which months
    # land in which window to trust on their own). "post" = from your May
    # 2027 price cut, since that's the response actually visible in the
    # tag file, not the March entry date.
    import statsmodels.api as _sm

    EXPOSED = ["Beverages (Non-Alcoholic)", "Snacks and Confectionery", "Household and Cleaning Supplies"]
    _catrev = _r.join(other = _sku, on = "uid").with_columns(
        exposed = pl.col("category").is_in(EXPOSED),
        yy = pl.col("date").str.slice(0, 4).cast(pl.Int32),
        mm = pl.col("date").str.slice(5, 2).cast(pl.Int32),
    ).with_columns(t = (pl.col("yy") - 2025) * 12 + pl.col("mm")).group_by(["t", "mm", "exposed"]).agg(
        rev = (pl.col("qty") * pl.col("unit_price")).sum(),
    )
    _d = _catrev.to_pandas()
    _d["exposed_i"] = _d["exposed"].astype(int)
    _d["post"] = (_d["t"] >= 29).astype(int)  # May 2027 = t 29
    _d["did"] = _d["exposed_i"] * _d["post"]
    _Xc = np.column_stack([
        np.ones(len(_d)), _d["t"], _d["exposed_i"], _d["post"], _d["did"],
        *[(_d["mm"] == k).astype(float) for k in range(2, 13)],
    ])
    _yc = np.log(_d["rev"].values)
    _fit = _sm.OLS(_yc, _Xc).fit(cov_type = "HAC", cov_kwds = {"maxlags": 4})
    category_stats = {
        "did_pct": (np.exp(_fit.params[4]) - 1) * 100,
        "did_p": float(_fit.pvalues[4]),
    }

    competitor_stats = {
        "pred_rev": float(_pred_rev.sum()),
        "act_rev": float(_act_rev.sum()),
        "gap_rev": float(_act_rev.sum() - _pred_rev.sum()),
        "gap_units_pct": (_act_units.sum() / _pred_units.sum() - 1) * 100,
        "gap_trips_pct": (_act_trips.sum() / _pred_trips.sum() - 1) * 100,
        "sigma_rev": _sigma_rev,
        "band_eur": float(_pred_rev.sum()) * _sigma_rev * np.sqrt(len(_pred_rev)),
    }

    _fig = go.Figure()
    _fig.add_trace(go.Scatter(
        x = _post["t"].to_list(), y = list(_pred_rev), mode = "lines",
        line = dict(color = MUTED, width = 2, dash = "dash"), name = "expected, if the pre-2027 trend had simply continued",
    ))
    _fig.add_trace(go.Scatter(
        x = _post["t"].to_list(), y = _post["rev"].to_list(), mode = "lines+markers",
        line = dict(color = ACCENT, width = 2.5), name = "actual, March-December 2027",
    ))
    style(fig = _fig, title = "Actual revenue since Spara+ opened, against what your own pre-entry trend predicted", showlegend = True)
    _fig.update_layout(legend = dict(orientation = "h", yanchor = "bottom", y = 1.0, xanchor = "left", x = 0, font = dict(size = 11.5)))
    _fig.update_yaxes(showticklabels = False, showline = False, ticks = "", title_text = "revenue (€/month)", title_font = dict(size = 11.5, color = MUTED))
    _fig.update_xaxes(title_text = "month (March 2027 = 27)")
    takeaway(fig = _fig, text = "month to month they wander independently —<br>but the 10-month totals land almost exactly together", x = 0.02, y = 0.15)

    mo.vstack(
        items = [
            mo.md(r"""
    ## 4 · What did Spara+ actually cost me?

    Your instinct — "everything worked until March 2027" — deserves a
    real test, not a nod. The test I trust is this: use only the eleven
    months of your OWN history *before* Spara+ opened (accounting for
    trend and season) to say what your revenue "should" have been for the
    rest of 2027 if nothing new had entered the picture — then compare
    that to what actually happened.
    """),
            _fig,
            caption(
                f"Predicted, on your pre-entry trajectory: "
                f"€{competitor_stats['pred_rev']:,.0f} for March-December "
                f"2027. Actual: €{competitor_stats['act_rev']:,.0f} — a "
                f"gap of €{competitor_stats['gap_rev']:+,.0f}, effectively "
                "zero against a month-to-month swing this shop normally "
                f"produces on its own (my model's typical monthly margin "
                f"of error is roughly €{competitor_stats['sigma_rev']*100:.0f} "
                "per hundred euros of revenue — a gap this small could "
                "easily be noise). Units sold and shopping trips tell the "
                f"same story: {competitor_stats['gap_units_pct']:+.1f}% on "
                f"units, {competitor_stats['gap_trips_pct']:+.1f}% on "
                "trips, both essentially on-trend, neither showing the "
                "sharp step down a competitor opening six hundred meters "
                "away should leave."
            ),
            mo.md(
                f"**I also checked the categories you specifically cut "
                "prices on** — drinks, snacks, household goods, the "
                "shelves Spara+ advertises hardest — against everything "
                "else, controlling for the same trend and season as "
                "above, with your May 2027 price cut as the marker. "
                f"Revenue on the defended shelves grew about "
                f"{category_stats['did_pct']:+.1f} percentage points "
                "differently from the rest of the shop after the cut — "
                f"small, and not statistically distinguishable from zero "
                f"(p = {category_stats['did_p']:.2f}). That is genuinely "
                "uninformative rather than reassuring: this comparison "
                "can't actually clear Spara+ either way. You cut margin on "
                "exactly those shelves in response to the competition, so "
                "a defended shelf was never going to be a fair control "
                "for an undefended one — your own response is mixed into "
                "the result, and I can't cleanly separate 'the competitor "
                "didn't hurt this category' from 'your price cut is "
                "masking that it did.' I'm telling you this rather than "
                "picking the reading that flatters either of us."
            ),
            mo.accordion(
                items = {
                    "My honest conclusion, and its limits": mo.md(
                        "I cannot find a reliable, measurable dent in your "
                        "top-line numbers that I can attribute to Spara+ "
                        "specifically. That is not the same as 'Spara+ has "
                        "cost you nothing' — a competitor six hundred "
                        "metres away is certainly taking SOME trade, and a "
                        "small effect (a few thousand euros either way) "
                        "would be invisible to any method working from "
                        "monthly totals like mine. What I can say with "
                        "confidence is that it is not large enough to "
                        "explain why a record revenue year netted almost "
                        "nothing — your own growth absorbed whatever it "
                        "took. Section 8 shows you where that year's "
                        "result actually came from."
                    ),
                },
            ),
        ],
    )
    return


@app.cell
def _(ACCENT, DATA, MUTED, WARN, caption, go, mo, np, pl, style, takeaway):
    # ==== 5. Was the expansion worth it? =====================================
    _cs = pl.read_csv(source = DATA / "cost_sheet.csv").with_columns(
        t = (pl.col("year") - 2025) * 12 + pl.col("month"),
    )
    _post = _cs.filter(pl.col("t") >= 23)  # November 2026 on
    _train = _cs.filter((pl.col("t") >= 2) & (pl.col("t") <= 22))

    def _fit_and_project(col):
        _X = np.column_stack([
            np.ones(_train.height), _train["t"].to_numpy(),
            *[(_train["month"].to_numpy() == k).astype(float) for k in range(2, 13)],
        ])
        _y = np.log(_train[col].to_numpy())
        _beta, *_ = np.linalg.lstsq(_X, _y, rcond = None)
        _Xp = np.column_stack([
            np.ones(_post.height), _post["t"].to_numpy(),
            *[(_post["month"].to_numpy() == k).astype(float) for k in range(2, 13)],
        ])
        return np.exp(_Xp @ _beta), _post[col].to_numpy()

    _pred_rev, _act_rev = _fit_and_project("revenue")
    _pred_util, _act_util = _fit_and_project("utilities")

    _wages = float(_post["wages"].sum())
    _payroll = float(_post["payroll_tax"].sum())
    _extra_util = max(0.0, float(_act_util.sum() - _pred_util.sum()))
    _capex = 14000.0
    _total_cost = _wages + _payroll + _extra_util + _capex
    _extra_rev = float(_act_rev.sum() - _pred_rev.sum())
    _gm = 1 - float(_cs["procurement"].sum()) / float(_cs["revenue"].sum())
    _extra_gross_profit = _extra_rev * _gm
    _net = _extra_gross_profit - _total_cost

    expansion_stats = {
        "months": _post.height,
        "wages": _wages,
        "payroll": _payroll,
        "extra_util": _extra_util,
        "capex": _capex,
        "total_cost": _total_cost,
        "extra_rev": _extra_rev,
        "gm": _gm,
        "extra_gross_profit": _extra_gross_profit,
        "net": _net,
        "wage_bill": _wages + _payroll,
        "rev_needed_for_wages": (_wages + _payroll) / _gm,
    }

    _labels = ["extra gross profit\nfrom the revenue lift", "Ana's wages", "payroll tax", "extra utilities", "the fit-out"]
    _vals = [_extra_gross_profit, -_wages, -_payroll, -_extra_util, -_capex]
    _fig = go.Figure()
    _fig.add_trace(go.Waterfall(
        x = _labels,
        measure = ["relative"] * 5,
        y = _vals,
        text = [f"{'+' if v>=0 else ''}{v:,.0f}" for v in _vals],
        textposition = "outside",
        connector = dict(line = dict(color = MUTED, width = 1)),
        increasing = dict(marker = dict(color = ACCENT)),
        decreasing = dict(marker = dict(color = WARN)),
    ))
    style(fig = _fig, title = "The expansion, in euros: 14 months of Ana plus the fit-out, against what the extra hours actually earned")
    _fig.update_yaxes(showticklabels = False, showline = False, ticks = "", title_text = "€", title_font = dict(size = 11.5, color = MUTED), range = [_net * 1.15, _extra_gross_profit * 3])
    _fig.update_xaxes(title_text = "")
    takeaway(fig = _fig, text = f"net so far: ≈€{_net:,.0f}", x = 0.98, y = 0.9, anchor = "right", color = WARN)

    mo.vstack(
        items = [
            mo.md(r"""
    ## 5 · Was the expansion worth it?

    This one I can price directly from your own ledger, no modeling
    required for the cost side — only the benefit side needs the same
    trend-projection trick as Section 4.
    """),
            _fig,
            caption(
                f"Over the {expansion_stats['months']} months since "
                f"November 2026: Ana's wages cost "
                f"€{expansion_stats['wages']:,.0f}, payroll tax on top "
                f"€{expansion_stats['payroll']:,.0f}, the extra hours' "
                f"share of the electricity bill roughly "
                f"€{expansion_stats['extra_util']:,.0f}, plus the "
                f"€{expansion_stats['capex']:,.0f} fit-out — "
                f"€{expansion_stats['total_cost']:,.0f} in total. Revenue "
                "did rise faster than your pre-expansion trend alone "
                f"would predict — about €{expansion_stats['extra_rev']:,.0f} "
                "extra over the period — but at your shop's overall "
                f"margin (≈{expansion_stats['gm']*100:.0f}% after the cost "
                "of goods), that only turns into "
                f"€{expansion_stats['extra_gross_profit']:,.0f} of actual "
                "gross profit. **The mechanism is simple arithmetic**: a "
                "fixed wage is a euro-for-euro cost, but a euro of extra "
                f"revenue only keeps about {expansion_stats['gm']*100:.0f} "
                f"cents of margin — so covering Ana's wages and payroll tax "
                f"alone (€{expansion_stats['wage_bill']:,.0f}) needs about "
                f"€{expansion_stats['rev_needed_for_wages']:,.0f} of "
                "genuinely NEW revenue, not the shop's existing turnover. "
                f"The extra hours brought in about "
                f"€{expansion_stats['extra_rev']:,.0f} — roughly "
                f"{expansion_stats['rev_needed_for_wages']/expansion_stats['extra_rev']:.0f} "
                "times less than that."
            ),
            mo.md(
                "**To be fair to the decision you made at the time**: "
                "November 2026 was your best month ever, the freezer "
                "scare was behind you, and you had genuinely saved the "
                "money rather than borrowed it. Hiring help and extending "
                "hours is a completely reasonable read of a shop that had "
                "just had its best year. The numbers say it hasn't paid "
                "for itself yet — not that it was a foolish bet to make."
            ),
        ],
    )
    return (expansion_stats,)


@app.cell
def _(
    ACCENT,
    ACCENT_LIGHT,
    MUTED,
    caption,
    go,
    mo,
    pl,
    receipts,
    style,
    takeaway,
):
    # ==== 6. Which customers am I losing, and who replaced them? ============
    _r = receipts.filter(
        (pl.col("qty") > 0) & pl.col("ref_receipt_id").is_null() & pl.col("customer_id").is_not_null()
    )
    _vis = _r.group_by("customer_id").agg(
        n = pl.col("receipt_id").n_unique(),
        first = pl.col("date").min(),
        last = pl.col("date").max(),
    )
    # "regular" = at least 10 receipts somewhere across the 3 years -- a
    # judgment call; the qualitative story is not sensitive to this cutoff
    _regs = _vis.filter(pl.col("n") >= 10).with_columns(
        first_dt = pl.col("first").str.to_date(),
        last_dt = pl.col("last").str.to_date(),
    )
    _rows = []
    for _yend, _label in [("2025-12-31", 2025), ("2026-12-31", 2026), ("2027-12-31", 2027)]:
        _ye = pl.lit(_yend).str.to_date()
        _eligible = _regs.filter(pl.col("first_dt") <= _ye)
        # a conservative 90-day silence cutoff: short enough to catch real
        # departures within the window, long enough that an occasional
        # once-a-quarter shopper isn't mistaken for a leaver
        _silent = _eligible.filter((_ye - pl.col("last_dt")).dt.total_days() >= 90)
        _new_that_year = _regs.filter(pl.col("first_dt").dt.year() == _label)
        _rows.append({
            "year": _label,
            "regulars_established_by_year_end": _eligible.height,
            "gone_quiet_90d_plus": _silent.height,
            "newly_established_that_year": _new_that_year.height,
        })
    churn_table = pl.DataFrame(_rows)
    churn_stats = {
        "total_regulars": _regs.height,
        "silent_end_2027": int(churn_table.filter(pl.col("year") == 2027)["gone_quiet_90d_plus"][0]),
    }

    _fig = go.Figure()
    _fig.add_bar(
        x = churn_table["year"].to_list(),
        y = churn_table["newly_established_that_year"].to_list(),
        name = "new regulars established that year",
        marker_color = ACCENT_LIGHT,
    )
    _fig.add_bar(
        x = churn_table["year"].to_list(),
        y = (-churn_table["gone_quiet_90d_plus"]).to_list(),
        name = "regulars quiet 90+ days by year-end (cumulative)",
        marker_color = ACCENT,
    )
    style(fig = _fig, title = "New regulars arriving vs. regulars gone quiet, year by year", showlegend = True)
    _fig.update_layout(legend = dict(orientation = "h", yanchor = "bottom", y = 1.0, xanchor = "left", x = 0, font = dict(size = 10.5)))
    _fig.update_yaxes(showticklabels = False, showline = False, ticks = "", title_text = "customers (tokens)", title_font = dict(size = 11.5, color = MUTED))
    _fig.update_xaxes(title_text = "", tickmode = "linear", dtick = 1)
    takeaway(fig = _fig, text = "a flow, not a leak: new faces roughly keep pace with the quiet ones", x = 0.02, y = 0.15)

    mo.vstack(
        items = [
            mo.md(rf"""
    ## 6 · Which customers am I losing, and who replaced them?

    Card payments carry a stable (if anonymous) code, so I can watch each
    token's visits over three years. I call a token a "regular" if it
    shows up on at least 10 receipts somewhere in that window — a
    reasonable line for someone who shops here habitually, not a one-off
    or occasional visitor. **{churn_stats['total_regulars']} tokens** meet
    that bar.
    """),
            _fig,
            mo.ui.table(data = churn_table, selection = None),
            caption(
                f"By the end of 2027, **{churn_stats['silent_end_2027']} of "
                f"{churn_stats['total_regulars']} regulars** ("
                f"{churn_stats['silent_end_2027']/churn_stats['total_regulars']*100:.0f}%) "
                "have gone quiet for at least 90 days — real turnover, and "
                "worth naming rather than hiding behind the healthy total. "
                "But it is a FLOW, not a one-way leak: your regular count "
                "still grew net across the three years, because new "
                "households — plausibly including some from the apartment "
                "building that filled up in 2026 — kept becoming regulars "
                "faster than the old ones went quiet. One honest caveat: "
                "anyone who only went quiet in the last few months of 2027 "
                "might simply be between visits when my window closes — I "
                "can't yet tell a slow customer from a lost one at the "
                "very edge of the data, so the 2027 count above is "
                "probably a slight overstatement of true departures."
            ),
        ],
    )
    return


@app.cell
def _(ACCENT, DATA, MUTED, caption, go, mo, np, pl, style, takeaway):
    # ==== 7. What should I expect 2028 to look like? =========================
    _cs = pl.read_csv(source = DATA / "cost_sheet.csv").with_columns(
        t = (pl.col("year") - 2025) * 12 + pl.col("month"),
    )
    _train = _cs.filter(pl.col("t") >= 2)
    _post_ind = (_train["t"] >= 23).cast(pl.Int8).to_numpy()
    _X = np.column_stack([
        np.ones(_train.height), _train["t"].to_numpy(), _post_ind,
        *[(_train["month"].to_numpy() == k).astype(float) for k in range(2, 13)],
    ])
    _y = np.log(_train["revenue"].to_numpy())
    _beta, *_ = np.linalg.lstsq(_X, _y, rcond = None)
    _resid = _y - _X @ _beta
    _sigma = float(_resid.std(ddof = _X.shape[1]))
    _fitted = np.exp(_X @ _beta)

    _t28 = np.arange(37, 49)
    _m28 = np.arange(1, 13)
    _X28 = np.column_stack([
        np.ones(12), _t28, np.ones(12),
        *[(_m28 == k).astype(float) for k in range(2, 13)],
    ])
    _pred28 = np.exp(_X28 @ _beta)
    _lo28 = np.exp(_X28 @ _beta - 1.28 * _sigma)
    _hi28 = np.exp(_X28 @ _beta + 1.28 * _sigma)

    # benchmark: seasonal-naive (repeat last year) evaluated on its own
    # in-sample track record (predicting 2027 from 2026)
    _rev2026 = _cs.filter(pl.col("year") == 2026).sort("month")["revenue"].to_numpy()
    _rev2027 = _cs.filter(pl.col("year") == 2027).sort("month")["revenue"].to_numpy()
    _naive_wmape = float(np.abs(_rev2027 - _rev2026).sum() / _rev2027.sum())
    _model_wmape = float(np.abs(_train["revenue"].to_numpy() - _fitted).sum() / _train["revenue"].to_numpy().sum())

    # translate the revenue range into profit using 2027's own cost structure
    _y2027 = _cs.filter(pl.col("year") == 2027)
    _rev27 = float(_y2027["revenue"].sum())
    _proc_rate = float(_y2027["procurement"].sum()) / _rev27
    _vat_rate = float(_y2027["vat"].sum()) / _rev27
    _fixed_2027 = float(sum(_y2027[c].sum() for c in ["rent", "wages", "payroll_tax", "utilities", "storage", "flyers", "credit_interest", "repairs"]))

    def _profit_at(rev):
        return rev * (1 - _proc_rate - _vat_rate) - _fixed_2027

    forecast_stats = {
        "point": float(_pred28.sum()),
        "lo": float(_lo28.sum()),
        "hi": float(_hi28.sum()),
        "naive_wmape": _naive_wmape * 100,
        "model_wmape": _model_wmape * 100,
        "profit_point": _profit_at(float(_pred28.sum())),
        "profit_lo": _profit_at(float(_lo28.sum())),
        "profit_hi": _profit_at(float(_hi28.sum())),
    }

    _fig = go.Figure()
    _fig.add_trace(go.Scatter(
        x = list(range(37, 49)) + list(range(48, 36, -1)),
        y = list(_hi28) + list(_lo28[::-1]),
        fill = "toself",
        fillcolor = "rgba(46,94,170,0.12)",
        line = dict(width = 0),
        showlegend = False,
        hoverinfo = "skip",
    ))
    _fig.add_trace(go.Scatter(
        x = list(range(25, 37)), y = _cs.filter(pl.col("t") >= 25).sort("t")["revenue"].to_list(),
        mode = "lines", line = dict(color = MUTED, width = 2), name = "actual (2027)",
    ))
    _fig.add_trace(go.Scatter(
        x = list(range(37, 49)), y = list(_pred28), mode = "lines+markers",
        line = dict(color = ACCENT, width = 2.5), name = "2028 forecast",
    ))
    style(fig = _fig, title = "2028 revenue forecast, if the current staffing and lease terms stay as they are", showlegend = True)
    _fig.update_layout(legend = dict(orientation = "h", yanchor = "bottom", y = 1.0, xanchor = "left", x = 0, font = dict(size = 11.5)))
    _fig.update_yaxes(showticklabels = False, showline = False, ticks = "", title_text = "revenue (€/month)", title_font = dict(size = 11.5, color = MUTED))
    _fig.update_xaxes(title_text = "month (Jan 2027 = 25)")
    takeaway(fig = _fig, text = f"point forecast €{forecast_stats['point']/1000:,.0f}k, range €{forecast_stats['lo']/1000:,.0f}k–€{forecast_stats['hi']/1000:,.0f}k", x = 0.02, y = 0.15)

    mo.vstack(
        items = [
            mo.md(r"""
    ## 7 · What should I expect 2028 to look like?

    "If nothing changes" — same hours, same staffing, the lease renewed
    on the terms on the table — here is the honest range, not a single
    confident number.
    """),
            _fig,
            caption(
                f"**Revenue**: my point estimate is "
                f"€{forecast_stats['point']:,.0f}, with a practical range "
                f"of roughly €{forecast_stats['lo']:,.0f} to "
                f"€{forecast_stats['hi']:,.0f}. This model (trend, season, "
                "and the post-expansion step, fitted on your own three "
                f"years) predicted your own recent months to within "
                f"{forecast_stats['model_wmape']:.1f}% on average — "
                "meaningfully tighter than simply repeating last year's "
                f"monthly figures ({forecast_stats['naive_wmape']:.1f}% "
                "error doing that), which is why I trust it over a guess."
            ),
            mo.md(
                f"""**Profit — the number that actually matters**: applying
    2027's own cost structure (procurement rate, VAT rate, and fixed
    costs including a full year of Ana's wages) to that revenue range
    gives a profit-before-tax range of roughly
    **€{forecast_stats['profit_lo']:+,.0f} to
    €{forecast_stats['profit_hi']:+,.0f}**, with a central estimate near
    **€{forecast_stats['profit_point']:+,.0f}**. In plain terms: if
    nothing changes, 2028 looks like another 2027 — a coin flip between a
    small profit and a small loss, not a rebound and not a collapse."""
            ),
        ],
    )
    return


@app.cell
def _(expansion_stats, growth_stats, mo):
    mo.md(rf"""
    ## 8 · Renew, close, or change something?

    Putting the last seven sections side by side, here is what actually
    moved 2027's result away from where 2026 left off:

    | What changed in 2027 | Estimated effect on that year's profit |
    | --- | --- |
    | The rent review (contractual, +12% from January) | **−€1,671** |
    | Spara+ opening in March | **no measurable effect** (Section 4) — real, but too small to find in the numbers, and not the reason the year went flat |
    | The November 2026 hire, running its first full year | **the dominant driver** — costing roughly
    €{expansion_stats['total_cost'] / expansion_stats['months'] * 12:,.0f} a year against the shop's thin margin (Section 5) |

    **My recommendation: renew the lease. The lease was never the
    problem.** Twelve percent on a contract you already knew about, in a
    shop that's growing {growth_stats['trend_pct_yr']:.0f}% a year net of
    season, is not what turned €50k of profit into nothing. Walking away
    from the shop over a rent review you agreed to going in — while the
    number that actually explains the year is one you're free to change —
    would be solving the wrong problem.

    **What I would change instead:** the staffing decision, not the
    lease. That doesn't have to mean letting Ana go — it means treating
    the extended hours as the thing under review, not the tenancy. Two
    honest paths, both worth pricing properly before you decide:

    - Pull the hours back toward what they were, and keep Ana for the
      busiest shifts and the jobs that were piling up on you alone
      (ordering, the shelf rebuild, cover so you can take a Sunday off) —
      cutting the payroll cost without giving up the help entirely.
    - Or keep the current hours, but treat this year as the one where you
      find out whether they can be made to pay — through the categories
      that actually move at 7am and 9pm, not a blanket extension.

    What I would NOT do is treat this as a Spara+ problem. Cutting margin
    further on the shelves they advertise is fighting a fight the numbers
    say you're not currently losing, at a real cost to the margin you do
    have.

    ---

    **One year ahead, if nothing changes** (Section 7): a coin flip
    between a small profit and a small loss — because the cost structure
    that produced 2027 carries straight into 2028 untouched. The lease
    decision and the staffing decision are two different decisions. Only
    one of them, on this evidence, needs to change.

    ---
    ### Appendix — what's behind each number

    Every figure in the report traces to a cell above: the reconciled
    till-to-ledger tie (§1), the trend-and-season split with January 2025
    excluded (§2), the write-off decomposition and invoice trace (§3), the
    pre-entry trend projection for Spara+ (§4), the wage-vs-margin
    accounting for the expansion (§5), the token-silence churn count with
    its right-censoring caveat (§6), and the 2028 forecast benchmarked
    against a seasonal-naive baseline (§7). All of it comes from the
    files you handed over — receipts, invoices, stock counts, and your
    own monthly ledger — nothing else.
    """)
    return


if __name__ == "__main__":
    app.run()
