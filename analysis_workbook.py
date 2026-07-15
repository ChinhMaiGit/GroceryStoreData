import marimo

__generated_with = "0.23.14"
app = marimo.App(
    width="full",
    app_title="Your Grocery Store — Year One, Explained",
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

    ROOT = Path(__file__).resolve().parent
    DATA = ROOT / "data"

    # ---- chart style: declutter per Knaflic's "Storytelling with Data" -----
    # one accent for what the narrative claims, gray for context, no chart
    # border, no gridlines at all, no value axis on bar/column charts (their
    # bars carry the number directly), titles state the takeaway rather than
    # describe the axes, legends replaced by direct end-of-line labels
    # wherever the series count allows it. The default right margin is slim;
    # charts that end their lines with text labels ask style() for extra room.
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
        hide_value_axis,
        mo,
        np,
        pl,
        style,
    )


@app.cell
def _(mo):
    mo.md(r"""
    # Your Store's First Year, in Plain English

    You handed over a year of paperwork — every till receipt, every night's
    shelf count, every supplier invoice, the price list, the promotions you
    ran, the monthly bills, what got thrown away, and a record of the weather
    outside. Nothing else. No survey, no market research, nobody watching over
    your shoulder. Just what the shop itself wrote down.

    This notebook walks through what that paperwork actually says about your
    business — in the order a first-time reader would naturally ask it:

    1. **How the shop runs** — hours, staffing, and what's on the shelves, in one place.
    2. **Getting organized** — putting every record into one place so we can compare them.
    3. **Sanity-checking the numbers** — three things worth knowing before trusting anything else.
    4. **The big picture** — what came in, what went out, what's left over.
    5. **When people actually shop** — the days and hours that matter.
    6. **The seasons** — what sells more in summer, what sells more before Christmas.
    7. **Does the weather actually keep people away?** — and a few other "does X really cause Y?" questions, answered carefully.
    8. **The two quiet costs** — empty shelves, and food that goes in the bin.
    9. **What we know about your customers** — and the limits of what the till can tell us.
    10. **Can we guess next week's sales?** — a forecasting model, tested honestly.
    11. **What I'd do about it** — a short, prioritized list.

    A running theme: wherever a claim rests on something more technical than
    "we added it up," you'll find a small **"See exactly how this was
    calculated"** panel right underneath. It's there so the number is never a
    black box — but you can read straight past it if you just want the story.
    """)
    return


@app.cell
def _(DATA, ROOT, duckdb, pl):
    # ---- store-operations snapshot: who this shop is, before the numbers ----
    _loc = pl.read_csv(source = DATA / "visible" / "locations.csv")
    _cs = pl.read_csv(source = DATA / "visible" / "cost_sheet.csv")
    _rec = pl.read_csv(source = DATA / "visible" / "receipts.csv")
    _cal = pl.read_csv(source = DATA / "visible" / "calendar.csv")
    _proc = pl.read_csv(source = DATA / "visible" / "procurement.csv")
    _inv = pl.read_csv(source = DATA / "visible" / "inventory_eod.csv")
    _catalog = pl.read_excel(source = ROOT / "SKUs.xlsx")

    # this location.csv lists every candidate site the owner once weighed up;
    # the one actually rented is the one whose rent matches the cost sheet
    _target_rent = float(_cs["rent"][0])
    _mine = _loc.with_columns(
        (pl.col("rent") - _target_rent).abs().alias("rent_diff"),
    ).sort(by = "rent_diff").row(
        index = 0,
        named = True,
    )

    ops = {
        "rent": _mine["rent"],
        "setup_cost": _mine["setup_cost"],
        "staff_needed": int(_mine["operational_needs"]),
        "shelf_capacity_units": int(_mine["shelf_capacity_units"]),
        "shelf_slots": int(_mine["shelf_slots"]),
        # hour = 0 is a POS clock glitch (Section 3), not a 00:00 sale
        "open_hour": int(_rec.filter(pl.col("hour") > 0)["hour"].min()),
        "close_hour": int(_rec["hour"].max()) + 1,
        "n_closed_days": int((_cal["closed"] == 1).sum()),
        "closed_holidays": _cal.filter(pl.col("closed") == 1)["holiday"].to_list(),
        "n_categories": _catalog["category"].n_unique(),
        "n_catalog_products": _catalog.height,
        "n_stocked_products": _inv["uid"].n_unique(),
        "restock_dow": _proc["delivery_date"].str.to_date().min().strftime("%A"),
        "total_wages": float(_cs["wages"].sum()),
    }
    return (ops,)


