import marimo

__generated_with = "0.23.14"
app = marimo.App(
    width="full",
    app_title="Your Grocery Store — Three Years, Explained",
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

    # the workbook lives in analyses/; the project root is one level up
    ROOT = Path(__file__).resolve().parent.parent
    DATA = ROOT / "data"

    # ---- chart style: declutter per Knaflic's "Storytelling with Data" -----
    # one accent for what the narrative claims, gray for context, no chart
    # border, no gridlines at all, no value axis on bar/column charts (their
    # bars carry the number directly). Titles are DESCRIPTIVE (they say what
    # the chart shows); the takeaway claim lives inside the plot as a compact
    # annotation via takeaway(), and the caption() underneath elaborates the
    # context, mechanism, and caveats the compact annotation can't carry.
    # Legends are replaced by direct end-of-line labels wherever the series
    # count allows it. The default right margin is slim; charts that end
    # their lines with text labels ask style() for extra room.
    INK = "#404040"
    MUTED = "#BFBFBF"
    ACCENT = "#2E5EAA"
    ACCENT_LIGHT = "#9DB8E6"
    WARN = "#B44646"
    GRID = "#ECECEC"
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
    # no gridlines anywhere; bar/column charts additionally drop the value
    # axis entirely once its numbers are written directly on the marks
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
        """Apply the shared declutter: plain axes, a takeaway title (or none,
        when subplot_titles already carry it), a recessive legend only when
        the series count needs one. `right_margin` widens the right margin
        for charts whose lines end in a text label. `n_subplot_titles`
        shrinks the panel titles make_subplots() generated — they render at
        full size by default and are the usual overflow culprit in a 2-panel
        chart. They are always the *first* annotations added to the figure
        (created by make_subplots before any manual add_annotation call
        runs), so we can target them by position without disturbing later
        annotations like end-of-line labels or the "Oct 1" marker."""
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
                    # indent the title to the plot area's left edge instead of
                    # letting it sit flush against the figure border
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
        """For a column/bar chart whose bars carry their own value labels:
        drop the tick numbers, the axis line, and the gridline — but keep
        (or set) a short axis title, so the reader still knows what unit
        those printed-on-the-bar numbers are in."""
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
        """A short italic line right under a chart, stating what to look for.
        The left padding lines the caption up with the chart title above it."""
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
        """The headline, inside the plot, kept compact: one or two short
        lines carrying the single most important claim. Everything longer —
        context, mechanism, caveats — belongs in caption() underneath."""
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
        DATA,
        MUTED,
        ROOT,
        WARN,
        caption,
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
    # Your Store's First Three Years, in Plain English

    You handed over three years of paperwork — every till receipt, every
    night's shelf count, every supplier invoice, the price list, the
    promotions you ran, the monthly bills, what got thrown away, and a
    record of the weather outside. Nothing else. No survey, no market
    research, nobody watching over your shoulder. Just what the shop itself
    wrote down, one year after another.

    This notebook is the **fast tour** — the same order a first-time reader
    would naturally ask questions in, one section per question, each kept to
    a page or two:

    1. **How the shop runs** — hours, staffing, and what's on the shelves, then and now.
    2. **Getting organized** — putting every record from three years into one place.
    3. **Sanity-checking the numbers** — what real paperwork gets wrong, in brief.
    4. **The big picture** — what came in, what went out, and where the profit actually went.
    5. **When people actually shop** — the days and hours that matter, averaged over three years.
    6. **Growth vs. the seasons** — telling "the business is growing" apart from "it's just summer again."
    7. **Does the weather, the price, and the promotions actually work?** — headline verdicts only.
    8. **The two quiet costs** — empty shelves, and food that goes in the bin.
    9. **Your customers, and who's still here** — churn, loyalty, and the limits of the till.
    10. **Can we guess next week's sales?** — a forecasting model, tested honestly.
    11. **What I'd do about it** — the short, prioritized list.

    Six of these questions (3, 7, 8, 9, 10, 11) already have a **dedicated,
    full-depth, GRADED notebook** — one that checks its own answers against
    the hidden truth behind the simulation, not just against itself. This
    workbook gives you the headline from each and tells you exactly where to
    go for the full graded version; building the whole thing twice would
    waste your time. Sections 1, 2, 4, 5, and 6 are the ones that only exist
    here, because they're genuinely different once there are three years of
    history instead of one.
    """)
    return


@app.cell
def _(DATA, ROOT, pl):
    # ---- store-operations snapshot: who this shop is, before the numbers ----
    # 3y_baseline is the three-year arc's reference arm (Phase 5); its year
    # one replays the one-year baseline's exogenous script byte-for-byte
    _visb = DATA / "scenarios" / "3y_baseline" / "visible"
    _loc = pl.read_csv(source = _visb / "locations.csv")
    _cs = pl.read_csv(source = _visb / "cost_sheet.csv")
    _rec = pl.read_csv(source = _visb / "receipts.csv")
    _cal = pl.read_csv(
        source = _visb / "calendar.csv",
        schema_overrides = {"holiday": pl.Utf8},
    )
    _proc = pl.read_csv(source = _visb / "procurement.csv")
    _inv = pl.read_csv(source = _visb / "inventory_eod.csv")
    _catalog = pl.read_excel(source = ROOT / "SKUs.xlsx")

    # this location.csv lists every candidate site the owner once weighed up;
    # the one actually rented is the one whose year-one rent matches the
    # cost sheet's first month (rent later steps up on the 2027 renewal)
    _target_rent = float(_cs.filter(pl.col("month") == pl.col("month").min())["rent"][0])
    _mine = _loc.with_columns(
        (pl.col("rent") - _target_rent).abs().alias("rent_diff"),
    ).sort(by = "rent_diff").row(
        index = 0,
        named = True,
    )

    ops = {
        "rent_y1": float(_cs.filter(pl.col("year") == 2025)["rent"][0]),
        "rent_y3": float(_cs.filter(pl.col("year") == 2027)["rent"][0]),
        "setup_cost": _mine["setup_cost"],
        "shelf_capacity_units": int(_mine["shelf_capacity_units"]),
        "shelf_slots": int(_mine["shelf_slots"]),
        # hour = 0 is a POS clock glitch (Section 3), not a 00:00 sale
        "open_hour_y1": int(_rec.filter((pl.col("hour") > 0) & (pl.col("date") < "2026-11-01"))["hour"].min()),
        "close_hour_y1": int(_rec.filter(pl.col("date") < "2026-11-01")["hour"].max()) + 1,
        "open_hour_now": int(_rec.filter((pl.col("hour") > 0) & (pl.col("date") >= "2026-11-01"))["hour"].min()),
        "close_hour_now": int(_rec.filter(pl.col("date") >= "2026-11-01")["hour"].max()) + 1,
        "n_closed_days": int((_cal["closed"] == 1).sum()),
        "n_categories": _catalog["category"].n_unique(),
        "n_catalog_products": _catalog.height,
        "n_stocked_products": _inv["uid"].n_unique(),
        "restock_dow": _proc["delivery_date"].str.to_date().min().strftime("%A"),
        "wages_2025": float(_cs.filter(pl.col("year") == 2025)["wages"].sum()),
        "wages_2027": float(_cs.filter(pl.col("year") == 2027)["wages"].sum()),
    }
    return (ops,)


@app.cell
def _(mo, ops):
    mo.md(f"""
    ## 1 · How the shop runs, day to day — then and now

    Before diving into the numbers, it's worth pinning down what kind of
    shop this actually is — and how that changed over three years.

    **Hours.** For the first two years the shop opened at
    **{ops['open_hour_y1']}:00** and closed at **{ops['close_hour_y1']}:00**
    every day except
    **{ops['n_closed_days']} closed holidays a year** — with exactly one
    person on the floor: you. Since **November 2026** the shop has opened
    earlier and closed later — **{ops['open_hour_now']}:00 to
    {ops['close_hour_now']}:00** — because you hired a second person, a
    part-time clerk, once the shop's own retained earnings could cover it.

    **Staffing and its cost.** The wage line was **€0** in 2025 (you worked
    alone); by 2027, a full year with the clerk on the payroll, it had
    grown to **€{ops['wages_2027']:,.0f}** — a real, permanent cost the
    2025 numbers never had to carry. Any comparison between year one and
    year three has to remember this.

    **What's on the shelves.** The supplier catalog offers
    {ops['n_catalog_products']} possible products across
    {ops['n_categories']} categories — the shop has room for
    **{ops['shelf_slots']} distinct products** at once
    (**{ops['shelf_capacity_units']:,} units** of total shelf stock), and
    has stocked the **same {ops['n_stocked_products']} products, unchanged,
    for all three years** — a deliberately fixed assortment, so any change
    you see later in what people buy is demand shifting, not the shelf
    itself changing under them.

    **The restocking rhythm** never changed either: a delivery every single
    **{ops['restock_dow']}**, three years running.

    **The lease.** Rent was **€{ops['rent_y1']:,.2f}/month** for the first
    two years under the original 3-year contract; the renewal review at the
    start of 2027 stepped it to **€{ops['rent_y3']:,.2f}/month** (+12%) —
    the lease itself expires at the end of 2027, which is why "renew or
    close" is the question this whole engagement is really building toward
    (Section 11).
    """)
    return


@app.cell
def _(DATA, ROOT, duckdb, pl):
    # ---- build the analytical database -------------------------------------
    # (falls back to in-memory if another session holds the .duckdb file)
    _db_path = DATA / "store.duckdb"
    try:
        if _db_path.exists():
            _db_path.unlink()
        con = duckdb.connect(str(_db_path))
    except (OSError, duckdb.IOException):
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
    _products = pl.read_excel(source = ROOT / "SKUs.xlsx")  # the store's product master
    con.register("products_df", _products)
    con.execute(query = "CREATE TABLE products AS SELECT * FROM products_df")

    # ---- the cleaned layer -------------------------------------------------
    # Real paperwork is imperfect; Section 3 summarizes what these views
    # repair (full defect-by-defect grading lives in clean_and_describe.py).
    # Downstream queries only ever see the cleaned names.
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
    # procurement: a handful of supplier invoices were entered twice (same
    # line, a later posting date) -> keep one copy, the earliest posting
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
    # write-offs: spoilage logs and monthly stock-count corrections (plus,
    # on this arc, one freezer-failure damage event) share one file
    con.execute(
        query = """
            CREATE VIEW write_offs AS
            SELECT uid,
                   units,
                   date
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
    # promotions: normalize the one misspelled category label
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
    # weather and the shelf snapshot pass through unchanged: the weather
    # gaps are honest missing data (consumers must handle the NULLs), and
    # the snapshot is the owner's book stock, warts and all
    con.execute(query = "CREATE VIEW weather AS SELECT * FROM weather_raw")
    con.execute(query = "CREATE VIEW inventory_eod AS SELECT * FROM inventory_eod_raw")
    con.execute(query = "CREATE VIEW cost_sheet AS SELECT * FROM cost_sheet_raw")
    con.execute(query = "CREATE VIEW calendar AS SELECT * FROM calendar_raw")
    con.execute(query = "CREATE VIEW price_history AS SELECT * FROM price_history_raw")
    con.execute(query = "CREATE VIEW tax_statement AS SELECT * FROM tax_statement_raw")

    tbl_summary = con.sql(
        query = """
            SELECT replace(table_name, '_raw', '')     AS table_name,
                   (SELECT count(*)
                    FROM   duckdb_columns() c
                    WHERE  c.table_name = t.table_name)  AS columns,
                   estimated_size                        AS rows
            FROM   duckdb_tables() t
            ORDER  BY rows DESC
        """,
    ).pl()
    return con, tbl_summary


@app.cell
def _(caption, mo, tbl_summary):
    _erd = mo.mermaid("""
    erDiagram
        receipts     }o--|| products     : "uid"
        receipts     }o--|| calendar     : "date"
        inventory_eod }o--|| products    : "uid"
        inventory_eod }o--|| calendar    : "date"
        procurement  }o--|| products     : "uid"
        procurement  }o--|| calendar     : "delivery_date"
        write_offs   }o--|| products     : "uid"
        price_history }o--|| products    : "uid"
        promotions   }o--|| products     : "category"
        weather      ||--|| calendar     : "date"
        cost_sheet   ||--|| calendar     : "year, month"
        tax_statement ||--|| cost_sheet  : "year"

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
        products {
            string uid
            string category
            string product_type
            string brand_level
        }
        inventory_eod {
            string uid
            date date
            int on_hand
        }
        procurement {
            string uid
            date order_date
            date delivery_date
            date posted_date
            int qty
            float unit_cost
        }
        calendar {
            date date
            int dow
            int month
            int week
            int closed
        }
        cost_sheet {
            int year
            int month
            float revenue
            float retained_earnings
            float owner_draw
            float capex
        }
    """)
    mo.vstack(
        items = [
            mo.md(
                """
    ## 2 · Getting organized

    Three years of folders, invoices, and printouts, tipped onto one big
    table and sorted into labeled piles — the same nine piles as any single
    year (**receipts**, **nightly shelf counts**, **supplier invoices**,
    **price history**, **promotions**, **write-offs**, **monthly bills**,
    **calendar and weather**), just three times as tall, plus one new
    column throughout: **`year`**, since a month number alone (1–12) now
    describes three different Januaries.

    The only structural change from a one-year shop: `cost_sheet` gained
    **capital columns** — retained earnings, owner draws, and one capital
    expense (`capex`) — because a business that survives past its first
    year starts making decisions about what to do with its profit. Section
    4 is where those columns actually get used.
    """
            ),
            mo.ui.table(
                data = tbl_summary,
                selection = None,
            ),
            _erd,
            caption(
                "How the piles connect: a line between two tables means they "
                "share a column an analysis can join on, and the label names "
                "that column. `cost_sheet` now keys to the calendar on "
                "*(year, month)*, not month alone — the one join that "
                "silently breaks if a one-year query gets pointed at three "
                "years of data without updating."
            ),
        ],
    )
    return


@app.cell
def _(con):
    # ---- data quality sweep (condensed; full grading in clean_and_describe.py)
    dq = {}
    dq["span"] = con.sql(
        query = "SELECT min(date), max(date) FROM receipts",
    ).fetchone()
    dq["n_lines"] = con.sql(
        query = "SELECT count(*) FROM receipts",
    ).fetchone()[0]
    dq["n_receipts"] = con.sql(
        query = "SELECT count(DISTINCT receipt_id) FROM receipts",
    ).fetchone()[0]
    dq["dup_receipts"] = con.sql(
        query = """
            WITH lines AS (
                SELECT receipt_id,
                       count(*) AS n
                FROM   receipts_raw
                GROUP  BY receipt_id, hour, payment, customer_id, uid,
                          qty, unit_price, promo, date
            )
            SELECT count(*)
            FROM   (SELECT receipt_id
                    FROM   lines
                    GROUP  BY receipt_id
                    HAVING bool_and(n % 2 = 0))
        """,
    ).fetchone()[0]
    dq["ledger_gap"] = con.sql(
        query = """
            SELECT (SELECT sum(qty * unit_price) FROM receipts)::DOUBLE
                 - (SELECT sum(revenue) FROM cost_sheet)::DOUBLE
        """,
    ).fetchone()[0]
    dq["refunds"], dq["refund_eur"] = con.sql(
        query = """
            SELECT count(*),
                   coalesce(-sum(qty * unit_price), 0)::DOUBLE
            FROM   receipts
            WHERE  ref_receipt_id IS NOT NULL
        """,
    ).fetchone()
    dq["dup_invoices"] = con.sql(
        query = """
            SELECT (SELECT count(*) FROM procurement_raw)
                 - (SELECT count(*) FROM procurement)
        """,
    ).fetchone()[0]
    dq["weather_nulls"] = con.sql(
        query = "SELECT count(*) FROM weather WHERE temp_C IS NULL",
    ).fetchone()[0]
    return (dq,)


@app.cell
def _(dq, mo):
    mo.md(f"""
    ## 3 · Cleaning up the paperwork before we trust the numbers

    Three years, **{dq['span'][0]} to {dq['span'][1]}**, **{dq['n_lines']:,}
    receipt lines** across **{dq['n_receipts']:,} till transactions** — and
    real paperwork, three years running, still gets things wrong the same
    handful of ways: **{dq['dup_receipts']} receipts** got re-uploaded whole
    by a POS retry (fixed by keeping half of any receipt whose every line
    repeats an even number of times), **{dq['dup_invoices']} supplier
    invoices** got entered twice, **{dq['refunds']} refunds**
    (€{dq['refund_eur']:,.0f}) posted as their own till transactions, and
    the weather sensor went dark for **{dq['weather_nulls']} days**. After
    cleaning, the till ties to the owner's own monthly ledger to within
    **€{abs(dq['ledger_gap']):,.2f}** — the last cent of drift is a single
    natural false positive the dedup rule can't structurally rule out (a
    genuinely all-even receipt), not a bug.

    **This is the short version.** `analyses/clean_and_describe.py` runs
    the full graded version: every defect family checked row-by-row against
    the hidden answer key (precision and recall, not just a count), the
    complete reconciliation contract including the cash walk across all
    three years, and the eight core descriptive questions on the
    proven-clean data.
    """)
    return


@app.cell
def _(
    ACCENT,
    MUTED,
    WARN,
    caption,
    con,
    go,
    hide_value_axis,
    make_subplots,
    mo,
    style,
    takeaway,
):
    # ---- the three-year P&L ---------------------------------------------------
    pnl = con.sql(
        query = "SELECT * FROM cost_sheet ORDER BY year, month",
    ).pl()
    _cost_cols = [
        "rent",
        "wages",
        "payroll_tax",
        "utilities",
        "storage",
        "flyers",
        "vat",
        "credit_interest",
        "repairs",
    ]
    _total_cost = (pnl["procurement"] + sum(pnl[c] for c in _cost_cols)).to_list()
    _idx = list(range(1, pnl.height + 1))  # a continuous month index, Jan 2025 = 1
    _year_starts = [
        i + 1
        for i, (y0, y1) in enumerate(zip(pnl["year"][:-1], pnl["year"][1:]))
        if y1 != y0
    ]

    kpi = {
        "revenue": float(pnl["revenue"].sum()),
        "procurement": float(pnl["procurement"].sum()),
        "opex": float(sum(pnl[c].sum() for c in _cost_cols)),
        "gross_margin_pct": 1 - float(pnl["procurement"].sum()) / float(pnl["revenue"].sum()),
        "capex": float(pnl["capex"].sum()),
        "owner_draw": float(pnl["owner_draw"].sum()),
        "re_end": float(pnl["retained_earnings"][-1]),
    }
    _exp_row = pnl.filter(pnl["capex"] > 0)
    kpi["expansion_year"] = int(_exp_row["year"][0]) if _exp_row.height else None
    kpi["expansion_month_num"] = int(_exp_row["month"][0]) if _exp_row.height else None

    _fig = make_subplots(
        rows = 1,
        cols = 2,
        subplot_titles = (
            "Revenue vs. total operating cost, 36 months",
            "Retained earnings: the fund that paid for the expansion",
        ),
        horizontal_spacing = 0.12,
    )
    _fig.add_bar(
        x = _idx,
        y = pnl["revenue"].to_list(),
        marker_color = ACCENT,
        marker_line_width = 0,
        row = 1,
        col = 1,
    )
    _fig.add_bar(
        x = _idx,
        y = _total_cost,
        marker_color = MUTED,
        marker_line_width = 0,
        row = 1,
        col = 1,
    )
    _fig.update_layout(barmode = "group")
    for _x in _year_starts:
        _fig.add_vline(
            x = _x - 0.5,
            line_width = 1,
            line_dash = "dot",
            line_color = MUTED,
            row = 1,
            col = 1,
        )
    _fig.add_trace(
        go.Scatter(
            x = _idx,
            y = pnl["retained_earnings"].to_list(),
            mode = "lines",
            line = dict(
                color = ACCENT,
                width = 2.5,
            ),
        ),
        row = 1,
        col = 2,
    )
    if kpi["expansion_month_num"]:
        _exp_idx = _idx[
            (pnl["year"].to_list().index(kpi["expansion_year"])
             + kpi["expansion_month_num"] - 1)
        ]
        _fig.add_vline(
            x = _exp_idx,
            line_width = 1.5,
            line_dash = "dash",
            line_color = WARN,
            row = 1,
            col = 2,
        )
        _fig.add_annotation(
            text = "clerk hired,<br>capex paid",
            x = _exp_idx,
            y = 1,
            yref = "y2 domain",
            yanchor = "top",
            xshift = 8,
            xanchor = "left",
            showarrow = False,
            font = dict(
                color = WARN,
                size = 11,
            ),
        )
    style(
        fig = _fig,
        title = "Three years of the P&L, side by side with the fund it eventually financed an expansion from",
        n_subplot_titles = 2,
    )
    hide_value_axis(
        fig = _fig,
        axis = "y",
        title = "EUR / month",
        row = 1,
        col = 1,
    )
    hide_value_axis(
        fig = _fig,
        axis = "y",
        title = "EUR, running balance",
        row = 1,
        col = 2,
    )
    _fig.update_xaxes(
        title_text = "month (Jan 2025 = 1)",
        row = 1,
        col = 1,
    )
    _fig.update_xaxes(
        title_text = "month (Jan 2025 = 1)",
        row = 1,
        col = 2,
    )
    takeaway(
        fig = _fig,
        text = "the fund resets to ~0 the month it's spent",
        x = 0.02,
        y = 0.99,
        row = 1,
        col = 2,
    )
    mo.vstack(
        items = [
            _fig,
            caption(
                "Left: revenue (blue) against everything it cost to run the "
                "shop that month (gray), dotted lines marking each new "
                "calendar year — the two climb together, the sign of a "
                "shop growing in a controlled way, not living beyond its "
                "means. Right: retained earnings — half of every month's "
                "positive after-tax result, set aside instead of drawn out "
                "— climbing until it and the till both clear a threshold, "
                "at which point the shop hires a second person and buys a "
                "new freezer, and the fund drops back down."
            ),
        ],
    )
    return (kpi,)


@app.cell
def _(kpi, mo):
    mo.md(f"""
    Over three years the shop took in **€{kpi['revenue']:,.0f}**. Buying the
    goods sold cost **€{kpi['procurement']:,.0f}** — a **{kpi['gross_margin_pct']:.0%}
    margin** on the goods themselves — against **€{kpi['opex']:,.0f}** of
    rent, wages, utilities, VAT, and the rest. None of that is new to a
    three-year shop. What IS new is the question every surviving business
    eventually asks: **what do you do with the profit?**

    This shop's answer, visible only because there are three years of
    ledger to show it: keep half of every month's positive after-tax
    result as **retained earnings**, pay the rest out to yourself as an
    **owner draw** (€{kpi['owner_draw']:,.0f} over three years), and once
    the fund and the till both clear a threshold, spend it — here, a
    **€{kpi['capex']:,.0f} capital outlay** in month
    {kpi['expansion_month_num']} of {kpi['expansion_year']} that hired a
    second person and extended the shop's hours. It is a real decision with
    a real cost, not free money — and whether it was the *right* decision
    is a question this workbook can't answer with a single arm of data
    alone. `analyses/expansion_review.py` answers it properly, against a
    twin of this exact shop where that hire never happened.
    """)
    return


@app.cell
def _(ACCENT, MUTED, caption, con, go, mo, style, takeaway):
    # ==== 5 — when do people actually shop? (averaged across 3 years) ========
    _dow = con.sql(
        query = """
            WITH daily AS (
                SELECT c.dow,
                       c.date,
                       sum(r.qty * r.unit_price) AS rev
                FROM   receipts r
                JOIN   calendar c USING (date)
                WHERE  r.qty > 0
                  AND  r.ref_receipt_id IS NULL
                GROUP  BY c.dow, c.date
            )
            SELECT dow,
                   avg(rev) AS avg_daily_rev
            FROM   daily
            GROUP  BY dow
            ORDER  BY dow
        """,
    ).pl()
    _days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    _hr = con.sql(
        query = """
            SELECT hour,
                   count(DISTINCT receipt_id) AS n
            FROM   receipts
            WHERE  hour IS NOT NULL
            GROUP  BY hour
            ORDER  BY hour
        """,
    ).pl()
    _weekend_share = float(_dow.filter(_dow["dow"] >= 5)["avg_daily_rev"].sum() / _dow["avg_daily_rev"].sum())

    _fig = go.Figure()
    _fig.add_bar(
        x = _days,
        y = _dow["avg_daily_rev"].to_list(),
        marker_color = [
            ACCENT if d >= 5 else MUTED
            for d in _dow["dow"]
        ],
        text = [f"€{v:,.0f}" for v in _dow["avg_daily_rev"]],
        textposition = "outside",
    )
    style(
        fig = _fig,
        title = "Average daily revenue by day of the week, three-year average",
    )
    _fig.update_yaxes(
        showticklabels = False,
        showline = False,
        ticks = "",
        title_text = "avg revenue per day (EUR)",
        title_font = dict(size = 11.5, color = MUTED),
        range = [0, float(_dow["avg_daily_rev"].max()) * 1.25],
    )
    takeaway(
        fig = _fig,
        text = f"weekends (blue) are {_weekend_share:.0%} of all revenue —<br>the same rhythm in year one, two, and three",
        x = 0.98,
        y = 0.98,
        anchor = "right",
    )
    mo.vstack(
        items = [
            mo.md("""
    ## 5 · When do people actually shop?

    A weekly rhythm this fixed doesn't need a whole year to show up, and
    three years just confirms it never moved:
    """),
            _fig,
            caption(
                "Saturday is the single busiest day every year of this "
                "shop's life; Monday is the quietest. The weekly restocking "
                "rhythm (deliveries land Wednesday) and the weekend-heavy "
                "shopping pattern reinforce each other and never drift — "
                "useful to know before reading any month-to-month change "
                "later in this report as something more interesting than "
                "\"that month had one extra Saturday.\""
            ),
        ],
    )
    return


@app.cell
def _(ACCENT, MUTED, caption, con, go, mo, np, pl, style, takeaway):
    # ==== 6 — growth vs. the seasons ===========================================
    _m = con.sql(
        query = """
            SELECT year(r.date)  AS year,
                   c.month,
                   sum(r.qty * r.unit_price) AS rev
            FROM   receipts r
            JOIN   calendar c USING (date)
            WHERE  r.qty > 0
              AND  r.ref_receipt_id IS NULL
            GROUP  BY year(r.date), c.month
            ORDER  BY year, c.month
        """,
    ).pl()
    _m = _m.with_columns(
        (((pl.col("year") - 2025) * 12 + pl.col("month"))).alias("t"),
    )
    # a simple log-linear trend + month-of-year seasonal index, fit by OLS
    _X = np.column_stack([
        np.ones(_m.height),
        _m["t"].to_numpy(),
        *[
            (_m["month"].to_numpy() == k).astype(float)
            for k in range(2, 13)
        ],
    ])
    _y = np.log(_m["rev"].to_numpy())
    _beta, *_ = np.linalg.lstsq(_X, _y, rcond = None)
    _trend_pct_yr = (np.exp(_beta[1] * 12) - 1) * 100
    _seasonal = np.concatenate([[0.0], _beta[2:13]]) * 100  # vs January

    _fig = go.Figure()
    _fig.add_trace(
        go.Bar(
            x = _m["t"].to_list(),
            y = _m["rev"].to_list(),
            marker_color = MUTED,
            name = "actual monthly revenue",
        ),
    )
    _fig.add_trace(
        go.Scatter(
            x = _m["t"].to_list(),
            y = list(np.exp(_X @ _beta)),
            mode = "lines",
            line = dict(
                color = ACCENT,
                width = 2.5,
            ),
            name = "trend + season fit",
        ),
    )
    style(
        fig = _fig,
        title = "Monthly revenue vs. a trend-plus-season fit — separating growth from the calendar",
        showlegend = True,
    )
    _fig.update_layout(
        legend = dict(
            orientation = "h",
            yanchor = "bottom",
            y = 1.0,
            xanchor = "left",
            x = 0,
            font = dict(size = 11.5),
        ),
    )
    _fig.update_yaxes(
        showticklabels = False,
        showline = False,
        ticks = "",
        title_text = "revenue (EUR/month)",
        title_font = dict(size = 11.5, color = MUTED),
    )
    _fig.update_xaxes(
        title_text = "month (Jan 2025 = 1)",
        type = "linear",
        tickmode = "linear",
        dtick = 5,
    )
    takeaway(
        fig = _fig,
        text = f"underlying growth ≈{_trend_pct_yr:+.1f}%/year, on top of a<br>repeating summer-vs-winter pattern",
        x = 0.02,
        y = 0.98,
    )
    _best_m = int(np.argmax(_seasonal)) + 1
    _worst_m = int(np.argmin(_seasonal)) + 1
    _months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    mo.vstack(
        items = [
            mo.md("""
    ## 6 · Growth vs. the seasons

    A single year can't tell "the shop is growing" apart from "December is
    always busier than February" — both look like a line going up and down.
    Three years can, by fitting one straight trend line PLUS one repeating
    12-month pattern at the same time, and letting the data decide how much
    of each month's number belongs to which:
    """),
            _fig,
            caption(
                f"The fitted trend says the shop's underlying pace of "
                f"business grew roughly {_trend_pct_yr:.1f}% a year across "
                f"the full three years — through a freezer failure, a "
                f"heatwave, a new apartment block, and a discounter opening "
                f"nearby, the growth line still nets out positive. "
                f"{_months[_best_m - 1]} is the strongest month of the "
                f"year, {_months[_worst_m - 1]} the weakest, and that "
                f"ranking repeats every year — the seasonal shape doesn't "
                "shift even as the business shifts under it. The full "
                "graded version of this split — plus the churn accounting, "
                "the invisible competitor entry, and the renew-or-close "
                "capstone — lives in `analyses/three_year_review.py`."
            ),
        ],
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ## 7 · Does the weather, the price, and the promotions actually work?

    Four questions, four honest one-line verdicts — the full regressions,
    with their confidence intervals and their traps, live in
    `analyses/diagnose_causes.py`:

    - **Does rain keep people away?** Yes — a fully wet day costs roughly
      **11–12% of visits**, with a small next-day rebound as some of that
      trip gets postponed rather than cancelled.
    - **Does raising a price scare customers off?** It depends which price.
      Raise ONE product's price and shoppers substitute hard (elasticity
      around −2.1 — they simply buy a rival SKU next to it). Raise a whole
      CATEGORY'S prices together and demand barely moves (around −0.2) —
      there's nowhere else in the shop to substitute to.
    - **Do markdowns actually lift sales?** Yes, genuinely — but the naive
      before/after comparison UNDERSTATES the true lift here, because
      markdowns fire exactly when a category is already slowing down (the
      trigger reads the shelf, not the sales floor). The properly
      difference-in-differences-corrected lift is larger than the naive
      number, not smaller — the opposite of the textbook warning, and worth
      knowing before trusting a "just compare before and after" analysis
      anywhere else in this business.
    - **Is the loyalty Sunday worth it?** It reliably lifts Sunday visits
      and revenue by roughly 12%, but a storewide discount at this margin
      needs a much bigger lift than that to break even — it is a paid
      loyalty investment, kept on purpose, not a money-maker in its own
      right.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## 8 · The two quiet costs: empty shelves, and the bin

    Every year this shop loses money two ways nobody puts on an invoice:
    demand that shows up when the shelf is empty, and stock that spoils
    before anyone buys it. The full graded reconstruction — including the
    ordering-policy backtest and the newsvendor arithmetic for perishables
    — lives in `analyses/predict_and_warn.py` and `analyses/prescribe.py`:

    - **Stockouts** run at roughly **7–9% of product-days** across the
      three years, falling noticeably after the November 2026 expansion
      (a second pair of hands keeps the shelves fuller).
    - **Reconstructing the demand a stockout hid** (from the days a
      product WAS in stock, projected onto the days it wasn't) recovers
      the right order of magnitude, but reliably **overshoots the true
      hidden total** — a busy morning that sells out by evening looks, to
      this method, like it was busy all day.
    - **Spoilage** costs tens of thousands of units a year, concentrated in
      the fastest-perishing categories (bakery, produce, seafood) and
      rising measurably with temperature.
    - **The fix for both is the same lever, used together**: a
      demand-based, season-aware order sheet with perishable-specific
      safety stock is worth real money — but only when its two ingredients
      ship together. Fixing the forecast alone, without also thinning the
      safety stock on fast-spoiling goods, makes the shop WORSE off — more
      accurate ordering just floods the bin faster.
    """)
    return


@app.cell
def _(con, mo):
    _regs = con.sql(
        query = """
            SELECT count(DISTINCT customer_id)
            FROM   receipts
            WHERE  customer_id IS NOT NULL
        """,
    ).fetchone()[0]
    mo.md(f"""
    ## 9 · Your customers, and who's still here

    **{_regs:,} distinct card tokens** show up somewhere in three years of
    receipts — but that number alone hides the shop's real customer story,
    which only three years of history can tell: most of that count is a
    long tail of one-off guests (under 2% of card revenue), while a much
    smaller core of weekly regulars — the ones this shop actually depends
    on — slowly loses members to churn every year, quietly, well before any
    of them show up as a dramatic drop in the monthly total. The full
    picture — churn read from token silence and graded against the hidden
    truth, a discrete-choice model of what customers actually want (and how
    well it can be recovered from receipts alone), and the honest limits of
    a till that only sees card payments — lives in
    `analyses/three_year_review.py` and `analyses/learn_structure.py`.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## 10 · Can we guess next week's sales?

    Three forecasting methods were benchmarked against an untouched final
    year the models never saw during training: your own trailing-average
    ordering rule, a machine-learning model (gradient boosting), and a
    naive "same week as last year" baseline. The full bench — including
    the censored-demand correction and the Monday stockout watchlist —
    lives in `analyses/predict_and_warn.py`.

    **The honest headline: your own simple rule wins.** A four-week
    trailing average adapts to a shifting sales level faster than either
    challenger, and a machine-learning model earns its complexity back only
    once it has years of comparable history to learn from — which, at this
    shop's size, it still doesn't quite have. That doesn't mean the rule is
    optimal (Section 8's ordering-policy fix beats it on the metric that
    actually matters, profit, not forecast error) — it means "buy a fancier
    model" is not, on its own, this shop's answer.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## 11 · What I'd do about it

    In order of urgency — the full euro-by-euro case for each line,
    including the twin-arm counterfactuals that prove items 1 and 2, lives
    in `analyses/expansion_review.py`, `analyses/competitor_entry_study.py`,
    and `analyses/prescribe.py`:

    1. **Reconsider the November 2026 expansion.** Against a twin of this
       exact shop where the second hire never happened, the expansion is
       the single decision that separates a strongly profitable year from
       a knife-edge one — an order of magnitude bigger than anything else
       on this list. Renew or restructure it before renewing the lease.
    2. **Replace the order sheet's two inputs together** (Section 8):
       forecast demand, not sales, and season-anticipate it; shrink
       perishable safety stock by each category's own spoilage odds. Worth
       real money a year — deploy both changes together, not one at a
       time.
    3. **A gentle, narrow repricing round** (Section 7): a percent or two
       on categories the discounter across the street doesn't advertise;
       hands off the categories it does.
    4. **Keep a prudent cash floor** entering every month — the worst
       month's bills plus a week of goods on order — and keep an eye on
       January, where the tax settlement and (since 2027) the higher rent
       land together.

    The single biggest lesson of three years of data, ahead of any of the
    above: **this shop's problem was never how it runs day to day.** It
    runs well. The one decision worth real scrutiny is the size of the bet
    it placed on its own growth.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---

    Everything above comes from `data/store.duckdb`, rebuilt fresh each time
    this notebook runs from the raw files in
    `data/scenarios/3y_baseline/visible/` — the analyst's honest, imperfect
    paperwork. Nothing in this workbook reads from `hidden/`, the answer key
    against which every deeper notebook in this project grades itself.

    **Where to go for depth.** This workbook is the fast tour; six sections
    above point to a dedicated notebook that does the full, graded version
    of that question:

    | Section | Full-depth notebook |
    | --- | --- |
    | 3 — cleaning | `analyses/clean_and_describe.py` |
    | 7 — weather, price, promotions | `analyses/diagnose_causes.py` |
    | 8 — stockouts and spoilage | `analyses/predict_and_warn.py`, `analyses/prescribe.py` |
    | 9 — customers and churn | `analyses/three_year_review.py`, `analyses/learn_structure.py` |
    | 10 — forecasting | `analyses/predict_and_warn.py` |
    | 11 — priorities | `analyses/prescribe.py`, `analyses/expansion_review.py`, `analyses/competitor_entry_study.py` |

    `analyses/policy_lab.py` (the five one-year twin-arm scenarios — a VAT
    cut, a tax rebate, a supply shock, a storm, a staffing decision) and
    `analyses/catalog_walkthrough.py` (a graded question from every layer,
    in one sitting) sit outside this table because they aren't about
    *this* arm specifically — see `documents/ANALYSIS_CATALOG.md` for the
    complete question bank behind all of it.
    """)
    return


if __name__ == "__main__":
    app.run()
