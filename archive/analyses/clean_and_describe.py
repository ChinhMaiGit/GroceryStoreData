import marimo

__generated_with = "0.23.14"
app = marimo.App(
    width="full",
    app_title="Layers 0–1 — Clean the Records, Describe the Business",
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
        ROOT,
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
    # Layers 0–1: clean the records, then describe the business

    This is the first notebook of the catalog series
    (`documents/ANALYSIS_CATALOG.md`), covering **Layer 0** (data cleaning,
    questions 0.1–0.7) and **Layer 1** (descriptive analysis, 1.1–1.8) at
    full depth on the analysis baseline: the **three-year dataset**,
    `data/scenarios/3y_baseline/` — thirty-six months, ~243,000 till lines,
    three recording-layer "binders" of defects, a business that grew,
    expanded, and met a competitor along the way.

    Two rules govern everything below:

    - **Layer 0 is graded.** Every defect this notebook finds is scored
      row-by-row against the hidden answer key
      (`hidden/imperfections.csv`). Real cleaning work never gets a grade;
      this dataset exists so that, for once, it can. The grading panels
      are clearly marked and nothing outside them depends on the key.
    - **Layer 1 runs only on the cleaned views.** Every descriptive claim
      sits on top of Layer 0's output, in the order a real engagement
      would enforce.

    The same pipeline applies unchanged to every arm in `data/scenarios/`
    — including the original one-year `baseline/`, whose exogenous script
    (weather, costs, events) is byte-identical to this dataset's first
    year.
    """)
    return


@app.cell
def _(DATA, ROOT, duckdb, pl):
    # ---- load the RAW paperwork only — this notebook builds the cleaning ---
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

    # the answer key, used ONLY inside the grading panels
    truth = pl.read_csv(
        source = DATA / "scenarios" / "3y_baseline" / "hidden" / "imperfections.csv",
        schema_overrides = {"key": pl.Utf8},
    )
    return con, truth


@app.cell
def _(caption, mo):
    _erd = mo.mermaid("""
    erDiagram
        receipts_raw }o--|| products : "uid"
        inventory_eod_raw }o--|| products : "uid"
        procurement_raw }o--|| products : "uid"
        write_offs_raw }o--|| products : "uid"
        price_history_raw }o--|| products : "uid"
        receipts_raw }o--|| calendar : "date"
        weather_raw ||--|| calendar : "date"
        cost_sheet ||--|| tax_statement : "year"

        receipts_raw {
            int receipt_id "NOT unique per upload"
            date date "2025-01-01 .. 2027-12-31"
            int hour "0 = clock glitch"
            string payment "label drift"
            int qty "negative = refund OR void"
            int ref_receipt_id "refund -> original sale"
        }
        products {
            string uid PK
            string category
            string brand_level
        }
        cost_sheet {
            int year
            int month
            float owner_draw "the capital columns"
            float retained_earnings
            float capex
            float profit_tax_paid
        }
        write_offs_raw {
            string uid FK
            int units
            string reason "spoilage | stock_count | damage"
        }
        inventory_eod_raw {
            string uid FK
            int on_hand "BOOK stock, not truth"
        }
    """)
    mo.vstack(
        items = [
            mo.md("## The raw paperwork, mapped"),
            _erd,
            caption(
                "The `_raw` suffix is the point: these are the documents as "
                "the back office produced them — duplicated uploads, voided "
                "mis-rings, label drift, posting lags, digit slips, sensor "
                "gaps — injected one calendar year (one binder) at a time. "
                "The cost sheet is the one exception: it is the owner's own "
                "ledger and, by the accounting contract (ACCOUNTING.md §1), "
                "always right about money; on this horizon it also carries "
                "the capital columns (draws, retained earnings, capex, "
                "January tax payments). Everything below reconciles the "
                "paperwork TO the ledger, never the other way around."
            ),
        ],
    )
    return


@app.cell
def _(con, mo, pl, truth):
    # ==== Layer 0.1 — which receipts were uploaded twice? ====================
    # the all-even rule: a POS retry re-posts an entire receipt, so a retry
    # is a receipt where EVERY distinct line appears an even number of times
    _flagged = con.sql(
        query = """
            WITH lines AS (
                SELECT receipt_id,
                       min(date)                     AS d,
                       sum(qty * unit_price * n) / 2 AS half_value,
                       bool_and(n % 2 = 0)           AS all_even
                FROM (
                    SELECT receipt_id,
                           date,
                           qty,
                           unit_price,
                           count(*) AS n
                    FROM   receipts_raw
                    GROUP  BY receipt_id, hour, payment, customer_id, uid,
                              qty, unit_price, promo, date, ref_receipt_id
                )
                GROUP  BY receipt_id
            )
            SELECT receipt_id,
                   year(d)              AS y,
                   round(half_value, 2) AS half_value
            FROM   lines
            WHERE  all_even
        """,
    ).pl()
    # the residue hunt: after halving every flagged receipt, does each
    # year's till tie to its ledger? Any residue must be a FALSE POSITIVE —
    # and its amount should match exactly one flagged receipt's half-value
    _gaps = con.sql(
        query = """
            WITH lines AS (
                SELECT receipt_id, hour, payment, customer_id, uid, qty,
                       unit_price, promo, date, ref_receipt_id, count(*) AS n
                FROM   receipts_raw
                GROUP  BY ALL
            ),
            retry AS (
                SELECT receipt_id,
                       bool_and(n % 2 = 0) AS is_retry
                FROM   lines
                GROUP  BY receipt_id
            ),
            rc AS (
                SELECT l.date,
                       l.unit_price,
                       sum(l.qty * CASE WHEN r.is_retry THEN l.n // 2
                                        ELSE l.n END) AS q
                FROM   lines l
                JOIN   retry r USING (receipt_id)
                GROUP  BY l.receipt_id, l.hour, l.payment, l.customer_id,
                          l.uid, l.unit_price, l.promo, l.date, l.ref_receipt_id
                HAVING q != 0
            ),
            led AS (
                SELECT year,
                       sum(revenue)::DOUBLE AS ledger
                FROM   cost_sheet_raw
                GROUP  BY 1
            )
            SELECT led.year,
                   round(sum(rc.q * rc.unit_price) - any_value(led.ledger), 2) AS gap
            FROM   rc
            JOIN   led ON year(rc.date) = led.year
            GROUP  BY led.year
            ORDER  BY led.year
        """,
    ).pl()
    # locate each residue's culprit from VISIBLE data alone: the one flagged
    # receipt in that year whose half-value equals the missing money
    suspects = []
    for _g in _gaps.filter(pl.col("gap").abs() > 0.01).iter_rows(named = True):
        _cand = _flagged.filter(
            (pl.col("y") == _g["year"])
            & ((pl.col("half_value") - abs(_g["gap"])).abs() < 0.01)
        )
        if len(_cand) == 1:
            suspects.append({
                "year": _g["year"],
                "residue": abs(_g["gap"]),
                "suspect_receipt": int(_cand["receipt_id"][0]),
            })
    _found = set(_flagged["receipt_id"].cast(pl.Utf8).to_list())
    _true = set(truth.filter(pl.col("kind") == "dup_receipt")["key"].to_list())
    _fp = _found - _true
    grade_01 = {
        "found": len(_found),
        "injected": len(_true),
        "tp": len(_found & _true),
        "fp_confirmed": sorted(int(_r) for _r in _fp),
        "precision": len(_found & _true) / max(1, len(_found)),
        "recall": len(_found & _true) / max(1, len(_true)),
    }
    _rev = con.sql(
        query = """
            SELECT sum(qty * unit_price)::DOUBLE                     AS raw_rev,
                   (SELECT sum(revenue) FROM cost_sheet_raw)::DOUBLE AS ledger_rev
            FROM   receipts_raw
        """,
    ).pl()
    _suspect_txt = "; ".join(
        f"{_s['year']}: €{_s['residue']:.2f} → receipt {_s['suspect_receipt']}"
        for _s in suspects
    )
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 0.1 · Which receipts were uploaded twice — and what was revenue, really?

    Summing the raw till gives **€{float(_rev['raw_rev'][0]):,.2f}**; the
    owner's ledger says **€{float(_rev['ledger_rev'][0]):,.2f}** — the
    paperwork overstates revenue by
    €{float(_rev['raw_rev'][0]) - float(_rev['ledger_rev'][0]):,.2f}, the
    signature of receipts uploaded twice by a flaky POS terminal.

    **The rule:** a retry re-posts an *entire* receipt, so a duplicated
    receipt is one where every distinct line appears an even number of
    times (a genuine double-scan only doubles one line). That flags
    **{grade_01['found']} receipts** across the three binders.

    **The residue hunt — where the rule meets reality.** After halving
    every flagged receipt, each year's till should tie to its ledger. It
    doesn't quite: {_suspect_txt}. In each case *exactly one* flagged
    receipt's half-value matches the missing money — so the rule itself
    identifies its own likely false positives: honest one-item baskets
    whose single line was scanned twice at the till, which satisfies the
    all-even test by pure chance. Keep those two receipts whole, and every
    year ties to the cent.
    """
            ),
            mo.accordion(
                items = {
                    "Grading against the answer key": mo.md(
                        f"""
    `imperfections.csv` records **{grade_01['injected']}** injected retry
    uploads. The all-even rule flags **{grade_01['found']}**:
    **precision {grade_01['precision']:.1%}, recall
    {grade_01['recall']:.0%}**. The two false positives are exactly the
    receipts the residue hunt fingered
    ({', '.join(str(_r) for _r in grade_01['fp_confirmed'])}) — both
    absent from the answer key, both single-distinct-line baskets. Roughly
    one error per hundred-thousand lines, and each one locatable from
    visible data alone: that is what a good heuristic looks like in
    production (ACCOUNTING §9 documents this blind spot as part of the
    reconciliation contract).
    """
                    ),
                },
            ),
        ],
    )
    return grade_01, suspects