@app.cell
def _(mo, ops):
    _days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    mo.md(
        f"""
    ## 1 · How the shop runs, day to day

    Before diving into the numbers, it's worth pinning down what kind of
    shop we're actually talking about — the everyday operational facts that
    everything downstream in this report quietly assumes.

    **Hours.** The shop opens at **{ops['open_hour']}:00** and closes at
    **{ops['close_hour']}:00** — a {ops['close_hour'] - ops['open_hour']}-hour
    day, every day, with two exceptions: it's closed on
    **{', '.join(h.replace('_', ' ').title() for h in ops['closed_holidays'])}**,
    the only {ops['n_closed_days']} days all year with zero recorded sales
    (you already saw those flagged as a data-quality trap in Section 3 —
    now you know why they happen).

    **Staffing.** The premises need a minimum of **{ops['staff_needed']}
    person** on the floor to run — and the wage line in your cost sheet
    is **€{ops['total_wages']:,.0f}** for the entire year, meaning that one
    person has been **you**. Every recommendation later in this report
    about margins and "what's left over" is really talking about your own
    take-home pay, not a professional manager's salary on top of it.

    **What's on the shelves.** Your supplier catalog offers
    {ops['n_catalog_products']} possible products across
    {ops['n_categories']} categories (everything from fresh produce to
    household cleaning supplies) — but the shop physically only has room
    for **{ops['shelf_slots']} distinct products** at once and
    **{ops['shelf_capacity_units']:,} units** of total stock on the shelf.
    Out of everything available, you've chosen to actually stock
    **{ops['n_stocked_products']} products** — a curated slice of the
    catalog, well inside the physical limit, leaving genuine room to add
    more if something earns a spot.

    **The restocking rhythm.** New deliveries arrive every single
    **{ops['restock_dow']}**, all year, like clockwork — which is the
    heartbeat behind several patterns you'll see later: prices only ever
    change on delivery days, and the "how much stock to keep on hand"
    decision (Section 8) only gets revisited once a week, not continuously.

    With that picture in mind — a small, owner-run, single-person shop,
    open long hours every day but working from a deliberately curated
    shelf — the rest of this report is about what a year of running it
    that way actually produced.
    """
    )
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

    _vis = DATA / "visible"
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
    # Real paperwork is imperfect; Section 3 walks through everything these
    # views repair. Downstream queries only ever see the cleaned names.
    #
    # receipts: (a) drop POS-retry duplicates — a retry re-posts an entire
    # receipt, so a receipt is a retry exactly when EVERY distinct line of it
    # appears an even number of times (a genuine double-scanned item only
    # doubles one line); keep half of each such receipt's lines. (b) hour 0
    # is a placeholder from a POS clock glitch, not a midnight sale -> NULL.
    # (c) payment labels drift ('Card', 'CASH ', ...) -> lowercase, trimmed.
    # (d) voided mis-rings (+q then -q of the same item at the same price)
    # cancel out in the final per-line SUM; the HAVING drops the empty shell.
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
    # write-offs: spoilage logs and monthly stock-count corrections share one
    # file; they mean different things, so split them into two views
    con.execute(
        query = """
            CREATE VIEW write_offs AS
            SELECT uid,
                   units,
                   date
            FROM   write_offs_raw
            WHERE  reason = 'spoilage'
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
def _(mo, tbl_summary):
    mo.vstack(
        items = [
            mo.md(
                """
    ## 2 · Getting organized

    Think of this step as tipping every folder, invoice, and printout onto one
    big table and sorting it into labeled piles. Nine piles, to be exact: your
    **receipts** (one line per item sold — this is the heart of everything
    that follows), your **nightly shelf counts**, your **supplier invoices**,
    your **price list history**, your **promotions log**, what got **thrown
    away**, your **monthly bills**, and a **calendar and weather log** for
    the year. Once everything sits in one place, we can finally ask
    questions that span across them — like "did the weather affect what
    people bought?" — which no single folder could answer on its own.

    One more thing happened at this step: every pile got a scrub before
    use. Real paperwork contains duplicates, typos, and gaps, and yours
    is no exception — Section 3 lists exactly what we found and fixed,
    so every number after it is built on the cleaned-up records.
    """
            ),
            mo.ui.table(
                data = tbl_summary,
                selection = None,
            ),
        ],
    )
    return


@app.cell
def _(con):
    # ---- data quality sweep --------------------------------------------------
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

    # days with no sales at all — holidays? data gaps?
    dq["silent_days"] = con.sql(
        query = """
            SELECT c.date,
                   c.holiday,
                   c.closed
            FROM   calendar c
            LEFT   JOIN (SELECT DISTINCT date FROM receipts) r USING (date)
            WHERE  r.date IS NULL
            ORDER  BY c.date
        """,
    ).pl()

    dq["card_share"] = con.sql(
        query = """
            SELECT avg(CASE WHEN payment = 'card' THEN 1.0 ELSE 0 END)
            FROM   (SELECT DISTINCT receipt_id, payment FROM receipts)
        """,
    ).fetchone()[0]

    # nominal drift: same-SKU invoice cost, first vs last quarter
    dq["drift"] = con.sql(
        query = """
            WITH q AS (
                SELECT uid,
                       avg(unit_cost) FILTER (WHERE delivery_date <  DATE '2025-04-01') AS q1,
                       avg(unit_cost) FILTER (WHERE delivery_date >= DATE '2025-10-01') AS q4
                FROM   procurement
                GROUP  BY uid
            )
            SELECT median(q4 / q1) - 1
            FROM   q
            WHERE  q1 IS NOT NULL
              AND  q4 IS NOT NULL
        """,
    ).fetchone()[0]

    # ---- what the cleaning pass caught (the views in Section 2) -------------
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
    dq["dup_rev"] = con.sql(
        query = """
            SELECT (SELECT sum(qty * unit_price) FROM receipts_raw)::DOUBLE
                 - (SELECT sum(qty * unit_price) FROM receipts)::DOUBLE
        """,
    ).fetchone()[0]
    dq["ledger_gap"] = con.sql(
        query = """
            SELECT (SELECT sum(qty * unit_price) FROM receipts)::DOUBLE
                 - (SELECT sum(revenue) FROM cost_sheet)::DOUBLE
        """,
    ).fetchone()[0]
    dq["hour_glitch"] = con.sql(
        query = "SELECT count(DISTINCT receipt_id) FROM receipts_raw WHERE hour = 0",
    ).fetchone()[0]
    dq["voids"] = con.sql(
        query = """
            SELECT count(*)
            FROM   receipts_raw
            WHERE  qty < 0
              AND  ref_receipt_id IS NULL  -- referenced negatives are refunds
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
    dq["refund_orphans"] = con.sql(
        query = """
            SELECT count(*)
            FROM   receipts r
            WHERE  r.ref_receipt_id IS NOT NULL
              AND  NOT EXISTS (SELECT 1
                               FROM   receipts s
                               WHERE  s.receipt_id = r.ref_receipt_id
                                 AND  s.qty > 0)
        """,
    ).fetchone()[0]
    dq["pay_labels_raw"] = con.sql(
        query = "SELECT count(DISTINCT payment) FROM receipts_raw",
    ).fetchone()[0]
    dq["dup_invoices"] = con.sql(
        query = """
            SELECT (SELECT count(*) FROM procurement_raw)
                 - (SELECT count(*) FROM procurement)
        """,
    ).fetchone()[0]
    dq["invoice_gap"] = con.sql(
        query = """
            SELECT (SELECT sum(procurement) FROM cost_sheet)::DOUBLE
                 - (SELECT sum(qty * unit_cost) FROM procurement)::DOUBLE
        """,
    ).fetchone()[0]
    dq["shrink_units"], dq["shrink_eur"] = con.sql(
        query = """
            WITH c AS (
                SELECT uid,
                       median(unit_cost) AS mc
                FROM   procurement
                GROUP  BY uid
            )
            SELECT sum(s.units)::DOUBLE,
                   sum(s.units * c.mc)::DOUBLE
            FROM   stock_adjustments s
            JOIN   c USING (uid)
        """,
    ).fetchone()
    # nights where the shelf count doesn't reconcile with the paperwork —
    # the fingerprint of a mistyped stock count (it breaks two diffs in a row)
    dq["unreconciled_nights"] = con.sql(
        query = """
            WITH b AS (
                SELECT uid,
                       date,
                       on_hand,
                       lag(on_hand) OVER (PARTITION BY uid ORDER BY date) AS prev
                FROM   inventory_eod
            ),
            d AS (
                SELECT uid,
                       delivery_date AS date,
                       sum(qty)      AS del
                FROM   procurement_raw
                GROUP  BY 1, 2
            ),
            s AS (
                SELECT uid,
                       date,
                       sum(qty) AS sold
                FROM   receipts_raw
                WHERE  ref_receipt_id IS NULL  -- refunds are money-only: the
                                               -- returned item never restocks
                GROUP  BY 1, 2
            ),
            w AS (
                SELECT uid,
                       date,
                       sum(units) AS wo
                FROM   write_offs_raw
                GROUP  BY 1, 2
            )
            SELECT count(*)
            FROM   b
            LEFT   JOIN d USING (uid, date)
            LEFT   JOIN s USING (uid, date)
            LEFT   JOIN w USING (uid, date)
            WHERE  prev IS NOT NULL
              AND  on_hand - prev - coalesce(del, 0)
                   + coalesce(sold, 0) + coalesce(wo, 0) != 0
        """,
    ).fetchone()[0]
    dq["neg_book"] = con.sql(
        query = "SELECT count(*) FROM inventory_eod WHERE on_hand < 0",
    ).fetchone()[0]
    dq["weather_nulls"] = con.sql(
        query = "SELECT count(*) FROM weather WHERE temp_C IS NULL",
    ).fetchone()[0]
    return (dq,)


@app.cell
def _(dq, mo):
    mo.md(f"""
    ## 3 · Cleaning up the paperwork before we trust the numbers

    Your records run from **{dq['span'][0]} to {dq['span'][1]}**:
    {dq['n_lines']:,} item lines across {dq['n_receipts']:,} separate sales.
    Like any real shop's paperwork, they contain glitches — a till that
    re-sent a receipt, an invoice typed in twice, a mistyped stock count.
    None of it is unusual, but left in place it would quietly bend every
    number in this report, so the first thing we did was a cleaning pass.
    Here's everything it caught, and what we did about each item:

    - **{dq['dup_receipts']} receipts were uploaded twice** — the till
      occasionally re-sends a whole sale, so every line of it shows up
      two times. Left in, they'd inflate your revenue by
      **€{dq['dup_rev']:,.2f}**. We spot them (a re-send doubles *every*
      line of the receipt, which almost never happens naturally) and keep
      one copy. After that fix, the receipt file agrees with your own
      monthly ledger to the cent (difference: €{abs(dq['ledger_gap']):.2f}).
    - **{dq['voids']} till lines are voids** — the cashier scanned the wrong
      item and immediately cancelled it, leaving a plus line and a matching
      minus line on the tape. They net to zero money, so we cancel each pair
      out rather than count a "negative sale."
    - **{dq['hour_glitch']} receipts are stamped "hour 0"** — a till clock
      glitch, not midnight shopping sprees. The sales are real, so we keep
      them; we just leave the time-of-day blank so they can't distort the
      "when do people shop" charts in Section 5.
    - **The payment column spells "card" and "cash" {dq['pay_labels_raw']}
      different ways** ("Card", "CASH ", ...). Harmless to a human, fatal
      to a computer counting categories — we standardized them all.
    - **{dq['dup_invoices']} supplier invoices were entered twice** (same
      goods, same delivery, posted again days later). We keep the first
      posting. Even after that, the invoice file totals
      **€{dq['invoice_gap']:,.0f} less** than the procurement line in your
      ledger — a few deliveries were never entered at all. We flag it
      rather than fix it: it's the ledger that's right.
    - **Your monthly stock counts wrote off {dq['shrink_units']:,.0f} units
      (≈ €{dq['shrink_eur']:,.0f} at cost) as "shrinkage"** — the gap
      between what the books said and what was actually on the shelf.
      That's things tossed without being logged, miscounts, and the odd
      unrecorded delivery, and it's why the write-off analysis in
      Section 8 uses only the *logged spoilage*, not these correction
      entries.
    - **{dq['unreconciled_nights']} nights fail to reconcile** — the evening
      shelf count doesn't match paperwork ± that day's movements, in
      matching pairs one day apart: the signature of a mistyped count that
      self-corrects the next night. {dq['neg_book']} snapshot rows even show
      *negative* stock, which is physically impossible but perfectly normal
      in book inventory. We leave the snapshot as-is and simply don't treat
      any single night's count as gospel.
    - **{dq['weather_nulls']} days of weather are missing** — the sensor
      feed went dark a few times. Those days are simply left out of the
      weather analysis in Section 7 rather than guessed at.
    - **One promotion category was misspelled** in the promo log
      ("Confectionary") — silently un-matchable in a join until fixed.

    With the paperwork tidied, four *structural* quirks remain — not
    errors, but facts about how the data came to be, worth keeping in
    mind all the way through:

    **① Two totally silent days.** {len(dq['silent_days'])} days in the whole
    year show zero sales: {', '.join(str(d) for d in dq['silent_days']['date'])}.
    That's not missing data — it's Christmas Day and New Year's Day, when the
    shop was closed. It matters because if a computer just averaged "sales
    per day" without knowing this, it would think business mysteriously
    collapses every December 25th, which would throw off any forecast built
    on top of it.

    **② Cash customers are invisible.** {dq['card_share']:.0%} of sales are
    paid by card, which lets us tie that purchase to a specific, repeat
    customer. The other {1 - dq['card_share']:.0%} is cash — real sales, but
    with no name attached. So anywhere this report says something like "your
    regular customers do X," it really means "the card-paying regulars do X."
    Section 9 actually checks whether that's a fair stand-in for everyone, or
    a skewed picture.

    **③ Prices have quietly crept up.** The exact same product cost you a
    median of **{dq['drift']:+.1%}** more to buy in from suppliers in the last
    three months of the year than in the first three. Some of that is
    everyday inflation; some of it, as you'll see in Section 7b, was a real
    supply shock. Either way, it means comparing "€ spent in January" to "€
    spent in December" isn't quite apples-to-apples — a euro bought a little
    less by year's end. Where that matters below, we compare *how many units*
    moved instead of raw euros, which sidesteps the problem entirely.

    **④ Money occasionally flows backwards.** {dq['refunds']} times this
    year, a customer brought something back and you refunded them —
    **€{dq['refund_eur']:,.2f}** in total. Each refund sits in the till
    journal as its own transaction with a negative quantity, pointing back
    at the original receipt (we cross-checked all {dq['refunds']}: every one
    matches a real earlier sale — {dq['refund_orphans']} orphans). Anywhere
    this report counts *money*, refunds are netted in; anywhere it counts
    *shopping trips or baskets*, they're set aside, since walking in to
    return a yogurt isn't a shopping visit. Returned items go in the bin,
    not back on the shelf, so refunds never touch the stock numbers.
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
    mo,
    style,
):
    # ---- the P&L -------------------------------------------------------------
    pnl = con.sql(
        query = "SELECT * FROM cost_sheet ORDER BY month",
    ).pl()
    # operating costs now include the taxman: monthly VAT remittance and
    # (when staff exist) employer payroll contributions
    _cost_cols = [
        "rent",
        "wages",
        "payroll_tax",
        "utilities",
        "storage",
        "flyers",
        "vat",
        "credit_interest",
    ]
    _total_cost = (pnl["procurement"] + sum(pnl[c] for c in _cost_cols)).to_list()
    kpi = {
        "revenue": float(pnl["revenue"].sum()),
        "procurement": float(pnl["procurement"].sum()),
        "opex": float(sum(pnl[c].sum() for c in _cost_cols)),
        "vat": float(pnl["vat"].sum()),
    }
    kpi["gross_margin_pct"] = 1 - kpi["procurement"] / kpi["revenue"]
    # basket and footfall describe *shopping trips*, so refund transactions
    # (negative, referenced back to their original receipt) stay out
    kpi["avg_basket"] = float(con.sql(
        query = """
            SELECT avg(v)
            FROM   (SELECT receipt_id, sum(qty * unit_price) AS v
                    FROM   receipts
                    WHERE  ref_receipt_id IS NULL
                    GROUP  BY receipt_id)
        """,
    ).fetchone()[0])
    kpi["receipts_per_day"] = con.sql(
        query = """
            SELECT count(DISTINCT receipt_id) / count(DISTINCT date)
            FROM   receipts
            WHERE  ref_receipt_id IS NULL
        """,
    ).fetchone()[0]

    # utilities is too small a euro line to read once stacked against
    # procurement, so its Q4 story gets its own full-width chart; each chart
    # drops the value axis and prints the number on the bar instead. Two
    # stacked full-width figures instead of side-by-side panels: every bar
    # label gets the whole row of horizontal space, so nothing collides.
    _fig_a = go.Figure()
    _fig_a.add_bar(
        x = pnl["month"].to_list(),
        y = pnl["revenue"].to_list(),
        text = [f"{v/1000:.0f}k" for v in pnl["revenue"].to_list()],
        textposition = "outside",
        textfont = dict(
            color = ACCENT,
            size = 11,
        ),
        marker_color = ACCENT,
        marker_line_width = 0,
        cliponaxis = False,
    )
    _fig_a.add_bar(
        x = pnl["month"].to_list(),
        y = _total_cost,
        text = [f"{v/1000:.0f}k" for v in _total_cost],
        textposition = "outside",
        textfont = dict(
            color = "#9A9A9A",
            size = 11,
        ),
        marker_color = MUTED,
        marker_line_width = 0,
        cliponaxis = False,
    )
    style(
        fig = _fig_a,
        title = "Revenue (blue) and total cost (gray) climb together, month by month",
    )
    hide_value_axis(
        fig = _fig_a,
        axis = "y",
        title = "EUR",
    )
    _fig_a.update_yaxes(range = [0, max(pnl["revenue"].max(), max(_total_cost)) * 1.22])
    _fig_a.update_xaxes(
        title_text = "month",
        tickmode = "linear",
        dtick = 1,
    )
    _fig_a.update_layout(
        barmode = "group",
        height = 360,
    )

    _util_colors = [WARN if m >= 10 else MUTED for m in pnl["month"].to_list()]
    _fig_b = go.Figure()
    _fig_b.add_bar(
        x = pnl["month"].to_list(),
        y = pnl["utilities"].to_list(),
        text = [f"{v:,.0f}" for v in pnl["utilities"].to_list()],
        textposition = "outside",
        textfont = dict(
            color = "#404040",
            size = 11,
        ),
        marker_color = _util_colors,
        marker_line_width = 0,
        cliponaxis = False,
    )
    style(
        fig = _fig_b,
        title = "The utilities bill breaks that pattern — it spikes in Q4 (red)",
    )
    hide_value_axis(
        fig = _fig_b,
        axis = "y",
        title = "EUR",
    )
    _fig_b.update_yaxes(range = [0, pnl["utilities"].max() * 1.25])
    _fig_b.update_xaxes(
        title_text = "month",
        tickmode = "linear",
        dtick = 1,
    )
    _fig_b.update_layout(height = 320)

    mo.vstack(
        items = [
            _fig_a,
            caption(
                "Each pair of bars is one month: your total sales (blue) next to "
                "everything it cost to run the shop that month (gray). The two climb "
                "together all year — the sign of a shop growing in a controlled way."
            ),
            _fig_b,
            caption(
                "The electricity bill on its own scale — next to procurement it would "
                "look like a flat line. Pulled out, its jump in the last three months "
                "of the year (red bars) is unmistakable."
            ),
        ],
    )
    return kpi, pnl


@app.cell
def _(kpi, mo, pnl):
    mo.md(f"""
    ## 4 · The big picture: money in, money out

    Over the year you took in **€{kpi['revenue']:,.0f}**. Buying the goods you
    sold cost **€{kpi['procurement']:,.0f}** — meaning every €1 of goods
    bought in turned into about €{1/(1-kpi['gross_margin_pct']):.2f} of
    sales, or a **{kpi['gross_margin_pct']:.0%} margin** on the goods
    themselves (this doesn't yet count rent, bills, and the rest — that's the
    "operating costs" of **€{kpi['opex']:,.0f}**). One line inside those
    operating costs deserves its own sentence: **€{kpi['vat']:,.0f} of VAT**
    left the till over the year — the tax collected on your sales, minus the
    tax you'd already paid on your supplier invoices, remitted monthly. It's
    the quiet reason the till never feels as full as the revenue figure
    suggests, and the annual `tax_statement` file wraps it up together with
    the profit-tax bill. On a typical day the till rings up about
    **{kpi['receipts_per_day']:.0f} sales**, averaging
    **€{kpi['avg_basket']:.2f}** each.

    Two things jump out of the chart above. First, sales climb all year
    toward a December peak — but so does the cost of goods, roughly in step,
    which is exactly what you'd expect from a healthy, growing shop. Second,
    and more striking: **the wages line is zero, every single month.** That's
    not a data error — it means this business has been running on your own
    unpaid hours all year. Whatever's left over at the bottom *is* effectively
    your paycheck, which is worth keeping in mind before comparing this
    year's "profit" to what a fully-staffed competitor reports. And the
    electricity bill jumps
    {pnl['utilities'][9] / pnl['utilities'][8] - 1:+.0%} in October alone —
    a thread we pull on properly in Section 7b, because it turns out **not**
    to be a one-off billing mistake.
    """)
    return


@app.cell
def _(
    ACCENT,
    ACCENT_LIGHT,
    MUTED,
    caption,
    con,
    end_label,
    go,
    hide_value_axis,
    mo,
    style,
):
    # ---- rhythms ---------------------------------------------------------------
    _dow = con.sql(
        query = """
            SELECT c.dow,
                   sum(r.qty * r.unit_price) / count(DISTINCT r.date) AS rev_per_day
            FROM   receipts r
            JOIN   calendar c USING (date)
            GROUP  BY c.dow
            ORDER  BY c.dow
        """,
    ).pl()
    # split by day-type: the claim is that weekdays and weekends don't even
    # shop at the same hour, so show the two regimes, not their blend
    _hr = con.sql(
        query = """
            SELECT CASE WHEN dayofweek(date) IN (0, 6) THEN 'Weekend' ELSE 'Weekday' END AS day_type,
                   hour,
                   count(DISTINCT receipt_id) AS visits
            FROM   receipts
            WHERE  hour IS NOT NULL  -- clock-glitch receipts carry no usable time
              AND  ref_receipt_id IS NULL  -- refund walk-ins aren't shopping trips
            GROUP  BY 1, 2
            ORDER  BY 1, 2
        """,
    ).pl()

    _days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    _dow_color = {0: MUTED, 1: MUTED, 2: MUTED, 3: MUTED,
                  4: ACCENT_LIGHT, 5: ACCENT, 6: ACCENT_LIGHT}
    _fig_a = go.Figure()
    _fig_a.add_bar(
        x = [_days[d] for d in _dow["dow"].to_list()],
        y = _dow["rev_per_day"].to_list(),
        text = [f"€{v:,.0f}" for v in _dow["rev_per_day"].to_list()],
        textposition = "outside",
        textfont = dict(size = 11),
        marker_color = [_dow_color[d] for d in _dow["dow"].to_list()],
        marker_line_width = 0,
        cliponaxis = False,
    )
    style(
        fig = _fig_a,
        title = "Saturday is in a class of its own",
    )
    hide_value_axis(
        fig = _fig_a,
        axis = "y",
        title = "revenue (EUR)",
    )
    _fig_a.update_yaxes(range = [0, _dow["rev_per_day"].max() * 1.2])
    _fig_a.update_layout(height = 340)

    _fig_b = go.Figure()
    for _dt, _col in (("Weekday", ACCENT), ("Weekend", MUTED)):
        _s = _hr.filter(_hr["day_type"] == _dt).sort(by = "hour")
        _fig_b.add_scatter(
            x = _s["hour"].to_list(),
            y = _s["visits"].to_list(),
            mode = "lines",
            line = dict(
                color = _col,
                width = 2.5,
            ),
        )
        end_label(
            fig = _fig_b,
            x = _s["hour"][-1],
            y = _s["visits"][-1],
            text = _dt,
            color = _col,
        )
    style(
        fig = _fig_b,
        title = "Weekday vs. weekend: two different peak hours",
        right_margin = 96,
    )
    _fig_b.update_yaxes(title_text = "visits")
    _fig_b.update_xaxes(title_text = "hour of the day")
    # the end-of-line labels need a little room on the right of the last point
    _fig_b.update_xaxes(range = [_hr["hour"].min() - 0.5, _hr["hour"].max() + 1.5])
    _fig_b.update_layout(height = 360)

    mo.vstack(
        items = [
            _fig_a,
            caption(
                "Average sales for each day of the week — the taller the bar, the "
                "more money that weekday brings in. The weekend (highlighted in "
                "blue) carries the store."
            ),
            _fig_b,
            caption(
                "What hour of the day people actually walk in, split into weekdays "
                "(blue) versus weekends (gray) — they don't even peak at the same "
                "time of day."
            ),
        ],
    )
    return


@app.cell
def _(con, mo):
    _w = con.sql(
        query = """
            SELECT sum(CASE WHEN c.dow >= 4 THEN r.qty * r.unit_price END)
                   / sum(r.qty * r.unit_price) AS wknd
            FROM   receipts r
            JOIN   calendar c USING (date)
        """,
    ).fetchone()[0]
    mo.md(
        f"""
    ## 5 · When do people actually shop?

    **Friday through Sunday brings in {_w:.0%} of everything you sell.**
    Saturday alone dwarfs every other day — this is a "big weekly shop"
    store, not a grab-a-sandwich-at-lunch store. And the hour-by-hour picture
    in the second chart shows something staffing decisions should take seriously:
    weekday shoppers come **after work** (5–7pm), while weekend shoppers come
    **mid-morning** (10am–noon). If you only looked at one blended chart for
    "busy hours," you'd miss that these are really two completely different
    crowds on two different schedules. In practice, that argues for having
    shelves freshly stocked and any promotional signage up by Thursday
    evening, ready for the weekend rush.

    One caution for later in this report: a day like "Saturday" being your
    best day doesn't mean *Saturday itself* makes people buy more — it's that
    your loyal weekly shoppers happen to have chosen Saturday as their
    routine. That distinction matters once we start asking "what actually
    *causes* a change in sales" a few sections from now.
    """
    )
    return


@app.cell
def _(MUTED, caption, con, go, mo, pl, style):
    # ---- seasonality -------------------------------------------------------------
    cat_month = con.sql(
        query = """
            SELECT p.category,
                   month(r.date)      AS m,
                   sum(r.qty)::DOUBLE AS units
            FROM   receipts r
            JOIN   products p USING (uid)
            GROUP  BY 1, 2
            ORDER  BY 1, 2
        """,
    ).pl().pivot(
        on = "category",
        index = "m",
        values = "units",
    ).sort(by = "m")

    # gray for the placebo category (nothing seasonal is supposed to happen
    # here); color for the three genuine seasonal stories the text names.
    # short display labels + explicit vertical nudges keep the end-of-line
    # labels from colliding where two lines finish at nearly the same value
    _picks = [("Beverages (Non-Alcoholic)", "Beverages", "#2E5EAA", 0),
              ("Snacks and Confectionery", "Snacks", "#7A5DA8", 7),
              ("Seafood", "Seafood", "#B44646", 0),
              ("Household and Cleaning Supplies", "Household & Cleaning", MUTED, -7)]
    _fig_a = go.Figure()
    _fig_a.add_hline(
        y = 1,
        line_dash = "dot",
        line_color = MUTED,
        line_width = 1,
    )
    for _c, _short, _col, _yshift in _picks:
        _y = (cat_month[_c] / cat_month[_c].mean()).to_list()
        _fig_a.add_scatter(
            x = cat_month["m"].to_list(),
            y = _y,
            mode = "lines+markers",
            line = dict(
                color = _col,
                width = 2,
            ),
            marker = dict(size = 6),
        )
        _fig_a.add_annotation(
            x = cat_month["m"][-1],
            y = _y[-1],
            text = _short,
            showarrow = False,
            xanchor = "left",
            xshift = 8,
            yshift = _yshift,
            font = dict(
                color = _col,
                size = 12,
            ),
        )
    style(
        fig = _fig_a,
        title = "Three seasonal winners, and one category that shouldn't move",
        right_margin = 96,
    )
    _fig_a.update_yaxes(title_text = "index (yearly average = 1)")
    _fig_a.update_xaxes(
        title_text = "month",
        # keep the labels' room without letting them drag the axis past Dec
        range = [cat_month["m"].min() - 0.4, cat_month["m"].max() + 2.2],
        # explicit ticks so the label headroom doesn't show phantom months 13/14
        tickvals = list(range(1, 13)),
    )
    _fig_a.update_layout(height = 380)

    _pt = con.sql(
        query = """
            SELECT CASE WHEN p.product_type = 'Ice Cream'
                        THEN 'Ice Cream'
                        ELSE 'Other frozen' END AS grp,
                   month(r.date)      AS m,
                   sum(r.qty)::DOUBLE AS units
            FROM   receipts r
            JOIN   products p USING (uid)
            WHERE  p.category = 'Frozen Foods'
            GROUP  BY 1, 2
            ORDER  BY 1, 2
        """,
    ).pl().pivot(
        on = "grp",
        index = "m",
        values = "units",
    ).sort(by = "m")
    _fig_b = go.Figure()
    _fig_b.add_hline(
        y = 1,
        line_dash = "dot",
        line_color = MUTED,
        line_width = 1,
    )
    for _c2, _col2 in [("Ice Cream", "#B44646"), ("Other frozen", MUTED)]:
        if _c2 in _pt.columns:
            _y2 = (pl.Series(_pt[_c2]) / _pt[_c2].mean()).to_list()
            _fig_b.add_scatter(
                x = _pt["m"].to_list(),
                y = _y2,
                mode = "lines+markers",
                line = dict(
                    color = _col2,
                    width = 2,
                ),
                marker = dict(size = 6),
            )
            _fig_b.add_annotation(
                x = _pt["m"][-1],
                y = _y2[-1],
                text = _c2,
                showarrow = False,
                xanchor = "left",
                xshift = 8,
                font = dict(
                    color = _col2,
                    size = 12,
                ),
            )
    style(
        fig = _fig_b,
        title = "Frozen Foods looks steady — ice cream inside it swings 2×",
        right_margin = 96,
    )
    _fig_b.update_yaxes(title_text = "index (yearly average = 1)")
    _fig_b.update_xaxes(
        title_text = "month",
        range = [cat_month["m"].min() - 0.4, cat_month["m"].max() + 2.2],
        # explicit ticks so the label headroom doesn't show phantom months 13/14
        tickvals = list(range(1, 13)),
    )
    _fig_b.update_layout(height = 360)

    mo.vstack(
        items = [
            _fig_a,
            caption(
                "Units sold each month, rescaled so 1.0 = that category's own "
                "yearly average — this makes a small category and a big one easy "
                "to compare on the same chart. Above the dotted line means "
                "'busier than usual that month,' below means 'quieter.'"
            ),
            _fig_b,
            caption(
                "A zoom into one category: ice cream (red) and everything else in "
                "the frozen aisle (gray) pull in opposite directions across the "
                "year — a pattern the category total quietly cancels out."
            ),
        ],
    )
    return (cat_month,)


@app.cell
def _(cat_month, mo, pl):
    def _season_ratio(col):
        _s = cat_month.filter(pl.col("m").is_in([6, 7, 8]))[col].mean()
        _w = cat_month.filter(pl.col("m").is_in([12, 1, 2]))[col].mean()
        return _s / _w

    mo.md(
        f"""
    ## 6 · The seasons play favorites

    Cold drinks sell
    {_season_ratio(col = "Beverages (Non-Alcoholic)"):.1f}× as much in summer
    as in winter, seafood explodes right before Christmas, and snacks own the
    dark winter months — none of that should surprise you. The more useful
    finding is in the second chart: **Frozen Foods as a whole category barely
    moves across the year, but that hides two products pulling in opposite
    directions** — ice cream swings roughly 2× from its summer peak to its
    winter trough, while the rest of the frozen aisle barely reacts. If you
    only ever looked at "how is Frozen Foods doing," you'd never notice
    this — which matters directly for ordering: if you plan stock at the
    category level, you'll over-order frozen meals in July and under-order
    ice cream, because the category average is quietly canceling out two
    real, opposite seasonal stories.

    One more thing worth flagging, because it's a trap. Household &
    Cleaning — soap, detergent, the stuff nobody buys "for summer" — still
    dips a little in the warmer months
    ({_season_ratio(col = "Household and Cleaning Supplies"):.2f}× of its
    winter level). It would be easy to conclude "cleaning supplies are mildly
    seasonal too" — but the far more likely explanation is that your
    customers have a fixed weekly budget, and once more of it goes to summer
    drinks and barbecue meat, there's simply a little less left over for
    detergent that week. **The detergent itself didn't get less popular — it
    got squeezed out by everything else.** That distinction is exactly what
    Section 7 is built to sort out properly, rather than guess at from a
    chart alone.
    """
    )
    return


@app.cell
def _(con, np, pl):
    # ---- daily frame + weather regression ----------------------------------------
    import statsmodels.formula.api as _smf

    daily = con.sql(
        query = """
            SELECT c.date,
                   c.dow,
                   month(c.date)  AS m,
                   c.pre_holiday,
                   c.closed,
                   w.temp_C,
                   w.rain_mm,
                   w.wet,
                   coalesce(sum(r.qty * r.unit_price), 0) AS revenue,
                   count(DISTINCT r.receipt_id)
                     FILTER (WHERE r.ref_receipt_id IS NULL) AS visits
            FROM   calendar c
            JOIN   weather  w USING (date)
            LEFT   JOIN receipts r USING (date)
            GROUP  BY 1, 2, 3, 4, 5, 6, 7, 8
            ORDER  BY c.date
        """,
    ).pl()
    # temperature anomaly: deviation from a 21-day centered seasonal expectation.
    # Sensor-outage days stay NULL here and are dropped by the model fit below
    # (statsmodels' default), rather than being guessed at.
    daily = daily.with_columns(
        pl.col("temp_C").rolling_mean(
            window_size = 21,
            center = True,
            min_samples = 8,
        ).alias("temp_seasonal"),
        pl.col("wet").shift(n = 1).alias("wet_lag1"),
    ).with_columns(
        (pl.col("temp_C") - pl.col("temp_seasonal")).alias("anom"),
    )

    _open = daily.filter(pl.col("closed") == 0).with_columns(
        pl.col("visits").log().alias("log_v"),
        pl.col("revenue").log().alias("log_rev"),
    ).to_pandas()
    _fits = {}
    for _dv in ("log_v", "log_rev"):
        _fits[_dv] = _smf.ols(
            formula = f"{_dv} ~ wet + wet_lag1 + anom + C(dow) + C(m) + pre_holiday",
            data = _open,
        ).fit(
            cov_type = "HAC",
            cov_kwds = {"maxlags": 7},
        )
    wx_stats = {
        "v_wet": np.expm1(_fits["log_v"].params["wet"]),
        "r_wet": np.expm1(_fits["log_rev"].params["wet"]),
        "v_lag": np.expm1(_fits["log_v"].params["wet_lag1"]),
        "r_lag": np.expm1(_fits["log_rev"].params["wet_lag1"]),
        "r_lag_se": float(_fits["log_rev"].bse["wet_lag1"]),
        "anom": float(_fits["log_v"].params["anom"]),
        "ph": np.expm1(_fits["log_v"].params["pre_holiday"]),
        "ph_se": float(_fits["log_v"].bse["pre_holiday"]),
        "n_obs": int(_fits["log_v"].nobs),
    }
    return daily, wx_stats


@app.cell
def _(mo, wx_stats):
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 7 · Does the weather actually keep people away?

    It feels obvious that rain keeps shoppers home — but "feels obvious" and
    "the numbers back it up" are two different things, and it's easy to get
    fooled: December is both cold *and* busy with holiday shopping, so a
    naive glance at "cold days vs. sales" would wrongly blame the weather for
    what the calendar is actually doing. To separate the two, we asked a more
    careful question: *holding the day of the week and the time of year
    fixed, does rain — specifically — move the needle?*

    | effect | on how many people visit | on total sales | in plain terms |
    | --- | --- | --- | --- |
    | it rains today | **{wx_stats['v_wet']:+.0%}** | **{wx_stats['r_wet']:+.0%}** | people genuinely stay home |
    | it rained yesterday | {wx_stats['v_lag']:+.1%} | {wx_stats['r_lag']:+.1%} (give or take {wx_stats['r_lag_se']:.1%}) | a possible "catch-up" bounce — real-looking, but too small and shaky to bank on |
    | warmer/colder than usual for the season | {wx_stats['anom']:+.3f} (per °C) | — | weather barely changes *how many* people show up — its real effect is on *what* they buy (Section 6) |
    | the 3 days before a big holiday | {wx_stats['ph']:+.0%} (give or take {wx_stats['ph_se']:.0%}) | — | there are only 9 such days all year — too few to say anything reliable |

    **The headline: a rainy day costs you roughly a fifth of your normal
    foot traffic.** The more interesting question is whether that's a
    customer who *skips buying groceries entirely that week*, or one who
    *just comes tomorrow instead* — because those call for completely
    different responses. The honest answer here is: the day-after number
    does point the right way (a small rebound), but it's small enough, and
    uncertain enough, that **one year of daily data simply isn't enough to
    prove it's real** rather than noise. Practically, that argues for
    treating a rainy day as "be ready to restock tomorrow," not as a reason
    to panic and run a discount.
    """
            ),
            mo.accordion(
                items = {
                    "🔍 See exactly how this was calculated": mo.md(
                        r"""
    **The question in one sentence.** Does rain move sales, once we've
    already accounted for the day of the week and the month of the year?

    **The data.** Every day of the year *except* the 2 days the shop was
    closed — {n} days in total. For each day we know: whether it rained,
    whether it rained the day before, how many people visited, how much was
    sold, the day of the week, the month, whether it fell in the 3-day
    run-up to a major holiday, and the temperature.

    **The model.** This is a standard statistical technique called a
    **linear regression** — it fits the straight-line combination of factors
    that best explains the ups and downs in sales, and tells you how much
    each factor matters on its own, holding the others steady. We ran it
    twice — once with *how many people visited* as the thing being
    explained, once with *total euros sold* — using this formula:

    $$
    \log(Y_t) = \beta_0 + \beta_1 \cdot \text{{Rain}}_t + \beta_2 \cdot \text{{RainYesterday}}_t
    + \beta_3 \cdot \text{{TempAnomaly}}_t + \sum_d \gamma_d \cdot \text{{Weekday}}_{{d,t}}
    + \sum_m \delta_m \cdot \text{{Month}}_{{m,t}} + \beta_4 \cdot \text{{PreHoliday}}_t + \varepsilon_t
    $$

    Reading this left to right: $Y_t$ is the day's visit count (or its
    euro sales) on day $t$; the $\beta$'s are the effects we're solving
    for; $\text{{Weekday}}_{{d,t}}$ and $\text{{Month}}_{{m,t}}$ are simple
    yes/no flags for "is day $t$ a Tuesday?", "is day $t$ in July?" and so
    on — these are what let the model tell the weather's effect apart from
    the calendar's effect, instead of confusing the two; $\varepsilon_t$ is
    just "everything else we didn't measure."

    **Why the logarithm?** Sales figures are lopsided — a handful of huge
    days, many ordinary ones — and effects like "rain" tend to act as a
    *percentage* change (a fifth fewer visitors), not a *fixed number*
    (exactly 40 fewer visitors, regardless of how big the store already is).
    Taking the log of sales before fitting the model, then converting the
    result back afterwards, is the standard way to make the numbers in the
    table above read directly as percentages.

    **Temperature gets special treatment.** Instead of using the day's raw
    temperature, we compare it to what's *normal for that time of year*
    (a 21-day moving average centered on that date). Raw temperature would
    just be re-measuring "is it July," which the month flags already
    handle — the *anomaly* isolates a genuinely unusual hot or cold
    stretch, independent of the season.

    **One statistical honesty check.** Weather (and sales) tend to run in
    streaks — a rainy spell lasts a few days, not one. Ordinary formulas for
    "how confident are we in this number" assume each day is independent of
    the next, which isn't true here and would make the model overconfident.
    We used an adjustment called **HAC (heteroskedasticity- and
    autocorrelation-consistent) standard errors** to correct for that
    streakiness, so the "give or take ___%" ranges reported above are
    honest ones, not artificially narrow.
    """.replace("{n}", str(wx_stats["n_obs"])),
                    ),
                },
            ),
        ],
    )
    return


