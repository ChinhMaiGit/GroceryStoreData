import marimo

__generated_with = "0.23.14"
app = marimo.App(width="full", app_title="Layer 3 — Predict and Warn")


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

    ROOT = Path(__file__).resolve().parent.parent
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

    def stars(p):
        return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""

    return (
        ACCENT,
        ACCENT_LIGHT,
        DATA,
        MUTED,
        ROOT,
        WARN,
        caption,
        duckdb,
        go,
        mo,
        np,
        pl,
        stars,
        style,
        takeaway,
    )


@app.cell
def _(mo):
    mo.md(r"""
    # Layer 3: predict — and warn

    Layer 2 established what *causes* what; this notebook asks what can be
    **seen coming** — the catalog's Layer 3 (questions 3.1–3.5) on the
    analysis baseline, `data/scenarios/3y_baseline/`. Five investigations:

    1. **What will next week sell?** (3.1) Three forecasters compete —
       the owner's own trailing-average rule, a seasonal-naive benchmark,
       and a gradient-boosted model — judged on a true holdout year
       (2027), at the grain where the money is decided: **weekly units per
       category**, the quantity the Wednesday order actually needs.
    2. **What would demand be if shelves never emptied?** (3.2) Sales are
       a *censored* record of demand: an empty shelf records a zero that
       was really a customer. Impute what the stockouts hid, and grade the
       imputation against the hidden ledger of unmet demand.
    3. **How wrong is the owner's own forecast — and why?** (3.3) The
       autopsy of Henrik's order sheet: his rule forecasts *sales*, sales
       are capped by his own orders, and the loop quietly teaches him to
       under-order exactly when demand peaks.
    4. **Which shelves will be empty next week?** (3.4) A stockout-risk
       model an owner could actually run, evaluated out of sample.
    5. **Which regulars are sliding into trouble?** (3.5) An early-warning
       screen for sustained down-trading, graded against the hidden record
       of genuine household budget squeezes.

    Machine-learning models are reported with the same discipline as
    regressions: objective, features, split, evaluation table, and
    importances — no black boxes with unexamined verdicts.
    """)
    return