@app.cell
def _(con, mo, pl, truth):
    # ==== Layer 0.2 — which negative lines are voids, which are refunds? =====
    _neg = con.sql(
        query = """
            WITH neg AS (
                SELECT receipt_id,
                       uid,
                       unit_price,
                       qty,
                       date,
                       ref_receipt_id
                FROM   receipts_raw
                WHERE  qty < 0
            )
            SELECT count(*) FILTER (WHERE ref_receipt_id IS NOT NULL)  AS refunds,
                   count(*) FILTER (WHERE ref_receipt_id IS NULL)      AS voids,
                   count(*) FILTER (WHERE ref_receipt_id IS NULL AND NOT EXISTS (
                       SELECT 1
                       FROM   receipts_raw p
                       WHERE  p.receipt_id = neg.receipt_id
                         AND  p.uid = neg.uid
                         AND  p.unit_price = neg.unit_price
                         AND  p.qty = -neg.qty
                   ))                                                  AS unmatched_voids,
                   count(*) FILTER (WHERE ref_receipt_id IS NOT NULL AND NOT EXISTS (
                       SELECT 1
                       FROM   receipts_raw s
                       WHERE  s.receipt_id = neg.ref_receipt_id
                         AND  s.qty > 0
                   ))                                                  AS orphan_refunds
            FROM   neg
        """,
    ).pl()
    _xyear = con.sql(
        query = """
            WITH sales AS (
                SELECT receipt_id,
                       min(date) AS d
                FROM   receipts_raw
                WHERE  qty > 0
                GROUP  BY 1
            )
            SELECT count(DISTINCT r.receipt_id) AS n
            FROM   receipts_raw r
            JOIN   sales s ON r.ref_receipt_id = s.receipt_id
            WHERE  r.qty < 0
              AND  year(r.date) != year(s.d)
        """,
    ).pl()
    _void_hosts = con.sql(
        query = """
            SELECT DISTINCT receipt_id
            FROM   receipts_raw
            WHERE  qty < 0
              AND  ref_receipt_id IS NULL
        """,
    ).pl()
    _found = set(_void_hosts["receipt_id"].cast(pl.Utf8).to_list())
    _true = set(truth.filter(pl.col("kind") == "void_pair")["key"].to_list())
    grade_02 = {
        "refunds": int(_neg["refunds"][0]),
        "voids": int(_neg["voids"][0]),
        "unmatched": int(_neg["unmatched_voids"][0]),
        "orphans": int(_neg["orphan_refunds"][0]),
        "xyear": int(_xyear["n"][0]),
        "tp": len(_found & _true),
        "found": len(_found),
        "injected": len(_true),
    }
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 0.2 · Negative till lines: cancelled mis-rings vs. real refunds

    The till tape holds two very different kinds of negative line, and
    `ref_receipt_id` separates them perfectly:

    - **{grade_02['refunds']} refund lines** point back at an earlier sale
      — real money leaving the till for a returned item (destroyed, never
      restocked). **{grade_02['orphans']} orphans**: every refund resolves
      to a genuine sale, including **{grade_02['xyear']}** that cross a
      year boundary — January returns of December purchases, a seam only
      a multi-year till can show.
    - **{grade_02['voids']} void lines** point at nothing — each a
      cashier's mis-ring cancelled on the spot, each finding its exact +q
      partner on the same receipt at the same price
      ({grade_02['unmatched']} unmatched). Net effect on money and stock:
      zero, by construction.

    The cleaning consequence differs: refunds are **kept** (they are
    economics), voids are **cancelled** (they are noise).
    """
            ),
            mo.accordion(
                items = {
                    "Grading against the answer key": mo.md(
                        f"""
    The answer key records **{grade_02['injected']}** receipts that
    received a void pair; the ref-less-negative-line rule identifies
    **{grade_02['found']}**, of which **{grade_02['tp']}** are true —
    **precision {grade_02['tp'] / max(1, grade_02['found']):.0%}, recall
    {grade_02['tp'] / max(1, grade_02['injected']):.0%}**. Refund lines
    are the sim's own economics (P3 §21), not defects, and correctly
    appear nowhere in the defect ledger.
    """
                    ),
                },
            ),
        ],
    )
    return


@app.cell
def _(con, mo, pl, truth):
    # ==== Layer 0.3 — do invoices reconcile to the ledger? ===================
    _per_year = con.sql(
        query = """
            WITH ded AS (
                SELECT DISTINCT uid,
                       qty,
                       unit_cost,
                       order_date,
                       delivery_date
                FROM   procurement_raw
            ),
            raw AS (
                SELECT year(delivery_date) AS y,
                       count(*)            AS raw_lines
                FROM   procurement_raw
                GROUP  BY 1
            ),
            d AS (
                SELECT year(delivery_date)            AS y,
                       count(*)                       AS dedup_lines,
                       sum(qty * unit_cost)::DOUBLE   AS invoices
                FROM   ded
                GROUP  BY 1
            ),
            led AS (
                SELECT year,
                       sum(procurement)::DOUBLE AS ledger
                FROM   cost_sheet_raw
                GROUP  BY 1
            )
            SELECT raw.y                                AS year,
                   raw.raw_lines,
                   d.dedup_lines,
                   raw.raw_lines - d.dedup_lines        AS duplicate_lines,
                   round(led.ledger - d.invoices, 2)    AS missing_gap_eur
            FROM   raw
            JOIN   d   ON raw.y = d.y
            JOIN   led ON raw.y = led.year
            ORDER  BY raw.y
        """,
    ).pl()
    _dups_found = con.sql(
        query = """
            SELECT uid,
                   delivery_date
            FROM   procurement_raw
            GROUP  BY uid, qty, unit_cost, order_date, delivery_date
            HAVING count(*) > 1
        """,
    ).pl()
    _true_dup = truth.filter(pl.col("kind") == "dup_invoice")
    _true_pairs = set(zip(
        _true_dup["key"].to_list(),
        _true_dup["date"].to_list(),
    ))
    _found_pairs = set(zip(
        _dups_found["uid"].to_list(),
        _dups_found["delivery_date"].cast(pl.Utf8).to_list(),
    ))
    grade_03 = {
        "tp": len(_found_pairs & _true_pairs),
        "found": len(_found_pairs),
        "injected": len(_true_dup),
        "n_missing": len(truth.filter(pl.col("kind") == "missing_invoice")),
    }
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 0.3 · Do supplier invoices reconcile to the ledger?

    Not quite — in *both* directions, one binder at a time:

    - **{int(_per_year['duplicate_lines'].sum())} invoice lines are exact
      duplicates** (same item, quantity, cost, and dates, posted twice
      days apart): a clerk keyed the same paperwork in twice. Dropping
      the later posting is safe and exact.
    - After dedup, each year's invoice file totals **less** than that
      year's ledger procurement — deliveries received but never entered.
      The goods arrived (the ledger paid, the shelves show them); the
      paperwork simply does not exist. **Flag it, don't fix it**: the
      ledger is authoritative, and nothing in the invoice file can
      reconstruct lines that were never typed.
    """
            ),
            mo.ui.table(
                data = _per_year,
                selection = None,
            ),
            mo.accordion(
                items = {
                    "Grading against the answer key": mo.md(
                        f"""
    Duplicate postings: **{grade_03['found']} found /
    {grade_03['injected']} injected**, {grade_03['tp']} matching on
    (product, delivery date) — precision
    {grade_03['tp'] / max(1, grade_03['found']):.0%}, recall
    {grade_03['tp'] / max(1, grade_03['injected']):.0%}. Missing
    invoices: the key records **{grade_03['n_missing']}** dropped lines
    (six per binder); they are unlocatable from the visible file by
    construction — the per-year € gaps above are their only trace,
    exactly as the contract says.
    """
                    ),
                },
            ),
        ],
    )
    return