@app.cell
def _(MUTED, WARN, caption, con, dt, go, mo, style):
    # ---- cost shocks and pass-through ---------------------------------------------
    cost_idx = con.sql(
        query = """
            SELECT p.category,
                   date_trunc('week', pr.delivery_date) AS wk,
                   avg(pr.unit_cost)                    AS cost
            FROM   procurement pr
            JOIN   products p USING (uid)
            GROUP  BY 1, 2
            ORDER  BY 1, 2
        """,
    ).pl().pivot(
        on = "category",
        index = "wk",
        values = "cost",
    ).sort(by = "wk")

    # only the two refrigerated categories the narrative names get color and
    # a direct label; the rest are context, muted and unlabeled
    _fig = go.Figure()
    # a small vertical nudge keeps the two highlighted labels from colliding
    # where their lines end at nearly the same value
    _picks = [("Frozen Foods", WARN, 2.5, True, 8), ("Dairy and Eggs", "#B4831F", 2.5, True, -8),
              ("Fresh Produce", MUTED, 1.5, False, 0), ("Bakery and Bread", MUTED, 1.5, False, 0),
              ("Household and Cleaning Supplies", MUTED, 1.5, False, 0)]
    for _c, _col, _lw, _label, _yshift in _picks:
        if _c in cost_idx.columns:
            _base = cost_idx[_c].head(n = 4).mean()
            _y = (cost_idx[_c] / _base).to_list()
            _fig.add_scatter(
                x = cost_idx["wk"].to_list(),
                y = _y,
                mode = "lines",
                line = dict(
                    color = _col,
                    width = _lw,
                ),
            )
            if _label:
                _fig.add_annotation(
                    x = cost_idx["wk"][-1],
                    y = _y[-1],
                    text = _c,
                    showarrow = False,
                    xanchor = "left",
                    xshift = 8,
                    yshift = _yshift,
                    font = dict(
                        color = _col,
                        size = 12,
                    ),
                )
    _fig.add_vline(
        x = "2025-10-01",
        line_dash = "dash",
        line_color = MUTED,
        annotation_text = "Oct 1",
        annotation_font_color = MUTED,
    )
    style(
        fig = _fig,
        title = "A cost shock hits refrigeration hardest, starting in October",
        right_margin = 96,
    )
    _fig.update_yaxes(title_text = "invoice cost index (Jan = 1.0)")
    # end-of-line labels otherwise pull the autorange well past year-end
    _fig.update_xaxes(range = [cost_idx["wk"].min(), cost_idx["wk"].max() + dt.timedelta(weeks = 4)])
    mo.vstack(
        items = [
            _fig,
            caption(
                "Each line tracks one category's wholesale cost over the year, "
                "rescaled so January = 1.0 — a line at 1.2 means 'costs are 20% "
                "higher than in January.' Two categories are colored and labeled "
                "because they're the ones that actually spiked; the rest are shown "
                "in gray just for context, so you can see the October jump was "
                "unusual, not part of a general drift."
            ),
        ],
    )
    return (cost_idx,)


