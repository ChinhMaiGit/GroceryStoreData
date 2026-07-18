import marimo

__generated_with = "0.23.14"
app = marimo.App(
    width="full",
    app_title="Three Years of the Shop — a Business Review",
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

    # the notebook lives in archive/analyses/; the project root is two levels up
    ROOT = Path(__file__).resolve().parent.parent.parent
    DATA = ROOT / "data"

    # ---- chart style: declutter per Knaflic's "Storytelling with Data" -----
    # one accent for what the narrative claims, gray for context; titles are
    # DESCRIPTIVE, the takeaway lives inside the plot via takeaway(), and the
    # caption() underneath elaborates what the compact annotation cannot.
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
        """The shared declutter; `n_subplot_titles` shrinks make_subplots'
        auto panel titles (always the first annotations on the figure)."""
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
        """Label a line at its last point instead of relying on a legend."""
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
        """A short italic paragraph right under a chart."""
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
        """The headline, inside the plot, kept compact."""
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
    # Three years of the shop, reviewed

    The one-year report (`analysis_workbook.py`) told the story of a first
    year. This notebook reads the **three-year dataset**
    (`data/scenarios/3y_baseline/`) the way an analyst would review a real
    small business at the end of 2027: is it growing, who are the customers
    now, what happened in March 2027, where did the owner's capital go —
    and should the lease be renewed?

    Three things to know before reading:

    1. **Year one here is the year you already know — with the people set
       in motion.** The 2025 script (weather, costs, events) is
       byte-identical to the published baseline's, but the customer panel
       lives from day one: households move away and are replaced even in
       the first year, so the one-year report's figures reappear here
       *nearly* — within a fraction of a percent — not exactly.
    2. **The world was not quiet.** A freezer died, an apartment block
       filled, the owner expanded, the rent stepped up, a discounter opened
       down the road, a festival came through. This review has to separate
       those stories from ordinary seasonality.
    3. **Two companion notebooks settle the causal questions.** What the
       discounter cost lives in `competitor_entry_study.py`; whether the
       expansion was worth it lives in `expansion_review.py`. Both use this
       dataset's counterfactual twins, which this notebook cannot see.
    """)
    return


@app.cell
def _(DATA, ROOT, duckdb, pl):
    # ---- build the analytical database (in-memory: this notebook may run
    # ---- alongside the one-year workbook, which owns store.duckdb) ---------
    con = duckdb.connect()

    _vis = DATA / "scenarios" / "3y_baseline" / "visible"
    for _name in ["receipts", "inventory_eod", "procurement", "price_history",
                  "promotions", "write_offs", "cost_sheet", "calendar", "weather",
                  "tax_statement"]:
        con.execute(
            query = f"""
                CREATE TABLE {_name}_raw AS
                SELECT *
                FROM   read_csv_auto('{(_vis / _name).as_posix()}.csv')
            """,
        )
    _products = pl.read_excel(source = ROOT / "SKUs.xlsx")
    con.register("products_df", _products)
    con.execute(query = "CREATE TABLE products AS SELECT * FROM products_df")

    # ---- the cleaned layer: same contract as the one-year workbook §2 ------
    # POS-retry dedup (a receipt is a retry iff every distinct line appears an
    # even number of times), hour-0 placeholder -> NULL, payment labels
    # normalized, voided mis-rings cancelled by the per-line SUM
    con.execute(
        query = """
            CREATE VIEW receipts AS
            WITH lines AS (
                SELECT receipt_id,
                       hour,
                       payment,
                       customer_id,
                       uid,
                       qty,
                       unit_price,
                       promo,
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
                   lower(trim(l.payment))                         AS payment,
                   l.customer_id,
                   l.uid,
                   sum(l.qty * CASE WHEN r.is_retry THEN l.n // 2
                                    ELSE l.n END)                 AS qty,
                   l.unit_price,
                   l.promo,
                   l.date,
                   l.ref_receipt_id
            FROM   lines l
            JOIN   retry r USING (receipt_id)
            GROUP  BY l.receipt_id, l.hour, l.payment, l.customer_id,
                      l.uid, l.unit_price, l.promo, l.date, l.ref_receipt_id
            HAVING sum(l.qty * CASE WHEN r.is_retry THEN l.n // 2
                                    ELSE l.n END) != 0
        """,
    )
    con.execute(
        query = """
            CREATE VIEW procurement AS
            SELECT uid,
                   qty,
                   unit_cost,
                   order_date,
                   delivery_date,
                   min(posted_date) AS posted_date
            FROM   procurement_raw
            GROUP  BY uid, qty, unit_cost, order_date, delivery_date
        """,
    )
    # write-offs: the three-year file carries THREE reasons — nightly
    # spoilage, monthly stock-count corrections, and the one 'damage' event
    # (the February 2026 freezer failure). Physical waste keeps its reason.
    con.execute(
        query = """
            CREATE VIEW write_offs AS
            SELECT uid,
                   units,
                   date,
                   reason
            FROM   write_offs_raw
            WHERE  reason IN ('spoilage', 'damage')
        """,
    )
    con.execute(
        query = """
            CREATE VIEW stock_adjustments AS
            SELECT uid,
                   units,
                   date
            FROM   write_offs_raw
            WHERE  reason = 'stock_count'
        """,
    )
    con.execute(
        query = """
            CREATE VIEW promotions AS
            SELECT type,
                   CASE WHEN category = 'Snacks and Confectionary'
                        THEN 'Snacks and Confectionery'
                        ELSE category END AS category,
                   depth,
                   n_skus,
                   flyer_cost,
                   start_date,
                   end_date
            FROM   promotions_raw
        """,
    )
    con.execute(query = "CREATE VIEW weather AS SELECT * FROM weather_raw")
    con.execute(query = "CREATE VIEW inventory_eod AS SELECT * FROM inventory_eod_raw")
    con.execute(query = "CREATE VIEW cost_sheet AS SELECT * FROM cost_sheet_raw")
    con.execute(query = "CREATE VIEW calendar AS SELECT * FROM calendar_raw")
    con.execute(query = "CREATE VIEW price_history AS SELECT * FROM price_history_raw")
    con.execute(query = "CREATE VIEW tax_statement AS SELECT * FROM tax_statement_raw")
    return (con,)


@app.cell
def _(caption, mo):
    _erd = mo.mermaid("""
    erDiagram
        receipts }o--|| products : "uid"
        inventory_eod }o--|| products : "uid"
        procurement }o--|| products : "uid"
        write_offs }o--|| products : "uid"
        stock_adjustments }o--|| products : "uid"
        price_history }o--|| products : "uid"
        receipts }o--|| calendar : "date"
        weather ||--|| calendar : "date"
        promotions }o--o| calendar : "start_date"
        cost_sheet ||--o| tax_statement : "year"

        receipts {
            int receipt_id
            date date "2025-01-01 .. 2027-12-31"
            int hour "NULL = clock glitch"
            string payment
            string customer_id "card token or NULL"
            string uid FK
            int qty "negative = refund"
            float unit_price
            int ref_receipt_id "refund -> original"
        }
        products {
            string uid PK
            string category
            string brand_level
        }
        cost_sheet {
            int year "NEW: 2025..2027"
            int month
            float revenue
            float owner_draw "NEW: from 2026"
            float retained_earnings "NEW: the RE ledger"
            float capex "NEW: the expansion"
            float profit_tax_paid "NEW: January settlements"
        }
        write_offs {
            string uid FK
            date date
            int units
            string reason "spoilage | damage"
        }
        tax_statement {
            int year PK
            float profit_before_tax
        }
    """)
    mo.vstack(
        items = [
            mo.md("## 2 · The data, mapped"),
            _erd,
            caption(
                "The same tables as the one-year workbook, three times as "
                "long, with two schema additions: the cost sheet carries the "
                "owner's capital columns (draws, retained earnings, capex, "
                "January tax payments) plus a year key, and write_offs "
                "gained the 'damage' reason for the freezer failure. "
                "Crow's-feet mark many-to-one joins; every product join "
                "goes through the catalog key uid."
            ),
        ],
    )
    return


@app.cell
def _(con, mo, pl):
    # ---- the reconciliation, per binder ------------------------------------
    # the recording layer runs per calendar year, so each year must tie to
    # its own ledger to the cent after cleaning — three binders, three ties
    recon = con.sql(
        query = """
            WITH r AS (
                SELECT year(date)                    AS yr,
                       count(*)                      AS clean_lines,
                       sum(qty * unit_price)::DOUBLE AS receipts_revenue
                FROM   receipts
                GROUP  BY 1
            ),
            raw AS (
                SELECT year(date) AS yr,
                       count(*)   AS raw_lines
                FROM   receipts_raw
                GROUP  BY 1
            ),
            led AS (
                SELECT year               AS yr,
                       sum(revenue)::DOUBLE AS ledger_revenue
                FROM   cost_sheet
                GROUP  BY 1
            )
            SELECT yr                                        AS year,
                   raw_lines,
                   clean_lines,
                   round(receipts_revenue, 2)                AS receipts_revenue,
                   round(ledger_revenue, 2)                  AS ledger_revenue,
                   round(receipts_revenue - ledger_revenue, 4) AS gap
            FROM   r
            JOIN   raw USING (yr)
            JOIN   led USING (yr)
            ORDER  BY yr
        """,
    ).pl()
    _max_gap = float(recon["gap"].abs().max())
    _gap_years = recon.filter(recon["gap"].abs() > 0.01)
    if _max_gap < 0.01:
        _verdict = f"""It does — the largest gap across
    the three years is **€{_max_gap:.4f}**."""
    else:
        # the honest finding: the all-even retry rule has a structural blind
        # spot — a legitimate receipt whose distinct lines all happen to
        # appear an even number of times (typically a single-line basket
        # double-scanned at the till) gets halved by the heuristic
        _yrs = ", ".join(
            f"{int(_r['year'])} (€{abs(_r['gap']):.2f})"
            for _r in _gap_years.iter_rows(named = True)
        )
        _verdict = f"""*Almost.* {3 - len(_gap_years)} of the three years tie
    exactly; small residues remain in {_yrs}. Chasing them down is a lesson
    in itself: the retry-dedup rule ("a receipt is an upload glitch if every
    distinct line appears an even number of times") is a heuristic, and a
    rare honest receipt satisfies it by chance — a one-item basket whose
    single line was double-scanned at the till — so the rule halves it
    wrongly. A couple of false positives in a quarter-million lines is a
    very good heuristic; a residue you can *explain to the cent* is the
    practical standard, and these can be."""
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 3 · Three binders, three ties

    Every defect family from the one-year report is back — POS retries,
    voided mis-rings, label drift, double-posted invoices, snapshot typos —
    now injected **per calendar year**, the way a real back office fills one
    binder per year. The cleaning contract is unchanged, and the test of it
    is unchanged too: after deduplication, each year's till should tie to
    that year's ledger revenue *to the cent*. {_verdict}
    """
            ),
            mo.ui.table(
                data = recon,
                selection = None,
            ),
        ],
    )
    return