@app.cell
def _(WARN, caption, con, go, hide_value_axis, mo, pl, style, takeaway, truth):
    # ==== Layer 0.4 — does book stock reconcile, night by night? =============
    broken = con.sql(
        query = """
            WITH s AS (
                SELECT uid,
                       date,
                       sum(qty) AS q
                FROM   receipts_raw
                WHERE  ref_receipt_id IS NULL
                GROUP  BY 1, 2
            ),
            d AS (
                SELECT uid,
                       delivery_date AS date,
                       sum(qty)      AS q
                FROM   procurement_raw
                GROUP  BY 1, 2
            ),
            w AS (
                SELECT uid,
                       date,
                       sum(units) AS q
                FROM   write_offs_raw
                GROUP  BY 1, 2
            ),
            x AS (
                SELECT b.uid,
                       b.date,
                       b.on_hand
                       - lag(b.on_hand) OVER (PARTITION BY b.uid ORDER BY b.date)
                       - coalesce(d.q, 0) + coalesce(s.q, 0) + coalesce(w.q, 0) AS res
                FROM   inventory_eod_raw b
                LEFT   JOIN d ON b.uid = d.uid AND b.date = d.date
                LEFT   JOIN s ON b.uid = s.uid AND b.date = s.date
                LEFT   JOIN w ON b.uid = w.uid AND b.date = w.date
            )
            SELECT uid,
                   date,
                   res
            FROM   x
            WHERE  res IS NOT NULL
              AND  abs(res) > 1e-9
            ORDER  BY uid, date
        """,
    ).pl()
    # breaks must come in next-day pairs with opposite signs: the typo night
    # breaks the diff INTO the bad snapshot and OUT of it the next day
    _pairs = broken.sort(by = ["uid", "date"]).with_columns(
        (pl.col("date").diff().over("uid") == pl.duration(days = 1)).alias("next_day"),
        ((pl.col("res") + pl.col("res").shift(1).over("uid")).abs() < 1e-9).alias("cancels"),
    )
    _typo_days = _pairs.filter(pl.col("next_day") & pl.col("cancels")).with_columns(
        (pl.col("date") - pl.duration(days = 1)).alias("typo_date"),
    )
    _found = set(zip(
        _typo_days["uid"].to_list(),
        _typo_days["typo_date"].cast(pl.Utf8).to_list(),
    ))
    _true_t = truth.filter(pl.col("kind") == "snapshot_typo")
    _true = set(zip(
        _true_t["key"].to_list(),
        _true_t["date"].to_list(),
    ))
    grade_04 = {
        "broken": len(broken),
        "pairs": len(_typo_days),
        "tp": len(_found & _true),
        "injected": len(_true_t),
    }
    _bq = broken.group_by(
        pl.col("date").dt.year().alias("y"),
        pl.col("date").dt.quarter().alias("q"),
    ).agg(pl.len().alias("n")).sort(by = ["y", "q"]).with_columns(
        (pl.col("y").cast(pl.Utf8) + " Q" + pl.col("q").cast(pl.Utf8)).alias("yq"),
    )
    _fig = go.Figure()
    _fig.add_bar(
        x = _bq["yq"].to_list(),
        y = _bq["n"].to_list(),
        marker_color = WARN,
        text = _bq["n"].to_list(),
        textposition = "outside",
    )
    style(
        fig = _fig,
        title = "Nights where the perpetual-inventory identity breaks, by quarter",
    )
    hide_value_axis(
        fig = _fig,
        axis = "y",
        title = "broken SKU-nights",
    )
    _fig.update_xaxes(
        title_text = "",
        tickfont = dict(size = 11),
    )
    _fig.update_yaxes(range = [0, float(_bq["n"].max()) * 1.45])
    takeaway(
        fig = _fig,
        text = f"all {grade_04['broken']} breaks form {grade_04['pairs']} perfect next-day pairs — digit slips, self-corrected",
        x = 0.02,
        y = 0.99,
    )
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 0.4 · Does book stock reconcile with the paperwork, night by night?

    For every product and every night:
    yesterday's stock + deliveries − sales − write-offs should equal
    tonight's stock (refund lines excluded — returned goods are destroyed,
    never restocked). Across ~140,000 SKU-nights the identity holds
    everywhere except **{grade_04['broken']} nights** — and those breaks
    have an unmistakable shape.
    """
            ),
            _fig,
            caption(
                "Every break comes as a next-day pair whose residuals "
                "cancel exactly: the book jumps by +Δ into one night and "
                "−Δ out of it. That is the fingerprint of a keying slip in "
                "one evening's stock snapshot (two digits transposed), not "
                "of theft or unlogged movement — a real loss would break "
                "the identity once and stay broken until a stock count. "
                "The first night of each pair pinpoints the mistyped "
                "snapshot exactly; the rate is steady across all twelve "
                "quarters, as befits a back office that never got better "
                "or worse at typing. Note what is NOT here: the February "
                "2026 freezer disaster (§0.5) does not break the identity "
                "at all, because its write-offs were properly logged."
            ),
            mo.accordion(
                items = {
                    "Grading against the answer key": mo.md(
                        f"""
    The pair rule locates **{len(_found)}** (product, night) typo
    candidates; the answer key injected **{grade_04['injected']}**
    snapshot typos, of which **{grade_04['tp']}** match exactly —
    precision {grade_04['tp'] / max(1, len(_found)):.0%}, recall
    {grade_04['tp'] / max(1, grade_04['injected']):.0%} across all three
    binders.
    """
                    ),
                },
            ),
        ],
    )
    return


@app.cell
def _(
    ACCENT_LIGHT,
    WARN,
    caption,
    con,
    go,
    make_subplots,
    mo,
    pl,
    style,
    takeaway,
    truth,
):
    # ==== Layer 0.5 — what is "shrinkage" here, and what causes it? ==========
    _wo = con.sql(
        query = """
            SELECT date_trunc('month', date) AS m,
                   reason,
                   sum(units)::BIGINT        AS units
            FROM   write_offs_raw
            GROUP  BY 1, 2
            ORDER  BY 1
        """,
    ).pl()
    _spoil = _wo.filter(pl.col("reason") == "spoilage")
    _damage = _wo.filter(pl.col("reason") == "damage")
    _adj = _wo.filter(pl.col("reason") == "stock_count")
    _drift = truth.filter(pl.col("kind").is_in([
        "unrecorded_spoilage",
        "dup_invoice",
        "missing_invoice",
        "dup_receipt",
    ])).group_by("kind").agg(pl.col("delta").sum().alias("book_minus_true"))
    grade_05 = {
        "adj_units": int(_adj["units"].sum()),
        "spoil_units": int(_spoil["units"].sum()),
        "damage_units": int(_damage["units"].sum()),
    }
    _fig = make_subplots(
        rows = 1,
        cols = 2,
        subplot_titles = (
            "Logged write-offs by month (spoilage + the freezer)",
            "Monthly stock-count corrections (shrinkage)",
        ),
        horizontal_spacing = 0.12,
    )
    _fig.add_bar(
        x = _spoil["m"].to_list(),
        y = _spoil["units"].to_list(),
        marker_color = ACCENT_LIGHT,
        row = 1,
        col = 1,
    )
    _fig.add_bar(
        x = _damage["m"].to_list(),
        y = _damage["units"].to_list(),
        marker_color = WARN,
        row = 1,
        col = 1,
    )
    _fig.add_bar(
        x = _adj["m"].to_list(),
        y = _adj["units"].to_list(),
        marker_color = WARN,
        row = 1,
        col = 2,
    )
    _fig.update_layout(barmode = "stack")
    style(
        fig = _fig,
        title = "Three kinds of disappearing stock: the bin, one bad morning, and the monthly surprise",
        n_subplot_titles = 2,
    )
    _fig.update_yaxes(
        title_text = "units",
        row = 1,
        col = 1,
    )
    _fig.update_yaxes(
        title_text = "units (+ = book above count)",
        row = 1,
        col = 2,
    )
    takeaway(
        fig = _fig,
        text = "the bin is seasonal — and Feb 2026's red sliver is the freezer",
        x = 0.02,
        y = 0.99,
        row = 1,
        col = 1,
    )
    takeaway(
        fig = _fig,
        text = "the counts keep finding LESS stock than the book",
        x = 0.02,
        y = 0.99,
        row = 1,
        col = 2,
    )
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 0.5 · What is "shrinkage" here, and what causes it?

    `write_offs.csv` now mixes **three** things under one roof, split by
    `reason`:

    - **spoilage** ({grade_05['spoil_units']:,} units): the logged nightly
      bin — perishables aging out, heaviest every summer;
    - **damage** ({grade_05['damage_units']:,} units, all on
      **2026-02-08**): the freezer failure — the entire frozen aisle and
      part of the dairy case written off in one morning, properly logged
      under its own reason;
    - **stock_count** ({grade_05['adj_units']:+,} units net): the monthly
      inventory count truing the book to the shelf — the classic
      *shrinkage* line every retailer knows.
    """
            ),
            _fig,
            caption(
                "Left: the logged bin follows the weather through all "
                "three summers — with the 2026 heatwave visibly worse than "
                "its neighbors — plus one red sliver in February 2026 that "
                "is not weather at all but a dead compressor. Right: the "
                "monthly count corrections, positive when the book claims "
                "stock the shelf lacks. The pattern to notice: the tallest "
                "bars are not gradual leakage but single events — drill "
                "into any spike month and its correction traces almost "
                "entirely to one supplier invoice that was keyed in twice, "
                "putting a delivery's worth of phantom units on the book "
                "until the month-end count removed them. A shrinkage "
                "analyst chasing 'theft' in those months would be chasing "
                "a typist. Shrinkage here is never theft: it is the "
                "accumulated echo of document defects — waste tossed "
                "without being logged, invoices posted twice, deliveries "
                "never entered, duplicated uploads. The grading panel ties "
                "the total to those causes from the answer key."
            ),
            mo.accordion(
                items = {
                    "Grading: decomposing shrinkage by cause": mo.vstack(
                        items = [
                            mo.md(
                                """
    The answer key records each defect's book-vs-truth effect. Summing per
    family (positive = the book ended too HIGH, which a count then writes
    off):
    """
                            ),
                            mo.ui.table(
                                data = _drift.sort(by = "book_minus_true", descending = True),
                                selection = None,
                            ),
                            mo.md(
                                f"""
    The families sum to the net correction the counts actually made
    ({grade_05['adj_units']:+,} units, opposite sign convention), closing
    the loop: every unit of "shrinkage" in this world traces to a document
    defect, none to un-modeled theft — a documented idealization
    (ACCOUNTING §10). The freezer's damage rows, by contrast, are REAL
    physical loss, properly logged, and correctly absent from this ledger.
    """
                            ),
                        ],
                    ),
                },
            ),
        ],
    )
    return