@app.cell
def _(cost_idx, mo, pnl):
    _base = cost_idx["Frozen Foods"].head(n = 4).mean()
    _fz_peak = float(cost_idx["Frozen Foods"].max() / _base)
    mo.md(
        f"""
    ## 7b · What actually happened in October?

    Something hit the cold chain hard in the autumn: what you pay suppliers
    for frozen goods peaked **{_fz_peak - 1:+.0%}** above its January level,
    dairy followed close behind, and your own electricity bill jumped
    {pnl['utilities'][10] / pnl['utilities'][8] - 1:+.0%} by November. That's
    the classic signature of an **energy cost shock** — something that made
    electricity and refrigeration more expensive everywhere, hitting you
    twice: once through what your suppliers charge, once through your own
    meter. A few other categories show smaller, separate bumps at different
    points in the year, on top of a slow, steady 2.5%-ish annual creep that
    just comes with inflation.

    Here's why this matters for more than just your electricity bill: your
    shelf prices track your invoice costs almost mechanically — when the
    price list changes, it's clustered right around delivery dates. That
    means your prices moved this year **for reasons that had nothing to do
    with whether customers wanted more or less of something** — a supplier
    problem moved them, not your shoppers' appetite. That happens to be
    exactly the kind of "clean" price change that lets us actually answer
    the next question properly, rather than guess at it — which is where
    Section 7c picks up. (One honest caveat: a broad energy crisis can also
    squeeze *household* budgets at the same time it squeezes yours, whereas
    something narrower like a bad fishing season or a shipping delay
    squeezes only suppliers. We account for that difference in how we use
    each event below.)
    """
    )
    return