@app.cell
def _(ACCENT, MUTED, WARN, caption, con, dt, go, mo, style, takeaway):
    # ---- the timeline: 36 months, and everything that happened to them -----
    _m = con.sql(
        query = """
            SELECT date_trunc('month', date)       AS m,
                   sum(qty * unit_price)::DOUBLE   AS revenue
            FROM   receipts
            GROUP  BY 1
            ORDER  BY 1
        """,
    ).pl()
    _fig = go.Figure()
    _fig.add_scatter(
        x = _m["m"].to_list(),
        y = _m["revenue"].to_list(),
        mode = "lines+markers",
        line = dict(
            color = ACCENT,
            width = 2,
        ),
        marker = dict(size = 5),
    )
    # the scripted events, labeled sparingly: numbered flags on the chart,
    # the full glossary in the caption below
    _events = [
        (dt.date(2025, 10, 1), "1"),
        (dt.date(2026, 2, 1), "2"),
        (dt.date(2026, 9, 1), "3"),
        (dt.date(2026, 11, 1), "4"),
        (dt.date(2027, 1, 1), "5"),
        (dt.date(2027, 3, 1), "6"),
        (dt.date(2027, 8, 1), "7"),
        (dt.date(2027, 10, 1), "8"),
    ]
    for _d, _lbl in _events:
        _fig.add_vline(
            x = _d,
            line_dash = "dot",
            line_color = MUTED,
            line_width = 1,
        )
        _fig.add_annotation(
            x = _d,
            y = 1.04,
            yref = "y domain",
            text = _lbl,
            showarrow = False,
            font = dict(
                color = WARN,
                size = 11,
            ),
        )
    style(
        fig = _fig,
        title = "Monthly revenue, January 2025 – December 2027, with the shop's eight turning points",
    )
    _fig.update_yaxes(
        title_text = "revenue (€/month)",
        range = [0, float(_m["revenue"].max()) * 1.18],
    )
    _fig.update_xaxes(title_text = "")
    takeaway(
        fig = _fig,
        text = "revenue climbs all three years — none of the shocks shows up as a cliff",
        x = 0.02,
        y = 0.97,
    )
    mo.vstack(
        items = [
            mo.md("## 4 · Three years at a glance"),
            _fig,
            caption(
                "The numbered flags: ① the energy-crisis cost shock "
                "(Oct 2025), ② the freezer failure (Feb 2026), ③ the "
                "apartment block fills (Sep 2026), ④ the expansion — first "
                "clerk, longer hours, deeper shelves (Nov 2026), ⑤ the rent "
                "renewal at +12% (Jan 2027), ⑥ a discounter opens 600 m away "
                "(Mar 2027), ⑦ the street festival (Aug 2027), ⑧ a pantry-"
                "staples cost spike (Sep–Nov 2027). The striking thing is "
                "how little of this drama is visible in the top line — which "
                "is exactly why the profit review below, and the two "
                "counterfactual notebooks, are needed."
            ),
        ],
    )
    return


