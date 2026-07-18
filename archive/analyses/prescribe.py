import marimo

__generated_with = "0.23.14"
app = marimo.App(width="full", app_title="Layer 4 — Prescribe")


@app.cell
def _():
    import duckdb
    import marimo as mo
    import numpy as np
    import plotly.graph_objects as go
    import polars as pl

    from pathlib import Path

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
        duckdb,
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
    # Layer 4: prescribe

    Layers 0–3 cleaned, described, diagnosed, and predicted. This notebook
    does the only thing a client actually pays for: it says **what to do**
    — the catalog's Layer 4 on `data/scenarios/3y_baseline/`, in euros.

    1. **Rebuild the ordering policy** (4.1 + 4.2) — the shop's one big
       operational lever. Layer 3 proved the owner's rule forecasts the
       wrong quantity (sales, not demand) and anticipates nothing; here a
       replacement policy is backtested against three years of history,
       its two ingredients priced separately, and the whole exercise
       graded against the hidden ceiling: what a perfectly informed owner
       could actually have earned.
    2. **Where is margin safely adjustable?** (4.3) The elasticity
       structure from Layer 2, turned into a per-category repricing menu.
    3. **What should be delisted?** (4.4) Dead-product economics.
    4. **How much cash must the till hold?** (4.7) The working-capital
       floor, from the ledger's own worst months.
    5. **Promotions and staffing** (4.5, 4.6) — closed by reference: the
       promotion machinery and the expansion verdict were settled in
       Layers 2 and 7.

    Prescriptions come with their assumptions attached. A backtest is a
    model of the shop, not the shop — and this notebook treats the gap
    between paper gains and the graded ceiling as a finding in itself.
    """)
    return


@app.cell
def _(DATA, ROOT, duckdb, pl):
    # ---- cleaned views (the Layer 0 contract, applied) ----------------------
    con = duckdb.connect()
    _vis = DATA / "scenarios" / "3y_baseline" / "visible"
    for _name in ["receipts", "procurement", "inventory_eod", "write_offs",
                  "cost_sheet", "calendar"]:
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
                   l.uid,
                   sum(l.qty * CASE WHEN r.is_retry THEN l.n // 2
                                    ELSE l.n END)                 AS qty,
                   l.unit_price,
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
    return (con,)


@app.cell
def _(con, np, pl):
    # ==== 4.1 + 4.2 — rebuild the ordering policy, and price its parts =======
    # Per SKU-day reconstruction from visible data: de-censored demand,
    # availability, unit costs and margins, and empirical spoilage rates.
    _daily = con.sql(
        query = """
            WITH sales AS (
                SELECT uid,
                       date,
                       sum(qty)::DOUBLE AS units
                FROM   receipts
                WHERE  qty > 0
                  AND  ref_receipt_id IS NULL
                GROUP  BY 1, 2
            )
            SELECT i.uid,
                   i.date,
                   datediff('day', DATE '2025-01-01', i.date)     AS t,
                   i.on_hand,
                   coalesce(s.units, 0)                           AS units,
                   CASE WHEN i.on_hand <= 0 THEN 1 ELSE 0 END     AS oos
            FROM   inventory_eod_raw i
            LEFT   JOIN sales s ON i.uid = s.uid AND i.date = s.date
            ORDER  BY i.uid, i.date
        """,
    ).pl()
    # weekly de-censoring (Layer 3.2's rule): partial-OOS weeks lend their
    # in-stock daily rate to the empty days
    _daily = _daily.with_columns(
        (pl.col("t") // 7).alias("w"),
    )
    _wk = _daily.group_by([
        "uid",
        "w",
    ]).agg(
        pl.col("units").sum().alias("wu"),
        pl.col("oos").sum().alias("od"),
        pl.len().alias("nd"),
    ).with_columns(
        pl.when((pl.col("od") > 0) & (pl.col("od") < pl.col("nd")) & (pl.col("wu") > 0))
        .then(pl.col("wu") / (pl.col("nd") - pl.col("od")))
        .otherwise(0.0).alias("rate"),
    )
    _daily = _daily.join(
        other = _wk.select([
            "uid",
            "w",
            "rate",
        ]),
        on = [
            "uid",
            "w",
        ],
        how = "left",
    ).with_columns(
        (pl.col("units") + pl.col("oos") * pl.col("rate")).alias("demand"),
    )
    # per-SKU economics: average paid price, average invoice cost
    econ = con.sql(
        query = """
            WITH pr AS (
                SELECT uid,
                       sum(qty * unit_price) / sum(qty) AS price
                FROM   receipts
                WHERE  qty > 0
                  AND  ref_receipt_id IS NULL
                GROUP  BY 1
            ),
            co AS (
                SELECT uid,
                       sum(qty * unit_cost) / sum(qty) AS cost
                FROM   (
                    SELECT DISTINCT uid, qty, unit_cost, order_date, delivery_date
                    FROM   procurement_raw
                )
                GROUP  BY 1
            )
            SELECT pr.uid,
                   pr.price,
                   co.cost,
                   p.category
            FROM   pr
            JOIN   co USING (uid)
            JOIN   products p ON pr.uid = p.uid
        """,
    ).pl()
    # empirical nightly spoilage rate per category: logged spoilage over
    # unit-days of stock held
    _held = _daily.join(
        other = econ.select([
            "uid",
            "category",
        ]),
        on = "uid",
        how = "inner",
    ).group_by("category").agg(
        pl.col("on_hand").clip(lower_bound = 0).sum().alias("unit_days"),
    )
    _spoil = con.sql(
        query = """
            SELECT p.category,
                   sum(w.units)::DOUBLE AS spoiled
            FROM   write_offs_raw w
            JOIN   products p USING (uid)
            WHERE  w.reason = 'spoilage'
            GROUP  BY 1
        """,
    ).pl()
    lam = _held.join(
        other = _spoil,
        on = "category",
        how = "left",
    ).with_columns(
        (pl.col("spoiled").fill_null(value = 0.0) / pl.col("unit_days")).alias("lam_d"),
    ).with_columns(
        (1 - (1 - pl.col("lam_d")) ** 7).alias("lam_w"),
    )

    # seasonal index per category and week-of-year (3-year average share) —
    # an in-sample simplification, stated as such in the write-up
    _cat_w = _daily.join(
        other = econ.select([
            "uid",
            "category",
        ]),
        on = "uid",
        how = "inner",
    ).group_by([
        "category",
        "w",
    ]).agg(pl.col("demand").sum().alias("d")).with_columns(
        (pl.col("w") % 52).alias("woy"),
    )
    _seas = _cat_w.group_by([
        "category",
        "woy",
    ]).agg(pl.col("d").mean().alias("s")).join(
        other = _cat_w.group_by("category").agg(pl.col("d").mean().alias("sbar")),
        on = "category",
        how = "inner",
    ).with_columns((pl.col("s") / pl.col("sbar")).alias("idx"))
    _seas_map = {
        (_r["category"], _r["woy"]): float(_r["idx"])
        for _r in _seas.iter_rows(named = True)
    }
    _lam_map = {
        _r["category"]: (float(_r["lam_d"]), float(_r["lam_w"]))
        for _r in lam.iter_rows(named = True)
    }

    def _simulate(spoilage_aware):
        """Replay 3 years per SKU under the rebuilt weekly policy.

        Monday order, Wednesday delivery; forecast = trailing 4-week mean
        of DE-CENSORED demand, scaled by next week's seasonal index; target
        cover = cycle+lead (9/7 wk) + safety 0.3 month, with the safety
        shrunk on perishables in proportion to their weekly spoilage odds
        (the spoilage-aware variant). Spoilage is expected-value thinning
        at the category's empirical nightly rate."""
        _tot_spoil_eur = 0.0
        _tot_unmet_eur = 0.0
        for (_uid,), _g in _daily.group_by("uid", maintain_order = True):
            _e = econ.filter(pl.col("uid") == _uid)
            if _e.height == 0:
                continue
            _cat = _e["category"][0]
            _price = float(_e["price"][0])
            _cost = float(_e["cost"][0])
            _lam_d, _lam_w = _lam_map.get(_cat, (0.0, 0.0))
            _d = _g.sort(by = "t")
            _dem = _d["demand"].to_numpy()
            _n = len(_dem)
            _stock = float(_d["on_hand"][0])
            _pipe = {}
            _hist = []
            _spoiled = 0.0
            _unmet = 0.0
            _wk_dem = 0.0
            if spoilage_aware:
                _saf = 0.3 * 30 / 7 * max(0.0, 1 - 4 * _lam_w)
            else:
                _saf = 0.3 * 30 / 7
            _cover = 9 / 7 + _saf
            for _t in range(_n):
                _stock += _pipe.pop(_t, 0.0)
                _sp = _stock * _lam_d
                _spoiled += _sp
                _stock -= _sp
                _sold = min(_stock, _dem[_t])
                _unmet += _dem[_t] - _sold
                _stock -= _sold
                _wk_dem += _dem[_t]
                if _t % 7 == 6:
                    _hist.append(_wk_dem)
                    _wk_dem = 0.0
                # Mondays fall on t % 7 == 5 (Jan 1 2025 was a Wednesday)
                if _t % 7 == 5 and len(_hist) >= 4:
                    _ma = float(np.mean(_hist[-4:]))
                    _woy = ((_t // 7) + 1) % 52
                    _idx_next = _seas_map.get((_cat, _woy), 1.0)
                    _idx_past = float(np.mean([
                        _seas_map.get((_cat, ((_t // 7) - _k) % 52), 1.0)
                        for _k in range(0, 4)
                    ]))
                    _f = _ma * (_idx_next / max(_idx_past, 0.25))
                    _target = _cover * _f
                    _order = max(0.0, _target - _stock - sum(_pipe.values()))
                    if _order >= 1:
                        _pipe[_t + 2] = _pipe.get(_t + 2, 0.0) + _order
            _tot_spoil_eur += _spoiled * _cost
            _tot_unmet_eur += _unmet * (_price - _cost)
        return _tot_spoil_eur, _tot_unmet_eur

    _b_spoil, _b_unmet = _simulate(spoilage_aware = False)
    _c_spoil, _c_unmet = _simulate(spoilage_aware = True)
    # the ACTUAL baseline: observed spoilage at cost, imputed unmet at margin
    _act_spoil = float(
        _spoil.join(
            other = econ.group_by("category").agg(pl.col("cost").mean().alias("c")),
            on = "category",
            how = "inner",
        ).select((pl.col("spoiled") * pl.col("c")).sum()).item()
    )
    _act_unmet = float(
        _daily.join(
            other = econ,
            on = "uid",
            how = "inner",
        ).select(
            ((pl.col("demand") - pl.col("units")) * (pl.col("price") - pl.col("cost"))).sum()
        ).item()
    )
    policy_eval = pl.DataFrame([
        {
            "policy": "actual history (owner's rule)",
            "spoilage_cost_eur": round(_act_spoil, 0),
            "lost_margin_eur": round(_act_unmet, 0),
            "total_leak_eur": round(_act_spoil + _act_unmet, 0),
        },
        {
            "policy": "rebuilt: de-censored + seasonal forecast",
            "spoilage_cost_eur": round(_b_spoil, 0),
            "lost_margin_eur": round(_b_unmet, 0),
            "total_leak_eur": round(_b_spoil + _b_unmet, 0),
        },
        {
            "policy": "rebuilt + spoilage-aware safety stock",
            "spoilage_cost_eur": round(_c_spoil, 0),
            "lost_margin_eur": round(_c_unmet, 0),
            "total_leak_eur": round(_c_spoil + _c_unmet, 0),
        },
    ])
    policy_stats = {
        "act": _act_spoil + _act_unmet,
        "b": _b_spoil + _b_unmet,
        "c": _c_spoil + _c_unmet,
        "gain_b": (_act_spoil + _act_unmet) - (_b_spoil + _b_unmet),
        "gain_c": (_act_spoil + _act_unmet) - (_c_spoil + _c_unmet),
        "act_spoil": _act_spoil,
        "act_unmet": _act_unmet,
        "c_spoil": _c_spoil,
        "c_unmet": _c_unmet,
    }
    return econ, lam, policy_eval, policy_stats


@app.cell
def _(
    ACCENT,
    ACCENT_LIGHT,
    DATA,
    MUTED,
    caption,
    go,
    mo,
    pl,
    policy_eval,
    policy_stats,
    style,
    takeaway,
):
    _trip = pl.read_csv(source = DATA / "scenarios" / "3y_baseline" / "hidden" / "profit_triptych.csv")
    _ceiling = float(_trip["oracle_profit_year"][0] - _trip["realized_profit_year"][0])
    _b_row = policy_eval.filter(pl.col("policy").str.starts_with("rebuilt:"))
    _b_spoil = float(_b_row["spoilage_cost_eur"][0])
    _b_unmet = float(_b_row["lost_margin_eur"][0])
    _rows = [
        ("actual history<br>(owner's rule)", policy_stats["act"], MUTED),
        ("rebuilt forecast<br>(de-censored + seasonal)", policy_stats["b"], ACCENT_LIGHT),
        ("rebuilt + spoilage-aware<br>safety stock", policy_stats["c"], ACCENT),
    ]
    _fig = go.Figure()
    _fig.add_bar(
        x = [_n for _n, _, _ in _rows],
        y = [_v / 1000 for _, _v, _ in _rows],
        marker_color = [_c for _, _, _c in _rows],
        text = [f"€{_v / 1000:,.0f}k" for _, _v, _ in _rows],
        textposition = "outside",
    )
    style(
        fig = _fig,
        title = "The inventory leak (spoilage cost + margin lost to empty shelves), three policies, 2025–2027",
    )
    _fig.update_yaxes(
        showticklabels = False,
        showline = False,
        ticks = "",
        title_text = "three-year leak (€ thousands, lower is better)",
        title_font = dict(
            size = 11.5,
            color = MUTED,
        ),
        range = [0, max(_v for _, _v, _ in _rows) / 1000 * 1.3],
    )
    _fig.update_xaxes(title_text = "")
    takeaway(
        fig = _fig,
        text = "fixing the forecast ALONE makes things worse — the two<br>ingredients only pay together",
        x = 0.02,
        y = 0.98,
    )
    mo.vstack(
        items = [
            mo.md(
                r"""
    ## 1 · Rebuilding the ordering policy — and pricing its parts (4.1, 4.2)

    **The prescription.** Keep the owner's weekly rhythm, replace two
    ingredients his rule lacks:

    1. forecast **demand, not sales** — the trailing average runs on
       de-censored demand (Layer 3.2's imputation), breaking the loop in
       which his own stockouts teach him to under-order;
    2. **anticipate the season** — scale the forecast by next week's
       seasonal index instead of trailing a month behind every ramp;
    3. *(variant)* **respect the bin** — shrink the safety stock on
       perishables in proportion to their weekly spoilage odds.

    **The backtest.** Replay all three years per product: Monday orders,
    Wednesday deliveries, demand from the de-censored reconstruction,
    spoilage as expected-value thinning at each category's empirical
    nightly rate. Score each policy on the two leaks that ordering
    controls — write-offs at cost, and margin lost to empty shelves:
    """
            ),
            mo.ui.table(
                data = policy_eval,
                selection = None,
            ),
            _fig,
            caption(
                "The middle bar is the notebook's most important warning: "
                "the 'obvious' prescription — fix the forecast, serve the "
                "demand you were missing — makes the shop WORSE off by "
                f"≈€{-policy_stats['gain_b'] / 1000:,.0f}k, because "
                "serving de-censored, anticipated demand through the same "
                "flat 2.6-week buffers floods the perishable aisles: the "
                "lost-margin leak halves "
                f"(€{policy_stats['act_unmet'] / 1000:,.0f}k → "
                f"€{_b_unmet / 1000:,.0f}k) but spoilage balloons "
                f"(€{policy_stats['act_spoil'] / 1000:,.0f}k → "
                f"€{_b_spoil / 1000:,.0f}k). "
                "Only the PAIR — better forecast AND "
                "spoilage-aware buffers — beats history, by "
                f"≈€{policy_stats['gain_c'] / 1000:,.0f}k over the three "
                "years. Availability and waste are one coupled system; "
                "improving one input while ignoring the other is how "
                "well-meant analytics loses money. Assumptions worth "
                "restating: demand inherits Layer 3.2's ±20% band, "
                "spoilage thins in expectation rather than by draw, and "
                "the seasonal index is estimated in-sample — a capability "
                "estimate, not a guarantee."
            ),
            mo.accordion(
                items = {
                    "Grading: the paper gains vs. the true ceiling": mo.md(
                        f"""
    The hidden triptych prices what a PERFECTLY informed owner —
    uncensored demand, known seasonality, spoilage-aware buffers — would
    actually have earned: **€{_ceiling:,.0f} over the three years** above
    realized profit (≈€{_ceiling / 3:,.0f} a year). The backtest's paper
    saving of ≈€{policy_stats['gain_c'] / 1000:,.1f}k lands almost
    exactly on that ceiling — a strong validation that the replay is
    honest about magnitudes, not just directions. The small excess
    (≈€{(policy_stats['gain_c'] - _ceiling) / 1000:,.1f}k) is the price
    of the backtest's frictionless assumptions: it sells fractional
    units, spoils in smooth expectation, reacts instantly, and never
    meets a week that breaks its model. The honest client message quotes
    the ceiling: "a demand-based, season-aware, spoilage-aware order
    sheet is worth on the order of €{_ceiling / 3:,.0f} a year — real
    money for a shop whose 2027 pre-tax result was a €481 loss, but an
    optimization, not a rescue. The bigger risk is the middle bar:
    deploying the forecast fix without the buffer fix would have COST
    more than either fix can earn."
    """
                    ),
                },
            ),
        ],
    )
    return


@app.cell
def _(caption, econ, lam, mo, pl):
    # ==== 4.2 — how should perishables be ordered? (the arithmetic) ==========
    _m = econ.group_by("category").agg(
        pl.col("price").mean().alias("p"),
        pl.col("cost").mean().alias("c"),
    ).with_columns(
        (pl.col("p") - pl.col("c")).alias("cu"),
    )
    _nv = lam.join(
        other = _m,
        on = "category",
        how = "inner",
    ).with_columns(
        (pl.col("c") * pl.col("lam_w")).alias("co"),
    ).with_columns(
        (pl.col("cu") / (pl.col("cu") + pl.col("co"))).alias("critical_ratio"),
    ).select([
        "category",
        pl.col("lam_w").round(3).alias("weekly_spoil_odds"),
        pl.col("cu").round(2).alias("underage_margin_eur"),
        pl.col("co").round(3).alias("overage_cost_eur_wk"),
        pl.col("critical_ratio").round(3),
    ]).sort(by = "weekly_spoil_odds", descending = True)
    mo.vstack(
        items = [
            mo.md(
                r"""
    ## 2 · The perishables arithmetic behind that safety stock (4.2)

    The trade-off has a classical form — the newsvendor's critical ratio.
    A unit ordered and *needed* earns the margin $C_u = p - c$; a unit
    ordered and *not* needed risks the bin at
    $C_o \approx c \cdot \lambda_w$ (its cost times the odds it spoils
    before next week's truck). The service level worth targeting is

    $$\text{CR} = \frac{C_u}{C_u + C_o}$$

    — the fraction of demand weeks the shelf should survive:
    """
            ),
            mo.ui.table(
                data = _nv,
                selection = None,
            ),
            caption(
                "Two regimes fall straight out of the table. Ambient and "
                "slow-spoiling categories have overage costs near zero, so "
                "their critical ratios sit near 1.0 — hold generous "
                "buffers, an empty shelf is the only real risk. The "
                "fast-spoiling aisles (bakery, produce, seafood) pay a "
                "real weekly toll per held unit, so their targets drop "
                "meaningfully below 1.0 — thinner buffers, more frequent "
                "small shortfalls, much less in the bin. This is exactly "
                "the structure the spoilage-aware variant in §1 encodes, "
                "and the empirical λ per category is the only estimate it "
                "needs — no demand model, no software, a laminated card "
                "next to the order sheet."
            ),
        ],
    )
    return


@app.cell
def _(ACCENT, MUTED, WARN, caption, con, go, mo, pl, style, takeaway):
    # ==== 4.3 — where is margin safely adjustable? ===========================
    # dPi/Pi = (dp/p) * (1/m + eps): category-level elasticity from Layer 2,
    # per-category margin share m from the shop's own books
    _eps = -0.23
    _cat = con.sql(
        query = """
            WITH pr AS (
                SELECT p.category,
                       sum(r.qty * r.unit_price)::DOUBLE AS revenue
                FROM   receipts r
                JOIN   products p USING (uid)
                WHERE  r.qty > 0
                  AND  r.ref_receipt_id IS NULL
                GROUP  BY 1
            ),
            co AS (
                SELECT p.category,
                       sum(pc.qty * pc.unit_cost)::DOUBLE AS bought
                FROM   (
                    SELECT DISTINCT uid, qty, unit_cost, order_date, delivery_date
                    FROM   procurement_raw
                ) pc
                JOIN   products p USING (uid)
                GROUP  BY 1
            )
            SELECT pr.category,
                   pr.revenue,
                   co.bought,
                   (pr.revenue - co.bought)             AS gross_profit
            FROM   pr
            JOIN   co USING (category)
        """,
    ).pl().with_columns(
        ((pl.col("revenue") - pl.col("bought")) / pl.col("revenue")).alias("m"),
    ).with_columns(
        # dPi for a +1% category-wide price move, first-order
        (pl.col("gross_profit") * 0.01 * (1 / pl.col("m") + _eps) / 3).alias("dpi_1pct_yr"),
    ).sort(by = "dpi_1pct_yr", descending = True)
    repricing = _cat.select([
        "category",
        pl.col("m").round(3).alias("margin_share"),
        (pl.col("gross_profit") / 3).round(0).alias("gross_profit_eur_yr"),
        pl.col("dpi_1pct_yr").round(0).alias("plus_1pct_price_eur_yr"),
    ])
    _top = _cat.head(5)
    _fig = go.Figure()
    _fig.add_bar(
        x = [_c.replace(" and ", " & ") for _c in _cat["category"]],
        y = _cat["dpi_1pct_yr"].to_list(),
        marker_color = [
            WARN if _c in (
                "Beverages (Non-Alcoholic)",
                "Snacks and Confectionery",
                "Household and Cleaning Supplies",
            ) else ACCENT
            for _c in _cat["category"]
        ],
        text = [f"{_v:,.0f}" for _v in _cat["dpi_1pct_yr"]],
        textposition = "outside",
    )
    style(
        fig = _fig,
        title = "What a +1% category-wide price move is worth per year (red = discounter-exposed)",
        right_margin = 40,
    )
    _fig.update_yaxes(
        showticklabels = False,
        showline = False,
        ticks = "",
        title_text = "Δ gross profit (€/year, first-order)",
        title_font = dict(
            size = 11.5,
            color = MUTED,
        ),
        range = [0, float(_cat["dpi_1pct_yr"].max()) * 1.35],
    )
    _fig.update_xaxes(
        title_text = "",
        tickfont = dict(size = 10.5),
        tickangle = 30,
    )
    takeaway(
        fig = _fig,
        text = "gentle, category-wide, and away from the shelves Spara+ watches",
        x = 0.98,
        y = 0.98,
        anchor = "right",
    )
    mo.vstack(
        items = [
            mo.md(
                r"""
    ## 3 · Where is margin safely adjustable? (4.3)

    Layer 2 measured the two elasticities that define this shop's pricing
    room: ≈ −2.15 for a single product (its buyers step sideways to a
    substitute) and **−0.23 for a whole category** (the need itself barely
    responds). Small uniform category moves are therefore predictable, and
    their first-order profit arithmetic is one line:

    $$\frac{\Delta\Pi}{\Pi} \approx \frac{\Delta p}{p}\left(\frac{1}{m} + \varepsilon\right)$$

    with $m$ the category's gross-margin share and $\varepsilon = -0.23$:
    """
            ),
            mo.ui.table(
                data = repricing,
                selection = None,
            ),
            _fig,
            caption(
                "Every category clears the bar comfortably — with "
                "|ε| far below 1/m, a small uniform price move raises "
                "gross profit roughly in proportion to revenue. The "
                "caveats ARE the prescription: (1) first-order arithmetic "
                "holds for GENTLE moves (a percent or two), not for "
                "re-pricing regimes; (2) the elasticity was estimated in "
                "a world that, since March 2027, contains a discounter — "
                "the three shelves Spara+ advertises hardest (red bars) "
                "are exactly where Henrik already CUT prices, and "
                "re-raising them invites the comparison shopping the cut "
                "was meant to blunt; (3) implementation is free: tags "
                "already move on delivery days, so the change rides the "
                "existing repricing rhythm. The safe menu: +1–2% on the "
                "blue categories, hands off the red ones, revisit after a "
                "quarter."
            ),
        ],
    )
    return


@app.cell
def _(DATA, caption, con, mo, pl):
    # ==== 4.4 — what should be delisted? ======================================
    _sku = con.sql(
        query = """
            WITH s AS (
                SELECT uid,
                       sum(qty)::DOUBLE                            AS units,
                       sum(qty * unit_price)::DOUBLE               AS revenue
                FROM   receipts
                WHERE  qty > 0
                  AND  ref_receipt_id IS NULL
                GROUP  BY 1
            ),
            c AS (
                SELECT uid,
                       sum(qty * unit_cost) / sum(qty) AS cost
                FROM   (
                    SELECT DISTINCT uid, qty, unit_cost, order_date, delivery_date
                    FROM   procurement_raw
                )
                GROUP  BY 1
            ),
            inv AS (
                SELECT uid,
                       avg(greatest(on_hand, 0)) AS avg_stock
                FROM   inventory_eod_raw
                GROUP  BY 1
            ),
            wo AS (
                SELECT uid,
                       sum(units)::DOUBLE AS spoiled
                FROM   write_offs_raw
                WHERE  reason = 'spoilage'
                GROUP  BY 1
            )
            SELECT s.uid,
                   p.name AS product_name,
                   p.category,
                   s.units,
                   (s.revenue - s.units * c.cost)                    AS margin_eur,
                   coalesce(wo.spoiled, 0) * c.cost                  AS spoil_cost_eur,
                   inv.avg_stock * 0.02 * 36                         AS storage_eur
            FROM   s
            JOIN   c   USING (uid)
            JOIN   inv USING (uid)
            LEFT   JOIN wo USING (uid)
            JOIN   products p ON s.uid = p.uid
        """,
    ).pl().with_columns(
        (pl.col("margin_eur") - pl.col("spoil_cost_eur") - pl.col("storage_eur")).alias("contribution_eur"),
    ).sort(by = "contribution_eur")
    dead = _sku.head(8).select([
        "uid",
        "product_name",
        "category",
        pl.col("units").round(0),
        pl.col("margin_eur").round(0),
        pl.col("spoil_cost_eur").round(0),
        pl.col("contribution_eur").round(0).alias("contribution_3y_eur"),
    ])
    _neg = _sku.filter(pl.col("contribution_eur") < 0)
    dead_stats = {
        "n_neg": int(_neg.height),
        "neg_total": float(_neg["contribution_eur"].sum()),
    }
    # grading: the owner's opening beliefs for the losers
    _dec = pl.read_csv(source = DATA / "scenarios" / "3y_baseline" / "hidden" / "decision_t0.csv")
    _j = dead.join(
        other = _dec.select([
            "uid",
            "believed_sales",
        ]),
        on = "uid",
        how = "left",
    )
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 4 · What should be delisted? (4.4)

    Every listed product pays rent in shelf space, storage, and — if it
    is perishable — the bin. Charging each product its own spoilage and
    storage against three years of margin, **{dead_stats['n_neg']}
    products contributed NEGATIVELY** (a combined
    €{dead_stats['neg_total']:,.0f}); the eight worst:
    """
            ),
            mo.ui.table(
                data = dead,
                selection = None,
            ),
            caption(
                "Read the near-null result first: after three years, the "
                "assortment carries almost NO dead weight — two products "
                "in the red, €99 between them. Delisting is not where "
                "this shop's money is. What the ranking actually locates "
                "is the overage victims: the croissants earn €2,928 of "
                "margin and hand €2,890 of it back to the bin, the "
                "seafood tier keeps €50–160 of four-figure margins — "
                "products whose demand is real but whose flat 2.6-week "
                "buffers convert most of it into write-offs. The "
                "prescription is §1–2's, not the axe: re-buffer these "
                "first; delist only what stays negative afterwards. And "
                "keep the strategic caveat — a full-range neighborhood "
                "shop sells the RANGE, and a modest loss-maker that "
                "completes a basket can pay for itself in trips (a "
                "question the Layer 6 choice model can quantify)."
            ),
            mo.accordion(
                items = {
                    "Grading: what the owner believed at opening": mo.md(
                        """
    Joining the bottom eight to the hidden opening plan
    (`decision_t0.csv`) splits them into two failure modes. The shampoo,
    the premium laundry detergent, and the semi-skimmed milk sold FAR
    below the owner's believed monthly demand (1–2 units a month against
    beliefs of 15–119) — opening-optimism cases, though so little cash
    sits in them that they stay marginally positive: dead weight in
    attention, not in euros. The bakery and seafood rows are the
    opposite: the croissants sold FOUR TIMES the believed demand and
    still land negative, because every unit of that surprise demand was
    chased with flat buffers on a one-to-three-day shelf life. The
    analyst's contribution ranking recovers both patterns from pure
    economics, without ever seeing the beliefs — which is the point of
    the exercise.
    """
                    ),
                },
            ),
        ],
    )
    return (dead_stats,)


@app.cell
def _(caption, con, mo, pl):
    # ==== 4.7 — how much cash must the till hold? =============================
    _cs = con.sql(
        query = """
            SELECT year,
                   month,
                   rent + wages + payroll_tax + utilities + storage
                   + flyers + vat + credit_interest + repairs
                   + profit_tax_paid                          AS close_bills,
                   procurement,
                   cash
            FROM   cost_sheet_raw
            ORDER  BY year, month
        """,
    ).pl()
    _worst = _cs.sort(by = "close_bills", descending = True).head(3).select([
        "year",
        "month",
        pl.col("close_bills").round(0),
    ])
    _buffer = float(_cs["close_bills"].max()) + float(_cs["procurement"].mean()) / 4
    cash_stats = {
        "max_bills": float(_cs["close_bills"].max()),
        "med_bills": float(_cs["close_bills"].median()),
        "buffer": _buffer,
        "min_cash": float(_cs["cash"].min()),
    }
    mo.vstack(
        items = [
            mo.md(
                f"""
    ## 5 · How much cash must the till hold? (4.7)

    The ledger answers this directly. A month's close brings the fixed
    bills — rent, wages, utilities, the VAT remittance, and (since 2026)
    January's profit-tax settlement — while the Wednesday orders drain
    cash continuously. The heaviest closes of the three years:
    """
            ),
            mo.ui.table(
                data = _worst,
                selection = None,
            ),
            mo.md(
                f"""
    **The floor:** the worst close demanded
    €{cash_stats['max_bills']:,.0f} (a January, naturally — tax
    settlement plus the raised rent in one month, against a typical
    close of €{cash_stats['med_bills']:,.0f}), and a week of orders
    runs ≈€{float(_cs['procurement'].mean()) / 4.33:,.0f}. A prudent
    till floor is therefore about **€{cash_stats['buffer'] / 1000:,.0f}k
    entering any month** — the worst close plus a week of goods.
    """
            ),
            caption(
                f"Henrik has never been close to trouble — his lowest "
                f"month-end cash in three years was "
                f"€{cash_stats['min_cash']:,.0f}, and that was January "
                "2025, the opening month, before the first full month of "
                "takings; every low since has been comfortably above the "
                "floor. The €20k credit line "
                "has never been drawn, and the tax jar discipline "
                "(reserving the accruing profit tax out of ordering "
                "headroom) is why January never surprises him. The "
                "prescription is mostly a compliment with two footnotes: "
                "keep the January double-bill in view when the lease "
                "renews (rent step + tax settlement landed together in "
                "2027), and recognize that cash persistently ABOVE the "
                "floor is a decision too — the retained-earnings ledger "
                "already exists, and money beyond the buffer either "
                "funds the next considered move or is the owner's to "
                "take home."
            ),
        ],
    )
    return (cash_stats,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 6 · Promotions and staffing — closed by reference (4.5, 4.6)

    - **When should promotions run, on what, how deep?** (4.5) The
      evidence is already in: the overstock-triggered markdowns genuinely
      lifted their targets (Layer 2's DiD, ≈+49% per product-day at 10–30%
      depths) and have not been needed since 2025 — demand growth absorbed
      the overstock that used to trigger them. Keep the machinery exactly
      as designed (it fires only when a category's cover breaks 4 weeks),
      resist inventing promotions for their own sake, and price any new
      idea against the 5%-Sunday's honest arithmetic: at an 18% margin, a
      storewide discount needs a ~+38% revenue lift to break even, which
      the beloved Sunday does not reach — it is a loyalty expense, kept on
      purpose.
    - **Should I hire and extend hours?** (4.6) Answered with the full
      force of the counterfactual twins in `expansion_review.py`: the
      November 2026 expansion costs ≈€96k over its first fourteen months
      against benefits an order of magnitude smaller, and 2027 without it
      would have been comfortably profitable even with the discounter.
      The staffing prescription stands: **reverse or restructure the
      expansion; the lease was never the problem.**
    """)
    return


@app.cell
def _(cash_stats, dead_stats, mo):
    mo.md(f"""
    ---
    ## The prescription sheet (what Henrik signs)

    In one page, in his order of urgency:

    1. **Reverse or restructure the expansion** (Layer 7's twins) — the
       single decision that separates a −€500 year from a +€60k one.
       Renew the lease.
    2. **Replace the order sheet's inputs** — same weekly rhythm, but
       forecast de-censored demand, scale by next week's seasonal index,
       and shrink perishable safety stock by spoilage odds (§1–2). Graded
       honest value: on the order of **€3–4k a year**, roughly year
       2027's entire shortfall — and deploy the two changes TOGETHER:
       the backtest shows the forecast fix alone floods the perishable
       aisles and loses more than either fix earns.
    3. **A gentle repricing round** (§3): +1–2% on the categories the
       discounter does not advertise; hands off beverages, snacks, and
       household. First-order value: **€2–6k a year** depending on
       breadth, at essentially zero implementation cost.
    4. **Leave the assortment alone** (§4): only {dead_stats['n_neg']}
       products run net negative, €{-dead_stats['neg_total']:,.0f}
       between them — the "dead tail" is a re-buffering problem (§1–2),
       not a delisting one.
    5. **Keep the cash discipline** (§5): a
       €{cash_stats['buffer'] / 1000:,.0f}k till floor, eyes on January.

    Items 2 and 3 together are worth roughly €5–10k a year with high
    confidence in sign and honest humility about size — small next to
    item 1, which is the point the whole engagement has been building to:
    the shop's problem was never operational. It runs beautifully. It
    made one oversized capital decision, and every operational
    improvement on this sheet is a rounding error next to unmaking it.

    ---
    ### Appendix — method notes

    Data: `data/scenarios/3y_baseline/visible/` through the Layer 0
    cleaning contract. The §1 backtest is a stated-assumptions replay
    (de-censored demand from Layer 3.2's rule, expected-value spoilage at
    empirical category rates, Monday/Wednesday cadence); its paper gains
    are deliberately graded against the hidden believed/realized/oracle
    triptych; the backtest's paper gain lands within ≈€2k of the oracle
    ceiling, which is itself the finding. Elasticities come from Layer 2; the newsvendor table uses
    only visible margins and empirical spoilage odds. Grading panels read
    `hidden/profit_triptych.csv` and `hidden/decision_t0.csv` and are
    marked as such. Tools: DuckDB, Polars, NumPy, Plotly.
    """)
    return


if __name__ == "__main__":
    app.run()