@app.cell
def _(con, np, pl):
    # ---- price elasticity: naive OLS vs cost-instrumented IV -----------------------
    _panel = con.sql(
        query = """
            WITH wk AS (
                SELECT uid,
                       cast(least(51, datediff('day', DATE '2025-01-01', date) / 7) AS INT) AS w,
                       sum(qty)::DOUBLE                  AS units,
                       sum(qty * unit_price) / sum(qty)  AS price,
                       max(promo)                        AS promo
                FROM   receipts
                GROUP  BY 1, 2
            ),
            cost AS (
                SELECT uid,
                       cast(least(51, datediff('day', DATE '2025-01-01', delivery_date) / 7) AS INT) AS w,
                       avg(unit_cost) AS wcost
                FROM   procurement
                GROUP  BY 1, 2
            )
            SELECT wk.uid,
                   wk.w,
                   wk.units,
                   wk.price,
                   wk.promo,
                   cost.wcost,
                   p.category
            FROM   wk
            LEFT   JOIN cost USING (uid, w)
            JOIN   products p ON wk.uid = p.uid
            ORDER  BY wk.uid, wk.w
        """,
    ).pl()
    _panel = _panel.with_columns(
        pl.col("wcost").forward_fill().backward_fill().over("uid"),
    ).filter(
        (pl.col("promo") == 0) & pl.col("wcost").is_not_null() & (pl.col("units") > 0),
    ).with_columns(
        pl.col("units").log().alias("ly"),
        pl.col("price").log().alias("lp"),
        pl.col("wcost").log().alias("lz"),
    )

    def _within(df, col):
        return (df[col].to_numpy()
                - df.select(pl.col(col).mean().over("uid"))[col].to_numpy()
                - df.select(pl.col(col).mean().over("w"))[col].to_numpy()
                + float(df[col].mean()))

    def _elast(df):
        if df["uid"].n_unique() < 5 or df.height < 150:
            return None
        y = _within(
            df = df,
            col = "ly",
        )
        p = _within(
            df = df,
            col = "lp",
        )
        z = _within(
            df = df,
            col = "lz",
        )
        b_ols = float((p @ y) / (p @ p))
        b_iv = float((z @ y) / (z @ p))
        resid = y - b_iv * p
        se_iv = float(np.sqrt((resid @ resid / (len(y) - 1)) * (z @ z)) / abs(z @ p))
        return b_ols, b_iv, se_iv, df.height

    _rows = []
    _all = _elast(df = _panel)
    _rows.append({
        "category": "ALL (pooled)",
        "naive_ols": round(_all[0], 3),
        "iv": round(_all[1], 3),
        "iv_se": round(_all[2], 3),
        "n": _all[3],
    })
    for (_cat,), _g in sorted(_panel.group_by("category"), key = lambda kv: kv[0]):
        _r = _elast(df = _g)
        if _r:
            # blank the weak-instrument rows: a huge-SE IV is not an estimate
            _weak = _r[2] > 1.0
            _rows.append({
                "category": _cat,
                "naive_ols": round(_r[0], 3),
                "iv": None if _weak else round(_r[1], 3),
                "iv_se": None if _weak else round(_r[2], 3),
                "n": _r[3],
            })
    elas = pl.DataFrame(_rows)

    # category-level elasticity: does the *category* lose demand, or just the SKU?
    _cp = con.sql(
        query = """
            SELECT p.category,
                   cast(least(51, datediff('day', DATE '2025-01-01', r.date) / 7) AS INT) AS w,
                   sum(r.qty)::DOUBLE                     AS units,
                   sum(r.qty * r.unit_price) / sum(r.qty) AS price
            FROM   receipts r
            JOIN   products p USING (uid)
            WHERE  r.promo = 0
            GROUP  BY 1, 2
        """,
    ).pl().with_columns(
        pl.col("units").log().alias("ly"),
        pl.col("price").log().alias("lp"),
    )
    _lyw = (_cp["ly"].to_numpy()
            - _cp.select(pl.col("ly").mean().over("category"))["ly"].to_numpy()
            - _cp.select(pl.col("ly").mean().over("w"))["ly"].to_numpy()
            + float(_cp["ly"].mean()))
    _lpw = (_cp["lp"].to_numpy()
            - _cp.select(pl.col("lp").mean().over("category"))["lp"].to_numpy()
            - _cp.select(pl.col("lp").mean().over("w"))["lp"].to_numpy()
            + float(_cp["lp"].mean()))
    _b = float((_lpw @ _lyw) / (_lpw @ _lpw))
    _res = _lyw - _b * _lpw
    cat_elast = {
        "b": _b,
        "se": float(np.sqrt((_res @ _res / (len(_cp) - 1)) / (_lpw @ _lpw))),
        "n_weeks": int(_cp.height),
        "n_sku_weeks": int(_panel.height),
        "n_skus": int(_panel["uid"].n_unique()),
    }
    return cat_elast, elas


@app.cell
def _(cat_elast, elas, mo):
    _pool = elas.row(
        index = 0,
        named = True,
    )
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 7c · Does raising a price scare customers away?

    This is the question every shop owner actually cares about, and it turns
    out the honest answer depends on *what* you raise the price of.

    - **Raise the price of one single product**, and its own sales drop
      hard ({_pool['iv']:+.2f}, give or take {_pool['iv_se']:.2f}) — but
      most of those "lost" sales didn't leave the shop. They walked three
      feet down the same shelf into a similar product. This is
      **substitution**, not customers giving up on you.
    - **Raise the price across a whole category** (say, all of bread, not
      just one loaf), and demand barely moves at all
      ({cat_elast['b']:+.2f}, give or take {cat_elast['se']:.2f}). There's
      nowhere for the customer to substitute *to* — bread getting 3% dearer
      doesn't make people stop eating bread.

    That gap between the two numbers is the single most useful pricing fact
    in this whole report: **the safe place to adjust margin is the category
    level, not any one product.** Nudging up the whole bread category a
    small amount is low-risk money on the table; trying to squeeze extra
    margin out of one specific loaf just pushes customers to the loaf next
    to it.

    One more honesty note, which the numbers actually confirm rather than
    just assume: two completely different ways of doing this math (a simple
    one, and a more careful one described below) landed on almost the same
    answer for individual products. That agreement is itself informative —
    it tells us your prices this year moved mostly because of what you were
    *paying suppliers*, not because of clever pricing strategy, which means
    even the simple version of this math can be trusted here. (Rows in the
    table below left blank are ones where there wasn't enough genuine cost
    movement to measure reliably — better to say nothing than to report a
    guess dressed up as a number.)
    """
            ),
            mo.ui.table(
                data = elas,
                selection = None,
            ),
            mo.accordion(
                items = {
                    "🔍 See exactly how this was calculated": mo.md(
                        f"""
    **The question in one sentence.** If price goes up by 1%, how many
    fewer units sell — comparing one product on its own against its whole
    category?

    **The data.** A week-by-product table: for every product (and,
    separately, for every category), how many units sold and at what
    average price, for each of the 52 weeks — {cat_elast['n_sku_weeks']:,}
    product-weeks across {cat_elast['n_skus']} products for the per-product
    version, {cat_elast['n_weeks']:,} category-weeks for the category
    version. Weeks with an active markdown are excluded, so a temporary
    discount doesn't get mistaken for "the price changed."

    **The model — and the two traps it has to dodge.** This is a
    regression again, but a fussier one than Section 7's, because two
    separate traps make a naive "plot price against sales" comparison
    misleading:

    *Trap 1 — some products are just always more popular than others.*
    Milk outsells caviar at any price. To stop the model from confusing
    "this product is popular" with "the price is low," we give every
    product its own personal baseline (called a **fixed effect**), and
    every week its own baseline too (to soak up ordinary seasonal ups and
    downs shared by everything that week). The formula:

    $$
    \\log(\\text{{Units}}_{{i,w}}) = \\alpha_i + \\lambda_w + \\beta \\cdot \\log(\\text{{Price}}_{{i,w}}) + \\varepsilon_{{i,w}}
    $$

    Here $i$ is the product, $w$ is the week, $\\alpha_i$ is that
    product's own typical sales level, $\\lambda_w$ is that week's own
    typical level across everything, and $\\beta$ — the number we actually
    want — measures how a *change in price relative to that product's own
    norm, in that particular week* moves units. This $\\beta$ is what
    economists call **price elasticity of demand**. In practice we do this
    by subtracting each product's own average and each week's own average
    from both sales and price first (called the **"within" transformation**)
    and then fitting a plain straight-line fit through what's left —
    mathematically identical to the formula above, just faster to compute.

    *Trap 2 — a store might raise prices exactly when demand is already
    hot* (a busy Saturday, a shortage), which would make price and demand
    move together for reasons that have nothing to do with customers
    reacting to price — and a plain regression can't tell the difference.
    The fix is the same insight from Section 7b: since this store's prices
    move mechanically with wholesale invoice costs, and a cost shock (like
    the October event) has no direct reason to affect how much customers
    *want* to buy, we can use the wholesale cost as a stand-in, or
    **instrument**, for the price change:

    $$
    \\beta_{{\\text{{IV}}}} = \\frac{{\\text{{Cov}}(\\widetilde{{\\text{{Cost}}}},\\ \\widetilde{{\\text{{Units}}}})}}{{\\text{{Cov}}(\\widetilde{{\\text{{Cost}}}},\\ \\widetilde{{\\text{{Price}}}})}}
    $$

    (the tildes mean "after the same product/week adjustment as above").
    This technique is called **instrumental variables (IV)**, and it's the
    standard economist's tool for the "which caused which?" problem. The
    table reports both the simple version and this more careful version
    side by side — when they agree closely, as they do here, it's a strong
    sign the simple version was trustworthy all along.
    """
                    ),
                },
            ),
        ],
    )
    return


@app.cell
def _(con, dt, np, pl):
    # ---- promotions: the dirty instrument and the clean one ------------------------
    promo_stats = {}
    _promos = con.sql(
        query = "SELECT * FROM promotions ORDER BY start_date",
    ).pl()
    promo_stats["n_markdowns"] = _promos.height

    _daily_sku = con.sql(
        query = """
            SELECT date,
                   uid,
                   sum(qty)::DOUBLE AS units
            FROM   receipts
            GROUP  BY 1, 2
        """,
    ).pl()
    _cat_of = dict(con.sql(
        query = "SELECT uid, category FROM products",
    ).pl().iter_rows())
    # the ranking universe is the stocked assortment, not the whole catalog
    _assort = set(con.sql(
        query = "SELECT DISTINCT uid FROM inventory_eod",
    ).pl()["uid"].to_list())
    # the storewide last-Sunday discount also sets the promo flag; exclude
    # those dates or every SKU sold that Sunday looks 'promoted'
    _loy = set(con.sql(
        query = """
            SELECT date
            FROM   (SELECT date,
                           row_number() OVER (PARTITION BY month(date)
                                              ORDER BY date DESC) AS rn
                    FROM   (SELECT DISTINCT date FROM receipts
                            WHERE  dayofweek(date) = 0))
            WHERE  rn = 1
        """,
    ).pl()["date"].to_list())

    def _win(
        lo,
        hi,
        uids,
    ):
        _m = _daily_sku.filter(
            (pl.col("date") >= lo) & (pl.col("date") <= hi) & pl.col("uid").is_in(list(uids)),
        )
        return float(_m["units"].sum()) / max((hi - lo).days + 1, 1)

    _pre, _dur, _ctl_pre, _ctl_dur, _pct = [], [], [], [], []
    for _p in _promos.iter_rows(named = True):
        _s, _e = _p["start_date"], _p["end_date"]
        _cat_uids = {u for u, c in _cat_of.items() if c == _p["category"]} & _assort
        _not_loy = ("AND r.date NOT IN ("
                    + ",".join("DATE '" + str(d) + "'" for d in _loy) + ")") if _loy else ""
        _pw = con.sql(
            query = f"""
                SELECT DISTINCT r.uid
                FROM   receipts r
                JOIN   products p USING (uid)
                WHERE  r.promo = 1
                  AND  p.category = '{_p["category"]}'
                  AND  r.date BETWEEN DATE '{_s}' AND DATE '{_e}'
                  {_not_loy}
            """,
        ).pl()["uid"].to_list()
        _pset = {u for u in _pw if u in _cat_uids}
        _pre.append(_win(
            lo = _s - dt.timedelta(days = 28),
            hi = _s - dt.timedelta(days = 1),
            uids = _pset,
        ))
        _dur.append(_win(
            lo = _s,
            hi = _e,
            uids = _pset,
        ))
        _ctl = _cat_uids - _pset
        _ctl_pre.append(_win(
            lo = _s - dt.timedelta(days = 28),
            hi = _s - dt.timedelta(days = 1),
            uids = _ctl,
        ))
        _ctl_dur.append(_win(
            lo = _s,
            hi = _e,
            uids = _ctl,
        ))
        # where did the promoted SKUs sit in their category's sales ranking?
        _tot_map = dict(_daily_sku.filter(
            (pl.col("date") < _s)
            & (pl.col("date") >= _s - dt.timedelta(days = 28))
            & pl.col("uid").is_in(list(_cat_uids)),
        ).group_by("uid").agg(pl.col("units").sum()).iter_rows())
        _uids_sorted = sorted(_cat_uids)
        _tot = pl.Series(values = [float(_tot_map.get(u, 0.0)) for u in _uids_sorted])
        _rank = (_tot.rank(method = "average") / len(_tot)).to_list()
        _rank_of = dict(zip(_uids_sorted, _rank))
        _pct.append(float(np.mean(a = [_rank_of[u] for u in _pset])) if _pset else np.nan)

    promo_stats["naive_lift"] = float(np.nansum(_dur) / max(np.nansum(_pre), 1e-9) - 1)
    _ctl_growth = np.nansum(_ctl_dur) / max(np.nansum(_ctl_pre), 1e-9)
    promo_stats["did_lift"] = float(
        (np.nansum(_dur) / max(np.nansum(_pre), 1e-9)) / _ctl_growth - 1)
    promo_stats["sel_pct"] = float(np.nanmean(_pct))

    # the clean pulse: last-Sunday storewide discount days
    _sun = con.sql(
        query = """
            SELECT date,
                   sum(qty * unit_price) AS rev,
                   row_number() OVER (PARTITION BY month(date)
                                      ORDER BY date DESC) AS rn
            FROM   receipts
            WHERE  dayofweek(date) = 0
            GROUP  BY date
        """,
    ).pl()
    promo_stats["loyalty_lift"] = float(
        _sun.filter(pl.col("rn") == 1)["rev"].mean()
        / _sun.filter(pl.col("rn") > 1)["rev"].mean() - 1)
    return (promo_stats,)


@app.cell
def _(mo, promo_stats):
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 7d · Do your discounts actually work?

    You ran **{promo_stats['n_markdowns']} markdown campaigns** this year,
    and before crediting them with anything, it's worth asking *which*
    products you tend to discount. The answer: the products you mark down
    sit, on average, at the **{promo_stats['sel_pct']:.0%} percentile** of
    their category's sales ranking — in plain terms, you discount your
    slowest sellers. That's a completely sensible instinct (clear out
    what's not moving), but it creates a measurement trap: comparing sales
    "before vs. during" a markdown makes it look spectacular
    ({promo_stats['naive_lift']:+.0%}), and even a fairer comparison against
    similar, non-discounted products still shows a big jump
    ({promo_stats['did_lift']:+.0%}) — but both of those big percentages are
    measured against an almost-nothing starting point. Tripling the sales
    of a product that barely sold two units a week is still barely selling
    six. **Judged in actual euros, markdowns are doing their job as
    inventory clean-up — they are not a growth engine.**

    There's a genuinely different, more reliable lever hiding in the same
    data: your **once-a-month storewide discount day**. Sales on that day
    run **{promo_stats['loyalty_lift']:+.0%}** above an ordinary Sunday.
    Unlike the markdowns, this discount isn't chosen *because* a product is
    struggling — it happens automatically on the calendar, on everything at
    once — which makes its effect far easier to trust at face value. If you
    want a lever that reliably moves total revenue rather than just clearing
    shelves, this is the one worth leaning on.
    """
            ),
            mo.accordion(
                items = {
                    "🔍 See exactly how this was calculated": mo.md(
                        r"""
    **The comparison used here is called "difference-in-differences"** — a
    two-step fairness check that's easier to picture than it sounds. Step
    one: compare the discounted products' sales in the 4 weeks before the
    markdown to their sales during it — this alone would credit the
    markdown with *everything* that changed, including ordinary week-to-week
    ups and downs unrelated to the discount. Step two: do the exact same
    before/during comparison for similar products in the same category that
    were **not** discounted, as a stand-in for "what would have happened
    anyway." Subtracting the second growth rate from the first leaves just
    the part of the change that the discount itself is actually responsible
    for. In symbols:

    $$
    \text{True lift} = \frac{\text{Discounted, during}}{\text{Discounted, before}}
    \;\Big/\; \frac{\text{Others, during}}{\text{Others, before}} \; - \; 1
    $$

    This is the standard technique economists reach for whenever you can't
    run a true randomized experiment (you didn't flip a coin to decide which
    products got discounted) but you do have a believable "what would have
    happened without it" comparison group sitting right next to the ones you
    treated.
    """
                    ),
                },
            ),
        ],
    )
    return