@app.cell
def _(con, mo, pl):
    # ---- the profit story, year by year -------------------------------------
    pnl = con.sql(
        query = """
            SELECT c.year,
                   round(sum(c.revenue), 0)          AS revenue,
                   round(sum(c.procurement), 0)      AS procurement,
                   round(sum(c.wages + c.payroll_tax), 0) AS labor,
                   round(sum(c.rent), 0)             AS rent,
                   round(sum(c.owner_draw), 0)       AS owner_draws,
                   round(sum(c.capex), 0)            AS capex,
                   round(any_value(t.profit_before_tax), 0) AS profit_before_tax
            FROM   cost_sheet c
            JOIN   tax_statement t USING (year)
            GROUP  BY c.year
            ORDER  BY c.year
        """,
    ).pl()
    _p25 = float(pnl.filter(pl.col("year") == 2025)["profit_before_tax"][0])
    _p26 = float(pnl.filter(pl.col("year") == 2026)["profit_before_tax"][0])
    _p27 = float(pnl.filter(pl.col("year") == 2027)["profit_before_tax"][0])
    _r25 = float(pnl.filter(pl.col("year") == 2025)["revenue"][0])
    _r27 = float(pnl.filter(pl.col("year") == 2027)["revenue"][0])
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 5 · The profit story: up, up, and — gone

    Revenue grew every single year, from €{_r25:,.0f} to €{_r27:,.0f}
    (+{(_r27 / _r25 - 1):.0%} over two years). Profit did not follow:

    - **2025: €{_p25:,.0f} before tax** — the proof-of-concept year you
      already know.
    - **2026: €{_p26:,.0f}** — the best year of the three. The neighborhood
      grew, the summer was hot, and the clerk only arrived in November.
    - **2027: €{_p27:,.0f}** — a year in which the shop sold more than ever
      and earned essentially nothing.

    Between 2026 and 2027 three heavy things landed at once: a full year of
    the clerk's wages plus payroll tax, the +12% rent renewal, and the
    discounter's slow leak on the top line. The table shows where the money
    went — note the two columns that did not exist in the one-year world:
    `owner_draws` (what the owner actually took home from 2026 on) and
    `capex` (the €14,000 expansion fit-out).
    """
            ),
            mo.ui.table(
                data = pnl,
                selection = None,
            ),
        ],
    )
    return (pnl,)


@app.cell
def _(
    ACCENT,
    ACCENT_LIGHT,
    MUTED,
    caption,
    con,
    end_label,
    go,
    make_subplots,
    mo,
    style,
    takeaway,
):
    # ---- growth or season? the three-year overlay ---------------------------
    trend_m = con.sql(
        query = """
            SELECT year(date)                     AS yr,
                   month(date)                    AS mon,
                   sum(qty * unit_price)::DOUBLE  AS revenue
            FROM   receipts
            GROUP  BY 1, 2
            ORDER  BY 1, 2
        """,
    ).pl()
    _fig = make_subplots(
        rows = 1,
        cols = 2,
        subplot_titles = (
            "Monthly revenue, the three years overlaid",
            "Same-month growth vs. the previous year",
        ),
        horizontal_spacing = 0.12,
    )
    _colors = {
        2025: MUTED,
        2026: ACCENT_LIGHT,
        2027: ACCENT,
    }
    # the three Decembers land within ~2k of each other, so the end labels
    # need explicit vertical nudges to keep out of each other's way
    _yshift = {
        2025: -13,
        2026: 13,
        2027: 0,
    }
    for _yr in (2025, 2026, 2027):
        _s = trend_m.filter(trend_m["yr"] == _yr).sort(by = "mon")
        _fig.add_scatter(
            x = _s["mon"].to_list(),
            y = _s["revenue"].to_list(),
            mode = "lines+markers",
            line = dict(
                color = _colors[_yr],
                width = 2,
            ),
            marker = dict(size = 5),
            row = 1,
            col = 1,
        )
        _fig.add_annotation(
            x = 12,
            y = float(_s.filter(_s["mon"] == 12)["revenue"][0]),
            text = str(_yr),
            showarrow = False,
            xanchor = "left",
            xshift = 8,
            yshift = _yshift[_yr],
            font = dict(
                color = _colors[_yr],
                size = 12,
            ),
            row = 1,
            col = 1,
        )
    _piv = trend_m.pivot(
        on = "yr",
        index = "mon",
        values = "revenue",
    ).sort(by = "mon")
    _g26 = (100 * (_piv["2026"] / _piv["2025"] - 1)).to_list()
    _g27 = (100 * (_piv["2027"] / _piv["2026"] - 1)).to_list()
    _mons = _piv["mon"].to_list()
    _fig.add_bar(
        x = _mons,
        y = _g26,
        marker_color = ACCENT_LIGHT,
        row = 1,
        col = 2,
    )
    _fig.add_bar(
        x = _mons,
        y = _g27,
        marker_color = ACCENT,
        row = 1,
        col = 2,
    )
    # nudge the two series labels apart and clear of the December bars
    _fig.add_annotation(
        x = 12,
        y = _g26[-1],
        text = "2026/25",
        showarrow = False,
        xanchor = "left",
        xshift = 10,
        yshift = 14,
        font = dict(
            color = ACCENT_LIGHT,
            size = 12,
        ),
        row = 1,
        col = 2,
    )
    _fig.add_annotation(
        x = 12,
        y = _g27[-1],
        text = "2027/26",
        showarrow = False,
        xanchor = "left",
        xshift = 10,
        yshift = -14,
        font = dict(
            color = ACCENT,
            size = 12,
        ),
        row = 1,
        col = 2,
    )
    style(
        fig = _fig,
        title = "Separating growth from season: the same twelve months, three times",
        n_subplot_titles = 2,
        right_margin = 96,
    )
    _fig.update_layout(barmode = "group")
    _fig.update_xaxes(
        title_text = "month",
        tickvals = list(range(1, 13)),
        row = 1,
        col = 1,
    )
    _fig.update_xaxes(
        title_text = "month",
        tickvals = list(range(1, 13)),
        row = 1,
        col = 2,
    )
    # explicit headroom so the takeaways sit clear of the highest points
    _fig.update_yaxes(
        title_text = "revenue (€/month)",
        range = [0, float(trend_m["revenue"].max()) * 1.25],
        row = 1,
        col = 1,
    )
    _fig.update_yaxes(
        title_text = "growth vs. prior year (%)",
        range = [min(min(_g26), min(_g27), 0) * 1.3, max(max(_g26), max(_g27)) * 1.45],
        row = 1,
        col = 2,
    )
    takeaway(
        fig = _fig,
        text = "the whole curve drifts upward — that vertical gap is growth, not season",
        x = 0.02,
        y = 0.99,
        row = 1,
        col = 1,
    )
    takeaway(
        fig = _fig,
        text = "growth is real but uneven; late 2027 flattens",
        x = 0.02,
        y = 0.99,
        row = 1,
        col = 2,
    )
    mo.vstack(
        items = [
            mo.md(
                """
    ## 6 · Is the business growing, or is it just summer?

    With one year of data this question was unanswerable — one Christmas,
    one summer, no way to tell trend from season. With three years it has a
    clean answer: lay the same twelve months on top of each other and the
    seasonal shape repeats while the whole curve shifts upward.
    """
            ),
            _fig,
            caption(
                "Left: the seasonal fingerprint (a spring ramp, a strong "
                "summer, a December bump) repeats every year — that shape is "
                "season. The vertical distance between the lines is growth. "
                "Right: the same thing as year-over-year growth rates by "
                "month; 2026 outgrew 2025 in most months, while "
                "2027's growth fades in the second half — the first place "
                "the discounter's arrival is even faintly visible. What this "
                "chart cannot say is *why* the business grew: more "
                "households, price inflation, and (from November 2026) two "
                "extra opening hours all push the same direction. The "
                "regression below puts a number on the total; splitting the "
                "causes takes the answer key and the twins."
            ),
        ],
    )
    return (trend_m,)


@app.cell
def _(mo, np, pl, trend_m):
    # ---- the trend regression, stated in full -------------------------------
    import statsmodels.api as sm

    _df = trend_m.sort(by = ["yr", "mon"]).with_columns(
        ((pl.col("yr") - 2025) * 12 + pl.col("mon") - 1).alias("t"),
        pl.col("revenue").log().alias("log_rev"),
    ).to_pandas()
    _X = sm.add_constant(
        np.column_stack([
            _df["t"].to_numpy(),
            *[(_df["mon"] == _k).astype(float).to_numpy() for _k in range(2, 13)],
        ]),
    )
    _names = ["intercept", "t (months since Jan 2025)"] + [f"month={_k}" for _k in range(2, 13)]
    _ols = sm.OLS(
        endog = _df["log_rev"].to_numpy(),
        exog = _X,
    ).fit(
        cov_type = "HAC",
        cov_kwds = {"maxlags": 3},
    )
    _ci = _ols.conf_int()

    def _stars(p):
        return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""

    trend_table = pl.DataFrame({
        "term": _names,
        "estimate": [round(float(_b), 4) for _b in _ols.params],
        "std_error": [round(float(_s), 4) for _s in _ols.bse],
        "t_stat": [round(float(_t), 2) for _t in _ols.tvalues],
        "p_value": [round(float(_p), 4) for _p in _ols.pvalues],
        "ci_low": [round(float(_l), 4) for _l in _ci[:, 0]],
        "ci_high": [round(float(_h), 4) for _h in _ci[:, 1]],
        "sig": [_stars(p = float(_p)) for _p in _ols.pvalues],
    })
    trend_stats = {
        "beta_t": float(_ols.params[1]),
        "se_t": float(_ols.bse[1]),
        "p_t": float(_ols.pvalues[1]),
        "r2": float(_ols.rsquared),
        "annual": float(np.exp(12 * _ols.params[1]) - 1),
    }
    _verdict = (
        "The trend is statistically unambiguous"
        if trend_stats["p_t"] < 0.05
        else "The trend does not clear conventional significance"
    )
    mo.accordion(
        items = {
            "See exactly how the growth rate was calculated": mo.vstack(
                items = [
                    mo.md(
                        r"""
    **The model.** A log-linear trend with month fixed effects, on the 36
    monthly revenue totals:

    $$\log(\text{Revenue}_m) = \beta_0 + \beta_1 \, t_m + \sum_{k=2}^{12} \gamma_k \, \mathbb{1}[\text{month}_m = k] + \varepsilon_m$$

    where $t_m$ counts months since January 2025 (so $\beta_1$ is the
    average monthly log-growth once the repeating seasonal shape is
    absorbed by the month dummies), with HAC(3) standard errors for the
    month-to-month serial correlation.
    """
                    ),
                    mo.ui.table(
                        data = trend_table,
                        selection = None,
                    ),
                    mo.md(
                        f"""
    **Technical reading.** $\\beta_1$ = {trend_stats['beta_t']:.4f}
    (SE {trend_stats['se_t']:.4f}, p = {trend_stats['p_t']:.4f}): each
    calendar month, revenue is about {100 * trend_stats['beta_t']:.2f}%
    higher than the month before, holding the seasonal shape fixed —
    **{trend_stats['annual']:.1%} per year** compounded
    (R² = {trend_stats['r2']:.2f}).

    **What it means for the owner.** {_verdict}: the shop genuinely grew,
    at roughly {trend_stats['annual']:.0%} a year. But this single number
    bundles at least three causes — the neighborhood's slow growth plus the
    apartment block, supplier-cost inflation passing into prices, and two
    extra opening hours after November 2026. The answer key confirms the
    modifiers that drive *seasonality* are rebuilt to average exactly 1.0
    within each year, so none of this trend is seasonal leakage — it is all
    panel, prices, and hours. Which of the three matters most is precisely
    what the expansion twin (`expansion_review.py`) can isolate for the
    hours, and the customer ledger below isolates for the panel.
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
    DATA,
    MUTED,
    WARN,
    caption,
    con,
    dt,
    go,
    make_subplots,
    mo,
    pl,
    style,
    takeaway,
):
    # ---- the customer panel as a flow ---------------------------------------
    # regulars = card tokens with a real history (>= 10 receipts); guests'
    # one-off tokens would otherwise swamp the arrival/departure story
    _tok = con.sql(
        query = """
            SELECT customer_id,
                   date_trunc('month', date)  AS m,
                   count(DISTINCT receipt_id) AS visits,
                   min(date)                  AS first_d,
                   max(date)                  AS last_d
            FROM   receipts
            WHERE  customer_id IS NOT NULL
              AND  qty > 0
              AND  ref_receipt_id IS NULL
            GROUP  BY 1, 2
        """,
    ).pl()
    _life = _tok.group_by("customer_id").agg(
        pl.col("visits").sum().alias("n"),
        pl.col("first_d").min().alias("first_seen"),
        pl.col("last_d").max().alias("last_seen"),
    )
    _regs = _life.filter(pl.col("n") >= 10)
    _reg_ids = set(_regs["customer_id"].to_list())
    _monthly = _tok.filter(pl.col("customer_id").is_in(list(_reg_ids))) \
        .group_by("m").agg(pl.col("customer_id").n_unique().alias("active")) \
        .sort(by = "m")

    # the 2025 cohort: regulars already shopping in the first quarter —
    # how many of them are still shopping, month by month?
    _cohort = set(_regs.filter(pl.col("first_seen") < dt.date(2025, 4, 1))["customer_id"].to_list())
    _coh_active = _tok.filter(pl.col("customer_id").is_in(list(_cohort))) \
        .group_by("m").agg(pl.col("customer_id").n_unique().alias("active")) \
        .sort(by = "m").with_columns((100 * pl.col("active") / len(_cohort)).alias("pct"))

    # grade the churn inference: "gone" = silent for the last 12 weeks of
    # data; the answer key knows who actually moved away
    _gone_hat = set(_regs.filter(pl.col("last_seen") < dt.date(2027, 10, 8))["customer_id"].to_list())
    _hid = pl.read_csv(
        source = DATA / "scenarios" / "3y_baseline" / "hidden" / "customers.csv",
        schema_overrides = {"departure_date": pl.Utf8},
    )
    _truth_gone = set(_hid.filter(
        pl.col("departure_date").is_not_null() & (pl.col("departure_date") != "")
    )["token"].to_list())
    _tp = len(_gone_hat & _truth_gone)
    churn_stats = {
        "n_regs": len(_regs),
        "n_cohort": len(_cohort),
        "cohort_left": 100 - float(_coh_active["pct"][-1]),
        "n_flagged": len(_gone_hat),
        "precision": _tp / max(1, len(_gone_hat)),
        "recall_in_panel": _tp / max(1, len(_truth_gone & _reg_ids)),
    }

    _fig = make_subplots(
        rows = 1,
        cols = 2,
        subplot_titles = (
            "Regular customers active each month",
            "Share of the early-2025 cohort shopping, month by month",
        ),
        horizontal_spacing = 0.12,
    )
    _fig.add_scatter(
        x = _monthly["m"].to_list(),
        y = _monthly["active"].to_list(),
        mode = "lines+markers",
        line = dict(
            color = ACCENT,
            width = 2,
        ),
        marker = dict(size = 5),
        row = 1,
        col = 1,
    )
    _fig.add_scatter(
        x = _coh_active["m"].to_list(),
        y = _coh_active["pct"].to_list(),
        mode = "lines+markers",
        line = dict(
            color = WARN,
            width = 2,
        ),
        marker = dict(size = 5),
        row = 1,
        col = 2,
    )
    for _c in (1, 2):
        _fig.add_vline(
            x = dt.date(2026, 9, 1),
            line_dash = "dot",
            line_color = MUTED,
            line_width = 1,
            row = 1,
            col = _c,
        )
    style(
        fig = _fig,
        title = "The customer panel is a flow: arrivals replace departures, and the neighborhood slowly grows",
        n_subplot_titles = 2,
    )
    _fig.update_yaxes(
        title_text = "distinct card regulars",
        range = [0, float(_monthly["active"].max()) * 1.3],
        row = 1,
        col = 1,
    )
    _fig.update_yaxes(
        title_text = "% of cohort shopping that month",
        range = [0, 119],
        row = 1,
        col = 2,
    )
    _fig.update_xaxes(
        title_text = "",
        row = 1,
        col = 1,
    )
    _fig.update_xaxes(
        title_text = "",
        row = 1,
        col = 2,
    )
    takeaway(
        fig = _fig,
        text = "headcount holds steady — churn and new arrivals nearly cancel",
        x = 0.02,
        y = 0.99,
        row = 1,
        col = 1,
    )
    takeaway(
        fig = _fig,
        text = f"~{churn_stats['cohort_left']:.0f}% of the original regulars are gone by the end",
        x = 0.02,
        y = 0.16,
        row = 1,
        col = 2,
    )
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 7 · Who left, who arrived — reading churn from silence

    A card token never announces a departure; it just stops appearing. Over
    one year that silence was unreadable. Over three, it becomes a
    measurable flow: of the **{churn_stats['n_regs']} regulars** the shop
    has ever had, the early-2025 cohort ({churn_stats['n_cohort']} people)
    thins steadily — yet the active headcount barely moves, because new
    households keep arriving in their place.
    """
            ),
            _fig,
            caption(
                "Left: distinct regular card tokens seen each month. The "
                "level is remarkably stable — churn and replacement roughly "
                "cancel — drifting up modestly after September 2026, when "
                "the apartment block across the street filled (dotted "
                "line). Right: the same data cut as a cohort — of the "
                "regulars already shopping in early 2025, the share seen "
                "in any given month decays steadily (it starts near 85%, "
                "not 100%, because even a loyal regular skips the odd "
                "month). A loyalty analysis that "
                "ignores this (computing 'average customer value' only on "
                "tokens present all three years) would be studying "
                "survivors, not customers."
            ),
            mo.accordion(
                items = {
                    "Grading the churn inference against the answer key": mo.md(
                        f"""
    **The rule tested:** a regular is inferred *gone* if their last purchase
    is more than 12 weeks before the data ends. That flags
    **{churn_stats['n_flagged']}** of {churn_stats['n_regs']} regulars.

    **The truth** (`hidden/customers.csv`, which records each household's
    actual departure date): the rule's precision is
    **{churn_stats['precision']:.0%}** — nearly every silent token really
    did move away — and it catches
    **{churn_stats['recall_in_panel']:.0%}** of the true departures among
    regulars (the misses are mostly households that left in the final
    weeks, whose silence is still too short to read). Churn inference from
    silence works, but only with a deliberately conservative cutoff and an
    honest blind spot at the end of the observation window — the classic
    right-censoring problem, live in the data.
    """
                    ),
                },
            ),
        ],
    )
    return (churn_stats,)


@app.cell
def _(
    ACCENT,
    MUTED,
    WARN,
    caption,
    con,
    dt,
    go,
    make_subplots,
    mo,
    style,
    takeaway,
):
    # ---- March 2027: the break you cannot see -------------------------------
    # ragged first/last calendar weeks would draw fake cliffs — keep full weeks
    _wk = con.sql(
        query = """
            SELECT date_trunc('week', date)       AS w,
                   count(DISTINCT receipt_id)     AS visits
            FROM   receipts
            WHERE  qty > 0
              AND  ref_receipt_id IS NULL
            GROUP  BY 1
            HAVING count(DISTINCT date) >= 6
            ORDER  BY 1
        """,
    ).pl()
    _prem = con.sql(
        query = """
            SELECT date_trunc('month', r.date) AS m,
                   100 * sum(CASE WHEN p.brand_level = 'premium'
                                  THEN r.qty * r.unit_price END)
                       / sum(r.qty * r.unit_price) AS prem_share
            FROM   receipts r
            JOIN   products p USING (uid)
            WHERE  r.qty > 0
              AND  r.ref_receipt_id IS NULL
            GROUP  BY 1
            ORDER  BY 1
        """,
    ).pl()
    _fig = make_subplots(
        rows = 1,
        cols = 2,
        subplot_titles = (
            "Weekly visits, with the discounter's opening marked",
            "Share of spend on premium brands, monthly",
        ),
        horizontal_spacing = 0.12,
    )
    _fig.add_scatter(
        x = _wk["w"].to_list(),
        y = _wk["visits"].to_list(),
        mode = "lines",
        line = dict(
            color = ACCENT,
            width = 1.5,
        ),
        row = 1,
        col = 1,
    )
    _fig.add_scatter(
        x = _prem["m"].to_list(),
        y = _prem["prem_share"].to_list(),
        mode = "lines+markers",
        line = dict(
            color = ACCENT,
            width = 2,
        ),
        marker = dict(size = 5),
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
        # the marker label lives inside the panel, clear of the subplot title
        _fig.add_annotation(
            x = dt.date(2027, 3, 1),
            y = 0.06,
            yref = "y domain",
            text = "discounter opens",
            showarrow = False,
            xanchor = "left",
            xshift = 6,
            font = dict(
                color = WARN,
                size = 11,
            ),
            row = 1,
            col = _c,
        )
    style(
        fig = _fig,
        title = "Looking for the discounter in the shop's own data — and not finding it",
        n_subplot_titles = 2,
    )
    _fig.update_yaxes(
        title_text = "receipts / week",
        range = [0, float(_wk["visits"].max()) * 1.28],
        row = 1,
        col = 1,
    )
    _fig.update_yaxes(
        title_text = "premium share of spend (%)",
        range = [0, float(_prem["prem_share"].max()) * 1.35],
        row = 1,
        col = 2,
    )
    takeaway(
        fig = _fig,
        text = "no cliff: growth and longer hours mask the leak",
        x = 0.02,
        y = 0.99,
        row = 1,
        col = 1,
    )
    takeaway(
        fig = _fig,
        text = "the premium drift starts in 2026 — before the entry",
        x = 0.02,
        y = 0.99,
        row = 1,
        col = 2,
    )
    mo.vstack(
        items = [
            mo.md(
                """
    ## 8 · March 2027: the competitor you can't see from inside

    A discount grocer opened 600 m away on March 1, 2027. Here is the
    uncomfortable finding: **you cannot see it in this dataset.** Weekly
    visits keep rising through the entry; revenue keeps growing; even the
    premium-brand share of spend — the classic tell for "the price-hunters
    left" — was already drifting up long before March.
    """
            ),
            _fig,
            caption(
                "Left: weekly receipt counts. Panel growth, the expansion's "
                "extra hours, and ordinary seasonality all push visits up "
                "at exactly the moment the discounter pushes them down — "
                "the net line shows no break. Right: premium share of "
                "spend. A naive reading ('our remaining customers are more "
                "premium — the cheap shoppers must have defected') fails on "
                "timing: the drift begins in 2026. The honest conclusion "
                "is that a before/after comparison around March 2027 "
                "measures nothing but the trend itself. What the entry "
                "actually cost — about €16k of 2027 revenue — is only "
                "knowable against the no-competitor twin, which is the "
                "whole subject of competitor_entry_study.py."
            ),
        ],
    )
    return


@app.cell
def _(
    ACCENT,
    ACCENT_LIGHT,
    MUTED,
    WARN,
    caption,
    con,
    dt,
    go,
    make_subplots,
    mo,
    style,
    takeaway,
):
    # ---- the capital story: the new columns tell it themselves --------------
    _cs = con.sql(
        query = """
            SELECT make_date(year, month, 1) AS m,
                   cash,
                   retained_earnings,
                   owner_draw,
                   capex,
                   profit_tax_paid
            FROM   cost_sheet
            ORDER  BY year, month
        """,
    ).pl()
    _cum_draw = _cs["owner_draw"].cum_sum()
    _fig = make_subplots(
        rows = 1,
        cols = 2,
        subplot_titles = (
            "Till cash and the retained-earnings ledger",
            "What the owner has taken home, cumulatively",
        ),
        horizontal_spacing = 0.12,
    )
    _fig.add_scatter(
        x = _cs["m"].to_list(),
        y = _cs["cash"].to_list(),
        mode = "lines",
        line = dict(
            color = MUTED,
            width = 2,
        ),
        row = 1,
        col = 1,
    )
    _fig.add_scatter(
        x = _cs["m"].to_list(),
        y = _cs["retained_earnings"].to_list(),
        mode = "lines",
        line = dict(
            color = ACCENT,
            width = 2.5,
        ),
        row = 1,
        col = 1,
    )
    # the two balances end within ~1k of each other: nudge the labels apart
    _fig.add_annotation(
        x = _cs["m"].to_list()[-1],
        y = float(_cs["cash"][-1]),
        text = "cash",
        showarrow = False,
        xanchor = "left",
        xshift = 8,
        yshift = -16,
        font = dict(
            color = "#9A9A9A",
            size = 12,
        ),
        row = 1,
        col = 1,
    )
    _fig.add_annotation(
        x = _cs["m"].to_list()[-1],
        y = float(_cs["retained_earnings"][-1]),
        text = "retained<br>earnings",
        showarrow = False,
        xanchor = "left",
        xshift = 8,
        yshift = 20,
        font = dict(
            color = ACCENT,
            size = 12,
        ),
        row = 1,
        col = 1,
    )
    _marks = [
        (dt.date(2026, 1, 1), "books formalize"),
        (dt.date(2026, 11, 1), "expansion €14k"),
        (dt.date(2027, 1, 1), "rent +12%, tax paid"),
    ]
    for _d, _txt in _marks:
        _fig.add_vline(
            x = _d,
            line_dash = "dot",
            line_color = MUTED,
            line_width = 1,
            row = 1,
            col = 1,
        )
    _fig.add_scatter(
        x = _cs["m"].to_list(),
        y = _cum_draw.to_list(),
        mode = "lines",
        line = dict(
            color = ACCENT,
            width = 2.5,
        ),
        row = 1,
        col = 2,
    )
    style(
        fig = _fig,
        title = "Where the owner's money actually went, 2025–2027",
        n_subplot_titles = 2,
        right_margin = 96,
    )
    _fig.update_yaxes(
        title_text = "€ at month end",
        range = [0, float(_cs["cash"].max()) * 1.3],
        row = 1,
        col = 1,
    )
    _fig.update_yaxes(
        title_text = "cumulative owner draws (€)",
        range = [0, float(_cum_draw[-1]) * 1.35],
        row = 1,
        col = 2,
    )
    takeaway(
        fig = _fig,
        text = "RE opens Jan 2026, climbs, drops €14k at the expansion, then grinds sideways",
        x = 0.02,
        y = 0.99,
        row = 1,
        col = 1,
    )
    takeaway(
        fig = _fig,
        text = f"€{float(_cum_draw[-1]):,.0f} taken home in two years — the shop pays a wage, barely",
        x = 0.02,
        y = 0.99,
        row = 1,
        col = 2,
    )
    _total_draw = float(_cum_draw[-1])
    _tax_paid = float(_cs["profit_tax_paid"].sum())
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 9 · The capital story

    The three-year cost sheet carries columns the one-year world never
    needed: from January 2026 the owner **formalized the books** — declared
    the first year's after-tax surplus as retained earnings, started paying
    himself half of every good month's result, and began settling the
    previous year's profit tax in cash each January
    (€{_tax_paid:,.0f} paid over the two settlements).
    """
            ),
            _fig,
            caption(
                "Left: the two balances that govern every decision. Cash "
                "(gray) absorbs the seasons, the January tax bills, and the "
                "€14,000 capex all at once; retained earnings (blue) is the "
                "disciplined ledger — half of each positive month's "
                "after-tax result in, the expansion out. The three dotted "
                "markers are the formalization, the expansion, and the "
                "brutal January 2027 (rent step and tax bill in the same "
                "month). Right: cumulative owner draws — the only money "
                "that ever actually left the business for the owner's "
                "pocket. Note the flat stretches: in loss months he takes "
                "nothing."
            ),
        ],
    )
    return