@app.cell
def _(con, mo, pl, truth):
    # ==== Layer 0.6 — standardize the label mess =============================
    _pay = con.sql(
        query = """
            SELECT payment,
                   count(DISTINCT receipt_id) AS receipts
            FROM   receipts_raw
            GROUP  BY 1
            ORDER  BY 2 DESC
        """,
    ).pl()
    _stats = con.sql(
        query = """
            SELECT (SELECT count(DISTINCT receipt_id) FROM receipts_raw WHERE hour = 0) AS hour0,
                   (SELECT count(*) FROM weather_raw WHERE temp_C IS NULL)              AS wx_nulls,
                   (SELECT count(*) FROM promotions_raw
                    WHERE category = 'Snacks and Confectionary')                        AS promo_typos
        """,
    ).pl()
    _t = truth.group_by("kind").agg(pl.len().alias("n"))

    def _tn(kind):
        _r = _t.filter(pl.col("kind") == kind)
        return int(_r["n"][0]) if len(_r) else 0

    _n_variants = int(_pay.filter(~pl.col("payment").is_in([
        "card",
        "cash",
    ]))["receipts"].sum())
    grade_06 = pl.DataFrame({
        "defect": [
            "payment label variants ('Card', 'CASH', 'cash ')",
            "hour = 0 placeholder (POS clock glitch)",
            "weather sensor dark days (NULLs)",
            "promotions category misspelling",
        ],
        "found": [
            _n_variants,
            int(_stats["hour0"][0]),
            int(_stats["wx_nulls"][0]),
            int(_stats["promo_typos"][0]),
        ],
        "injected": [
            _tn(kind = "payment_variant"),
            _tn(kind = "hour_glitch"),
            int(truth.filter(pl.col("kind") == "weather_outage")["delta"].sum()),
            _tn(kind = "category_typo"),
        ],
    }).with_columns((pl.col("found") == pl.col("injected")).alias("exact_match"))
    mo.vstack(
        items = [
            mo.md(
                """
    ## 0.6 · Standardizing the label mess

    Four small defect families need no detective work, only discipline —
    normalize, null, or flag:

    - **payment labels** drift through hand-keyed variants: lowercase and
      trim, or every `GROUP BY payment` silently splits;
    - **hour = 0** is a placeholder from a POS clock glitch, not a
      midnight sale: set to NULL, or every hourly profile grows a phantom
      midnight rush;
    - **weather NULLs** are honest sensor outages (a few dark spells per
      year): drop those days from weather regressions, never impute;
    - **the promotions log** misspells one category ('Confectionary') —
      both offending rows sit in the 2025 binder, because 2025 is the
      only year with markdown campaigns at all (see §1.6).
    """
            ),
            mo.ui.table(
                data = grade_06,
                selection = None,
            ),
        ],
    )
    return