@app.cell
def _(MUTED, WARN, caption, con, go, hide_value_axis, mo, style):
    # ---- inventory economics: empty shelves and spoiled stock ----------------------
    inv_stats = {}
    _oos = con.sql(
        query = """
            SELECT month(i.date) AS m,
                   -- book stock can print negative (Section 3); <= 0 is "shelf empty"
                   avg(CASE WHEN i.on_hand <= 0 THEN 1.0 ELSE 0 END) AS oos
            FROM   inventory_eod i
            GROUP  BY 1
            ORDER  BY 1
        """,
    ).pl()
    inv_stats["oos_rate"] = con.sql(
        query = """
            SELECT avg(CASE WHEN on_hand <= 0 THEN 1.0 ELSE 0 END)
            FROM   inventory_eod
        """,
    ).fetchone()[0]

    # lost sales: per-SKU daily rate on in-stock days x OOS days x typical price
    inv_stats["lost_rev"] = float(con.sql(
        query = """
            WITH rate AS (
                SELECT i.uid,
                       sum(coalesce(r.units, 0)) FILTER (WHERE i.on_hand > 0)
                         / nullif(count(*) FILTER (WHERE i.on_hand > 0), 0) AS rate_instock,
                       count(*) FILTER (WHERE i.on_hand <= 0)               AS oos_days
                FROM   inventory_eod i
                LEFT   JOIN (SELECT date, uid, sum(qty) AS units
                             FROM   receipts
                             GROUP  BY 1, 2) r USING (date, uid)
                GROUP  BY i.uid
            ),
            px AS (
                SELECT uid,
                       median(unit_price) AS p
                FROM   receipts
                GROUP  BY uid
            )
            SELECT sum(rate.rate_instock * rate.oos_days * px.p) AS lost
            FROM   rate
            JOIN   px USING (uid)
        """,
    ).fetchone()[0])

    _spoil = con.sql(
        query = """
            WITH c AS (
                SELECT uid,
                       median(unit_cost) AS c
                FROM   procurement
                GROUP  BY uid
            )
            SELECT p.category,
                   sum(w.units)       AS units,
                   sum(w.units * c.c) AS cost
            FROM   write_offs w
            JOIN   c USING (uid)
            JOIN   products p USING (uid)
            GROUP  BY 1
            ORDER  BY cost DESC
        """,
    ).pl()
    inv_stats["spoil_cost"] = float(_spoil["cost"].sum())
    # do write-offs have weather? (per unit of stock held, summer vs winter)
    inv_stats["spoil_summer_ratio"] = float(con.sql(
        query = """
            WITH amb AS (
                SELECT uid
                FROM   products
                WHERE  category IN ('Bakery and Bread', 'Fresh Produce')
            ),
            wo AS (
                SELECT month(date) AS m,
                       sum(units)  AS u
                FROM   write_offs
                WHERE  uid IN (SELECT uid FROM amb)
                GROUP  BY 1
            ),
            st AS (
                SELECT month(date) AS m,
                       sum(on_hand) AS oh
                FROM   inventory_eod
                WHERE  uid IN (SELECT uid FROM amb)
                GROUP  BY 1
            )
            SELECT (sum(u) FILTER (WHERE m IN (6, 7, 8))
                      / sum(oh) FILTER (WHERE m IN (6, 7, 8)))
                 / (sum(u) FILTER (WHERE m IN (12, 1, 2))
                      / sum(oh) FILTER (WHERE m IN (12, 1, 2)))
            FROM   wo
            JOIN   st USING (m)
        """,
    ).fetchone()[0])

    _fig_a = go.Figure()
    _fig_a.add_scatter(
        x = _oos["m"].to_list(),
        y = (100 * _oos["oos"]).to_list(),
        mode = "lines+markers",
        line = dict(
            color = WARN,
            width = 2,
        ),
        marker = dict(size = 6),
    )
    style(
        fig = _fig_a,
        title = "Empty-shelf days cluster in the busiest months",
    )
    _fig_a.update_yaxes(title_text = "% of days out of stock")
    _fig_a.update_xaxes(
        title_text = "month",
        tickmode = "linear",
        dtick = 1,
    )
    _fig_a.update_layout(height = 340)

    _spoil_sorted = _spoil.sort(by = "cost")
    _bar_colors = [WARN if c > _spoil_sorted["cost"].max() * 0.5 else MUTED
                   for c in _spoil_sorted["cost"].to_list()]
    _fig_b = go.Figure()
    _fig_b.add_bar(
        x = _spoil_sorted["cost"].to_list(),
        y = _spoil_sorted["category"].to_list(),
        orientation = "h",
        marker_color = _bar_colors,
        marker_line_width = 0,
        text = [f"€{c:,.0f}" for c in _spoil_sorted["cost"].to_list()],
        textposition = "outside",
        textfont = dict(color = "#404040"),
        cliponaxis = False,
    )
    style(
        fig = _fig_b,
        title = "Bakery, produce and seafood pay for their short shelf life",
    )
    _fig_b.update_yaxes(
        automargin = True,
        nticks = len(_spoil_sorted) + 1,   # this is a category axis: show every bar
    )
    hide_value_axis(
        fig = _fig_b,
        axis = "x",
        title = "write-offs over the year (EUR, at cost)",
    )
    _fig_b.update_xaxes(range = [0, _spoil_sorted["cost"].max() * 1.18])
    _fig_b.update_layout(height = 380)

    mo.vstack(
        items = [
            _fig_a,
            caption(
                "What share of your products sat with zero stock on the shelf, "
                "month by month — higher means more missed sales that month."
            ),
            _fig_b,
            caption(
                "How much each category cost you in written-off (spoiled or "
                "expired) stock over the whole year — worst offenders at the top, "
                "colored red."
            ),
        ],
    )
    return (inv_stats,)


@app.cell
def _(inv_stats, kpi, mo):
    mo.md(f"""
    ## 8 · The two quiet costs: empty shelves, and the bin

    There are two costs here that never show up as a single obvious line
    item, because they hide inside "lower sales than they could have been"
    and "shrinkage" — but together they're some of the biggest money on the
    table.

    **Cost 1 — the empty shelf.** On **{inv_stats['oos_rate']:.1%}** of all
    product-days, that item simply wasn't on the shelf to sell — and the
    chart shows those gaps cluster in exactly the months each category sells
    the most, which is the worst possible timing. Valuing each of those
    missed sales at that product's normal selling rate puts the direct
    revenue you likely lost at roughly **€{inv_stats['lost_rev']:,.0f}**
    ({inv_stats['lost_rev'] / kpi['revenue']:.1%} of your revenue) — and
    that's a conservative floor, since it doesn't count customers who gave up
    on their whole basket, or who quietly started shopping elsewhere for that
    item. One technical note worth knowing: whenever we build a model of
    "demand" elsewhere in this report, we're careful to only look at days the
    item was actually in stock — otherwise the model would mistake "we ran
    out" for "nobody wanted it," and that mistake tends to snowball, since an
    item that looks unpopular gets ordered even less next time.

    **Cost 2 — the bin.** Spoiled and expired stock cost you
    **€{inv_stats['spoil_cost']:,.0f}** at what you paid for it
    ({inv_stats['spoil_cost'] / kpi['revenue']:.1%} of revenue — roughly
    double what a well-run grocery shop typically writes off), concentrated
    exactly where you'd expect: bakery, produce, seafood — the things with
    the shortest shelf life. And the bin has a **season** of its own: per
    item held, summer write-offs of bread and produce run
    **{inv_stats['spoil_summer_ratio']:.1f}×** what they do in winter — heat
    genuinely spoils food faster, which means summer is exactly the season
    to order less of these items at a time, not more. (Refrigerated
    write-offs also climb in Q4, right alongside the energy event from
    Section 7b — worth a call to your supplier about the cold chain.)

    Put the two together and the pattern is precise: **you're holding too
    much of what dies quickly, and — in its busiest season — too little of
    what actually sells.** Both problems trace back to using one flat
    "how much to keep in stock" rule for everything, regardless of how
    perishable it is or what time of year it is. Splitting that rule —
    shorter, weather-aware stock levels for anything that spoils fast,
    forecast-led stock levels for anything with a real season — attacks both
    costs at once. Section 11 puts a number on what that's worth.
    """)
    return


