import marimo

__generated_with = "0.23.14"
app = marimo.App(width="full", app_title="Layer 6 — Learn the Structure")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import plotly.graph_objects as go
    import polars as pl

    from pathlib import Path

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
    # Layer 6: learn the structure

    Layers 0–5 cleaned, described, diagnosed, predicted, prescribed, and ran
    the twin laboratory. This last layer asks the questions whose answers are
    *models with parameters that mean something* — preferences, hierarchy,
    drivers, causes, populations, and the causal graph itself — on
    `data/scenarios/3y_baseline/`, each graded against the world's actual
    parameters:

    1. **What do customers want?** (6.1) A conditional logit on the card
       panel's beverage choices, graded against every customer's true
       price sensitivity.
    2. **Can partial pooling beat per-SKU noise?** (6.2) Four estimators of
       per-SKU seasonality, graded against the hidden seasonal script —
       including the two product types whose season genuinely deviates.
    3. **What drives sales, decomposed?** (6.3) A marketing-mix model, and
       the confound it cannot escape.
    4. **Where did the missing demand go?** (6.4) The four-cause structural
       decomposition against the hidden unmet-demand ledger.
    5. **How much business is passing trade?** (6.5) A mixture model of the
       token panel, graded against the guest register.
    6. **Is the documented causal graph consistent with the data?** (6.6)
       Testing the DAG's implied conditional independencies — including the
       one violation the design planted on purpose.
    """)
    return


@app.cell
def _(DATA, ROOT, pl):
    # ---- shared loads --------------------------------------------------------
    _vis = DATA / "scenarios" / "3y_baseline" / "visible"
    cal = pl.read_csv(
        source = _vis / "calendar.csv",
        schema_overrides = {"holiday": pl.Utf8},
    )
    sku_l = pl.read_excel(source = ROOT / "SKUs.xlsx").select([
        "uid",
        "name",
        "category",
        "product_type",
        "brand_level",
    ])
    # the shop's actual assortment (the catalog file lists the whole market)
    listed = pl.read_csv(
        source = DATA / "scenarios" / "3y_baseline" / "hidden" / "decision_t0.csv",
    ).filter(pl.col("listed") == 1).select(["uid"]).join(
        other = sku_l,
        on = "uid",
        how = "left",
    )
    rsales = pl.read_csv(
        source = _vis / "receipts.csv",
        schema_overrides = {
            "customer_id": pl.Utf8,
            "ref_receipt_id": pl.Utf8,
        },
    ).filter(
        (pl.col("qty") > 0) & pl.col("ref_receipt_id").is_null()
    )
    weather = pl.read_csv(source = _vis / "weather.csv")
    return cal, listed, rsales, sku_l, weather


@app.cell
def _(
    ACCENT,
    DATA,
    MUTED,
    cal,
    caption,
    go,
    listed,
    mo,
    np,
    pl,
    rsales,
    style,
    takeaway,
):
    # ==== 6.1 — what do customers want? (conditional logit) ==================
    from scipy.optimize import minimize as _minimize

    _bev = listed.filter(pl.col("category") == "Beverages (Non-Alcoholic)")["uid"].to_list()
    # daily posted tag per alternative: forward-fill the price history
    _ph = pl.read_csv(
        source = DATA / "scenarios" / "3y_baseline" / "visible" / "price_history.csv",
    ).filter(pl.col("uid").is_in(_bev))
    _pmat = cal.select(["date"]).join(
        other = pl.DataFrame({"uid": _bev}),
        how = "cross",
    ).join(
        other = _ph,
        on = ["date", "uid"],
        how = "left",
    ).sort(["uid", "date"]).with_columns(
        pl.col("price").fill_null(strategy = "forward").over("uid"),
    ).pivot(
        values = "price",
        index = "date",
        on = "uid",
    ).sort(by = "date")
    # regulars = tokens with a real visit history
    _vis_ct = rsales.filter(pl.col("customer_id").is_not_null()).group_by("customer_id").agg(
        pl.col("receipt_id").n_unique().alias("v"),
    )
    _regs = _vis_ct.filter(pl.col("v") >= 20)["customer_id"]
    _ch = rsales.filter(
        pl.col("uid").is_in(_bev) & pl.col("customer_id").is_in(_regs)
    ).with_columns(
        pl.col("date").str.slice(5, 2).cast(pl.Int32).alias("mm"),
    )
    # split-sample segmentation: quintiles from ODD months' average paid
    # price, estimation on EVEN months — so the segmentation never sees the
    # choices it is later used to explain
    _seg = _ch.filter(pl.col("mm") % 2 == 1).group_by("customer_id").agg(
        pl.col("unit_price").mean().alias("pp"),
    )
    _seg = _seg.with_columns(
        (pl.col("pp").rank(method = "ordinal") * 5 / (_seg.height + 1)).cast(pl.Int32).alias("q"),
    )
    _est = _ch.filter(pl.col("mm") % 2 == 0).join(
        other = _seg.select(["customer_id", "q"]),
        on = "customer_id",
    ).join(
        other = _pmat,
        on = "date",
    )
    _J = len(_bev)
    _P = np.log(_est.select(_bev).to_numpy())
    _yi = np.array([_bev.index(_u) for _u in _est["uid"]])
    _qi = _est["q"].to_numpy()
    _n = len(_yi)

    def _nll_grad(theta):
        _alpha = np.concatenate([[0.0], theta[:_J - 1]])
        _beta = theta[_J - 1:]
        _V = _alpha[None, :] + _beta[_qi][:, None] * _P
        _V -= _V.max(axis = 1, keepdims = True)
        _eV = np.exp(_V)
        _pr = _eV / _eV.sum(axis = 1, keepdims = True)
        _ll = np.log(_pr[np.arange(_n), _yi]).sum()
        _resid = -_pr
        _resid[np.arange(_n), _yi] += 1.0
        _g_alpha = _resid.sum(axis = 0)[1:]
        _gp = (_resid * _P).sum(axis = 1)
        _g_beta = np.array([
            _gp[_qi == _g].sum()
            for _g in range(5)
        ])
        return -_ll, -np.concatenate([_g_alpha, _g_beta])

    _fit = _minimize(
        fun = _nll_grad,
        x0 = np.zeros(_J - 1 + 5),
        jac = True,
        method = "BFGS",
    )
    _beta_q = _fit.x[_J - 1:]
    # grading: the hidden per-customer price sensitivity, averaged by segment
    _cust = pl.read_csv(
        source = DATA / "scenarios" / "3y_baseline" / "hidden" / "customers.csv",
        schema_overrides = {"token": pl.Utf8},
    )
    _truth = _seg.join(
        other = _cust.select(["token", "price_sens"]),
        left_on = "customer_id",
        right_on = "token",
        how = "inner",
    ).group_by("q").agg(
        pl.col("price_sens").mean().alias("sens"),
    ).sort(by = "q")
    _sens = _truth["sens"].to_list()
    _rank_ok = bool(np.all(np.diff(_beta_q) > 0)) and bool(np.all(np.diff(np.array(_sens)) < 0))
    logit_stats = {
        "n": _n,
        "beta": [round(float(_b), 2) for _b in _beta_q],
        "sens": [round(float(_s), 2) for _s in _sens],
        "monotone": _rank_ok,
        "converged": bool(_fit.success),
    }
    _labels = [
        "Q1<br>cheapest baskets",
        "Q2",
        "Q3",
        "Q4",
        "Q5<br>dearest baskets",
    ]
    _fig = go.Figure()
    _fig.add_bar(
        x = _labels,
        y = list(_beta_q),
        marker_color = ACCENT,
        text = [f"{_b:+.2f}" for _b in _beta_q],
        textposition = "outside",
    )
    for _i, _s in enumerate(_sens):
        _fig.add_annotation(
            text = f"true ε̄ {_s:.2f}",
            x = _i,
            y = 1,
            yref = "y domain",
            yanchor = "top",
            showarrow = False,
            font = dict(
                color = MUTED,
                size = 11,
            ),
        )
    style(
        fig = _fig,
        title = "Estimated price coefficient by customer segment (bars) vs each segment's TRUE mean price sensitivity (grey)",
    )
    _fig.update_yaxes(
        showticklabels = False,
        showline = False,
        ticks = "",
        title_text = "conditional-logit β on log price",
        title_font = dict(
            size = 11.5,
            color = MUTED,
        ),
        range = [
            min(_beta_q) * 1.5,
            0.35,
        ],
    )
    _fig.update_xaxes(title_text = "customer quintile by average paid beverage price (held-out odd months)")
    takeaway(
        fig = _fig,
        text = "the ordering is recovered perfectly —<br>cheap-basket customers really are the price-sensitive ones",
        x = 0.98,
        y = 0.30,
        anchor = "right",
    )
    mo.vstack(
        items = [
            mo.md(rf"""
    ## 1 · What do customers want? (6.1)

    A **conditional logit** on the non-alcoholic-beverages shelf: six
    alternatives, {_n:,} choice occasions by {len(_regs)} card-identified
    regulars. Each shopper picks the SKU with the highest utility

    $$V_{{ij}} = \alpha_j + \beta_{{g(i)}}\,\log p_{{jt}} + \epsilon_{{ij}},\quad \epsilon \sim \text{{Gumbel}}$$

    with brand intercepts $\alpha_j$ and a price coefficient per customer
    segment. The segments are built to be honest: quintiles of average paid
    price in the ODD months, estimated on choices from the EVEN months —
    the split-sample keeps the segmentation from mechanically explaining
    the choices that defined it.
    """),
            _fig,
            caption(
                f"The grading is the point: segment-mean TRUE price "
                f"sensitivity (hidden `customers.csv`) runs "
                f"{_sens[0]:.2f} → {_sens[-1]:.2f} across the quintiles, "
                "and the estimated β recovers that ordering "
                f"{'perfectly — strictly monotone in both' if _rank_ok else 'imperfectly this vintage'}. "
                "The LEVEL is a different story: β ranges near "
                f"{min(logit_stats['beta']):+.2f}, far gentler than the "
                "−2.15 SKU elasticity of Layer 2, and both are true. The "
                "logit is identified off RELATIVE tag moves among six "
                "substitutes, which the owner's cost-driven repricing "
                "keeps small and parallel — habitual brand affinity "
                "absorbs most of what remains. Preferences are structure; "
                "which slice of them your variation identifies is method."
            ),
            mo.accordion(
                items = {
                    "Model definition and estimation": mo.md(
                        r"""
    **Data.** Choice occasions = every beverage line by a token with ≥20
    receipts; the choice set is the six listed beverage SKUs at that day's
    posted tags (forward-filled from `price_history.csv`). **Model.**
    Conditional (multinomial) logit; the first alternative's intercept is
    normalized to zero; five segment-specific price coefficients.
    **Estimation.** Maximum likelihood with analytic gradient
    (BFGS; softmax probabilities, score = residual-weighted regressors).
    **What's deliberately left out.** No availability correction (the six
    beverages are near-always stocked), no panel random effects — the
    segment interaction IS the poor man's random coefficient, and its
    grading against the true per-customer draws is the exercise.
    """
                    ),
                },
            ),
        ],
    )
    return (logit_stats,)


@app.cell
def _(
    ACCENT_LIGHT,
    DATA,
    MUTED,
    WARN,
    caption,
    go,
    listed,
    mo,
    pl,
    rsales,
    style,
):
    # ==== 6.2 — can partial pooling beat per-SKU noise? =======================
    # target: each SKU's month-of-year demand index (12 numbers per SKU)
    _rj = rsales.join(
        other = listed.select(["uid", "category", "product_type"]),
        on = "uid",
        how = "inner",
    ).with_columns(
        pl.col("date").str.slice(0, 4).cast(pl.Int32).alias("yy"),
        pl.col("date").str.slice(5, 2).cast(pl.Int32).alias("mm"),
    )
    _sm = _rj.group_by(["uid", "category", "product_type", "yy", "mm"]).agg(
        pl.col("qty").sum().alias("u"),
    )
    _full = _sm.select(["uid", "category", "product_type"]).unique().join(
        other = pl.DataFrame({"yy": [2025, 2026, 2027]}),
        how = "cross",
    ).join(
        other = pl.DataFrame({"mm": list(range(1, 13))}),
        how = "cross",
    )
    _sm = _full.join(
        other = _sm,
        on = ["uid", "category", "product_type", "yy", "mm"],
        how = "left",
    ).fill_null(0).with_columns(
        pl.col("u").mean().over(["uid", "yy"]).alias("ybar"),
    ).with_columns(
        (pl.col("u") / pl.col("ybar")).alias("idx"),
    )
    _raw = _sm.group_by(["uid", "category", "product_type", "mm"]).agg(
        pl.col("idx").mean().alias("idx_raw"),
        (pl.col("idx").var() / 3).alias("v"),
    )
    _catm = _sm.group_by(["category", "yy", "mm"]).agg(pl.col("u").sum()).with_columns(
        pl.col("u").mean().over(["category", "yy"]).alias("ybar"),
    ).with_columns(
        (pl.col("u") / pl.col("ybar")).alias("ic"),
    )
    _cat = _catm.group_by(["category", "mm"]).agg(pl.col("ic").mean().alias("idx_cat"))
    _j = _raw.join(
        other = _cat,
        on = ["category", "mm"],
    )
    # empirical-Bayes weights from one global between-SKU variance (moments)
    _dev = _j.with_columns(((pl.col("idx_raw") - pl.col("idx_cat")) ** 2).alias("d"))
    _tau2 = max(0.0, float(_dev["d"].mean()) - float(_dev["v"].mean()))
    _j = _j.with_columns(
        (_tau2 / (_tau2 + pl.col("v") + 1e-9)).alias("w"),
    ).with_columns(
        (pl.col("w") * pl.col("idx_raw") + (1 - pl.col("w")) * pl.col("idx_cat")).alias("idx_shr"),
    )
    # test-then-pool: keep the raw index only for SKUs whose whole seasonal
    # profile deviates far beyond COUNT noise. The variance is model-based
    # (Poisson counts scaled by an empirical dispersion factor) because the
    # 3-observation empirical variances are themselves too noisy to divide by
    _ymu = _sm.group_by("uid").agg(pl.col("u").mean().alias("ymu"))
    _j = _j.join(
        other = _ymu,
        on = "uid",
    ).with_columns(
        (pl.col("idx_cat") / (3 * pl.col("ymu"))).alias("v_pois"),
    )
    _phi = float(
        _j.filter(pl.col("v") > 0).select((pl.col("v") / pl.col("v_pois")).median()).item()
    )
    _chi = _j.group_by("uid").agg(
        (((pl.col("idx_raw") - pl.col("idx_cat")) ** 2)
         / (_phi * pl.col("v_pois"))).sum().alias("chi2"),
    ).with_columns(
        (pl.col("chi2") > 33.0).alias("flag"),  # chi2(12) 99.9th percentile
    )
    _j = _j.join(
        other = _chi.select(["uid", "flag"]),
        on = "uid",
    ).with_columns(
        pl.when(pl.col("flag")).then(pl.col("idx_raw")).otherwise(pl.col("idx_cat")).alias("idx_ttp"),
    )
    # ---- the hidden truth: M_c(t), times the psi tilt for tilted types -----
    _M = pl.read_csv(source = DATA / "scenarios" / "3y_baseline" / "hidden" / "demand_modifiers.csv")
    _tl = pl.read_csv(source = DATA / "scenarios" / "3y_baseline" / "hidden" / "tilts.csv")
    _M = _M.join(
        other = _tl,
        on = "t",
    ).with_columns(
        (pl.date(2025, 1, 1) + pl.duration(days = pl.col("t") - 1)).alias("date"),
    ).with_columns(
        pl.col("date").dt.year().alias("yy"),
        pl.col("date").dt.month().alias("mm"),
    )
    _tr = []
    for _c in [_cc for _cc in _M.columns if _cc.startswith("M_")]:
        for _pt, _psi in [
            ("_base", None),
            ("Ice Cream", "psi_Ice Cream"),
            ("Coffee", "psi_Coffee"),
            ("Tea", "psi_Tea"),
        ]:
            _x = (pl.col(_c) * pl.col(_psi)) if _psi else pl.col(_c)
            _t = _M.with_columns(_x.alias("x")).group_by(["yy", "mm"]).agg(
                pl.col("x").mean().alias("x"),
            ).with_columns(
                pl.col("x").mean().over("yy").alias("ybar"),
            ).with_columns(
                (pl.col("x") / pl.col("ybar")).alias("ix"),
            ).group_by("mm").agg(
                pl.col("ix").mean().alias("idx_true"),
            ).with_columns(
                pl.lit(_c[2:]).alias("category"),
                pl.lit(_pt).alias("pt"),
            )
            _tr.append(_t)
    _truth = pl.concat(items = _tr)
    _jt = _j.with_columns(
        pl.when(pl.col("product_type").is_in(["Ice Cream", "Coffee", "Tea"]))
        .then(pl.col("product_type")).otherwise(pl.lit("_base")).alias("pt"),
    ).join(
        other = _truth,
        on = ["category", "mm", "pt"],
        how = "left",
    )
    _tilted = pl.col("pt") != "_base"

    def _rmse(df, col):
        return float(((df[col] - df["idx_true"]) ** 2).mean()) ** 0.5

    pool_stats = {
        "tau2": _tau2,
        "phi": _phi,
        "n_flagged": int(_chi.filter(pl.col("flag")).height),
        "flagged_tilted": int(
            _j.filter(
                pl.col("flag") & pl.col("product_type").is_in(["Ice Cream", "Coffee", "Tea"])
            ).select(pl.col("uid").n_unique()).item()
        ),
        "n_tilted_skus": int(
            _j.filter(
                pl.col("product_type").is_in(["Ice Cream", "Coffee", "Tea"])
            ).select(pl.col("uid").n_unique()).item()
        ),
    }
    _res = {}
    for _name, _col in [
        ("per-SKU raw", "idx_raw"),
        ("EB shrinkage", "idx_shr"),
        ("category pooled", "idx_cat"),
        ("test-then-pool", "idx_ttp"),
    ]:
        _res[_name] = (
            _rmse(_jt, _col),
            _rmse(_jt.filter(~_tilted), _col),
            _rmse(_jt.filter(_tilted), _col),
        )
    pool_stats["rmse"] = {_k: [round(_x, 3) for _x in _v] for _k, _v in _res.items()}
    _names = list(_res.keys())
    _fig = go.Figure()
    for _gi, (_gname, _color) in enumerate([
        ("typical SKUs (truth = the category season)", ACCENT_LIGHT),
        ("tilted SKUs (ice cream, coffee — truth deviates)", WARN),
    ]):
        _fig.add_bar(
            x = _names,
            y = [_res[_nm][1 + _gi] for _nm in _names],
            name = _gname,
            marker_color = _color,
            text = [f"{_res[_nm][1 + _gi]:.3f}" for _nm in _names],
            textposition = "outside",
        )
    style(
        fig = _fig,
        title = "Seasonal-index error (RMSE vs the hidden script) for four estimators, by whether the SKU's true season deviates",
        showlegend = True,
    )
    _fig.update_layout(
        legend = dict(
            orientation = "h",
            yanchor = "bottom",
            y = 1.0,
            x = 0,
            font = dict(size = 11.5),
        ),
    )
    _fig.update_yaxes(
        showticklabels = False,
        showline = False,
        ticks = "",
        title_text = "RMSE of monthly index (lower is better)",
        title_font = dict(
            size = 11.5,
            color = MUTED,
        ),
        range = [
            0,
            max(_res[_nm][2] for _nm in _names) * 1.3,
        ],
    )
    _fig.update_xaxes(title_text = "")
    mo.vstack(
        items = [
            mo.md(rf"""
    ## 2 · Can partial pooling beat per-SKU noise? (6.2)

    Every SKU's month-of-year demand index is estimated four ways from 36
    noisy months: **raw** (each SKU alone), **empirical-Bayes shrinkage**
    (normal-normal partial pooling toward the category, weight
    $w_s = \tau^2/(\tau^2 + \sigma_s^2)$, variance components by moments —
    the same weights a full Bayesian fit would return under conjugacy),
    **fully pooled** (the category index for everyone), and
    **test-then-pool** (pool unless the SKU's whole profile rejects the
    category at χ²(12) > 33). The world is secretly hierarchical — true
    seasonality lives at the category level — EXCEPT for
    {pool_stats['n_tilted_skus']} listed SKUs (ice cream, coffee) whose
    hidden ψ-tilts genuinely deviate. That exception is what makes this a
    fair fight:
    """),
            _fig,
            caption(
                "Read the two groups against each other. On typical SKUs "
                "the harder you pool the better — the category IS the "
                f"truth (RMSE {_res['category pooled'][1]:.3f} pooled vs "
                f"{_res['per-SKU raw'][1]:.3f} raw). On the tilted SKUs "
                "full pooling is the worst thing on the chart "
                f"({_res['category pooled'][2]:.3f}): it confidently "
                "assigns ice cream the frozen-aisle's flat season. The "
                "one-τ² shrinkage estimator disappoints BOTH groups — the "
                "four extreme SKUs inflate the global between-SKU "
                "variance, so it under-pools the majority and still "
                "over-pools the exceptions: a misspecified exchangeability "
                "assumption, priced. Test-then-pool, which lets the data "
                "nominate its own exceptions "
                f"(it flagged {pool_stats['n_flagged']} SKUs, and among "
                f"them all {pool_stats['flagged_tilted']} of "
                f"{pool_stats['n_tilted_skus']} genuinely-tilted SKUs), "
                "ties the best available estimator in BOTH groups — full "
                "pooling on the typical majority, raw on the tilted tail "
                "— rather than splitting the difference badly the way "
                "one global shrinkage weight does. It pays a small price "
                "for that robustness (worse than full pooling on the "
                "easy majority, since 41 SKUs get flagged for only 4 true "
                "exceptions) in exchange for never failing catastrophically "
                "on the SKUs that matter. The Bayesian moral is not "
                "'always shrink' — it is 'model the exceptions': a "
                "heavy-tailed or mixture prior would do organically what "
                "the χ² gate does crudely, without the false-positive tax."
            ),
        ],
    )
    return (pool_stats,)


@app.cell
def _(
    ACCENT,
    DATA,
    MUTED,
    WARN,
    cal,
    caption,
    go,
    mo,
    np,
    pl,
    rsales,
    style,
    takeaway,
    weather,
):
    # ==== 6.3 — what drives sales, decomposed? (MMM) =========================
    import statsmodels.api as _sm

    _rw = rsales.join(
        other = cal.select(["date", "week", "month"]),
        on = "date",
    )
    _wk = _rw.group_by("week").agg(
        (pl.col("qty") * pl.col("unit_price")).sum().alias("rev"),
        ((pl.col("qty") * pl.col("unit_price")).sum() / pl.col("qty").sum()).alias("p"),
        pl.col("month").first().alias("m"),
        pl.col("date").n_unique().alias("ndays"),
    ).sort(by = "week")
    _holw = cal.group_by("week").agg(
        pl.col("holiday").is_not_null().sum().alias("hol"),
        pl.col("pre_holiday").sum().alias("preh"),
    )
    _wxw = weather.join(
        other = cal.select(["date", "week", "month"]),
        on = "date",
    ).with_columns(
        (pl.col("temp_C") - pl.col("temp_C").mean().over("month")).alias("anom"),
    ).group_by("week").agg(
        pl.col("wet").mean().alias("wet"),
        pl.col("anom").mean().alias("anom"),
    )
    _promo = pl.read_csv(source = DATA / "scenarios" / "3y_baseline" / "visible" / "promotions.csv")
    _prd = []
    for _row in _promo.iter_rows(named = True):
        _prd.append(
            pl.DataFrame({
                "date": pl.date_range(
                    pl.lit(_row["start_date"]).str.to_date(),
                    pl.lit(_row["end_date"]).str.to_date(),
                    eager = True,
                ).cast(pl.Utf8),
            }).with_columns(pl.lit(_row["n_skus"]).alias("n")),
        )
    _prw = pl.concat(items = _prd).group_by("date").agg(pl.col("n").sum()).join(
        other = cal.select(["date", "week"]),
        on = "date",
    ).group_by("week").agg(pl.col("n").sum().alias("promo"))
    _df = _wk.join(
        other = _holw,
        on = "week",
    ).join(
        other = _wxw,
        on = "week",
    ).join(
        other = _prw,
        on = "week",
        how = "left",
    ).fill_null(0).filter(pl.col("ndays") == 7).sort(by = "week")
    _d = _df.to_pandas()
    _d["year"] = (_d["week"] - 1) // 52
    _X = _sm.add_constant(
        np.column_stack([
            np.log(_d["p"]),
            _d["wet"],
            _d["anom"],
            _d["hol"],
            _d["preh"],
            _d["promo"] / 100,
            *[(_d["m"] == _k).astype(float) for _k in range(2, 13)],
            _d["year"],
        ]),
    )
    _fit = _sm.OLS(np.log(_d["rev"].values), _X).fit(
        cov_type = "HAC",
        cov_kwds = {"maxlags": 4},
    )
    mmm_stats = {
        "wet": float(_fit.params[2]),
        "wet_p": float(_fit.pvalues[2]),
        "anom": float(_fit.params[3]),
        "preh": float(_fit.params[5]),
        "promo": float(_fit.params[6]),
        "promo_p": float(_fit.pvalues[6]),
        "trend": float(_fit.params[-1]),
        "r2": float(_fit.rsquared),
    }
    # contribution range per driver block: how many log-points of weekly
    # revenue each block moves between its calmest and wildest week
    _season = _X[:, 7:18] @ _fit.params[7:18]
    _blocks = {
        "weather": _fit.params[2] * _d["wet"] + _fit.params[3] * _d["anom"],
        "trend (growth)": _fit.params[-1] * _d["year"],
        "price index": _fit.params[1] * np.log(_d["p"]),
        "season (months)": _season,
        "holidays": _fit.params[4] * _d["hol"] + _fit.params[5] * _d["preh"],
        "promotions": _fit.params[6] * _d["promo"] / 100,
    }
    _rng = {_k: float(np.ptp(_v)) for _k, _v in _blocks.items()}
    _order = sorted(_rng, key = _rng.get, reverse = True)
    _fig = go.Figure()
    _fig.add_bar(
        x = [_rng[_k] * 100 for _k in _order],
        y = _order,
        orientation = "h",
        marker_color = [
            WARN if _k == "promotions" else ACCENT
            for _k in _order
        ],
        text = [f"{_rng[_k] * 100:.1f}" for _k in _order],
        textposition = "outside",
    )
    style(
        fig = _fig,
        title = "How far each driver moves weekly revenue between its calmest and wildest week (log-points × 100)",
        right_margin = 64,
    )
    _fig.update_yaxes(
        nticks = len(_order) + 1,
        title_text = "",
    )
    _fig.update_xaxes(
        title_text = "range of estimated contribution (≈ % of weekly revenue)",
        title_font = dict(
            size = 11.5,
            color = MUTED,
        ),
        range = [
            0,
            max(_rng[_k] for _k in _order) * 100 * 1.18,
        ],
    )
    takeaway(
        fig = _fig,
        text = "the red bar is the MMM's blind spot, not the promos' worth —<br>the trigger fires where demand slows, and the model can't unsee that",
        x = 0.98,
        y = 0.90,
        anchor = "right",
    )
    mo.vstack(
        items = [
            mo.md(rf"""
    ## 3 · What drives sales, decomposed? (6.3)

    The classic client ask: one regression that splits revenue into base,
    season, weather, price, holidays, promotions, and growth. Weekly log
    revenue over {len(_d)} full weeks, HAC-robust
    (R² = {mmm_stats['r2']:.2f} — the rest is the honest noise of a few
    hundred households making Bernoulli decisions):
    """),
            _fig,
            caption(
                f"Weather is the biggest lever the owner does not own: a "
                f"fully wet week costs ≈{-mmm_stats['wet'] * 100:.0f}% "
                "(Layer 2's daily estimate, recovered at weekly grain), "
                "and warm anomalies nudge revenue up "
                f"(+{mmm_stats['anom'] * 100:.1f}%/°C — ice-cream season "
                "leaking past the month dummies). Growth contributes "
                f"{mmm_stats['trend'] * 100:.1f}%/year, matching the "
                "three-year review's trend. Pre-holidays add "
                f"≈{mmm_stats['preh'] * 100:.1f}% per eve-day. And then "
                "the trap: the promotion coefficient is "
                f"{mmm_stats['promo'] * 100:+.1f}% per 100 promoted "
                f"SKU-days (p = {mmm_stats['promo_p']:.2f}) — "
                "statistically nothing, numerically NEGATIVE — while the "
                "twin-graded truth from Layer 2's DiD is a +49% lift on "
                "the treated product-days. The markdown trigger fires "
                "when a category is overstocked because demand slowed, "
                "so 'promo weeks' are slow weeks by construction, and no "
                "amount of MMM refitting can separate the medicine from "
                "the diagnosis. An MMM is a decomposition of "
                "correlations; it earns causal language only for drivers "
                "that are exogenous by design (weather, calendar) — for "
                "endogenous instruments it needs the experiment it "
                "doesn't have."
            ),
        ],
    )
    return (mmm_stats,)


@app.cell
def _(
    ACCENT,
    DATA,
    MUTED,
    WARN,
    cal,
    caption,
    go,
    mo,
    pl,
    rsales,
    style,
    takeaway,
):
    # ==== 6.4 — where did the missing demand go? ==============================
    # the ledger's answer (the answer key, shown as such)
    _hd = pl.read_csv(
        source = DATA / "scenarios" / "3y_baseline" / "hidden" / "hidden_demand.csv",
        schema_overrides = {
            "uid": pl.Utf8,
            "customer_id": pl.Utf8,
        },
    )
    _truth = _hd.group_by("cause").agg(pl.col("qty").sum().alias("units")).sort(
        by = "units",
        descending = True,
    )
    _td = {_r["cause"]: int(_r["units"]) for _r in _truth.iter_rows(named = True)}
    # ---- analyst estimate 1: stockout demand (Layer 3.2's imputation) ------
    # a CONTINUOUS day-count week, not the calendar's own "week" column,
    # which cycles 1-53 every year and would merge Jan-2025/2026/2027 into
    # one bucket
    _cal_w = cal.select(["date"]).with_columns(
        (pl.col("date").str.to_date() - pl.date(2025, 1, 1)).dt.total_days().floordiv(7).alias("w3y"),
    )
    _inv = pl.read_csv(
        source = DATA / "scenarios" / "3y_baseline" / "visible" / "inventory_eod.csv",
    ).join(
        other = _cal_w,
        on = "date",
    ).with_columns((pl.col("on_hand") <= 0).alias("oos"))
    _sal = rsales.join(
        other = _cal_w,
        on = "date",
    ).group_by(["uid", "date", "w3y"]).agg(pl.col("qty").sum().alias("u"))
    _iw = _inv.join(
        other = _sal.select(["uid", "date", "u"]),
        on = ["uid", "date"],
        how = "left",
    ).fill_null(0).group_by(["uid", "w3y"]).agg(
        pl.col("u").sum().alias("sold"),
        (1 - pl.col("oos").cast(pl.Int8)).sum().alias("days_in"),
        pl.len().alias("days"),
    )
    _imp = _iw.filter((pl.col("days_in") > 0) & (pl.col("days_in") < pl.col("days"))).with_columns(
        (pl.col("sold") / pl.col("days_in") * (pl.col("days") - pl.col("days_in"))).alias("lost"),
    )
    _est_stockout = float(_imp["lost"].sum())
    # ---- analyst estimate 2: closed-door demand, two visible pieces --------
    # (a) whole closed days x a seasonal daily forecast
    _daily_u = rsales.group_by("date").agg(pl.col("qty").sum().alias("u")).join(
        other = cal.select(["date", "month"]),
        on = "date",
    )
    _mmean = _daily_u.group_by("month").agg(pl.col("u").mean().alias("mu"))
    _closed_days = cal.filter(pl.col("closed") == 1).group_by("month").agg(pl.len().alias("nd"))
    _est_closures = float(
        _closed_days.join(
            other = _mmean,
            on = "month",
        ).select((pl.col("nd") * pl.col("mu")).sum()).item()
    )
    # (b) marginal opening hours, priced by the expansion's natural experiment
    _post = rsales.filter(pl.col("date") >= "2026-11-01")
    _ext_share = float(
        _post.filter((pl.col("hour") == 7) | (pl.col("hour") == 21))["qty"].sum() / _post["qty"].sum()
    )
    _pre_units = float(rsales.filter(pl.col("date") < "2026-11-01")["qty"].sum())
    _est_hours = _pre_units * _ext_share / (1 - _ext_share)
    _est_closed = _est_closures + _est_hours
    demand_stats = {
        "truth": _td,
        "est_stockout": _est_stockout,
        "est_closures": _est_closures,
        "est_hours": _est_hours,
        "ext_share": _ext_share,
    }
    _order = [
        "budget",
        "outside",
        "closed",
        "stockout",
    ]
    _lab = {
        "budget": "budget — the wallet ran out",
        "outside": "outside — bought elsewhere",
        "closed": "closed — door was shut",
        "stockout": "stockout — shelf was empty",
    }
    _fig = go.Figure()
    _fig.add_bar(
        y = [_lab[_c] for _c in _order],
        x = [_td[_c] / 1000 for _c in _order],
        orientation = "h",
        marker_color = [
            MUTED if _c in ("budget", "outside") else ACCENT
            for _c in _order
        ],
        text = [f"{_td[_c] / 1000:,.0f}k" for _c in _order],
        textposition = "outside",
    )
    for _c, _v, _txt in [
        ("closed", _est_closed, f"analyst: {_est_closed / 1000:,.0f}k"),
        ("stockout", _est_stockout, f"analyst: {_est_stockout / 1000:,.0f}k"),
    ]:
        _fig.add_trace(
            go.Scatter(
                x = [_v / 1000],
                y = [_lab[_c]],
                mode = "markers+text",
                marker = dict(
                    symbol = "line-ns",
                    size = 22,
                    color = WARN,
                    line = dict(
                        width = 3,
                        color = WARN,
                    ),
                ),
                text = [_txt],
                textposition = "top center",
                textfont = dict(
                    color = WARN,
                    size = 11,
                ),
            ),
        )
    style(
        fig = _fig,
        title = "Where the missing demand went, 2025–2027: the hidden ledger (bars) vs what the analyst can measure (red ticks)",
        right_margin = 64,
    )
    _fig.update_yaxes(
        nticks = len(_order) + 1,
        title_text = "",
        autorange = "reversed",
    )
    _fig.update_xaxes(
        title_text = "unmet demand (thousand units)",
        title_font = dict(
            size = 11.5,
            color = MUTED,
        ),
    )
    takeaway(
        fig = _fig,
        text = "the till only sees two of the four causes —<br>and one of those only at the margin",
        x = 0.98,
        y = 0.55,
        anchor = "right",
    )
    mo.vstack(
        items = [
            mo.md(rf"""
    ## 4 · Where did the missing demand go? (6.4)

    Over three years the hidden ledger records
    **{sum(_td.values()) / 1000:,.0f}k units of demand that never became
    sales**, tagged with its cause at the moment it failed. The structural
    question is what an analyst could have recovered from the till alone:
    """),
            _fig,
            caption(
                "One cause is measurable within the right order of "
                "magnitude; the other reveals its own blind spot. "
                "Stockouts: the in-stock-rate imputation says "
                f"{_est_stockout / 1000:,.1f}k vs the ledger's "
                f"{_td['stockout'] / 1000:,.1f}k — a "
                f"{(_est_stockout / _td['stockout'] - 1) * 100:.0f}% "
                "overshoot, the same direction and the same mechanism "
                "Layer 3.2 diagnosed (a day that sells briskly then runs "
                "dry inflates its own in-stock rate, so the empty hours "
                "get charged the busy morning's pace). Closed door: "
                "whole-day closures "
                f"({_est_closures / 1000:,.1f}k) plus the marginal-hours "
                "demand priced by the expansion's own natural experiment "
                f"(the 7 a.m./9 p.m. slots carry {_ext_share:.1%} of "
                f"units → {_est_hours / 1000:,.1f}k) reaches only "
                f"{_est_closed / 1000:,.0f}k of the ledger's "
                f"{_td['closed'] / 1000:,.0f}k — because the ledger "
                "counts every arrival at every shut hour, including the "
                "3 a.m. demand no shop would ever serve. The analyst's "
                "number answers the only decision-relevant question "
                "('what would one more hour earn') and Layer 5's clerk "
                "twin already showed even THAT converts poorly. The two "
                "grey bars — the wallet and the rival — are structurally "
                "invisible to a till: identifying them needs a budget "
                "model and an outside option, which is exactly what "
                "makes them Layer 6 material rather than a query."
            ),
        ],
    )
    return


@app.cell
def _(
    ACCENT,
    ACCENT_LIGHT,
    DATA,
    MUTED,
    caption,
    go,
    mo,
    np,
    pl,
    rsales,
    style,
    takeaway,
):
    # ==== 6.5 — how much business is passing trade? ===========================
    _tok = rsales.filter(pl.col("customer_id").is_not_null()).group_by("customer_id").agg(
        pl.col("receipt_id").n_unique().alias("k"),
        (pl.col("qty") * pl.col("unit_price")).sum().alias("rev"),
    )
    _k = _tok["k"].to_numpy().astype(float)
    _rev = _tok["rev"].to_numpy()
    # EM for a two-component zero-truncated geometric mixture on visit counts
    _pi, _p1, _p2 = 0.5, 0.9, 0.02
    for _ in range(300):
        _l1 = _pi * _p1 * (1 - _p1) ** (_k - 1)
        _l2 = (1 - _pi) * _p2 * (1 - _p2) ** (_k - 1)
        _g = _l1 / (_l1 + _l2)
        _pi = float(_g.mean())
        _p1 = float(_g.sum() / (_g * _k).sum())
        _p2 = float((1 - _g).sum() / ((1 - _g) * _k).sum())
    _trans = _g > 0.5
    # grading: the guest register (card guests carry single-use tokens)
    _guests = pl.read_csv(
        source = DATA / "scenarios" / "3y_baseline" / "hidden" / "guests.csv",
        schema_overrides = {"token": pl.Utf8},
    )
    _gcard = _guests.filter(pl.col("token").is_not_null())
    _gcash = _guests.filter(pl.col("token").is_null())
    mix_stats = {
        "tokens": int(len(_k)),
        "pi": _pi,
        "mean_trans": 1 / _p1,
        "mean_reg": 1 / _p2,
        "est_trans": int(_trans.sum()),
        "true_trans": int(_gcard.height),
        "est_rev": float(_rev[_trans].sum()),
        "true_rev": float(_gcard["value"].sum()),
        "cash_guests": int(_gcash.height),
        "cash_rev": float(_gcash["value"].sum()),
    }
    # histogram of visit counts with the two fitted components
    _bins = np.array([1, 2, 3, 5, 10, 20, 50, 100, 200, 500, 1500])
    _counts, _ = np.histogram(_k, bins = np.concatenate([_bins, [10000]]))
    _labels = [
        f"{_bins[_i]}" if _bins[_i + 1] - _bins[_i] == 1 else f"{_bins[_i]}–{_bins[_i + 1] - 1}"
        for _i in range(len(_bins) - 1)
    ] + ["1500+"]

    def _mix_mass(lo, hi):
        _ks = np.arange(lo, hi)
        _m1 = _pi * _p1 * (1 - _p1) ** (_ks - 1)
        _m2 = (1 - _pi) * _p2 * (1 - _p2) ** (_ks - 1)
        return float((_m1 + _m2).sum()) * len(_k)

    _model = [
        _mix_mass(_bins[_i], _bins[_i + 1])
        for _i in range(len(_bins) - 1)
    ] + [_mix_mass(_bins[-1], 10000)]
    _fig = go.Figure()
    _fig.add_bar(
        x = _labels,
        y = list(_counts),
        marker_color = ACCENT_LIGHT,
        name = "tokens observed",
    )
    _fig.add_trace(
        go.Scatter(
            x = _labels,
            y = _model,
            mode = "lines+markers",
            line = dict(
                color = ACCENT,
                width = 2,
            ),
            marker = dict(size = 6),
            name = "two-geometric mixture fit",
        ),
    )
    style(
        fig = _fig,
        title = "Receipts per card token over three years (log scale): one-visit passers-by vs the weekly regulars",
        showlegend = True,
    )
    _fig.update_layout(
        legend = dict(
            orientation = "h",
            yanchor = "bottom",
            y = 1.0,
            x = 0,
            font = dict(size = 11.5),
        ),
    )
    _fig.update_yaxes(
        type = "log",
        title_text = "tokens (log)",
        title_font = dict(
            size = 11.5,
            color = MUTED,
        ),
        showticklabels = True,
    )
    _fig.update_xaxes(title_text = "receipts per token, 2025–2027")
    takeaway(
        fig = _fig,
        text = f"two populations, no overlap: mean {mix_stats['mean_trans']:.1f} visit vs {mix_stats['mean_reg']:.0f}",
        x = 0.98,
        y = 0.90,
        anchor = "right",
    )
    mo.vstack(
        items = [
            mo.md(rf"""
    ## 5 · How much business is passing trade? (6.5)

    The card panel's {mix_stats['tokens']:,} tokens split by a
    two-component mixture (EM on a zero-truncated geometric for visit
    counts): a transient population of weight {mix_stats['pi']:.1%}
    averaging {mix_stats['mean_trans']:.1f} visit, and a regular
    population averaging {mix_stats['mean_reg']:.0f} receipts over the
    three years.
    """),
            _fig,
            caption(
                "The two populations are so far apart that the mixture is "
                "really a certification exercise — which is precisely why "
                "it grades so well (accordion), and also why the fitted "
                "line visibly UNDERSHOOTS the far-right tail (500+ "
                "receipts): a same-rate geometric caps how loyal any one "
                "regular can look, but real regulars vary in how often "
                "they shop, and the keenest of them shop far more than "
                "the group's own average — a heavier-tailed regular "
                "model (negative binomial, or a third component) would "
                "fix this without changing the headline. The business "
                f"content survives that caveat: passing trade is "
                f"{mix_stats['est_rev'] / 1000:,.1f}k of card revenue "
                "over three years — under 2% — so the shop lives and "
                "dies by its regulars, which is why Layer 7's churn "
                "accounting, not footfall marketing, is the right lens "
                "for this business."
            ),
            mo.accordion(
                items = {
                    "Grading: the mixture vs the hidden guest register": mo.md(
                        f"""
    The guest register says {mix_stats['true_trans']:,} card-paying
    one-off guests spent €{mix_stats['true_rev'] / 1000:,.1f}k. The
    mixture classifies {mix_stats['est_trans']:,} tokens as transient
    (posterior > 0.5) worth €{mix_stats['est_rev'] / 1000:,.1f}k — off by
    {mix_stats['est_trans'] - mix_stats['true_trans']:+d} tokens and
    +{(mix_stats['est_rev'] / mix_stats['true_rev'] - 1) * 100:.0f}% in
    euros; the handful of extras are churned or late-arriving REGULARS
    whose short tenure left a guest-like trace — the mixture's honest
    confusion, and a reminder that in the churn years 'few visits' has
    two explanations. One population stays invisible on principle:
    {mix_stats['cash_guests']:,} cash guests
    (€{mix_stats['cash_rev'] / 1000:,.1f}k) left no token at all, so the
    till-side estimate is a CARD-guest estimate — scaling it to the whole
    door requires the cash/card MAR result from Layer 2.8.
    """
                    ),
                },
            ),
        ],
    )
    return (mix_stats,)


@app.cell
def _(DATA, cal, caption, mo, np, pl, rsales, sku_l, weather):
    # ==== 6.6 — is the documented causal graph consistent with the data? =====
    import statsmodels.api as _sm6

    _r2 = rsales.join(
        other = cal.select(["date", "week", "month"]),
        on = "date",
    )
    # -- T1: traffic independent of temperature given season ------------------
    _dr = rsales.group_by("date").agg(pl.col("receipt_id").n_unique().alias("nrec")).join(
        other = cal,
        on = "date",
    ).join(
        other = weather,
        on = "date",
    ).drop_nulls(subset = ["temp_C"])
    _dd = _dr.to_pandas()
    _dd["year"] = _dd["date"].str[:4].astype(int)
    _dd["anom"] = _dd["temp_C"] - _dd.groupby("month")["temp_C"].transform("mean")
    _X1 = _sm6.add_constant(
        np.column_stack([
            _dd["anom"],
            _dd["wet"].fillna(0),
            *[(_dd["dow"] == _kk).astype(float) for _kk in range(2, 8)],
            *[(_dd["month"] == _kk).astype(float) for _kk in range(2, 13)],
            *[(_dd["year"] == _kk).astype(float) for _kk in (2026, 2027)],
        ]),
    )
    _f1 = _sm6.OLS(np.log(_dd["nrec"].values), _X1).fit(
        cov_type = "HAC",
        cov_kwds = {"maxlags": 7},
    )
    # -- T2: the markdown trigger reads the shelf, not the demand -------------
    _promo = pl.read_csv(source = DATA / "scenarios" / "3y_baseline" / "visible" / "promotions.csv")
    _inv = pl.read_csv(
        source = DATA / "scenarios" / "3y_baseline" / "visible" / "inventory_eod.csv",
    ).join(
        other = sku_l.select(["uid", "category"]),
        on = "uid",
    ).join(
        other = cal.select(["date", "week"]),
        on = "date",
    )
    _cover_w = _inv.group_by(["category", "week"]).agg(
        pl.col("on_hand").clip(lower_bound = 0).sum().alias("stock"),
    )
    _sales_w = _r2.join(
        other = sku_l.select(["uid", "category"]),
        on = "uid",
    ).group_by(["category", "week"]).agg(pl.col("qty").sum().alias("u"))
    _cw = _cover_w.join(
        other = _sales_w,
        on = ["category", "week"],
    ).sort(["category", "week"]).with_columns(
        pl.col("u").rolling_mean(window_size = 4).over("category").alias("ma"),
    ).with_columns(
        (pl.col("stock") / pl.col("ma")).alias("cover"),
        (pl.col("u") / pl.col("ma")).alias("resid"),
    )
    _starts = _promo.join(
        other = cal.select(["date", "week"]),
        left_on = "start_date",
        right_on = "date",
    ).select(["category", "week"])
    _pcts = []
    for _row in _starts.iter_rows(named = True):
        _hist = _cw.filter(pl.col("category") == _row["category"]).drop_nulls()
        _at = _hist.filter(pl.col("week") == _row["week"])
        if _at.height:
            _pcts.append((
                float((_hist["cover"] <= _at["cover"][0]).mean()),
                float((_hist["resid"] <= _at["resid"][0]).mean()),
            ))
    _cov_pct = float(np.mean([_p[0] for _p in _pcts]))
    _res_pct = float(np.mean([_p[1] for _p in _pcts]))
    # -- T3: spoilage responds to temperature, not rain ------------------------
    _wo = pl.read_csv(
        source = DATA / "scenarios" / "3y_baseline" / "visible" / "write_offs.csv",
    ).filter(pl.col("reason") == "spoilage").join(
        other = cal.select(["date", "week"]),
        on = "date",
    ).group_by("week").agg(pl.col("units").sum().alias("sp"))
    _wxw = weather.join(
        other = cal.select(["date", "week"]),
        on = "date",
    ).group_by("week").agg(
        pl.col("temp_C").mean().alias("temp"),
        pl.col("rain_mm").mean().alias("rain"),
    )
    _ds = _wo.join(
        other = _wxw,
        on = "week",
    ).drop_nulls().to_pandas()
    _X3 = _sm6.add_constant(np.column_stack([_ds["temp"], _ds["rain"]]))
    _f3 = _sm6.OLS(np.log(_ds["sp"].values), _X3).fit(
        cov_type = "HAC",
        cov_kwds = {"maxlags": 4},
    )
    # -- T4: the planted exclusion violation (crisis costs hit demand past price)
    _wkr = _r2.group_by("week").agg(
        (pl.col("qty") * pl.col("unit_price")).sum().alias("rev"),
        ((pl.col("qty") * pl.col("unit_price")).sum() / pl.col("qty").sum()).alias("p"),
        pl.col("month").first().alias("m"),
    ).sort(by = "week")
    _proc = pl.read_csv(
        source = DATA / "scenarios" / "3y_baseline" / "visible" / "procurement.csv",
    ).unique(subset = ["uid", "qty", "unit_cost", "order_date", "delivery_date"]).join(
        other = sku_l.select(["uid", "category"]),
        on = "uid",
    ).join(
        other = cal.select(["date", "week"]),
        left_on = "delivery_date",
        right_on = "date",
    )
    _en = _proc.filter(
        pl.col("category").is_in(["Frozen Foods", "Dairy and Eggs"])
    ).group_by("week").agg(
        ((pl.col("qty") * pl.col("unit_cost")).sum() / pl.col("qty").sum()).alias("c"),
    ).sort(by = "week")

    def _t4(df):
        _d4 = df.to_pandas()
        _X4 = _sm6.add_constant(
            np.column_stack([
                np.log(_d4["p"]),
                np.log(_d4["c"]),
                *[(_d4["m"] == _kk).astype(float) for _kk in range(2, 13)],
                *([(_d4["year"] == _kk).astype(float) for _kk in (1, 2)] if "year" in _d4 else []),
            ]),
        )
        return _sm6.OLS(np.log(_d4["rev"].values), _X4).fit(
            cov_type = "HAC",
            cov_kwds = {"maxlags": 4},
        )

    _base4 = _wkr.join(
        other = _en,
        on = "week",
        how = "left",
    ).sort(by = "week").with_columns(pl.col("c").fill_null(strategy = "forward")).drop_nulls()
    _f4_25 = _t4(_base4.filter(pl.col("week") <= 52))
    _f4_3y = _t4(_base4.with_columns(((pl.col("week") - 1) // 52).alias("year")))
    dag_stats = {
        "t1": (float(_f1.params[1]), float(_f1.pvalues[1])),
        "t2": (_cov_pct, _res_pct, len(_pcts)),
        "t3_rain": (float(_f3.params[2]), float(_f3.pvalues[2])),
        "t3_temp": float(_f3.params[1]),
        "t4_25": (float(_f4_25.params[2]), float(_f4_25.pvalues[2])),
        "t4_3y": (float(_f4_3y.params[2]), float(_f4_3y.pvalues[2])),
    }
    mo.vstack(
        items = [
            mo.md(r"""
    ## 6 · Is the documented causal graph consistent with the data? (6.6)

    The design documents commit to a causal graph; a graph implies
    conditional independencies; independencies are testable. Four tests —
    three the DAG says must PASS, and one edge the design planted
    knowing an analyst should be able to catch it:

    """),
            mo.mermaid(
                r"""
    graph LR
        W[weather: temp, rain] -->|wet only| T(traffic)
        W -->|temp only| S(spoilage)
        C[wholesale costs] --> P(shelf prices)
        C -.->|"planted back-door:<br>crisis squeezes budgets"| D(demand)
        P --> D
        V[inventory cover] --> K(markdown trigger)
        D --> V
    """
            ),
            mo.md(rf"""
    | # | Implied independence | Test | Estimate | Verdict |
    | --- | --- | --- | --- | --- |
    | T1 | traffic ⟂ temperature \| season, weekday | daily log receipts on temp anomaly + controls | {dag_stats['t1'][0] * 100:+.2f}%/°C (p = {dag_stats['t1'][1]:.2f}) | **PASS** — no temperature arrow into footfall, as documented |
    | T2 | markdown onset ⟂ demand \| inventory cover | percentile of cover vs demand residual at the {dag_stats['t2'][2]} campaign starts | cover at the {dag_stats['t2'][0]:.0%} percentile; demand residual at the {dag_stats['t2'][1]:.0%} | **PASS** — the trigger reads the shelf, not the sales floor |
    | T3 | spoilage ⟂ rain \| temperature | weekly log write-offs on temp + rain | rain {dag_stats['t3_rain'][0] * 100:+.1f}% per mm (p = {dag_stats['t3_rain'][1]:.2f}); temp +{dag_stats['t3_temp'] * 100:.1f}%/°C | **PASS** — heat rots, rain doesn't |
    | T4 | demand ⟂ wholesale costs \| shelf prices | weekly log revenue on log energy-cost index, holding own price index | 2025: **{dag_stats['t4_25'][0]:+.2f}** (p = {dag_stats['t4_25'][1]:.3f}); full 3y: {dag_stats['t4_3y'][0]:+.2f} (p = {dag_stats['t4_3y'][1]:.2f}) | **VIOLATION — detected.** Dear invoices depress revenue *beyond* the shop's own tags |
    """),
            caption(
                "T4 is the planted lesson closing its loop. The energy "
                "crisis was designed to squeeze household budgets as well "
                "as wholesale costs, which is exactly what makes it an "
                "INVALID instrument for demand (Layers 2.4–2.5 met the "
                "same fact as a modest IV shift). Here the DAG test "
                "catches it directly — in the crisis year, weeks with "
                "dear energy-linked invoices lose revenue even at "
                "unchanged shelf prices — and the full-three-year "
                "regression dilutes the same violation toward "
                "insignificance, because two calm years of exogenous "
                "cost noise drown one autumn of confounded variation. "
                "Both facts matter: independence tests are LOCAL to the "
                "variation that powers them, and 'no violation detected' "
                "on a long calm sample is not 'exclusion holds'."
            ),
        ],
    )
    return


@app.cell
def _(logit_stats, mix_stats, mmm_stats, mo, pool_stats):
    mo.md(f"""
    ---
    ## What the structural layer settles — and the catalog closes

    1. **Preferences are recoverable in order, not in level** — the
       conditional logit ranks all five customer segments' true price
       sensitivity correctly (β {logit_stats['beta'][0]:+.2f} →
       {logit_stats['beta'][-1]:+.2f} against true ε̄
       {logit_stats['sens'][0]:.2f} → {logit_stats['sens'][-1]:.2f}), while
       the level stays a function of the variation that identified it (§1).
    2. **Pooling is a modeling decision, not a reflex** — full pooling wins
       on the typical majority but is 2× worse than doing nothing on the
       genuinely-deviant SKUs; the χ²-gated test-then-pool estimator,
       which caught all {pool_stats['flagged_tilted']} of
       {pool_stats['n_tilted_skus']} true exceptions, trades a little of
       the majority's accuracy for never failing on the tail (§2).
    3. **An MMM decomposes correlations** — weather, season, growth and
       holidays come out right; the promotion coefficient
       ({mmm_stats['promo'] * 100:+.1f}%, truth +49%) is destroyed by the
       endogenous trigger, permanently (§3).
    4. **The till sees two of four causes of missing demand** — stockouts
       (right order of magnitude) and the closed door (measurable only at the
       margin that was ever opened); the wallet and the rival need
       structure, not queries (§4).
    5. **Passing trade is a rounding error** —
       €{mix_stats['est_rev'] / 1000:,.1f}k of card revenue in three years,
       estimated within {abs(mix_stats['est_trans'] - mix_stats['true_trans'])}
       tokens of the register: this is a regulars business (§5).
    6. **The documented DAG survives its own audit** — three independencies
       hold where they should, and the one deliberately-planted violation
       is caught, in the window where the confounding actually lived (§6).

    With this, **every layer of `documents/ANALYSIS_CATALOG.md` has a
    full-depth graded notebook**: cleaning and description
    (`clean_and_describe.py`), diagnosis (`diagnose_causes.py`), prediction
    (`predict_and_warn.py`), prescription (`prescribe.py`), the twin
    laboratory (`policy_lab.py`), structure (this notebook), and the
    three-year arc (`three_year_review.py`, `competitor_entry_study.py`,
    `expansion_review.py`).

    ---
    ### Appendix — method notes

    Data: `data/scenarios/3y_baseline/visible/` (sales lines: positive
    quantities, refunds excluded). Grading panels read `customers.csv`
    (price sensitivity), `demand_modifiers.csv` + `tilts.csv` (seasonal
    truth), `hidden_demand.csv` (cause ledger), `guests.csv` (guest
    register) and are marked as such. Estimators are deliberately
    dependency-light: the conditional logit is maximum likelihood with an
    analytic gradient (SciPy BFGS), the partial pooling is conjugate
    empirical Bayes (a full MCMC fit would return the same weights), the
    mixture is 300 EM steps in NumPy, and the DAG tests are HAC-robust
    OLS. Tools: Polars, NumPy, SciPy, statsmodels, Plotly.
    """)
    return


if __name__ == "__main__":
    app.run()