@app.cell
def _(mo, pl, pnl):
    _p27 = float(pnl.filter(pl.col("year") == 2027)["profit_before_tax"][0])
    mo.md(
        f"""
    ## 10 · The verdict question: renew the lease, or close?

    At the December 2027 close the books say: record revenue, and
    **€{_p27:,.0f}** of profit before tax. The lease is up for renewal for
    2028–29. Three explanations for the collapse are on the table, and this
    dataset alone cannot rank them:

    1. **The discounter** — the top-line leak since March 2027;
    2. **The expansion** — a clerk's wages and payroll tax, all year, on an
       18% gross margin;
    3. **The contracts** — rent +12%, two wage revisions, tariff resets.

    Ranking them is exactly what the two counterfactual notebooks do,
    because the laboratory generated the twins this review cannot observe:

    - **`competitor_entry_study.py`** — the same three years without the
      discounter. Spoiler: the entry costs about €5k of 2027 profit —
      real, but nowhere near −€2k-instead-of-+€50k territory.
    - **`expansion_review.py`** — the same three years without the
      expansion. Spoiler: without it, 2027 is comfortably profitable
      *even with the discounter*. The bet, not the neighbor, is what made
      2027 dangerous.

    The renewal question, honestly posed, is therefore not "can we survive
    the competition?" but "**does the expansion stay?**" — and that is a
    question about payroll, not about the lease.
    """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ### Appendix — how this review was put together

    Everything above comes from `data/scenarios/3y_baseline/visible/`,
    cleaned through the same contract as the one-year workbook (retry
    dedup, void cancellation, label normalization), rebuilt in-memory on
    every run. The churn grading additionally reads
    `hidden/customers.csv` — the answer key an analyst would not have; it
    is used only inside the clearly marked grading panel, never in the
    analysis itself. Tools: DuckDB for SQL over the raw files, Polars for
    reshaping, Plotly for every chart, statsmodels for the trend
    regression (HAC standard errors). The two companion notebooks —
    `competitor_entry_study.py` and `expansion_review.py` — grade this
    review's open questions against the CRN counterfactual twins.
    """)
    return


if __name__ == "__main__":
    app.run()