@app.cell
def _(DATA, ROOT, duckdb, pl):
    # ---- cleaned views (the Layer 0 contract, applied) ----------------------
    con = duckdb.connect()
    _vis = DATA / "scenarios" / "3y_baseline" / "visible"
    for _name in ["receipts", "procurement", "inventory_eod", "calendar", "weather"]:
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
    con.execute(
        query = """
            CREATE VIEW receipts AS
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
    # the weekly category panel every section below builds on: week = the
    # calendar-aligned index the shop itself plans by (Monday order cycle)
    wk_panel = con.sql(
        query = """
            SELECT p.category,
                   cast(least(155, datediff('day', DATE '2025-01-01', r.date) / 7) AS INT) AS w,
                   min(r.date)        AS wk_start,
                   sum(r.qty)::DOUBLE AS units
            FROM   receipts r
            JOIN   products p USING (uid)
            WHERE  r.qty > 0
              AND  r.ref_receipt_id IS NULL
            GROUP  BY 1, 2
            ORDER  BY 1, 2
        """,
    ).pl()
    return con, wk_panel


@app.cell
def _(np, pl, wk_panel):
    # ==== 3.1 — what will next week sell? =====================================
    from sklearn.ensemble import HistGradientBoostingRegressor as _HGB
    from sklearn.inspection import permutation_importance as _perm

    # one-week-ahead forecasts of weekly units per category, all of 2027
    # (weeks 105..155) as the untouched holdout
    _cats = sorted(wk_panel["category"].unique().to_list())
    _full = pl.DataFrame({
        "category": [_c for _c in _cats for _ in range(156)],
        "w": [_w for _ in _cats for _w in range(156)],
    }).join(
        other = wk_panel.select([
            "category",
            "w",
            "units",
        ]),
        on = [
            "category",
            "w",
        ],
        how = "left",
    ).with_columns(pl.col("units").fill_null(value = 0.0)).sort(by = ["category", "w"])
    _full = _full.with_columns(
        pl.col("units").shift(1).over("category").alias("lag1"),
        pl.col("units").shift(2).over("category").alias("lag2"),
        pl.col("units").shift(4).over("category").alias("lag4"),
        pl.col("units").shift(52).over("category").alias("lag52"),
        pl.col("units").shift(1).rolling_mean(window_size = 4).over("category").alias("ma4"),
        (pl.col("w") % 52).alias("woy"),
    ).with_columns(
        (2 * np.pi * pl.col("woy") / 52).sin().alias("s1"),
        (2 * np.pi * pl.col("woy") / 52).cos().alias("c1"),
        pl.col("category").cast(pl.Categorical).to_physical().alias("cat_id"),
    ).drop_nulls()
    _test_mask = _full["w"] >= 105
    _feat = [
        "lag1",
        "lag2",
        "lag4",
        "lag52",
        "ma4",
        "s1",
        "c1",
        "cat_id",
    ]
    _Xtr = _full.filter(~_test_mask)[_feat].to_numpy()
    _ytr = _full.filter(~_test_mask)["units"].to_numpy()
    _Xte = _full.filter(_test_mask)[_feat].to_numpy()
    _te = _full.filter(_test_mask)
    _gbm = _HGB(
        max_depth = 4,
        learning_rate = 0.06,
        max_iter = 400,
        random_state = 7,
    )
    _gbm.fit(_Xtr, _ytr)
    _te = _te.with_columns(
        pl.Series(name = "gbm", values = _gbm.predict(_Xte)),
        pl.col("ma4").alias("owner_ma"),
        pl.col("lag52").alias("seasonal_naive"),
    )

    def _wmape(pred):
        return float((_te["units"] - _te[pred]).abs().sum() / _te["units"].sum())

    fc_eval = pl.DataFrame([
        {
            "forecaster": "owner's rule (trailing 4-week average)",
            "wmape_2027": round(_wmape(pred = "owner_ma"), 4),
        },
        {
            "forecaster": "seasonal naive (same week last year)",
            "wmape_2027": round(_wmape(pred = "seasonal_naive"), 4),
        },
        {
            "forecaster": "gradient boosting (lags + season + category)",
            "wmape_2027": round(_wmape(pred = "gbm"), 4),
        },
    ]).sort(by = "wmape_2027")
    # error by 2027 half: does the March regime break degrade the models?
    _te = _te.with_columns((pl.col("w") >= 131).alias("h2"))

    def _wmape_half(pred, h2):
        _s = _te.filter(pl.col("h2") == h2)
        return float((_s["units"] - _s[pred]).abs().sum() / _s["units"].sum())

    fc_halves = pl.DataFrame([
        {
            "forecaster": _n,
            "wmape_2027_H1": round(_wmape_half(pred = _p, h2 = False), 4),
            "wmape_2027_H2": round(_wmape_half(pred = _p, h2 = True), 4),
        }
        for _n, _p in [
            ("owner's rule", "owner_ma"),
            ("seasonal naive", "seasonal_naive"),
            ("gradient boosting", "gbm"),
        ]
    ])
    _pi = _perm(
        _gbm,
        _Xte,
        _te["units"].to_numpy(),
        n_repeats = 8,
        random_state = 7,
    )
    fc_importance = pl.DataFrame({
        "feature": _feat,
        "importance": [round(float(_v), 3) for _v in _pi.importances_mean],
    }).sort(by = "importance", descending = True)
    fc_stats = {
        "best": fc_eval["forecaster"][0],
        "best_w": float(fc_eval["wmape_2027"][0]),
        "owner_w": _wmape(pred = "owner_ma"),
        "naive_w": _wmape(pred = "seasonal_naive"),
        "gbm_w": _wmape(pred = "gbm"),
        "n_test": int(_te.height),
    }
    return fc_eval, fc_halves, fc_importance, fc_stats


@app.cell
def _(
    ACCENT,
    ACCENT_LIGHT,
    MUTED,
    caption,
    fc_eval,
    fc_halves,
    fc_importance,
    fc_stats,
    go,
    mo,
    style,
    takeaway,
):
    _order = [
        ("owner's rule", fc_stats["owner_w"], ACCENT),
        ("seasonal naive", fc_stats["naive_w"], MUTED),
        ("gradient boosting", fc_stats["gbm_w"], ACCENT_LIGHT),
    ]
    _fig = go.Figure()
    _fig.add_bar(
        x = [_n for _n, _, _ in _order],
        y = [100 * _v for _, _v, _ in _order],
        marker_color = [_c for _, _, _c in _order],
        text = [f"{100 * _v:.1f}%" for _, _v, _ in _order],
        textposition = "outside",
    )
    style(
        fig = _fig,
        title = "Forecasting next week's units per category: error on the untouched 2027 holdout",
    )
    _fig.update_yaxes(
        showticklabels = False,
        showline = False,
        ticks = "",
        title_text = "weighted MAPE, weekly category units (lower is better)",
        title_font = dict(
            size = 11.5,
            color = MUTED,
        ),
        range = [0, 100 * max(_v for _, _v, _ in _order) * 1.3],
    )
    _fig.update_xaxes(title_text = "")
    takeaway(
        fig = _fig,
        text = "the humbling result: at one-week horizon the owner's own<br>trailing average beats both challengers",
        x = 0.98,
        y = 0.98,
        anchor = "right",
    )
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 1 · What will next week sell? (3.1)

    **The setup.** One-week-ahead forecasts of weekly units per category —
    the exact quantity the Wednesday order requires. Train on 2025–2026,
    evaluate on all of 2027 ({fc_stats['n_test']} category-weeks never
    touched during training). Three contestants: the owner's own rule (a
    trailing 4-week average — literally what his order sheet does), a
    seasonal naive (same category-week one year earlier), and a
    gradient-boosted trees model.

    **The ML model, stated in full** — objective: squared error on weekly
    units; features: last week, two and four weeks back, the trailing
    4-week mean, the same week last year, week-of-year harmonics, and the
    category; split: strictly chronological (no leakage — every feature is
    known before the forecast week starts); tuning: shallow trees
    (depth 4), 400 rounds.
    """
            ),
            mo.ui.table(
                data = fc_eval,
                selection = None,
            ),
            _fig,
            caption(
                "Weighted MAPE (total absolute error over total units) on "
                "2027 — and the ranking is a lesson in humility: the "
                "owner's trailing 4-week average WINS at the one-week "
                "horizon, ahead of the gradient boosting model and well "
                "ahead of the seasonal naive. The mechanics are honest: "
                "weekly category demand is dominated by a slowly moving "
                "level (growth, the entry's drift, the expansion's "
                "hours), and a short adaptive average tracks a moving "
                "level better than a year-old snapshot or a model "
                "regularized across twelve heterogeneous series. The "
                "lesson is NOT that modeling is useless — it is that at "
                "short horizons, simple adaptive baselines are brutal "
                "competition, and any model must beat them before it "
                "earns a place in the Wednesday order. The owner's real "
                "forecasting problem is not accuracy at all — it is that "
                "his rule forecasts the wrong QUANTITY, which is §3's "
                "story."
            ),
            mo.accordion(
                items = {
                    "Error by 2027 half: the regime break's tax": mo.vstack(
                        items = [
                            mo.ui.table(
                                data = fc_halves,
                                selection = None,
                            ),
                            mo.md(
                                """
    A discounter opened in March 2027, and none of these models was told —
    yet the one-week-ahead errors barely show it (the halves differ by a
    point or two, in mixed directions). That non-finding is the finding:
    ONE-STEP-AHEAD forecasting adapts to a level break within a few weeks
    and quietly hides it, which is exactly why 'our forecasts still look
    fine' is no evidence that the world hasn't changed. The regime break's
    real cost lives at longer horizons — the annual plan, the lease
    decision — where an unmonitored model keeps extrapolating the old
    world (catalog question 3.6; the brief's question 7 is answered as a
    conditioned range for exactly this reason).
    """
                            ),
                        ],
                    ),
                    "Permutation importances (what the model actually uses)": mo.vstack(
                        items = [
                            mo.ui.table(
                                data = fc_importance,
                                selection = None,
                            ),
                            mo.md(
                                """
    The recent lags and the trailing mean carry most of the weight — the
    model is, at heart, a smarter version of the owner's rule that also
    knows what month it is (the year-ago lag and the seasonal harmonics
    together absorb the scripted seasonality). Nothing exotic: with 12
    series and 104 training weeks each, features beyond lags and season
    have little to teach.
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
def _(DATA, caption, con, mo, pl):
    # ==== 3.2 — what would demand be if shelves never emptied? ================
    # in-stock-days imputation: a SKU-week's demand rate is estimated from
    # the days the shelf actually had stock; the empty days then owe the
    # same rate. Book stock proxies availability (Layer 0's caveat noted).
    _sw = con.sql(
        query = """
            WITH days AS (
                SELECT uid,
                       cast(least(155, datediff('day', DATE '2025-01-01', date) / 7) AS INT) AS w,
                       count(*) FILTER (WHERE on_hand <= 0)  AS oos_days,
                       count(*)                              AS n_days
                FROM   inventory_eod_raw
                GROUP  BY 1, 2
            ),
            sales AS (
                SELECT r.uid,
                       cast(least(155, datediff('day', DATE '2025-01-01', r.date) / 7) AS INT) AS w,
                       sum(r.qty)::DOUBLE                            AS units,
                       sum(r.qty * r.unit_price) / sum(r.qty)        AS price
                FROM   receipts r
                WHERE  r.qty > 0
                  AND  r.ref_receipt_id IS NULL
                GROUP  BY 1, 2
            )
            SELECT d.uid,
                   d.w,
                   d.oos_days,
                   d.n_days,
                   coalesce(s.units, 0)  AS units,
                   s.price,
                   p.category
            FROM   days d
            LEFT   JOIN sales s USING (uid, w)
            JOIN   products p ON d.uid = p.uid
        """,
    ).pl()
    _cens = _sw.filter(
        (pl.col("oos_days") > 0) & (pl.col("oos_days") < pl.col("n_days")) & (pl.col("units") > 0),
    ).with_columns(
        (pl.col("units") / (pl.col("n_days") - pl.col("oos_days"))
         * pl.col("oos_days")).alias("lost_units"),
    )
    _lost_units = float(_cens["lost_units"].sum())
    _lost_rev = float((_cens["lost_units"] * _cens["price"]).sum())
    _sold = float(_sw["units"].sum())
    # grading: the hidden ledger records every unmet stockout unit
    _hid = pl.read_csv(
        source = DATA / "scenarios" / "3y_baseline" / "hidden" / "hidden_demand.csv",
        schema_overrides = {"uid": pl.Utf8},
    )
    _true_lost = float(_hid.filter(pl.col("cause") == "stockout")["qty"].sum())
    cens_stats = {
        "lost_units": _lost_units,
        "lost_rev": _lost_rev,
        "sold": _sold,
        "true_lost": _true_lost,
        "ratio": _lost_units / _true_lost,
    }
    _top = _cens.group_by("category").agg(
        pl.col("lost_units").sum().round(0).alias("imputed_lost_units"),
        (pl.col("lost_units") * pl.col("price")).sum().round(0).alias("imputed_lost_revenue_eur"),
    ).sort(by = "imputed_lost_revenue_eur", descending = True).head(6)
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 2 · What would demand be if shelves never emptied? (3.2)

    Sales data is a *censored* record of demand: every empty-shelf day
    records zero sales for a product people may have wanted. The
    imputation is deliberately simple and defensible — for each product-
    week that was partly out of stock, estimate the demand rate from the
    in-stock days and charge the empty days the same rate:

    over three years that yields **≈{cens_stats['lost_units']:,.0f} units
    of invisible demand**, roughly **€{cens_stats['lost_rev']:,.0f} of
    revenue** ({cens_stats['lost_rev'] / 3:,.0f} a year) that customers
    were ready to spend while the shelf was bare —
    {100 * cens_stats['lost_units'] / cens_stats['sold']:.1f}% of all
    units actually sold.
    """
            ),
            mo.ui.table(
                data = _top,
                selection = None,
            ),
            caption(
                "The imputation concentrates exactly where Layer 1 found "
                "the empty shelves: high-velocity perishables and the "
                "busy-season categories. Two caveats are part of the "
                "method: availability is proxied by BOOK stock (Layer 0 "
                "showed the book drifts, mildly), and a day at zero "
                "after the shop sold out at 7pm still counts as a full "
                "lost day — the estimate leans conservative-to-fair "
                "rather than precise."
            ),
            mo.accordion(
                items = {
                    "Grading against the hidden unmet-demand ledger": mo.md(
                        f"""
    The world records every thwarted purchase attempt with its cause. True
    stockout-caused unmet demand over the three years:
    **{cens_stats['true_lost']:,.0f} units**; the in-stock-rate imputation
    estimates **{cens_stats['lost_units']:,.0f}** — the right order of
    magnitude, overshooting the ledger by about
    {100 * (cens_stats['ratio'] - 1):.0f}%. The overshoot has a known
    anatomy, and it teaches more than a perfect score would: (a) the
    availability proxy is END-OF-DAY book stock, so a day that sold
    briskly all morning and ran dry at 7pm counts as fully lost while its
    morning sales still inflate the estimated rate; (b) the drifting book
    occasionally shows phantom empty days; and (c) the two errors point
    the same way. Pulling the other direction — and partly cancelling —
    full-week stockouts contribute nothing (no in-stock days to rate),
    and shoppers who quietly bought a substitute never enter the hidden
    ledger as unmet at all. A defensible rule, an honestly-diagnosed ±20%
    band, and a number big enough to justify the deeper-shelf
    conversation the prescriptive layer will have.
    """
                    ),
                },
            ),
        ],
    )
    return (cens_stats,)


@app.cell
def _(DATA, MUTED, WARN, caption, con, go, mo, pl, style, takeaway):
    # ==== 3.3 — how wrong is the owner's own forecast, and why? ===============
    # Henrik's weekly order sheet (his own artifact, handed over with the
    # engagement) vs realized sales vs demand incl. the stockout-hidden part
    _fc = pl.read_csv(source = DATA / "scenarios" / "3y_baseline" / "hidden" / "owner_forecasts.csv")
    _sales_w = con.sql(
        query = """
            SELECT p.category,
                   c.week                AS week,
                   sum(r.qty)::DOUBLE    AS sold
            FROM   receipts r
            JOIN   products p USING (uid)
            JOIN   calendar_raw c ON r.date = c.date
            WHERE  r.qty > 0
              AND  r.ref_receipt_id IS NULL
            GROUP  BY 1, 2
        """,
    ).pl()
    _hidden = pl.read_csv(
        source = DATA / "scenarios" / "3y_baseline" / "hidden" / "hidden_demand.csv",
        schema_overrides = {"uid": pl.Utf8},
    ).filter(pl.col("cause") == "stockout")
    _cal = con.sql(query = "SELECT date, week FROM calendar_raw ORDER BY date").pl()
    _t2w = dict(zip(
        range(1, len(_cal) + 1),
        _cal["week"].to_list(),
    ))
    _hidden = _hidden.with_columns(
        pl.col("t").replace_strict(_t2w).alias("week"),
    ).group_by([
        "category",
        "week",
    ]).agg(pl.col("qty").sum().alias("unmet"))
    _j = _fc.join(
        other = _sales_w,
        on = [
            "category",
            "week",
        ],
        how = "inner",
    ).join(
        other = _hidden,
        on = [
            "category",
            "week",
        ],
        how = "left",
    ).with_columns(
        pl.col("unmet").fill_null(value = 0.0),
    ).with_columns(
        (pl.col("sold") + pl.col("unmet")).alias("demand"),
    ).filter(pl.col("demand") > 0)
    # quartiles of demand within category: where does his rule miss most?
    _j = _j.with_columns(
        (pl.col("demand").rank().over("category") / pl.col("demand").count().over("category")).alias("pct"),
    ).with_columns(
        pl.when(pl.col("pct") <= 0.25).then(pl.lit("Q1 (quietest weeks)"))
        .when(pl.col("pct") <= 0.5).then(pl.lit("Q2"))
        .when(pl.col("pct") <= 0.75).then(pl.lit("Q3"))
        .otherwise(pl.lit("Q4 (busiest weeks)")).alias("dq"),
    )
    _byq = _j.group_by("dq").agg(
        (100 * (pl.col("forecast_weekly") / pl.col("demand")).mean() - 100).alias("bias_pct"),
        pl.len().alias("n"),
    ).sort(by = "dq")
    own_stats = {
        "bias_all": float(100 * (_j["forecast_weekly"] / _j["demand"]).mean() - 100),
        "bias_q4": float(_byq.filter(pl.col("dq") == "Q4 (busiest weeks)")["bias_pct"][0]),
        "bias_q1": float(_byq.filter(pl.col("dq") == "Q1 (quietest weeks)")["bias_pct"][0]),
        "n": int(_j.height),
    }
    _fig = go.Figure()
    _fig.add_bar(
        x = _byq["dq"].to_list(),
        y = _byq["bias_pct"].to_list(),
        marker_color = [
            MUTED,
            MUTED,
            MUTED,
            WARN,
        ],
        text = [f"{_v:+.1f}%" for _v in _byq["bias_pct"]],
        textposition = "outside",
    )
    _fig.add_hline(
        y = 0,
        line_color = MUTED,
        line_width = 1,
    )
    style(
        fig = _fig,
        title = "Henrik's forecast vs. true weekly demand, by how busy the week really was",
    )
    _fig.update_yaxes(
        showticklabels = False,
        showline = False,
        ticks = "",
        title_text = "avg forecast ÷ demand − 1 (%)",
        title_font = dict(
            size = 11.5,
            color = MUTED,
        ),
        range = [
            min(float(_byq["bias_pct"].min()) * 1.6, -1),
            max(float(_byq["bias_pct"].max()) * 1.6, 6),
        ],
    )
    _fig.update_xaxes(title_text = "")
    takeaway(
        fig = _fig,
        text = "his rule under-orders exactly when the shop is busiest —<br>and his own empty shelves then hide the evidence",
        x = 0.98,
        y = 0.98,
        anchor = "right",
    )
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 3 · How wrong is the owner's own forecast — and why? (3.3)

    Henrik's order sheet runs on a trailing 4-week average of *sales*. The
    autopsy compares his {own_stats['n']:,} weekly category forecasts
    against true demand — sales **plus** the stockout-hidden units
    recovered in §2's spirit (here taken from the hidden ledger, since
    this panel grades him, not us):
    """
            ),
            _fig,
            caption(
                "In an ordinary week his rule is roughly unbiased — a "
                "trailing average is a fine thermostat. The failure is "
                "concentrated in the busiest quarter of weeks, where he "
                f"runs {abs(own_stats['bias_q4']):.0f}% short of true "
                "demand — and the mechanism is a loop, not a lapse: he "
                "forecasts SALES, his forecast sets the ORDER, the order "
                "caps what CAN sell, and the capped sales then feed the "
                "next forecast. Every stockout his under-order causes "
                "erases its own evidence. That is why the bias never "
                "self-corrects: the data he learns from is censored by "
                "the very decisions it teaches. The fix is Layer 4's "
                "business — forecast demand (de-censored, seasonally "
                "anticipating), not last month's till."
            ),
        ],
    )
    return (own_stats,)


@app.cell
def _(con, mo, np, pl, stars):
    # ==== 3.4 — which shelves will be empty next week? ========================
    import statsmodels.api as _sm

    # per SKU-week: does NEXT week contain any empty-shelf day? Features an
    # owner could compute every Monday from his own records.
    _sw = con.sql(
        query = """
            WITH inv AS (
                SELECT uid,
                       cast(least(155, datediff('day', DATE '2025-01-01', date) / 7) AS INT) AS w,
                       min(on_hand)                          AS min_on_hand,
                       max(CASE WHEN on_hand <= 0 THEN 1 ELSE 0 END) AS oos
                FROM   inventory_eod_raw
                GROUP  BY 1, 2
            ),
            sales AS (
                SELECT uid,
                       cast(least(155, datediff('day', DATE '2025-01-01', date) / 7) AS INT) AS w,
                       sum(qty)::DOUBLE AS units
                FROM   receipts
                WHERE  qty > 0
                  AND  ref_receipt_id IS NULL
                GROUP  BY 1, 2
            )
            SELECT i.uid,
                   i.w,
                   i.min_on_hand,
                   i.oos,
                   coalesce(s.units, 0) AS units
            FROM   inv i
            LEFT   JOIN sales s USING (uid, w)
            ORDER  BY i.uid, i.w
        """,
    ).pl()
    _sw = _sw.with_columns(
        pl.col("units").rolling_mean(window_size = 4).over("uid").alias("ma4"),
        pl.col("oos").shift(-1).over("uid").alias("oos_next"),
    ).drop_nulls().filter(pl.col("ma4") > 0)
    _sw = _sw.with_columns(
        (pl.col("min_on_hand").clip(lower_bound = 0) / pl.col("ma4")).alias("cover"),
        pl.col("oos").alias("oos_now"),
    )
    _train = _sw.filter(pl.col("w") < 105)
    _test = _sw.filter(pl.col("w") >= 105)
    _Xtr = _sm.add_constant(np.column_stack([
        np.log1p(_train["cover"].to_numpy()),
        _train["oos_now"].to_numpy().astype(float),
        np.log1p(_train["ma4"].to_numpy()),
    ]))
    _logit = _sm.Logit(
        endog = _train["oos_next"].to_numpy().astype(float),
        exog = _Xtr,
    ).fit(disp = 0)
    _Xte = _sm.add_constant(np.column_stack([
        np.log1p(_test["cover"].to_numpy()),
        _test["oos_now"].to_numpy().astype(float),
        np.log1p(_test["ma4"].to_numpy()),
    ]))
    _p = _logit.predict(_Xte)
    _y = _test["oos_next"].to_numpy().astype(float)
    _names = [
        "intercept",
        "log(1 + weeks of cover)",
        "out of stock THIS week",
        "log(1 + weekly velocity)",
    ]
    _ci = _logit.conf_int()
    oos_table = pl.DataFrame({
        "term": _names,
        "estimate": [round(float(_b), 3) for _b in _logit.params],
        "std_error": [round(float(_s), 3) for _s in _logit.bse],
        "z_stat": [round(float(_t), 2) for _t in _logit.tvalues],
        "p_value": [round(float(_v), 4) for _v in _logit.pvalues],
        "sig": [stars(p = float(_v)) for _v in _logit.pvalues],
    })
    # operating point: flag the riskiest N SKUs each Monday; how many of
    # next week's actual stockouts does the watchlist catch?
    _test = _test.with_columns(pl.Series(name = "risk", values = _p))
    _flag = _test.sort(by = "risk", descending = True).group_by("w").head(15)
    _caught = float(_flag["oos_next"].sum())
    _total = float(_test["oos_next"].sum())
    _prec = float(_flag["oos_next"].mean())
    oos_stats = {
        "recall": _caught / _total,
        "precision": _prec,
        "base": float(_test["oos_next"].mean()),
        "n_test": int(_test.height),
    }
    mo.vstack(
        items = [
            mo.md(
                r"""
    ## 4 · Which shelves will be empty next week? (3.4)

    **The model.** A logistic regression an owner could run from his own
    records every Monday — will this product hit an empty shelf at any
    point next week?

    $$\Pr(\text{OOS}_{i,w+1}) = \Lambda\big(\beta_0 + \beta_1 \log(1 + \text{Cover}_{i,w}) + \beta_2\,\text{OOS}_{i,w} + \beta_3 \log(1 + \text{Velocity}_{i,w})\big)$$

    where Cover is end-of-week stock over trailing 4-week weekly sales.
    Trained on 2025–2026, evaluated on 2027:
    """
            ),
            mo.ui.table(
                data = oos_table,
                selection = None,
            ),
            mo.md(
                f"""
    **Technical reading.** Cover is the dominant protective factor (each
    log-unit of cover multiplies the stockout odds by
    {float(np.exp(_logit.params[1])):.2f}); being empty *this* week is the
    loudest alarm for next week; and faster movers are structurally
    riskier at the same cover.

    **The operating point that matters.** As a Monday watchlist of the
    **15 riskiest products**, the screen catches
    **{100 * oos_stats['recall']:.0f}%** of the following week's actual
    stockouts, and {100 * oos_stats['precision']:.0f}% of watchlist slots
    are hits — three times the {100 * oos_stats['base']:.0f}% base rate.
    A third of stockouts from a one-page list is a modest, honest win:
    stockouts here are driven as much by within-week demand surprises as
    by Monday-visible cover, so no Monday screen will catch them all. The
    operational form is right, though — not a probability nobody reads,
    but fifteen products to double-order before Wednesday's truck.
    """
            ),
        ],
    )
    return (oos_stats,)


@app.cell
def _(DATA, caption, con, mo, pl):
    # ==== 3.5 — which regulars are sliding into trouble? ======================
    # sustained down-trading screen: >=3 consecutive observed weeks below
    # 75% of the customer's own median weekly spend
    _cw = con.sql(
        query = """
            SELECT customer_id,
                   cast(least(155, datediff('day', DATE '2025-01-01', date) / 7) AS INT) AS w,
                   sum(qty * unit_price)::DOUBLE AS spend
            FROM   receipts
            WHERE  customer_id IS NOT NULL
              AND  qty > 0
              AND  ref_receipt_id IS NULL
            GROUP  BY 1, 2
        """,
    ).pl()
    _regs = _cw.group_by("customer_id").agg(
        pl.len().alias("n_weeks"),
        pl.col("spend").median().alias("med"),
    ).filter(pl.col("n_weeks") >= 40)
    _cw = _cw.join(
        other = _regs,
        on = "customer_id",
        how = "inner",
    ).sort(by = ["customer_id", "w"]).with_columns(
        (pl.col("spend") < 0.75 * pl.col("med")).cast(pl.Int8).alias("low"),
    )
    # run-length of consecutive observed low weeks
    _cw = _cw.with_columns(
        (pl.col("low").rolling_sum(window_size = 3).over("customer_id") == 3).alias("flag3"),
    )
    _flagged = _cw.filter(pl.col("flag3") == True)  # noqa: E712
    _flag_cust = _flagged.group_by("customer_id").agg(
        pl.col("w").min().alias("first_flag_w"),
        pl.len().alias("flag_weeks"),
    )
    # grading: hidden spell flags (customer x week), mapped via tokens
    _hidc = pl.read_csv(
        source = DATA / "scenarios" / "3y_baseline" / "hidden" / "customers.csv",
        schema_overrides = {"departure_date": pl.Utf8},
    ).select([
        pl.col("token").alias("customer_id"),
        pl.col("customer_id").alias("cid"),
    ])
    _spell = pl.read_csv(source = DATA / "scenarios" / "3y_baseline" / "hidden" / "spell_flags.csv")
    _spell_long = _spell.unpivot(
        index = "customer_id",
        variable_name = "wk",
        value_name = "in_spell",
    ).with_columns(
        (pl.col("wk").str.strip_prefix("w").cast(pl.Int32) - 1).alias("w"),
        pl.col("customer_id").alias("cid"),
    ).select([
        "cid",
        "w",
        "in_spell",
    ])
    _fl = _flagged.select([
        "customer_id",
        "w",
    ]).join(
        other = _hidc,
        on = "customer_id",
        how = "inner",
    ).join(
        other = _spell_long,
        on = [
            "cid",
            "w",
        ],
        how = "left",
    ).with_columns(pl.col("in_spell").fill_null(value = 0))
    # a flag is a true positive if the customer is in (or within 2 weeks
    # after) a genuine budget spell at the flagged week
    _near = _flagged.select([
        "customer_id",
        "w",
    ]).join(
        other = _hidc,
        on = "customer_id",
        how = "inner",
    )
    _spell_pad = _spell_long.filter(pl.col("in_spell") == 1).with_columns(
        pl.col("w").alias("w0"),
    )
    _tp = 0
    _spell_by_cid = {
        _c: set(_g["w"].to_list())
        for (_c,), _g in _spell_pad.group_by("cid")
    }
    for _r in _near.iter_rows(named = True):
        _ws = _spell_by_cid.get(_r["cid"], set())
        if any((_r["w"] - _k) in _ws for _k in range(0, 4)):
            _tp += 1
    # the honest yardstick: how common are spell weeks in the first place?
    _panel_cids = set(_hidc.join(
        other = _regs.select("customer_id"),
        on = "customer_id",
        how = "inner",
    )["cid"].to_list())
    _base = float(_spell_long.filter(
        pl.col("cid").is_in(list(_panel_cids)),
    )["in_spell"].mean())
    spell_stats = {
        "n_regs": int(_regs.height),
        "n_flag_weeks": int(_flagged.height),
        "n_flag_cust": int(_flag_cust.height),
        "precision": _tp / max(1, int(_near.height)),
        "base": _base,
    }
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 5 · Which regulars are sliding into trouble? (3.5)

    Households hit rough patches — a lost job, a broken boiler — and their
    grocery spending shows it weeks before anything else the shop can see.
    The screen: for each of the {spell_stats['n_regs']} long-history
    regulars, flag **three consecutive observed weeks below 75% of that
    customer's own median weekly spend**. Over three years the screen
    raises {spell_stats['n_flag_weeks']} customer-week flags across
    {spell_stats['n_flag_cust']} customers.
    """
            ),
            caption(
                f"Graded against the hidden record of genuine household "
                f"budget squeezes: **{100 * spell_stats['precision']:.0f}%** "
                "of flagged weeks land inside (or within a month after) a "
                "real squeeze, against a base rate of only "
                f"{100 * spell_stats['base']:.1f}% of panel weeks — a "
                f"~{spell_stats['precision'] / max(spell_stats['base'], 1e-9):.0f}× "
                "enrichment from nothing but the till. Read both numbers "
                "honestly: most flags are still false alarms in absolute "
                "terms (weekly spend is noisy and shopping-elsewhere weeks "
                "look identical to squeezed weeks), so this is a "
                "SCREENING tool, not a verdict. Its limits are structural: "
                "spells shorter than three shopping weeks are invisible "
                "by construction, and the 25%-below-median threshold "
                "trades recall for precision. What would the shop DO with "
                "it? Nothing creepy: it is the analytics behind gentle "
                "levers — which weeks to run the staples promotions, how "
                "much of the panel is squeezed at once (a demand "
                "leading-indicator), and honesty about why 'average "
                "basket' fell in a given month."
            ),
        ],
    )
    return (spell_stats,)