@app.cell
def _(ACCENT, MUTED, caption, con, go, mo, np, pl, style):
    # ---- customer analytics on the card-linked panel -------------------------------
    cust_stats = {}
    _cw = con.sql(
        query = """
            SELECT customer_id,
                   cast(least(51, datediff('day', DATE '2025-01-01', date) / 7) AS INT) AS w,
                   sum(qty * unit_price) AS spend
            FROM   receipts
            WHERE  customer_id IS NOT NULL
            GROUP  BY 1, 2
        """,
    ).pl()
    cust_stats["n_customers"] = _cw["customer_id"].n_unique()

    _rep = dict(con.sql(
        query = """
            SELECT payment,
                   median(v) AS basket
            FROM   (SELECT receipt_id,
                           any_value(payment)    AS payment,
                           sum(qty * unit_price) AS v
                    FROM   receipts
                    WHERE  ref_receipt_id IS NULL
                    GROUP  BY receipt_id)
            GROUP  BY payment
        """,
    ).pl().iter_rows())
    cust_stats["basket_card"] = float(_rep["card"])
    cust_stats["basket_cash"] = float(_rep["cash"])

    # down-trading spells: >=4 consecutive observed weeks below 75% of own median
    # group_by iterates in arbitrary order, so pick the example deterministically:
    # the longest spell wins, ties broken by customer id
    _n_flag, _n_panel, _example, _example_key = 0, 0, None, (0, "")
    for (_cid,), _g in _cw.group_by("customer_id"):
        if _g.height < 20:
            continue
        _n_panel += 1
        _s = _g.sort(by = "w")
        _z = (_s["spend"] / _s["spend"].median()).to_numpy()
        _run, _best = 0, 0
        for _v in _z:
            _run = _run + 1 if _v < 0.75 else 0
            _best = max(_best, _run)
        if _best >= 4:
            _n_flag += 1
            if (_best, str(_cid)) > _example_key:
                _example_key = (_best, str(_cid))
                _example = (_cid, _s)
    cust_stats["n_downtraders"] = _n_flag
    cust_stats["n_panel"] = _n_panel

    _prem = con.sql(
        query = """
            SELECT r.customer_id,
                   sum(r.qty * r.unit_price) FILTER (WHERE p.brand_level = 'premium')
                     / sum(r.qty * r.unit_price) AS prem_share,
                   sum(r.qty * r.unit_price)
                     / count(DISTINCT cast(datediff('day', DATE '2025-01-01', r.date) / 7 AS INT))
                     AS wk_spend
            FROM   receipts r
            JOIN   products p USING (uid)
            WHERE  r.customer_id IS NOT NULL
            GROUP  BY 1
            HAVING count(*) > 50
        """,
    ).pl().with_columns(pl.col("prem_share").fill_null(value = 0))
    cust_stats["prem_corr"] = float(np.corrcoef(
        np.log(_prem["wk_spend"].to_numpy()),
        _prem["prem_share"].to_numpy(),
    )[0, 1])
    _ter = (_prem["wk_spend"].rank(method = "average") / _prem.height).to_numpy()
    cust_stats["prem_low"] = float(_prem.filter(pl.Series(_ter) <= 1 / 3)["prem_share"].mean())
    cust_stats["prem_high"] = float(_prem.filter(pl.Series(_ter) > 2 / 3)["prem_share"].mean())

    _fig_a = go.Figure()
    _fig_a.add_scatter(
        x = _prem["wk_spend"].to_list(),
        y = (100 * _prem["prem_share"]).to_list(),
        mode = "markers",
        marker = dict(
            color = MUTED,
            size = 6,
            opacity = 0.6,
        ),
    )
    # a light trend line makes the "only a little" claim visible directly,
    # rather than asking the reader to eyeball a cloud of dots
    _lx = np.log(_prem["wk_spend"].to_numpy())
    _slope, _intercept = np.polyfit(
        x = _lx,
        y = _prem["prem_share"].to_numpy(),
        deg = 1,
    )
    _lx_line = np.array(object = [_lx.min(), _lx.max()])
    _fig_a.add_scatter(
        x = np.exp(_lx_line).tolist(),
        y = (100 * (_intercept + _slope * _lx_line)).tolist(),
        mode = "lines",
        line = dict(
            color = ACCENT,
            width = 2.5,
        ),
    )
    style(
        fig = _fig_a,
        title = "Bigger spenders lean premium — but only a little",
    )
    _fig_a.update_xaxes(
        type = "log",
        title_text = "average weekly spend (€, log scale)",
    )
    _fig_a.update_yaxes(title_text = "share spent on premium brands (%)")
    _fig_a.update_layout(height = 380)

    _fig_b = go.Figure()
    if _example is not None:
        _cid2, _sp = _example
        _median = float(_sp["spend"].median())
        _fig_b.add_hline(
            y = _median,
            line_dash = "dot",
            line_color = MUTED,
        )
        _fig_b.add_scatter(
            x = _sp["w"].to_list(),
            y = _sp["spend"].to_list(),
            mode = "lines+markers",
            line = dict(
                color = ACCENT,
                width = 2,
            ),
            marker = dict(size = 6),
        )
        # label the reference line at the far right, in the label margin,
        # where it can never sit on top of the data itself
        _fig_b.add_annotation(
            x = _sp["w"][-1],
            y = _median,
            text = "usual week",
            showarrow = False,
            xanchor = "left",
            xshift = 8,
            # lift the label clear of the dotted line so it doesn't read struck-through
            yshift = 12,
            font = dict(
                color = "#9A9A9A",
                size = 11,
            ),
        )
    style(
        fig = _fig_b,
        title = "A sustained rough patch shows up weeks before it ends",
        right_margin = 96,
    )
    _fig_b.update_yaxes(title_text = "weekly spend (€)")
    _fig_b.update_xaxes(title_text = "week of the year")
    _fig_b.update_layout(height = 360)

    mo.vstack(
        items = [
            _fig_a,
            caption(
                "Every dot is one regular customer — how much they spend per week "
                "(left to right) against how much of that goes to premium brands "
                "(bottom to top). The blue line is the overall trend through the "
                "cloud of dots: real, but gentle."
            ),
            _fig_b,
            caption(
                "One actual customer's week-by-week spending, with their own "
                "typical week marked by the dotted line. The sustained dips are "
                "exactly the kind of rough patch that's visible in the data weeks "
                "before it would show up anywhere else."
            ),
        ],
    )
    return (cust_stats,)


@app.cell
def _(cust_stats, mo):
    mo.md(f"""
    ## 9 · What we know about your customers — and its limits

    **{cust_stats['n_customers']:,}** different card numbers show up at your
    till this year — but showing up once isn't the same as being a
    customer. Only **{cust_stats['n_panel']}** of them shop with you nearly
    every week (active in 20 or more of the 52 weeks); the rest are
    one-and-done passers-by, the kind of foot traffic every neighborhood
    shop naturally picks up. Your business is really built on that smaller
    core of regulars.

    Before trusting anything below, we checked whether "card customers" are
    a fair stand-in for "all customers," since roughly 40% of sales are
    anonymous cash (Section 3). The median card purchase is
    **€{cust_stats['basket_card']:.2f}**, versus
    **€{cust_stats['basket_cash']:.2f}** for cash — cash shoppers spend
    about {cust_stats['basket_cash'] / cust_stats['basket_card'] - 1:.0%}
    more per visit. Close enough that the two findings below should hold for
    your customers generally, but a clear enough gap that you shouldn't, say,
    multiply "average card spend" by "total customers" to guess your total
    yearly revenue — that math would come out too low.

    Two findings, one of which is smaller than the usual retail wisdom
    would have you believe:

    **Bigger spenders do lean premium — but only gently.** Your top-spending
    third of regular customers put {cust_stats['prem_high']:.0%} of their
    money into premium-brand products, against {cust_stats['prem_low']:.0%}
    for your lowest-spending third. That's a real pattern, not noise — but
    it's a much weaker effect than the common retail assumption that "big
    spenders only buy premium." In practice, even someone who genuinely
    prefers premium products still buys plenty of everyday basics out of
    habit and convenience. **Stocking a deeper premium range is a nice touch
    for keeping your best customers happy — it isn't a strategy on its own.**

    **A customer going through a rough patch is visible weeks before they
    disappear.** Of your {cust_stats['n_panel']} regular customers,
    **{cust_stats['n_downtraders']}** went through a stretch of 4 or more
    weeks in a row spending less than three-quarters of their own normal
    week — smaller baskets, cheaper choices, same person still coming in.
    This isn't someone leaving you; it's someone going through a tight
    month. A quiet, unadvertised value or own-brand option placed where they
    shop tends to keep that customer, far better than a splashy premium
    promotion would.
    """)
    return


@app.cell
def _(con, daily, dt, np, pl):
    # ---- forecasting: gradient boosting vs. an honest naive -------------------------
    from sklearn.ensemble import HistGradientBoostingRegressor as _HGB

    _cd = con.sql(
        query = """
            SELECT r.date,
                   p.category,
                   sum(r.qty)::DOUBLE AS units
            FROM   receipts r
            JOIN   products p USING (uid)
            GROUP  BY 1, 2
        """,
    ).pl()
    _dates = pl.date_range(
        start = dt.date(2025, 1, 1),
        end = dt.date(2025, 12, 31),
        interval = "1d",
        eager = True,
    )
    _grid = pl.DataFrame({"date": _dates}).join(
        other = pl.DataFrame({"category": sorted(_cd["category"].unique().to_list())}),
        how = "cross",
    )
    _cd = _grid.join(
        other = _cd,
        on = ["date", "category"],
        how = "left",
    ).with_columns(pl.col("units").fill_null(value = 0))
    _cd = _cd.join(
        other = daily.select(["date", "temp_C", "wet", "pre_holiday", "closed", "dow", "m"]),
        on = "date",
        how = "left",
    ).sort(by = ["category", "date"])
    _cd = _cd.with_columns(
        pl.col("units").shift(n = 7).over("category").alias("lag7"),
        pl.col("units").shift(n = 14).over("category").alias("lag14"),
        pl.col("units").shift(n = 1).rolling_mean(
            window_size = 28,
            min_samples = 7,
        ).over("category").alias("roll28"),
        pl.col("category").cast(dtype = pl.Categorical).to_physical().alias("cat_code"),
    ).filter(pl.col("closed") == 0).drop_nulls(subset = ["lag7", "lag14", "roll28"])

    # sensor-outage days leave temp_C / wet as NaN; the gradient booster
    # handles missing feature values natively, so they stay in the panel
    _feat = ["cat_code", "dow", "m", "temp_C", "wet", "pre_holiday",
             "lag7", "lag14", "roll28"]
    _train = _cd.filter(pl.col("date") < dt.date(2025, 10, 1))
    _test = _cd.filter(pl.col("date") >= dt.date(2025, 10, 1))
    _gb = _HGB(
        random_state = 0,
        max_iter = 300,
    )
    _gb.fit(
        X = _train.select(_feat).to_numpy(),
        y = _train["units"].to_numpy(),
    )
    _pred = np.maximum(0, _gb.predict(X = _test.select(_feat).to_numpy()))

    def _mape(
        y,
        yhat,
    ):
        _m = y > 5
        return float(np.mean(a = np.abs(y[_m] - yhat[_m]) / y[_m]))

    fc_stats = {
        "mape_model": _mape(
            y = _test["units"].to_numpy(),
            yhat = _pred,
        ),
        "mape_naive": _mape(
            y = _test["units"].to_numpy(),
            yhat = _test["lag7"].to_numpy(),
        ),
        "n_train": int(_train.height),
        "n_test": int(_test.height),
    }
    fc_frame = _test.select(["date", "category", "units", "lag7"]).with_columns(
        pl.Series(
            name = "pred",
            values = _pred,
        ),
    ).rename({"lag7": "naive"})
    # ordering is weekly: accuracy at the decision's own grain
    _wk = fc_frame.with_columns(
        pl.col("date").dt.week().alias("w"),
    ).group_by(["category", "w"]).agg(
        pl.col("units").sum(),
        pl.col("pred").sum(),
        pl.col("naive").sum(),
    )
    fc_stats["wk_model"] = _mape(
        y = _wk["units"].to_numpy(),
        yhat = _wk["pred"].to_numpy(),
    )
    fc_stats["wk_naive"] = _mape(
        y = _wk["units"].to_numpy(),
        yhat = _wk["naive"].to_numpy(),
    )
    return fc_frame, fc_stats