@app.cell
def _(con, mo, pl, suspects):
    # ==== the cleaned layer, built from everything Layer 0 established =======
    # the two residue-hunt suspects (§0.1) are kept WHOLE: the all-even rule
    # misfires on them, and the ledger tie proves it
    _keep_whole = ", ".join(str(_s["suspect_receipt"]) for _s in suspects) or "-1"
    con.execute(
        query = f"""
            CREATE OR REPLACE VIEW receipts AS
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
                       bool_and(n % 2 = 0)
                       AND receipt_id NOT IN ({_keep_whole}) AS is_retry
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
            CREATE OR REPLACE VIEW procurement AS
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
    con.execute(
        query = """
            CREATE OR REPLACE VIEW promotions AS
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

    # ---- 0.7: the reconciliation contract, run line by line -----------------
    _checks = []
    _ties = con.sql(
        query = """
            WITH r AS (
                SELECT year(date)                    AS y,
                       sum(qty * unit_price)::DOUBLE AS rev
                FROM   receipts
                GROUP  BY 1
            ),
            c AS (
                SELECT year,
                       sum(revenue)::DOUBLE AS led
                FROM   cost_sheet_raw
                GROUP  BY 1
            )
            SELECT max(abs(rev - led)) AS worst
            FROM   r
            JOIN   c ON r.y = c.year
        """,
    ).pl()
    _worst = float(_ties["worst"][0])
    _checks.append({
        "check": "cleaned till revenue vs ledger, every year (false positives kept whole)",
        "expected": "ties to the cent",
        "observed": f"worst yearly gap €{_worst:.4f}",
        "verdict": "PASS" if _worst < 0.01 else "FAIL",
    })
    _p = con.sql(
        query = """
            WITH d AS (
                SELECT year(delivery_date)          AS y,
                       sum(qty * unit_cost)::DOUBLE AS inv
                FROM   procurement
                GROUP  BY 1
            ),
            led AS (
                SELECT year,
                       sum(procurement)::DOUBLE AS proc
                FROM   cost_sheet_raw
                GROUP  BY 1
            )
            SELECT min(led.proc - d.inv) AS min_gap
            FROM   d
            JOIN   led ON d.y = led.year
        """,
    ).pl()
    _checks.append({
        "check": "deduped invoices vs ledger procurement, every year",
        "expected": "short by the missing invoices (flag, don't fix)",
        "observed": f"every year short; smallest gap €{float(_p['min_gap'][0]):,.2f}",
        "verdict": "PASS" if float(_p["min_gap"][0]) > 0 else "FAIL",
    })
    _rf = con.sql(
        query = """
            SELECT count(*) FILTER (WHERE qty < 0 AND ref_receipt_id IS NOT NULL
                       AND ref_receipt_id NOT IN (
                           SELECT receipt_id FROM receipts WHERE qty > 0)) AS orphans
            FROM   receipts
        """,
    ).pl()
    _checks.append({
        "check": "refund referential integrity (incl. cross-year refunds)",
        "expected": "0 orphans",
        "observed": f"{int(_rf['orphans'][0])} orphans",
        "verdict": "PASS" if int(_rf["orphans"][0]) == 0 else "FAIL",
    })
    _v = con.sql(
        query = """
            WITH cat AS (SELECT uid, category FROM products),
            vout AS (
                SELECT sum(r.qty * r.unit_price *
                    CASE WHEN c.category IN ('Alcoholic Beverages',
                         'Household and Cleaning Supplies', 'Personal Care and Health')
                         THEN 0.2 / 1.2 ELSE 0.1 / 1.1 END)::DOUBLE AS v
                FROM   receipts r
                JOIN   cat c USING (uid)
            ),
            vin AS (
                SELECT sum(p.qty * p.unit_cost *
                    CASE WHEN c.category IN ('Alcoholic Beverages',
                         'Household and Cleaning Supplies', 'Personal Care and Health')
                         THEN 0.2 / 1.2 ELSE 0.1 / 1.1 END)::DOUBLE AS v
                FROM   procurement p
                JOIN   cat c USING (uid)
            )
            SELECT (SELECT v FROM vout) - (SELECT v FROM vin)
                   - (SELECT sum(vat) FROM cost_sheet_raw)::DOUBLE AS gap
        """,
    ).pl()
    _checks.append({
        "check": "VAT recomputed from rate map vs remitted",
        "expected": "within invoice rounding + the missing invoices' input VAT",
        "observed": f"gap €{float(_v['gap'][0]):,.2f} over three years",
        "verdict": "PASS" if abs(float(_v["gap"][0])) < 250 else "FAIL",
    })
    # the capital columns make the till fully auditable: the cash walk
    # (cash, credit, draws, capex, tax payments) must close every month
    _cs = con.sql(query = "SELECT * FROM cost_sheet_raw ORDER BY year, month").pl()
    _flow = (_cs["revenue"] - _cs["procurement"] - _cs["rent"] - _cs["wages"]
             - _cs["payroll_tax"] - _cs["utilities"] - _cs["storage"]
             - _cs["flyers"] - _cs["vat"] - _cs["credit_interest"]
             - _cs["repairs"] - _cs["owner_draw"] - _cs["capex"]
             - _cs["profit_tax_paid"])
    _pred = _cs["cash"].shift(1) + _flow + (_cs["credit_balance"] - _cs["credit_balance"].shift(1))
    _walk_gap = float((_cs["cash"] - _pred).abs().max())
    _checks.append({
        "check": "the cash walk (incl. draws, capex, January tax) closes month over month",
        "expected": "closes to the cent, 35 transitions",
        "observed": f"worst monthly gap €{_walk_gap:.4f}",
        "verdict": "PASS" if _walk_gap < 0.01 else "FAIL",
    })
    _ts = con.sql(
        query = """
            SELECT max(abs(c.v - t.vat_remitted)) AS gap
            FROM   (SELECT year, sum(vat)::DOUBLE v FROM cost_sheet_raw GROUP BY 1) c
            JOIN   tax_statement_raw t USING (year)
        """,
    ).pl()
    _checks.append({
        "check": "tax statements vs ledger (VAT line), every year",
        "expected": "closes exactly",
        "observed": f"worst gap €{float(_ts['gap'][0]):.4f}",
        "verdict": "PASS" if float(_ts["gap"][0]) < 0.01 else "FAIL",
    })
    contract = pl.DataFrame(_checks)
    _all_pass = bool((contract["verdict"] == "PASS").all())
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 0.7 · The reconciliation contract, run end to end

    ACCOUNTING §9 promises exactly which totals tie after cleaning and
    which gaps are *supposed* to remain — including, on this horizon, the
    two documented dedup false positives (kept whole after §0.1's residue
    hunt) and the capital columns' cash walk. Running the contract:
    **{'every check passes' if _all_pass else 'FAILURES — investigate'}**.
    """
            ),
            mo.ui.table(
                data = contract,
                selection = None,
            ),
            mo.md(
                """
    With the contract green, everything below runs on the cleaned views —
    and nothing below needs to think about defects again. That is the
    whole point of doing Layer 0 first.
    """
            ),
        ],
    )
    return


@app.cell
def _(grade_01, mo, pl, truth):
    # ==== the Layer 0 scorecard ==============================================
    scorecard = pl.DataFrame([
        {
            "defect family": "duplicate receipt uploads",
            "rule": "all-even multiplicities + residue hunt",
            "precision": f"{grade_01['precision']:.1%} raw → 100% after the residue hunt",
            "recall": f"{grade_01['recall']:.0%}",
        },
        {
            "defect family": "voided mis-rings",
            "rule": "negative line without ref_receipt_id",
            "precision": "100%",
            "recall": "100%",
        },
        {
            "defect family": "duplicate invoice postings",
            "rule": "exact-key duplicates",
            "precision": "100%",
            "recall": "100%",
        },
        {
            "defect family": "snapshot typos",
            "rule": "cancelling next-day residual pairs",
            "precision": "100%",
            "recall": "100%",
        },
        {
            "defect family": "labels / clock / sensor / spelling",
            "rule": "normalization inventory (0.6)",
            "precision": "exact counts",
            "recall": "exact counts",
        },
        {
            "defect family": "missing invoices",
            "rule": "unlocatable — per-year € gap flagged",
            "precision": "n/a",
            "recall": "0% by design",
        },
        {
            "defect family": "unlogged tosses",
            "rule": "unlocatable — absorbed by stock counts",
            "precision": "n/a",
            "recall": "0% by design",
        },
    ])
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## The Layer 0 scorecard

    {len(truth)} defects were injected across ten families and three
    binders; the rules above find every locatable one (the per-section
    grading panels hold the exact counts):
    """
            ),
            mo.ui.table(
                data = scorecard,
                selection = None,
            ),
            mo.md(
                """
    Two honest asterisks. First, the flagship dedup rule is *not* perfect
    out of the box — its two false positives are the most instructive rows
    in the whole layer, because the residue hunt both detects and locates
    them from visible data alone before the answer key ever confirms them.
    Second, two families are invisible by construction — a delivery never
    typed in and a bin-bag never logged leave no row to find, only
    aggregate traces. Real cleaning has the same asymmetry: you can
    deduplicate what is there twice, but you cannot conjure what was never
    recorded.
    """
            ),
        ],
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    # Layer 1 — describe the business (on the cleaned views only)

    Eight questions, phrased the way the owner would ask them, now with
    three years of cleaned history to answer from. Everything here is
    *descriptive* — what the years looked like, not yet why (Layer 2's
    job) and not the three-year causal stories themselves (the discounter,
    the expansion — those live in the Layer 7 trio). Where a description
    is gradeable against the world's hidden mechanics, a grading panel
    says how close it lands.
    """)
    return


@app.cell
def _(MUTED, WARN, caption, con, go, hide_value_axis, mo, style, takeaway):
    # ==== 1.1 — where does the money come from and go? ======================
    _f = con.sql(
        query = """
            SELECT sum(revenue)::DOUBLE                    AS revenue,
                   sum(procurement)::DOUBLE                AS procurement,
                   sum(rent)::DOUBLE                       AS rent,
                   sum(wages + payroll_tax)::DOUBLE        AS labor,
                   sum(utilities + storage + flyers
                       + credit_interest + repairs)::DOUBLE AS running,
                   sum(vat)::DOUBLE                        AS vat
            FROM   cost_sheet_raw
        """,
    ).pl()
    _rev = float(_f["revenue"][0])
    _result = _rev - float(_f["procurement"][0]) - float(_f["rent"][0]) \
        - float(_f["labor"][0]) - float(_f["running"][0]) - float(_f["vat"][0])
    _steps = [
        ("revenue", _rev, "absolute"),
        ("goods bought", -float(_f["procurement"][0]), "relative"),
        ("rent", -float(_f["rent"][0]), "relative"),
        ("labor (from Nov 2026)", -float(_f["labor"][0]), "relative"),
        ("utilities & running", -float(_f["running"][0]), "relative"),
        ("VAT remitted", -float(_f["vat"][0]), "relative"),
        ("operating result", 0.0, "total"),
    ]
    _texts = [f"{_s[1] / 1000:+,.0f}k" for _s in _steps[:-1]] + [f"{_result / 1000:,.0f}k"]
    _fig = go.Figure(go.Waterfall(
        x = [_s[0] for _s in _steps],
        y = [_s[1] for _s in _steps],
        measure = [_s[2] for _s in _steps],
        text = _texts,
        textposition = "outside",
        connector = dict(line = dict(color = MUTED, width = 1)),
        increasing = dict(marker = dict(color = "#5B8C5A")),
        decreasing = dict(marker = dict(color = WARN)),
        totals = dict(marker = dict(color = "#4A6FA5")),
    ))
    style(
        fig = _fig,
        title = "Three years of money, from till to bottom line (2025–2027, € thousands)",
    )
    hide_value_axis(
        fig = _fig,
        axis = "y",
        title = "€ (values on the bars)",
    )
    # a small negative floor so the outside labels under the shallow cost
    # bars never collide with the axis line (the axis itself is hidden)
    _fig.update_yaxes(range = [-_rev * 0.07, _rev * 1.18])
    _fig.update_xaxes(title_text = "")
    takeaway(
        fig = _fig,
        text = "82 cents of every euro leave immediately for goods — and a<br>labor line now exists, carved out of what used to be the owner's",
        x = 0.98,
        y = 0.85,
        anchor = "right",
    )
    mo.vstack(
        items = [
            mo.md(
                """
    ## 1.1 · Where does the money come from and go?
    """
            ),
            _fig,
            caption(
                "The margin waterfall from the owner's ledger (which Layer "
                "0 verified to the cent, cash walk included). Groceries are "
                "a volume business: procurement dwarfs every other line, "
                "so small changes in buying or pricing move the bottom "
                "line more than any cost discipline further right. New on "
                "this horizon: a real labor line — zero for 22 months, "
                "then the expansion's clerk from November 2026 — and, "
                "outside this operating view, the capital flows the cost "
                "sheet also records (€14k capex, the owner's draws, "
                "January tax payments). The per-year arc is the sharper "
                "story: +€36.1k, +€49.9k, then −€0.5k before tax — three "
                "years that end on a knife edge (see three_year_review.py "
                "for why)."
            ),
        ],
    )
    return


@app.cell
def _(caption, con, go, mo, style, takeaway):
    # ==== 1.2 — when do people shop? =========================================
    _hm = con.sql(
        query = """
            SELECT dayofweek(date)            AS dow,
                   hour,
                   count(DISTINCT receipt_id) AS visits
            FROM   receipts
            WHERE  hour IS NOT NULL
              AND  qty > 0
            GROUP  BY 1, 2
            ORDER  BY 1, 2
        """,
    ).pl()
    _days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    _hours = sorted(_hm["hour"].unique().to_list())
    _z = [[0] * len(_hours) for _ in range(7)]
    for _r in _hm.iter_rows(named = True):
        _z[int(_r["dow"])][_hours.index(_r["hour"])] = _r["visits"]
    _fig = go.Figure(go.Heatmap(
        z = _z,
        x = [f"{_h}h" for _h in _hours],
        y = _days,
        colorscale = [
            [0, "#FFFFFF"],
            [1, "#2E5EAA"],
        ],
        showscale = False,
    ))
    style(
        fig = _fig,
        title = "Visits by day of week and hour of day, three years pooled (darker = busier)",
    )
    # the shared style caps y ticks at five, which would drop day labels
    _fig.update_yaxes(
        autorange = "reversed",
        nticks = 8,
    )
    _fig.update_xaxes(title_text = "")
    takeaway(
        fig = _fig,
        text = "two different shops: weekday evenings vs. weekend late mornings — plus new edge hours after the expansion",
        x = 0.02,
        y = 1.12,
    )
    mo.vstack(
        items = [
            mo.md(
                """
    ## 1.2 · When do people shop?
    """
            ),
            _fig,
            caption(
                "Weekdays peak at 17–19h (the after-work run); Saturday "
                "and Sunday peak at 10–12h and carry the heaviest cells. "
                "The pale 7h and 20h columns are not quiet hours — they "
                "are hours that only EXISTED for the final fourteen "
                "months, after the November 2026 expansion extended "
                "opening to 07–21; pooling three years dilutes them. Two "
                "traps for Layer 2: these rhythms are SCHEDULE "
                "COMPOSITION (who is free to shop when), not day "
                "preferences; and any hour-level comparison across years "
                "must handle the changing opening window. Hour-0 receipts "
                "(the clock glitch) are already NULLed by the cleaning — "
                "before Layer 0 this chart would show a phantom midnight "
                "rush."
            ),
        ],
    )
    return


@app.cell
def _(DATA, caption, con, go, mo, np, pl, style, takeaway):
    # ==== 1.3 — what sells when? =============================================
    _cm = con.sql(
        query = """
            SELECT p.category,
                   month(r.date)      AS m,
                   sum(r.qty)::DOUBLE AS units
            FROM   receipts r
            JOIN   products p USING (uid)
            WHERE  r.qty > 0
            GROUP  BY 1, 2
        """,
    ).pl()
    _idx = _cm.with_columns(
        (pl.col("units") / pl.col("units").mean().over("category")).alias("index"),
    )
    _cats = sorted(_idx["category"].unique().to_list())
    _z = []
    for _c in _cats:
        _row = _idx.filter(pl.col("category") == _c).sort(by = "m")
        _z.append(_row["index"].to_list())
    _fig = go.Figure(go.Heatmap(
        z = _z,
        x = list(range(1, 13)),
        y = [_c.replace(" and ", " & ") for _c in _cats],
        colorscale = [
            [0.0, "#2E5EAA"],
            [0.5, "#FFFFFF"],
            [1.0, "#B44646"],
        ],
        zmid = 1.0,
        showscale = False,
    ))
    style(
        fig = _fig,
        title = "Monthly sales index by category, averaged over three years (red = above own average)",
    )
    _fig.update_layout(height = 460)
    _fig.update_yaxes(
        autorange = "reversed",
        nticks = len(_cats) + 1,
        tickfont = dict(size = 11),
    )
    _fig.update_xaxes(
        title_text = "month of the year",
        tickvals = list(range(1, 13)),
    )
    takeaway(
        fig = _fig,
        text = "with three summers on record, the seasonal stories are no longer one-offs",
        x = 0.02,
        y = 1.10,
    )
    # grade: correlate each category's estimated index with the true modifier
    _mods = pl.read_csv(source = DATA / "scenarios" / "3y_baseline" / "hidden" / "demand_modifiers.csv")
    _cal = con.sql(query = "SELECT date FROM calendar_raw ORDER BY date").pl()
    _mods = _mods.with_columns(_cal["date"].alias("date")).with_columns(
        pl.col("date").dt.month().alias("m"),
    )
    _rows = []
    for _c in _cats:
        _true_m = _mods.group_by("m").agg(pl.col(f"M_{_c}").mean().alias("truth")).sort(by = "m")
        _est_m = _idx.filter(pl.col("category") == _c).sort(by = "m")
        if len(_est_m) == 12:
            _t = _true_m["truth"].to_numpy()
            # the placebo's true modifier is CONSTANT — a correlation with
            # it is undefined, which is itself the right answer
            if float(_t.std()) < 1e-9:
                _rows.append({
                    "category": _c,
                    "corr_with_true_modifier": None,
                })
            else:
                _r = float(np.corrcoef(
                    _est_m["index"].to_numpy(),
                    _t,
                )[0, 1])
                _rows.append({
                    "category": _c,
                    "corr_with_true_modifier": round(_r, 2),
                })
    season_grade = pl.DataFrame(_rows).sort(
        by = "corr_with_true_modifier",
        descending = True,
        nulls_last = True,
    )
    mo.vstack(
        items = [
            mo.md(
                """
    ## 1.3 · What sells when?
    """
            ),
            _fig,
            caption(
                "Each row is one category's monthly units across all three "
                "years, rescaled so its own average equals 1.0 — red "
                "months run hot. Averaging three years does what one year "
                "never could: a pattern that repeats every summer is "
                "season, not luck. Two traps still hide here. The January "
                "cold-start artifact — the shop opened January 1, 2025, "
                "and every household spent that first month filling its "
                "pantry — survives at one-third strength (one January of "
                "three), still tinting the slow-replenishing categories. "
                "And the aggregation trap: Frozen Foods looks mild because "
                "ice cream (strongly summer) and the rest of the freezer "
                "(mildly winter) cancel inside the category total — "
                "product-type detail recovers it. What survives both "
                "traps: beverages own every summer, and the 2026 heatwave "
                "made that one hotter than its neighbors."
            ),
            mo.accordion(
                items = {
                    "Grading: estimated seasonality vs. the true demand modifiers": mo.vstack(
                        items = [
                            mo.ui.table(
                                data = season_grade,
                                selection = None,
                            ),
                            mo.md(
                                """
    Correlation between each category's *estimated* monthly index (36
    months pooled by calendar month) and the *scripted* demand modifier
    it tries to recover, averaged the same way. Three years of pooling
    lifts the strongly seasonal categories toward 1.0 and steadies the
    weak ones — the single-year version of this table was visibly
    noisier. The placebo (Household & Cleaning) shows no value at all
    because its true modifier is a constant — a correlation with a
    constant is undefined, and an estimate near 1.0 in every month is
    exactly what recovering "no seasonality" looks like.
    """
                            ),
                        ],
                    ),
                },
            ),
        ],
    )
    return


@app.cell
def _(
    ACCENT,
    ACCENT_LIGHT,
    caption,
    con,
    make_subplots,
    mo,
    style,
    takeaway,
):
    # ==== 1.4 — what does a basket look like? ================================
    _b = con.sql(
        query = """
            SELECT receipt_id,
                   sum(qty * unit_price)::DOUBLE AS value,
                   sum(qty)::DOUBLE              AS units
            FROM   receipts
            WHERE  qty > 0
              AND  ref_receipt_id IS NULL
            GROUP  BY 1
        """,
    ).pl()
    basket_stats = {
        "n": len(_b),
        "med_value": float(_b["value"].median()),
        "med_units": float(_b["units"].median()),
        "p90_value": float(_b["value"].quantile(quantile = 0.9)),
    }
    _fig = make_subplots(
        rows = 1,
        cols = 2,
        subplot_titles = (
            "Distribution of basket value (€ per receipt)",
            "Distribution of basket size (units per receipt)",
        ),
        horizontal_spacing = 0.12,
    )
    _fig.add_histogram(
        x = _b["value"].to_list(),
        xbins = dict(
            start = 0,
            end = 150,
            size = 5,
        ),
        marker_color = ACCENT,
        row = 1,
        col = 1,
    )
    _fig.add_histogram(
        x = _b["units"].to_list(),
        xbins = dict(
            start = 0,
            end = 30,
            size = 1,
        ),
        marker_color = ACCENT_LIGHT,
        row = 1,
        col = 2,
    )
    style(
        fig = _fig,
        title = "The anatomy of a shopping trip, three years pooled",
        n_subplot_titles = 2,
    )
    _fig.update_yaxes(
        title_text = "receipts",
        row = 1,
        col = 1,
    )
    _fig.update_yaxes(
        title_text = "receipts",
        row = 1,
        col = 2,
    )
    _fig.update_xaxes(
        title_text = "€ (clipped at 150)",
        row = 1,
        col = 1,
    )
    _fig.update_xaxes(
        title_text = "units (clipped at 30)",
        row = 1,
        col = 2,
    )
    takeaway(
        fig = _fig,
        text = f"the typical trip: ~€{basket_stats['med_value']:.0f}, ~{basket_stats['med_units']:.0f} items — plus a long tail of stock-up hauls",
        x = 0.98,
        y = 0.98,
        anchor = "right",
        row = 1,
        col = 1,
    )
    takeaway(
        fig = _fig,
        text = "no artificial spike at any quantity",
        x = 0.98,
        y = 0.98,
        anchor = "right",
        row = 1,
        col = 2,
    )
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 1.4 · What does a basket look like?

    {basket_stats['n']:,} shopping trips over three years. The median
    basket is **€{basket_stats['med_value']:.2f}** and
    **{basket_stats['med_units']:.0f} units**; one trip in ten tops
    €{basket_stats['p90_value']:.0f} — the weekend stock-up runs that
    anchor the weekly rhythm of §1.2.
    """
            ),
            _fig,
            caption(
                "Both distributions are right-skewed with smooth tails — "
                "the two-population blend of quick top-ups (a few items, "
                "under €20) and primary weekly shops (€40–120). Basket "
                "size decays smoothly with no preferred quantity, and "
                "roughly one visit in twenty carries one extra unplanned "
                "line (the impulse mechanism, P3 §4) — too small a signal "
                "to isolate descriptively, which is exactly why it waits "
                "for Layer 6's structural tools. The shape is stable "
                "across all three years: what changed over time is who "
                "shops (§1.5) and when (§1.2), not how a basket is built."
            ),
        ],
    )
    return