@app.cell
def _(cens_stats, fc_stats, mo, oos_stats, own_stats, spell_stats):
    mo.md(f"""
    ---
    ## Where this leaves us

    The predictive scorecard:

    - **Next week's units** can be forecast to
      ~{100 * fc_stats['best_w']:.0f}% weighted error at the decision
      grain — and the winner is the owner's own trailing average, which
      both challengers must (and here fail to) beat at the one-week
      horizon. Short-horizon accuracy was never his problem; and because
      one-step forecasts absorb regime breaks silently, longer-horizon
      answers deserve ranges, not points.
    - **Invisible demand is real money**: ≈€{cens_stats['lost_rev'] / 3:,.0f}
      a year stands behind empty shelves, and a defensible imputation
      recovers about {100 * cens_stats['ratio']:.0f}% of the true unmet
      units from visible data alone.
    - **The owner's forecast fails non-randomly**: roughly unbiased in
      calm weeks, ~{abs(own_stats['bias_q4']):.0f}% short in the busiest
      quartile, and self-blinding — his under-orders erase the evidence
      of their own cost. This is the diagnosis Layer 4's ordering-policy
      rebuild must treat.
    - **Stockouts are watchable**: a Monday list of 15 products catches
      {100 * oos_stats['recall']:.0f}% of next week's empty shelves.
    - **Household trouble is visible early**: a simple own-median screen
      enriches for genuine budget squeezes
      ~{spell_stats['precision'] / max(spell_stats['base'], 1e-9):.0f}×
      over base rate — a screen, not a verdict.

    Every prediction here stops at *what will happen*. What to **do** —
    the ordering policy that closes the censoring loop, prices the
    waste-vs-stockout trade-off, and decides the expansion's fate — is
    Layer 4, next in the series.

    ---
    ### Appendix — method notes

    Data: `data/scenarios/3y_baseline/visible/` through the Layer 0
    cleaning contract. All evaluation is strictly out-of-sample on 2027;
    features use only information available at forecast time. Grading
    panels read `hidden/hidden_demand.csv`, `hidden/owner_forecasts.csv`
    (Henrik's own order sheet, treated as handed over), `hidden/
    customers.csv`, and `hidden/spell_flags.csv`, and are marked as such.
    Tools: DuckDB, Polars, scikit-learn (HistGradientBoosting +
    permutation importance), statsmodels (Logit), Plotly.
    """)
    return


if __name__ == "__main__":
    app.run()