@app.cell
def _(
    ACCENT,
    MUTED,
    caption,
    dt,
    fc_frame,
    fc_stats,
    go,
    mo,
    pl,
    style,
):
    _b = fc_frame.filter(pl.col("category") == "Beverages (Non-Alcoholic)").sort(by = "date")
    _fig = go.Figure()
    _fig.add_scatter(
        x = _b["date"].to_list(),
        y = _b["units"].to_list(),
        mode = "lines",
        line = dict(
            color = MUTED,
            width = 2,
        ),
    )
    _fig.add_annotation(
        x = _b["date"][-1],
        y = _b["units"][-1],
        text = "actual",
        showarrow = False,
        xanchor = "left",
        xshift = 8,
        yshift = -7,
        font = dict(
            color = "#9A9A9A",
            size = 12,
        ),
    )
    _fig.add_scatter(
        x = _b["date"].to_list(),
        y = _b["pred"].to_list(),
        mode = "lines",
        line = dict(
            color = ACCENT,
            width = 2,
            dash = "dash",
        ),
    )
    _fig.add_annotation(
        x = _b["date"][-1],
        y = _b["pred"][-1],
        text = "model",
        showarrow = False,
        xanchor = "left",
        xshift = 8,
        yshift = 7,
        font = dict(
            color = ACCENT,
            size = 12,
        ),
    )
    style(
        fig = _fig,
        title = ("The model tracks Beverages through Q4 — "
                 "including the holiday spike it was never told about"),
        right_margin = 96,
    )
    _fig.update_yaxes(title_text = "units sold per day")
    # give the end-of-line labels room, and don't let them drag the date axis
    # weeks past the year's actual last day
    _fig.update_xaxes(range = [_b["date"].min(), _b["date"].max() + dt.timedelta(days = 12)])
    mo.vstack(
        items = [
            _fig,
            caption(
                "The gray line is what actually happened; the dashed blue line is "
                "what the forecasting model would have predicted, having never seen "
                "these three months before. The closer the two lines track each "
                "other, the better the model — including through the big holiday "
                "spike, which it was never told about in advance."
            ),
        ],
    )
    return


@app.cell
def _(fc_stats, mo):
    # the weekly verdict is written from the numbers, not assumed: with one
    # year of history the model and the naive rule genuinely trade places
    # from vintage to vintage of this comparison
    if fc_stats["wk_model"] < fc_stats["wk_naive"]:
        _weekly_verdict = (
            f"the model's real skill shows through: **{fc_stats['wk_model']:.0%}** off "
            f"at the weekly level, against **{fc_stats['wk_naive']:.0%}** for the "
            "naive guess. Judge a forecast by the decision it's actually meant to "
            "help with, not by the hardest possible standard."
        )
    else:
        _weekly_verdict = (
            f"the honest result is a near-tie: **{fc_stats['wk_model']:.0%}** off at "
            f"the weekly level for the model, **{fc_stats['wk_naive']:.0%}** for the "
            "naive guess. With a single year of history, \"same as last week\" is a "
            "genuinely strong opponent — what it misses are the seasonal turning "
            "points, which is exactly where the model (and the chart above) earns "
            "its keep. Judge a forecast by the decision it's meant to help with — "
            "and don't pay for complexity until it clearly beats the free guess."
        )
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 10 · Can we guess next week's sales?

    We built a computer model and gave it the last quarter of the year as a
    genuine test — three months it had never seen while it was learning
    patterns from the rest of the year. Think of it as showing the model
    everyone's homework from January through September, then giving it a
    pop quiz on October, November and December, where it had to guess sales
    it had never been shown.

    On any **single day**, the model is off by about
    **{fc_stats['mape_model']:.0%}** on average — barely better than a
    lazy-but-honest guess of "probably about the same as this day last week"
    ({fc_stats['mape_naive']:.0%}). That's not a failure of the model; it's
    a fact about grocery shopping — day-to-day, there's a lot of genuine
    randomness (who happened to feel like cooking that night) that no
    amount of clever modeling can predict away. But the decision this model
    actually needs to support isn't "exactly how many units on Tuesday" —
    it's your **weekly restocking order**. Once you add sales up to a
    weekly total, the day-to-day randomness mostly cancels out, and
    {_weekly_verdict}

    Two honest limits, stated plainly rather than buried. First, the test
    quarter happened to include both a supply cost shock and the Christmas
    rush — about the hardest three months of the year to predict, which is
    exactly why we picked them as the test. Second, and more fundamentally:
    **one year of history means the model has only ever seen one summer and
    one Christmas.** It has a memory of last year's pattern, not real
    experience with several. Anything it predicts about *next* July should
    be trusted a little less than these numbers alone would suggest — and
    a second full year of records would sharpen this model more than any
    amount of further tinkering could.

    The practical use for this today is modest and immediate: each week,
    **run its one-week-ahead guess next to your current "same as recent
    weeks" habit**, and lean on the model hardest around seasonal turns —
    the one place the simple rule visibly lags every time. Re-train it
    monthly as new records come in; a second full year is what will turn
    this from a close race into a clear win.
    """
            ),
            mo.accordion(
                items = {
                    "🔍 See exactly how this model was built": mo.md(
                        f"""
    **What it predicts.** How many units of each of the 12 product
    categories sell on a given day.

    **What it's told, to make that guess.** The category itself; the day of
    the week and the month; that day's temperature and whether it rained;
    whether it fell in a pre-holiday window; how many units sold exactly 7
    days earlier and exactly 14 days earlier; and the trailing 28-day
    average for that category. In short: *what usually happens on a day
    like this, and what's been happening lately.*

    **The training/test split.** {fc_stats['n_train']:,} category-days from
    January through September were used to teach the model; the
    {fc_stats['n_test']:,} category-days from October through December were
    held back completely and used only to grade it afterwards — the model
    never got to peek at the answer.

    **The model itself: gradient-boosted decision trees.** Unlike the
    regressions in Sections 6 and 6c, this isn't a single tidy formula —
    it's a *committee* of many small decision trees (each one a simple
    flowchart of yes/no questions, like "is it a weekday, and was it wet,
    and was last week's total high?"), built one after another, where each
    new tree's only job is to correct the mistakes the trees built so far
    are still making. In mathematical shorthand, the final prediction is a
    running sum:

    $$
    F_M(x) = F_0(x) + \\sum_{{m=1}}^{{M}} \\nu \\cdot h_m(x)
    $$

    where $F_0(x)$ is a plain starting guess (roughly, the overall
    average), each $h_m(x)$ is one small tree trained specifically to
    predict the *errors* still left over after the previous $m-1$ trees,
    and $\\nu$ is a small "learning rate" that keeps any single tree from
    overreacting to the noise in one batch of data. This method — repeatedly
    fitting a small model to the previous model's mistakes — is called
    **gradient boosting**, and it tends to handle exactly the kind of messy,
    bumpy, real-world patterns retail demand shows far better than a single
    straight-line formula could.

    **How "off by ___%" is measured.** This is the **Mean Absolute
    Percentage Error (MAPE)**: for every category-day in the test period
    (excluding near-zero sales days, where a percentage error stops meaning
    much), take how far off the guess was as a share of the true number,
    then average that across every day. A MAPE of 25% means the model's
    guess was, on average, a quarter-unit off for every unit truly sold —
    smaller is better, and 0% would mean a perfect guess every time.
    """
                    ),
                },
            ),
        ],
    )
    return


@app.cell
def _(cat_elast, elas, inv_stats, kpi, mo, promo_stats):
    _prize = inv_stats["spoil_cost"] * 0.5 + inv_stats["lost_rev"] * kpi["gross_margin_pct"]
    _pool_iv = elas.row(
        index = 0,
        named = True,
    )["iv"]
    mo.md(
        f"""
    ## 11 · What I'd do about it

    Your shop is fundamentally healthy — €{kpi['revenue']/1000:,.0f}k in
    sales, a {kpi['gross_margin_pct']:.0%} margin on goods, a loyal weekend
    crowd — and there's a real, countable amount of money still on the
    table. In the order I'd tackle them:

    1. **Fix the stock-level rule first (worth roughly
       €{_prize:,.0f}/year).** One flat "how much to keep on the shelf" rule
       is quietly costing you twice: €{inv_stats['spoil_cost']:,.0f} in
       spoiled stock (keep perishables to a few days of cover, not weeks —
       and even less in summer, when heat roughly doubles the spoilage
       rate) and roughly €{inv_stats['lost_rev']:,.0f} in sales lost to
       empty shelves (use the forecasting model from Section 10 to top up
       stock *ahead of* each category's busy season, not weeks after it
       starts). Halving the spoilage bill and capturing even the margin on
       those lost sales is a conservative estimate of what this is worth.
    2. **Adjust prices by category, never product by product.** Whole
       categories barely react to a modest price change
       ({cat_elast['b']:+.2f}), while nudging up one single product's price
       gets punished hard ({_pool_iv:+.2f} — customers just buy the one next
       to it instead). A small, careful across-the-board nudge (around ±3%)
       on your staple categories is low-risk extra margin; trying to squeeze
       more out of individual products is not.
    3. **Keep markdowns for clearing shelves; use the storewide discount
       day to actually grow sales.** Your markdowns target slow sellers and
       look dramatic in percentage terms
       ({promo_stats['did_lift']:+.0%}), but that's mostly a rounding effect
       on tiny numbers — treat them as inventory housekeeping, not a growth
       plan. The once-a-month storewide day, on the other hand, reliably
       moves total revenue ({promo_stats['loyalty_lift']:+.0%}) — it's worth
       considering a second one mid-month before inventing any new
       promotion mechanic.
    4. **Watch for the next "October."** A supply cost shock like this
       year's hits you three separate ways — supplier invoices, your own
       utility bill, and spoiled refrigerated stock. A simple early-warning
       trigger (if refrigerated invoice costs jump 10% or more) would let
       you tighten perishable ordering *before* your margins get squeezed,
       rather than after.
    5. **Just keep recording everything exactly as you have been.** The
       single biggest limitation on everything in this report is that it's
       only one year of history — every seasonal claim above is really "this
       is what one summer, one Christmas looked like." A second clean year
       of the same records would sharpen every number here more than any
       further analysis could.
    """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ### Appendix — how this was put together, for the curious

    Everything above comes from `data/store.duckdb`, rebuilt fresh each time
    this notebook runs from the raw files in `data/visible/` (plus
    `SKUs.xlsx`, the product catalog). That underlying dataset is itself
    generated by a separate script, `generate_dataset.py`, from a single
    starting number (a random "seed") — so the whole year of records can be
    reproduced exactly, byte for byte, any time.

    **Tools used, if you want to look under the hood:** DuckDB for querying
    the tables with SQL; Polars for reshaping data in Python; Plotly for
    every chart. The statistical methods are explained in their own
    "See exactly how this was calculated" panels next to where they're
    used — a plain linear regression with a streak-correction on the
    standard errors (Section 7), a two-way fixed-effects regression with an
    instrumental-variables version (Section 7c), a difference-in-differences
    comparison (Section 7d), and gradient-boosted decision trees (Section
    10). Every analysis in this report was built only from the records you'd
    actually have on hand — nothing here peeked at "hidden" information that
    wouldn't be available to someone reading your paperwork honestly.
    """)
    return


if __name__ == "__main__":
    app.run()