@app.cell
def _(DATA, MUTED, caption, con, go, hide_value_axis, mo, pl, style, takeaway):
    # ==== 1.5 — who are the customers? =======================================
    _seg = con.sql(
        query = """
            WITH per_token AS (
                SELECT customer_id,
                       count(DISTINCT receipt_id)    AS visits,
                       sum(qty * unit_price)::DOUBLE AS spend
                FROM   receipts
                WHERE  customer_id IS NOT NULL
                  AND  qty > 0
                  AND  ref_receipt_id IS NULL
                GROUP  BY 1
            )
            SELECT CASE WHEN visits >= 10 THEN 'regulars (card, 10+ visits)'
                        ELSE 'occasional cards (guests & rare visitors)' END AS who,
                   count(*)                    AS identities,
                   sum(spend)::DOUBLE          AS revenue
            FROM   per_token
            GROUP  BY 1
        """,
    ).pl()
    _cash = con.sql(
        query = """
            SELECT 'anonymous cash'              AS who,
                   count(DISTINCT receipt_id)    AS identities,
                   sum(qty * unit_price)::DOUBLE AS revenue
            FROM   receipts
            WHERE  customer_id IS NULL
              AND  qty > 0
              AND  ref_receipt_id IS NULL
        """,
    ).pl()
    _mix = pl.concat(items = [
        _seg,
        _cash.with_columns(pl.col("identities").cast(pl.Int64)),
    ]).sort(by = "revenue", descending = True)
    _tot = float(_mix["revenue"].sum())
    _n_regs = int(_mix.filter(pl.col("who") == "regulars (card, 10+ visits)")["identities"][0])
    _true_guest = pl.read_csv(source = DATA / "scenarios" / "3y_baseline" / "hidden" / "guests.csv")
    guest_grade = {
        "visible_est": float(_mix.filter(
            pl.col("who") == "occasional cards (guests & rare visitors)"
        )["revenue"][0]),
        "truth": float(_true_guest["value"].sum()),
    }
    _fig = go.Figure()
    _fig.add_bar(
        x = _mix["revenue"].to_list(),
        y = _mix["who"].to_list(),
        orientation = "h",
        marker_color = [
            "#4A6FA5",
            MUTED,
            "#9DB8E6",
        ],
        text = [f"€{_v / 1000:,.0f}k ({_v / _tot:.0%})" for _v in _mix["revenue"]],
        textposition = "outside",
    )
    style(
        fig = _fig,
        title = "Who three years of revenue actually came from",
    )
    hide_value_axis(
        fig = _fig,
        axis = "x",
        title = "revenue (€, share of total)",
    )
    _fig.update_yaxes(
        title_text = "",
        nticks = 4,
    )
    _fig.update_xaxes(range = [0, _tot * 0.75])
    takeaway(
        fig = _fig,
        text = "a few hundred households ARE the business —<br>cash and passing trade fill the gaps",
        x = 0.97,
        y = 0.97,
        anchor = "right",
    )
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 1.5 · Who are the customers?

    Only card transactions carry an identity, so the panel splits three
    ways: **{_n_regs} identifiable regulars** (ever seen across the three
    years), identifiable-but-rare card users (mostly one-off passing
    trade), and **anonymous cash** — visible as money, invisible as
    people.
    """
            ),
            _fig,
            caption(
                "The regulars carry the majority of revenue — but on this "
                "horizon 'the regulars' is a FLOW, not a fixed club: "
                "households moved away and were replaced all three years, "
                "the apartment block added a cohort in late 2026, and the "
                "identity count here (everyone ever seen) overstates the "
                "headcount present in any given month by a fifth. Reading "
                "loyalty metrics without that survivorship lens is the "
                "planted trap, and unpicking it — cohorts, retention "
                "curves, churn graded against the answer key — is "
                "three_year_review.py §7's whole job. The other honest "
                "limitation stands too: a third of revenue has no "
                "identity, and 'customer analytics' silently assumes card "
                "behavior represents cash behavior (testable, and tested, "
                "in Layer 2's question 2.8)."
            ),
            mo.accordion(
                items = {
                    "Grading: how much business is passing trade?": mo.md(
                        f"""
    The visible ingredient: revenue on rare card identities (under ten
    visits in three years) = **€{guest_grade['visible_est']:,.0f}**. The
    answer key's guest ledger records **€{guest_grade['truth']:,.0f}** of
    true guest revenue across card *and* cash — the visible rare-token
    slice captures roughly the card share of it, and the rest hides
    inside the anonymous-cash bar, unrecoverable descriptively. Splitting
    it properly is Layer 6's mixture-model question (6.5).
    """
                    ),
                },
            ),
        ],
    )
    return


@app.cell
def _(
    ACCENT,
    ACCENT_LIGHT,
    MUTED,
    caption,
    con,
    make_subplots,
    mo,
    pl,
    style,
    takeaway,
):
    # ==== 1.6 — how are prices architected? ==================================
    _end = con.sql(
        query = """
            SELECT (round(price * 100)::INT % 10) AS cents,
                   count(*)                       AS n
            FROM   price_history_raw
            GROUP  BY 1
            ORDER  BY 2 DESC
        """,
    ).pl()
    # changes per SKU per YEAR (the 2025 rows include the opening tag, which
    # is not a change); zero-change SKU-years must be counted too
    _chg = con.sql(
        query = """
            WITH grid AS (
                SELECT DISTINCT ph.uid,
                       y.y
                FROM   price_history_raw ph
                CROSS  JOIN (SELECT unnest([2025, 2026, 2027]) AS y) y
            ),
            actual AS (
                SELECT uid,
                       year(date) AS y,
                       count(*) - CASE WHEN year(date) = 2025 THEN 1 ELSE 0 END AS changes
                FROM   price_history_raw
                GROUP  BY 1, 2
            )
            SELECT g.uid,
                   g.y,
                   coalesce(a.changes, 0) AS changes
            FROM   grid g
            LEFT   JOIN actual a ON g.uid = a.uid AND g.y = a.y
        """,
    ).pl()
    _depths = con.sql(
        query = """
            SELECT depth,
                   count(*)            AS campaigns,
                   min(year(start_date)) AS first_year,
                   max(year(start_date)) AS last_year
            FROM   promotions
            GROUP  BY 1
            ORDER  BY 1
        """,
    ).pl()
    price_stats = {
        "p9": float(_end.filter(pl.col("cents") == 9)["n"].sum() / _end["n"].sum()),
        "med_chg": float(_chg["changes"].median()),
        "p90_chg": float(_chg["changes"].quantile(quantile = 0.9)),
        "n_campaigns": int(_depths["campaigns"].sum()),
    }
    _fig = make_subplots(
        rows = 1,
        cols = 2,
        subplot_titles = (
            "What the last digit of a shelf tag looks like",
            "How often a product's tag changed, per year",
        ),
        horizontal_spacing = 0.14,
    )
    _end_s = _end.sort(by = "cents")
    _fig.add_bar(
        x = [f".x{_c}" for _c in _end_s["cents"]],
        y = _end_s["n"].to_list(),
        marker_color = [
            ACCENT if _c == 9 else MUTED
            for _c in _end_s["cents"]
        ],
        text = [f"{_n / _end['n'].sum():.0%}" for _n in _end_s["n"]],
        textposition = "outside",
        row = 1,
        col = 1,
    )
    _hist = _chg.group_by("changes").agg(pl.len().alias("n")).sort(by = "changes")
    _fig.add_bar(
        x = _hist["changes"].to_list(),
        y = _hist["n"].to_list(),
        marker_color = ACCENT_LIGHT,
        row = 1,
        col = 2,
    )
    style(
        fig = _fig,
        title = "The price book has habits: charm endings and a sticky hand",
        n_subplot_titles = 2,
    )
    _fig.update_yaxes(
        showticklabels = False,
        showline = False,
        ticks = "",
        title_text = "tag observations",
        title_font = dict(
            size = 11.5,
            color = MUTED,
        ),
        range = [0, float(_end["n"].max()) * 1.3],
        row = 1,
        col = 1,
    )
    _fig.update_yaxes(
        title_text = "SKU-years",
        row = 1,
        col = 2,
    )
    _fig.update_xaxes(
        title_text = "cents digit of the tag",
        row = 1,
        col = 1,
    )
    _fig.update_xaxes(
        title_text = "price changes in a year",
        row = 1,
        col = 2,
    )
    takeaway(
        fig = _fig,
        text = "psychological pricing: .x9 dominates",
        x = 0.98,
        y = 0.98,
        anchor = "right",
        row = 1,
        col = 1,
    )
    takeaway(
        fig = _fig,
        text = f"median {price_stats['med_chg']:.0f} changes a year, every year — the policy never wavered",
        x = 0.98,
        y = 0.98,
        anchor = "right",
        row = 1,
        col = 2,
    )
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 1.6 · How are prices architected?

    Three habits define the price book across all three years: **charm
    endings** ({price_stats['p9']:.0%} of tags end in 9), **stickiness**
    (the median product repriced {price_stats['med_chg']:.0f} times a
    year; the 90th percentile {price_stats['p90_chg']:.0f}), and a
    **small markdown menu** — {price_stats['n_campaigns']} campaigns at
    depths of {', '.join(f"{d:.0%}" for d in _depths['depth'])} — with one
    striking wrinkle: **every markdown campaign the shop ever ran sits in
    2025.**
    """
            ),
            _fig,
            caption(
                "Left: the tag-ending mix — mostly .x9 with real .x5 and "
                ".x0 minorities, per-product habits rather than a uniform "
                "rule. Right: reprice counts per SKU-year; tags move only "
                "on delivery days and only when the underlying cost trend "
                "has drifted enough to bother (menu-cost behavior — Layer "
                "2's pass-through question), and the distribution is the "
                "same in every year even as costs inflated. The markdown "
                "silence after 2025 is a descriptive fact with a causal "
                "smell: campaigns fire on overstock, and once the "
                "neighborhood started growing the owner stopped "
                "over-holding — worth knowing before Layer 2 asks whether "
                "'the markdowns worked', because after year one there are "
                "none to evaluate. (The one exception to price stability "
                "is deliberate: the May 2027 competitive price cuts on "
                "three categories — competitor_entry_study.py §5.)"
            ),
        ],
    )
    return


@app.cell
def _(
    ACCENT,
    MUTED,
    WARN,
    caption,
    con,
    dt,
    make_subplots,
    mo,
    pl,
    style,
    takeaway,
):
    # ==== 1.7 — how often are shelves empty, and what rots? ==================
    _oos = con.sql(
        query = """
            SELECT date_trunc('month', date) AS m,
                   100 * avg(CASE WHEN on_hand <= 0 THEN 1.0 ELSE 0.0 END) AS oos
            FROM   inventory_eod_raw
            GROUP  BY 1
            ORDER  BY 1
        """,
    ).pl()
    _rot = con.sql(
        query = """
            SELECT p.category,
                   sum(w.units * pr.retail_base_price_EUR)::DOUBLE AS cost
            FROM   write_offs_raw w
            JOIN   products p  ON w.uid = p.uid
            JOIN   products pr ON w.uid = pr.uid
            WHERE  w.reason = 'spoilage'
            GROUP  BY 1
            ORDER  BY 2 DESC
            LIMIT  6
        """,
    ).pl()
    _fig = make_subplots(
        rows = 1,
        cols = 2,
        column_widths = [
            0.5,
            0.5,
        ],
        subplot_titles = (
            "Share of product-days with an empty shelf, monthly",
            "What the bin cost over three years, by category",
        ),
        horizontal_spacing = 0.14,
    )
    _fig.add_scatter(
        x = _oos["m"].to_list(),
        y = _oos["oos"].to_list(),
        mode = "lines+markers",
        line = dict(
            color = ACCENT,
            width = 2,
        ),
        marker = dict(size = 4),
        row = 1,
        col = 1,
    )
    _fig.add_vline(
        x = dt.date(2026, 11, 1),
        line_dash = "dash",
        line_color = MUTED,
        line_width = 1.5,
        row = 1,
        col = 1,
    )
    _fig.add_annotation(
        x = dt.date(2026, 11, 1),
        y = 0.06,
        yref = "y domain",
        text = "shelves deepened",
        showarrow = False,
        xanchor = "left",
        xshift = 6,
        font = dict(
            color = "#9A9A9A",
            size = 11,
        ),
        row = 1,
        col = 1,
    )
    _rot_s = _rot.sort(by = "cost")
    _fig.add_bar(
        x = _rot_s["cost"].to_list(),
        y = [_c.replace(" and ", " & ") for _c in _rot_s["category"]],
        orientation = "h",
        marker_color = [
            WARN if _i >= len(_rot_s) - 2 else MUTED
            for _i in range(len(_rot_s))
        ],
        text = [f"€{_v / 1000:,.1f}k" for _v in _rot_s["cost"]],
        textposition = "outside",
        row = 1,
        col = 2,
    )
    style(
        fig = _fig,
        title = "The two quiet costs: empty shelves and the bin",
        n_subplot_titles = 2,
    )
    _fig.update_yaxes(
        title_text = "% of SKU-days",
        range = [0, float(_oos["oos"].max()) * 1.35],
        row = 1,
        col = 1,
    )
    _fig.update_xaxes(
        showticklabels = False,
        showline = False,
        ticks = "",
        title_text = "write-offs at cost (€)",
        title_font = dict(
            size = 11.5,
            color = MUTED,
        ),
        range = [0, float(_rot_s["cost"].max()) * 1.35],
        row = 1,
        col = 2,
    )
    _fig.update_yaxes(
        nticks = len(_rot_s) + 1,
        automargin = True,
        row = 1,
        col = 2,
    )
    takeaway(
        fig = _fig,
        text = "empty shelves halve when the expansion deepens the shelves",
        x = 0.02,
        y = 0.99,
        row = 1,
        col = 1,
    )
    takeaway(
        fig = _fig,
        text = "short shelf life pays the bin bill",
        x = 0.98,
        y = 0.10,
        anchor = "right",
        row = 1,
        col = 2,
    )
    mo.vstack(
        items = [
            mo.md(
                """
    ## 1.7 · How often are shelves empty, and what rots?
    """
            ),
            _fig,
            caption(
                "Left: the share of product-days ending at zero book stock, "
                "across thirty-six months. The old pattern (worst in the "
                "busy season) holds until November 2026, when the "
                "expansion's 20% deeper shelves cut the empty-shelf rate "
                "roughly in half — visibly, durably, and at a price: the "
                "extra depth partly rotted, which is half of why the "
                "expansion lost money (expansion_review.py §4). Right: "
                "logged spoilage at cost over the full horizon; fresh "
                "produce and bakery dominate because their shelf lives are "
                "days, not weeks. The two panels are the same trade-off "
                "seen from both ends — order more and the bin grows, order "
                "less and the empty-shelf days grow — and pricing that "
                "trade-off properly is the prescriptive layer's "
                "centerpiece (question 4.2)."
            ),
        ],
    )
    return


@app.cell
def _(caption, con, mo, pl):
    # ==== 1.8 — how much tax does the shop handle? ===========================
    _vat = con.sql(
        query = """
            WITH cat AS (SELECT uid, category FROM products)
            SELECT CASE WHEN c.category IN ('Alcoholic Beverages',
                        'Household and Cleaning Supplies', 'Personal Care and Health')
                        THEN 'standard rate (20%)'
                        ELSE 'reduced rate (10%)' END        AS rate_group,
                   round(sum(r.qty * r.unit_price), 0)       AS gross_sales,
                   round(sum(r.qty * r.unit_price *
                       CASE WHEN c.category IN ('Alcoholic Beverages',
                            'Household and Cleaning Supplies', 'Personal Care and Health')
                            THEN 0.2 / 1.2 ELSE 0.1 / 1.1 END), 0) AS output_vat
            FROM   receipts r
            JOIN   cat c USING (uid)
            GROUP  BY 1
        """,
    ).pl().with_columns(
        (100 * pl.col("output_vat") / pl.col("gross_sales")).round(2).alias("effective_rate_pct"),
    )
    _stmt = con.sql(query = "SELECT * FROM tax_statement_raw ORDER BY year").pl()
    _rem = float(_stmt["vat_remitted"].sum())
    _rev = float(con.sql(query = "SELECT sum(revenue) FROM cost_sheet_raw").pl().to_series()[0])
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 1.8 · How much tax does the shop handle?

    Every shelf price is **gross of VAT**: the shop collects the tax at
    the till, deducts what it paid suppliers, and remits the difference
    monthly — **€{_rem:,.0f}** over three years, about
    {_rem / _rev:.1%} of revenue. Because food carries the reduced rate
    and only three non-food categories the standard one, the blended
    effective rate sits much closer to 10% than 20%:
    """
            ),
            mo.ui.table(
                data = _vat,
                selection = None,
            ),
            mo.ui.table(
                data = _stmt.with_columns(
                    pl.col("vat_remitted").round(0),
                    pl.col("payroll_tax").round(0),
                    pl.col("profit_before_tax").round(0),
                    pl.col("profit_tax").round(0),
                    pl.col("profit_after_tax").round(0),
                ),
                selection = None,
            ),
            caption(
                "Top: output VAT by rate group, recomputed from the "
                "cleaned till at the statutory rate map — §0.7 verified "
                "the recomputation ties to the remitted line within "
                "rounding plus the missing invoices' input VAT. Bottom: "
                "the three annual statements, which on this horizon are "
                "cash-real — each year's profit tax actually left the "
                "till the following January (the cash walk in §0.7 "
                "includes it), payroll tax appears the moment the first "
                "clerk does, and the three bottom lines trace the arc the "
                "whole dataset is built around: prove, grow, squeeze."
            ),
        ],
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## Where this leaves us

    **Layer 0 verdict:** every locatable defect family is found across
    all three binders; the flagship dedup rule's two false positives are
    detected, located, and corrected *from visible data alone* before the
    answer key confirms them; the two unlocatable families are correctly
    flagged as aggregate gaps; and the reconciliation contract — now
    including the capital columns' month-by-month cash walk — passes end
    to end. The cleaned views are safe to build on.

    **Layer 1 verdict:** a €2.3M-over-three-years, 18%-margin grocery
    that grew every year, hired its first clerk, and ended on a knife
    edge; a two-regime week that gained two edge hours; seasonality now
    certified by repetition (with the January cold-start artifact
    diluted but alive); a customer base that is a flow, not a club; a
    price book whose habits never wavered while its markdown machinery
    fell silent after year one; and the empty-shelf/bin trade-off
    visibly reshaped by the expansion.

    Every "why" question raised here is deliberately left open: weather
    and the three cost-shock episodes (2.1–2.3), what price changes do to
    customers (2.4–2.5), the 2025 markdowns (2.6), and whether card data
    speaks for cash (2.8) — that is **Layer 2**, the next notebook in the
    series, now with three years of statistical power behind it.

    ---
    ### Appendix — method notes

    Data: `data/scenarios/3y_baseline/visible/` raw files — the project's
    analysis baseline; the cleaning is built inside this notebook
    (§0.1–0.6) and proven in §0.7 before any description runs. Grading
    panels read `hidden/imperfections.csv`, `hidden/demand_modifiers.csv`,
    and `hidden/guests.csv` — the answer keys an analyst would not have —
    and nothing outside those panels depends on them. The three-year
    causal stories (churn, the discounter, the expansion) are cross-
    referenced, not re-derived: they live in `three_year_review.py`,
    `competitor_entry_study.py`, and `expansion_review.py`. Tools: DuckDB,
    Polars, Plotly.
    """)
    return


if __name__ == "__main__":
    app.run()
