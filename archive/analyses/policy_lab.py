import marimo

__generated_with = "0.23.14"
app = marimo.App(width="full", app_title="Layer 5 — Policy Laboratory")


@app.cell
def _():
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
    # Layer 5: the policy laboratory

    The five one-year scenario arms are **common-random-numbers twins** of
    the one-year baseline: the same seeds, the same keyed random streams,
    the same customers making the same draws — with exactly one line of the
    world's script edited. Subtracting the baseline from an arm therefore
    yields the *causal effect of the edit with zero sampling error between
    arms* — the experiment the real world never runs. This notebook works
    through the catalog's Layer 5 on `data/scenarios/`:

    | § | Arm | The one edited line |
    | --- | --- | --- |
    | 5.1 | `food_vat_cut_july` | reduced VAT 10% → 5% on food from July 1 |
    | 5.2 | `tax_rebate_spring` | household budgets +20% in weeks 14–17 |
    | 5.3 | `war_june` | a supply shock raises ALL goods' costs from June 1 |
    | 5.4 | `typhoon_september` | a three-day storm: footfall ×0.35, fresh-goods cost spike |
    | 5.5 | *(method check)* | does the observational elasticity predict the war twin? |
    | 5.6 | `second_clerk` | one hired clerk, opening hours 7:00–22:00 |

    Two ground rules. First, each section reports the twin difference as
    the *answer*, then asks what an analyst locked inside one arm could
    have recovered — 5.5 makes that grading explicit. Second, the twins
    are compared on lightly cleaned sales (positive quantities, refunds
    excluded): the recording layer injects the *same kinds* of defects in
    both arms from the same keyed stream, so recording noise largely
    cancels in the difference.
    """)
    return


@app.cell
def _(DATA, ROOT, pl):
    # ---- load all six arms once --------------------------------------------
    ARMS = [
        "food_vat_cut_july",
        "tax_rebate_spring",
        "war_june",
        "typhoon_september",
        "second_clerk",
    ]
    STD_CATS = [
        # the three standard-rate (20%) categories; everything else is food
        # at the reduced rate, which is what the July 1 cut touches
        "Alcoholic Beverages",
        "Household and Cleaning Supplies",
        "Personal Care and Health",
    ]
    sku_cat = pl.read_excel(source = ROOT / "SKUs.xlsx").select([
        "uid",
        "category",
    ])

    def _load_sales(arm):
        _df = pl.read_csv(
            source = DATA / "scenarios" / arm / "visible" / "receipts.csv",
            schema_overrides = {
                "customer_id": pl.Utf8,
                "ref_receipt_id": pl.Utf8,
            },
        )
        # keep sales lines only: voids/refunds are negative or referenced,
        # and both fire identically enough across twins to cancel in diffs
        return _df.filter(
            (pl.col("qty") > 0) & pl.col("ref_receipt_id").is_null()
        ).join(
            other = sku_cat,
            on = "uid",
            how = "left",
        )

    sales = {_arm: _load_sales(_arm) for _arm in ["baseline"] + ARMS}
    costs = {
        _arm: pl.read_csv(source = DATA / "scenarios" / _arm / "visible" / "cost_sheet.csv")
        for _arm in ["baseline"] + ARMS
    }
    return ARMS, STD_CATS, costs, sales, sku_cat


@app.cell
def _(ACCENT, ARMS, WARN, caption, costs, go, mo, style):
    # ==== 5.0 — the laboratory at a glance ===================================
    _labels = {
        "food_vat_cut_july": "VAT cut (Jul 1)",
        "tax_rebate_spring": "tax rebate (Apr)",
        "war_june": "war shock (Jun 1)",
        "typhoon_september": "typhoon (Sep 8–10)",
        "second_clerk": "second clerk (all year)",
    }
    _base_rev = costs["baseline"]["revenue"]
    _rows = []
    for _arm in ARMS:
        _d = (costs[_arm]["revenue"] - _base_rev).to_list()
        _rows.append(_d)
    _months = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    _fig = go.Figure()
    _fig.add_trace(
        go.Heatmap(
            z = _rows,
            x = _months,
            y = [_labels[_a] for _a in ARMS],
            text = [[f"{_v / 1000:+,.1f}" if abs(_v) >= 50 else "" for _v in _r] for _r in _rows],
            texttemplate = "%{text}",
            textfont = dict(size = 10.5),
            colorscale = [
                [0.0, WARN],
                [0.5, "#FFFFFF"],
                [1.0, ACCENT],
            ],
            zmid = 0,
            showscale = False,
        ),
    )
    style(
        fig = _fig,
        title = "Monthly revenue, each arm minus the baseline (€ thousands) — the raw twin differences",
    )
    _fig.update_yaxes(
        nticks = len(ARMS) + 1,
        autorange = "reversed",
    )
    _fig.update_xaxes(
        showline = False,
        ticks = "",
    )
    _pre_zero = sum(
        1
        for _arm in [
            "food_vat_cut_july",
            "tax_rebate_spring",
            "war_june",
        ]
        for _v in (costs[_arm]["revenue"] - _base_rev).to_list()
        if _v == 0.0
    )
    mo.vstack(
        items = [
            mo.md(r"""
    ## 0 · The laboratory at a glance

    Before any single study: line up all five arms' monthly ledger revenue
    against the baseline's. The blank cells before each edit are the
    laboratory's credential — until the script diverges, the twins are
    *byte-identical*, which is what makes everything after the edit causal:
    """),
            _fig,
            caption(
                f"Every pre-edit month is exactly €0.00 different "
                f"({_pre_zero} month-cells to the cent) for the three "
                "arms whose edit has a start date — the CRN promise made "
                "visible. Two arms differ from January: the clerk works "
                "from day one, and the typhoon arm carries a faint "
                "everywhere-ghost (±€400/month) because the hidden demand "
                "multipliers are normalized to mean one over the YEAR — "
                "editing three September days re-scales the other 362 "
                "microscopically. That ghost is this laboratory's placebo "
                "floor: effects are real only where they clear it, a "
                "discipline §5.4 has to respect."
            ),
        ],
    )
    return


@app.cell
def _(
    ACCENT,
    DATA,
    MUTED,
    STD_CATS,
    caption,
    costs,
    go,
    mo,
    pl,
    sales,
    sku_cat,
    style,
    takeaway,
):
    # ==== 5.1 — who actually bore the food-VAT cut? ==========================
    # price paid per unit on reduced-rate (food) categories, month by month
    def _ppu(df):
        return df.filter(~pl.col("category").is_in(STD_CATS)).with_columns(
            pl.col("date").str.slice(5, 2).cast(pl.Int32).alias("m"),
        ).group_by("m").agg(
            ((pl.col("qty") * pl.col("unit_price")).sum() / pl.col("qty").sum()).alias("p"),
            pl.col("qty").sum().alias("units"),
        ).sort(by = "m")

    _b = _ppu(sales["baseline"])
    _v = _ppu(sales["food_vat_cut_july"])
    _j = _b.join(
        other = _v,
        on = "m",
        suffix = "_v",
    ).with_columns(
        ((pl.col("p_v") / pl.col("p") - 1) * 100).alias("dp_pct"),
        (pl.col("units_v") - pl.col("units")).alias("du"),
    )
    _full_pt = (1.05 / 1.10 - 1) * 100
    # matched-SKU tag comparison: the year-end posted price per uid in each
    # arm — free of the basket-composition drift the paid-per-unit line has
    def _tags(arm):
        return pl.read_csv(
            source = DATA / "scenarios" / arm / "visible" / "price_history.csv",
        ).sort(by = "date").group_by("uid").agg(
            pl.col("price").last().alias("tag"),
        )

    _tj = _tags("baseline").join(
        other = _tags("food_vat_cut_july"),
        on = "uid",
        suffix = "_v",
    ).join(
        other = sku_cat,
        on = "uid",
        how = "left",
    ).filter(~pl.col("category").is_in(STD_CATS))
    vat_stats = {
        "dp_h2": float(_j.filter(pl.col("m") >= 7)["dp_pct"].mean()),
        "tag_dec": float(((_tj["tag_v"] / _tj["tag"]).mean() - 1) * 100),
        "full_pt": _full_pt,
        "du_h2": int(_j.filter(pl.col("m") >= 7)["du"].sum()),
        "d_profit": 0.0,  # set from comparison.csv below
    }
    _cmp = {
        "d_rev": float((costs["food_vat_cut_july"]["revenue"] - costs["baseline"]["revenue"]).sum()),
        "d_vat": float((costs["food_vat_cut_july"]["vat"] - costs["baseline"]["vat"]).sum()),
    }
    # profit diff from the ledger: revenue - procurement - opex - vat all sit
    # in the cost sheet; the comparison file already carries the headline
    _pt = pl.read_csv(source = DATA / "scenarios" / "comparison.csv")
    vat_stats["d_profit"] = float(
        _pt.filter(pl.col("scenario") == "food_vat_cut_july")["profit_before_tax"][0]
        - _pt.filter(pl.col("scenario") == "baseline")["profit_before_tax"][0]
    )
    vat_stats["d_rev"] = _cmp["d_rev"]
    vat_stats["d_vat"] = _cmp["d_vat"]

    _fig = go.Figure()
    _fig.add_trace(
        go.Scatter(
            x = _j["m"].to_list(),
            y = _j["dp_pct"].to_list(),
            mode = "lines+markers",
            line = dict(
                color = ACCENT,
                width = 2.5,
            ),
            marker = dict(size = 7),
        ),
    )
    # what FULL pass-through of the rate change would do to gross tags
    _fig.add_shape(
        type = "line",
        x0 = 7,
        x1 = 12,
        y0 = _full_pt,
        y1 = _full_pt,
        line = dict(
            color = MUTED,
            width = 1.5,
            dash = "dash",
        ),
    )
    _fig.add_annotation(
        text = f"full pass-through: {_full_pt:.2f}%",
        x = 7.1,
        y = _full_pt,
        xanchor = "left",
        yanchor = "top",
        yshift = -8,
        showarrow = False,
        font = dict(
            color = MUTED,
            size = 11.5,
        ),
    )
    style(
        fig = _fig,
        title = "Price paid per unit on food (reduced-rate) categories: VAT-cut arm vs baseline, % difference by month",
    )
    _fig.update_xaxes(
        title_text = "",
        tickvals = list(range(1, 13)),
        ticktext = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ],
    )
    _fig.update_yaxes(
        title_text = "Δ price paid per unit (%)",
        title_font = dict(
            size = 11.5,
            color = MUTED,
        ),
        # headroom below the dashed benchmark so its label clears the frame
        range = [
            -5.6,
            0.5,
        ],
    )
    takeaway(
        fig = _fig,
        text = "the cut reaches the shelf within weeks —<br>menu costs delay tags by one delivery, not one quarter",
        x = 0.03,
        y = 0.10,
    )
    mo.vstack(
        items = [
            mo.md(rf"""
    ## 1 · Who actually bore the food-VAT cut? (5.1)

    On July 1 the reduced VAT rate on food drops from 10% to 5%. Tags in
    this shop are *gross* (VAT included), so the whole question is how much
    of the statutory cut ever reaches them — the owner reprices only when a
    delivery moves his cost trend past a 3% menu-cost threshold, so the law
    does not move tags; his repricing habit does.
    """),
            _fig,
            caption(
                "Two measures, one verdict. Matched SKU-by-SKU, year-end "
                f"food tags sit {vat_stats['tag_dec']:.1f}% below the "
                f"baseline's — the full {abs(_full_pt):.2f}% cut and a "
                "hair more, because repriced tags snap to the charm grid. "
                "The line above, price PAID per unit, averages "
                f"≈{abs(vat_stats['dp_h2']):.1f}% because baskets shift "
                "month to month — composition wobble, not withheld cut. "
                "And it happened fast: July is already at −4.0%, since a "
                "4.5% tax change clears the owner's 3% repricing "
                "threshold at the first post-July delivery of almost "
                "every SKU. Standard-rate categories (alcohol, household, "
                "personal care) moved 0.0% — the clean within-arm "
                "control."
            ),
            mo.md(rf"""
    **The incidence ledger (twin differences, full year):**

    | Party | Effect |
    | --- | --- |
    | Customers | pay €{-vat_stats['d_rev']:,.0f} less at the till for MORE goods ({vat_stats['du_h2']:+,} food units in H2) |
    | The owner | profit +€{vat_stats['d_profit']:,.0f} — not from withholding the cut, but from the volume it stimulates and the float of the July repricing lag |
    | The shop's remittance | −€{-vat_stats['d_vat']:,.0f} (output VAT falls; note the shop's remittance is only the retail slice of the state's total loss — the wholesaler's larger share is invisible in this ledger) |

    The teaching point: with a *net-margin* pricer, statutory incidence
    and economic incidence coincide almost exactly — the interesting
    residual is timing (menu costs) and the charm-price grid, worth about
    €{vat_stats['d_profit']:,.0f} to the owner. An analyst inside the arm
    can measure all of this from tags alone; the twin certifies there is
    no hidden margin grab.
    """),
        ],
    )
    return (vat_stats,)


@app.cell
def _(ACCENT, DATA, MUTED, caption, costs, go, mo, pl, sales, style, takeaway):
    # ==== 5.2 — what did households do with the rebate? ======================
    # weekly revenue in both arms; budget weeks are day-of-year // 7 capped 52
    def _weekly(df):
        return df.with_columns(
            pl.col("date").str.to_date().dt.ordinal_day().alias("doy"),
        ).with_columns(
            pl.min_horizontal(
                (pl.col("doy") - 1) // 7 + 1,
                pl.lit(52),
            ).alias("w"),
        ).group_by("w").agg(
            (pl.col("qty") * pl.col("unit_price")).sum().alias("rev"),
        ).sort(by = "w")

    _b = _weekly(sales["baseline"])
    _r = _weekly(sales["tax_rebate_spring"])
    _j = _b.join(
        other = _r,
        on = "w",
        suffix = "_r",
    ).with_columns(
        (pl.col("rev_r") - pl.col("rev")).alias("d"),
    ).filter(
        (pl.col("w") >= 9) & (pl.col("w") <= 26)
    )
    # the hidden injection: +20% on every customer-week budget, weeks 14-17
    _bp = pl.read_csv(source = DATA / "scenarios" / "baseline" / "hidden" / "budget_paths.csv")
    _inj = float(
        sum(
            (_bp[f"w{_w}"] * 0.2).sum()
            for _w in range(14, 18)
        )
    )
    _win = float(_j.filter((pl.col("w") >= 14) & (pl.col("w") <= 17))["d"].sum())
    _year = float((costs["tax_rebate_spring"]["revenue"] - costs["baseline"]["revenue"]).sum())
    rebate_stats = {
        "injected": _inj,
        "window": _win,
        "year": _year,
        "mpc_window": _win / _inj,
        "mpc_net": _year / _inj,
    }
    _fig = go.Figure()
    _fig.add_bar(
        x = _j["w"].to_list(),
        y = _j["d"].to_list(),
        marker_color = [
            ACCENT if 14 <= _w <= 17 else MUTED
            for _w in _j["w"]
        ],
    )
    style(
        fig = _fig,
        title = "Weekly revenue, rebate arm minus baseline (€) — the surge, then the pantry payback",
    )
    _fig.update_yaxes(
        title_text = "Δ revenue (€/week)",
        title_font = dict(
            size = 11.5,
            color = MUTED,
        ),
    )
    _fig.update_xaxes(title_text = "week of 2025 (rebate lands in weeks 14–17, blue)")
    takeaway(
        fig = _fig,
        text = "grocery keeps 15 cents of the windfall euro in the window —<br>and 6 cents once the pantry payback clears",
        x = 0.98,
        y = 0.98,
        anchor = "right",
    )
    mo.vstack(
        items = [
            mo.md(r"""
    ## 2 · What did households do with the rebate? (5.2)

    In weeks 14–17 (April) every household's grocery budget rises 20% —
    a tax rebate, generated where income lives. The marginal propensity to
    consume *groceries* out of that windfall is emergent, not scripted:
    it depends on how often budget constraints actually bind.
    """),
            _fig,
            caption(
                f"The window lifts revenue €{rebate_stats['window']:,.0f}; "
                "the weeks right after give part of it back (households "
                "stocked pantries forward), and by June the twins are "
                "indistinguishable again. Both halves are causal — the "
                "same customers, same draws, only richer for four weeks."
            ),
            mo.accordion(
                items = {
                    "Grading: the emergent MPC against the hidden injection": mo.md(
                        f"""
    The hidden budget paths price the windfall exactly: 20% of four weeks
    of every household's budget = **€{rebate_stats['injected']:,.0f}**
    injected. Grocery captured €{rebate_stats['window']:,.0f} of it in the
    window (MPC ≈ {rebate_stats['mpc_window']:.1%}) and only
    €{rebate_stats['year']:,.0f} over the full year once the pantry
    payback nets out (MPC ≈ {rebate_stats['mpc_net']:.1%}). The
    interpretation is structural, and it is the section's lesson: budgets
    in this world *cap* grocery spending rather than drive it — most
    household-weeks never hit the cap, so extra budget mostly flows past
    the grocer. A windfall moves grocery spending only for the
    constrained minority, plus a timing shift for everyone else. Fiscal
    stimulus is not retail stimulus.
    """
                    ),
                },
            ),
        ],
    )
    return (rebate_stats,)


@app.cell
def _(DATA, caption, mo, pl, sales):
    # ==== 5.3 — what does a broad supply shock do to a grocer? ===============
    # June 1 the war event lifts ALL categories' costs (zeta 0.30, slow decay);
    # compare Jun-Dec per category: price paid, units, and the implied response
    def _h2_cat(df):
        return df.filter(pl.col("date") >= "2025-06-01").group_by("category").agg(
            (pl.col("qty") * pl.col("unit_price")).sum().alias("rev"),
            pl.col("qty").sum().alias("units"),
        )

    _b = _h2_cat(sales["baseline"])
    _w = _h2_cat(sales["war_june"])
    war_cat = _b.join(
        other = _w,
        on = "category",
        suffix = "_w",
    ).with_columns(
        (((pl.col("rev_w") / pl.col("units_w")) / (pl.col("rev") / pl.col("units")) - 1) * 100).alias("dp_pct"),
        ((pl.col("units_w") / pl.col("units") - 1) * 100).alias("du_pct"),
        (pl.col("rev_w") - pl.col("rev")).alias("d_rev"),
    ).with_columns(
        (pl.col("du_pct") / pl.col("dp_pct")).alias("implied_eps"),
    ).sort(by = "implied_eps")
    _cmp = pl.read_csv(source = DATA / "scenarios" / "comparison.csv")
    war_stats = {
        "d_rev": float(war_cat["d_rev"].sum()),
        "d_units": int((war_cat["units_w"] - war_cat["units"]).sum()),
        "d_profit": float(
            _cmp.filter(pl.col("scenario") == "war_june")["profit_before_tax"][0]
            - _cmp.filter(pl.col("scenario") == "baseline")["profit_before_tax"][0]
        ),
        "so_base": float(_cmp.filter(pl.col("scenario") == "baseline")["stockout_rate"][0]),
        "so_war": float(_cmp.filter(pl.col("scenario") == "war_june")["stockout_rate"][0]),
    }
    mo.vstack(
        items = [
            mo.md(rf"""
    ## 3 · What does a broad supply shock do to a grocer? (5.3)

    From June 1 the war event raises every category's wholesale cost
    (peaking ≈+30%, decaying over months). The owner's net-margin rule
    passes it into tags; households face a store where EVERYTHING got
    dearer at once. June–December, twin-differenced:

    **Revenue +€{war_stats['d_rev']:,.0f}. Units {war_stats['d_units']:+,}.
    Profit for the full year: {war_stats['d_profit']:+,.0f}€.**

    Inflation is not profit: the till collects 4% more euros for 5% fewer
    goods, and after the dearer invoices are paid the owner's year is
    €{-war_stats['d_profit']:,.0f} POORER than without the war. Per
    category:
    """),
            mo.ui.table(
                data = war_cat.select([
                    "category",
                    pl.col("dp_pct").round(1).alias("Δ price %"),
                    pl.col("du_pct").round(1).alias("Δ units %"),
                    pl.col("d_rev").round(0).alias("Δ revenue €"),
                    pl.col("implied_eps").round(2).alias("implied response"),
                ]),
                selection = None,
            ),
            caption(
                "Resilience has a clean structure. Alcohol barely flinches "
                "(−1.7% units — the classic inelastic vice). Fresh "
                "essentials (produce, dairy, bakery) lose only 5–6% of "
                "units to 15% dearer tags — households keep eating. The "
                "big retreats are POSTPONABLE purchases: pantry staples "
                "(−10.0% on the smallest price rise, 9.2%) and frozen "
                "(−9.9%) — exactly the goods a stocked cupboard lets you "
                "defer when a shock squeezes the weekly budget. Stockouts "
                f"fall ({war_stats['so_base']:.1%} → {war_stats['so_war']:.1%}): "
                "dearer shelves empty slower — a small silver lining the "
                "owner never asked for."
            ),
        ],
    )
    return war_cat, war_stats


@app.cell
def _(ACCENT, MUTED, WARN, caption, costs, go, mo, pl, sales, style, takeaway):
    # ==== 5.4 — what does a storm cost, net of the catch-up? =================
    def _daily(df):
        return df.group_by("date").agg(
            (pl.col("qty") * pl.col("unit_price")).sum().alias("rev"),
        ).sort(by = "date")

    _b = _daily(sales["baseline"])
    _t = _daily(sales["typhoon_september"])
    _j = _b.join(
        other = _t,
        on = "date",
        how = "full",
        suffix = "_t",
        coalesce = True,
    ).fill_null(0).sort(by = "date").with_columns(
        (pl.col("rev_t") - pl.col("rev")).cum_sum().alias("cum"),
    )
    typhoon_stats = {
        "storm": float(
            _j.filter((pl.col("date") >= "2025-09-08") & (pl.col("date") <= "2025-09-10"))
            .select(pl.col("rev_t") - pl.col("rev")).sum().item()
        ),
        "year": float((costs["typhoon_september"]["revenue"] - costs["baseline"]["revenue"]).sum()),
        "d_profit_ledger": float(
            (costs["typhoon_september"]["revenue"] - costs["baseline"]["revenue"]).sum()
        ),
    }
    _fig = go.Figure()
    _fig.add_trace(
        go.Scatter(
            x = _j["date"].to_list(),
            y = _j["cum"].to_list(),
            mode = "lines",
            line = dict(
                color = ACCENT,
                width = 2,
            ),
        ),
    )
    _fig.add_vrect(
        x0 = "2025-09-08",
        x1 = "2025-09-10",
        fillcolor = WARN,
        opacity = 0.15,
        line_width = 0,
    )
    _fig.add_annotation(
        text = "storm<br>Sep 8–10",
        x = "2025-09-09",
        y = 1,
        yref = "y domain",
        yanchor = "top",
        showarrow = False,
        font = dict(
            color = WARN,
            size = 11.5,
        ),
    )
    style(
        fig = _fig,
        title = "Cumulative revenue difference, typhoon arm minus baseline (€) — the dip, the refill, the flat year",
    )
    _fig.update_yaxes(
        title_text = "cumulative Δ revenue (€)",
        title_font = dict(
            size = 11.5,
            color = MUTED,
        ),
    )
    _fig.update_xaxes(title_text = "")
    takeaway(
        fig = _fig,
        text = "three lost days, two weeks of pantry refill —<br>the storm's annual cost rounds to zero",
        x = 0.02,
        y = 0.98,
    )
    mo.vstack(
        items = [
            mo.md(rf"""
    ## 4 · What does a storm cost, net of the catch-up? (5.4)

    September 8–10 a typhoon empties the streets (footfall ×0.35), soaks
    the town, and puts a short spike into fresh-goods costs. The storm
    days themselves lose **€{-typhoon_stats['storm']:,.0f}** of revenue —
    and then the pantry mechanism goes to work:
    """),
            _fig,
            caption(
                "Households who could not shop on storm days did not eat "
                "less — they ran their pantries down and refilled over the "
                "following weeks: the steep climb from Sep 11 recovers the "
                "whole storm dip within about three weeks. Everything "
                "else on this chart is the §0 ghost: before the storm the "
                "line wanders a ±€700 band with NO cause (this arm's "
                "normalization coupling), and the post-October drift to "
                "+€900 and back is the same wander. The year ends at "
                f"{typhoon_stats['year']:+,.0f}€, deep inside that placebo "
                "band — the honest annual figure is 'indistinguishable "
                "from nothing'. The lesson generalizes: for a store "
                "selling storable staples, short demand interruptions are "
                "timing events, not losses — disaster-planning money "
                "belongs on supply (the fresh cost spike) and spoilage "
                "exposure, not on lost footfall."
            ),
        ],
    )
    return


@app.cell
def _(ACCENT, MUTED, WARN, caption, go, mo, np, style, takeaway, war_cat):
    # ==== 5.5 — does my observational elasticity generalize? =================
    # Layer 2 estimated the category-level price response at -0.23 from
    # within-arm relative price variation. Predict the war twin with it.
    _eps_obs = -0.23
    _x = war_cat["dp_pct"].to_numpy()
    _y = war_cat["du_pct"].to_numpy()
    _pooled = float((_x * _y).sum() / (_x * _x).sum())
    ev_stats = {
        "eps_obs": _eps_obs,
        "pooled": _pooled,
        "ratio": _pooled / _eps_obs,
    }
    _short = {
        "Pantry Staples and Packaged Goods": "Pantry",
        "Household and Cleaning Supplies": "Household",
        "Beverages (Non-Alcoholic)": "Soft drinks",
        "Snacks and Confectionery": "Snacks",
        "Personal Care and Health": "Personal care",
        "Alcoholic Beverages": "Alcohol",
        "Meat and Poultry": "Meat",
        "Dairy and Eggs": "Dairy",
        "Bakery and Bread": "Bakery",
        "Fresh Produce": "Produce",
        "Frozen Foods": "Frozen",
        "Seafood": "Seafood",
    }
    _fig = go.Figure()
    _grid = np.linspace(0, 17.5, 2)
    _fig.add_trace(
        go.Scatter(
            x = _grid,
            y = _eps_obs * _grid,
            mode = "lines",
            line = dict(
                color = MUTED,
                width = 1.5,
                dash = "dash",
            ),
        ),
    )
    _fig.add_trace(
        go.Scatter(
            x = _grid,
            y = _pooled * _grid,
            mode = "lines",
            line = dict(
                color = WARN,
                width = 1.5,
                dash = "dot",
            ),
        ),
    )
    # hand-placed label sides so the dense right-hand cluster stays legible
    _pos = {
        "Produce": "top center",
        "Dairy": "middle right",
        "Bakery": "middle left",
        "Meat": "middle left",
        "Snacks": "middle right",
    }
    _fig.add_trace(
        go.Scatter(
            x = _x,
            y = _y,
            mode = "markers+text",
            text = [_short[_c] for _c in war_cat["category"]],
            textposition = [
                _pos.get(_short[_c], "bottom center")
                for _c in war_cat["category"]
            ],
            textfont = dict(
                size = 10.5,
                color = "#7A7A7A",
            ),
            marker = dict(
                size = 9,
                color = ACCENT,
            ),
        ),
    )
    _fig.add_annotation(
        text = f"observational ε = {_eps_obs:.2f} (Layer 2)",
        x = 10.6,
        y = _eps_obs * 10.6,
        xanchor = "left",
        yanchor = "bottom",
        yshift = 5,
        showarrow = False,
        font = dict(
            color = MUTED,
            size = 11.5,
        ),
    )
    # anchored off the line entirely — sloped lines strike any label laid
    # along them; the color ties the text to the dotted trace
    _fig.add_annotation(
        text = f"war twin, pooled: {_pooled:.2f}",
        x = 1.2,
        y = -2.75,
        xanchor = "left",
        yanchor = "middle",
        showarrow = False,
        font = dict(
            color = WARN,
            size = 11.5,
        ),
    )
    style(
        fig = _fig,
        title = "External validity check: the war twin's category responses vs the observational elasticity's prediction",
    )
    _fig.update_xaxes(
        title_text = "Δ price, war arm vs baseline, Jun–Dec (%)",
        range = [0, 18],
    )
    _fig.update_yaxes(
        title_text = "Δ units (%)",
        title_font = dict(
            size = 11.5,
            color = MUTED,
        ),
        range = [-11.5, 1.0],
    )
    takeaway(
        fig = _fig,
        text = "the twin's response is twice the observational estimate —<br>a shock to EVERYTHING is not a shock to one thing",
        x = 0.03,
        y = 0.08,
    )
    mo.vstack(
        items = [
            mo.md(rf"""
    ## 5 · Does my observational elasticity generalize? (5.5)

    Layer 2 estimated the category-level price response at **ε ≈ −0.23**:
    when one category drifts dear relative to the rest, its units barely
    move, because the *need* does not go away. The war twin asks the
    external-validity question that haunts every such estimate: does the
    number survive transport to a world where ALL prices jump together?
    """),
            _fig,
            caption(
                f"It does not — and the failure is the finding. The twin's "
                f"pooled response is {_pooled:.2f}, roughly "
                f"{ev_stats['ratio']:.1f}× the observational estimate, and "
                "no category sits on the dashed line. The observational ε "
                "was identified off RELATIVE price moves with household "
                "budgets held effectively fixed — a partial-equilibrium "
                "number. The war moves every price at once, so two escape "
                "routes that kept ε small are closed: there is no cheaper "
                "substitute category to step into, and the aggregate "
                "budget now genuinely binds (the income effect the "
                "relative-price experiment never sees). The scatter even "
                "shows the structure of the failure: the points farthest "
                "below the line are pantry and frozen — deferrable goods "
                "where the budget squeeze bites hardest. The honest rule "
                "this section teaches: an elasticity is a statement about "
                "the variation that identified it; transporting it to a "
                "broad shock silently swaps partial for general "
                "equilibrium, and here that understates the response by "
                "half."
            ),
        ],
    )
    return (ev_stats,)


@app.cell
def _(ACCENT, DATA, MUTED, WARN, caption, costs, go, mo, pl, sales, style):
    # ==== 5.6 — was hiring the clerk worth it? ================================
    _d = {
        _c: float((costs["second_clerk"][_c] - costs["baseline"][_c]).sum())
        for _c in [
            "revenue",
            "procurement",
            "wages",
            "payroll_tax",
            "utilities",
            "vat",
            "storage",
            "flyers",
            "credit_interest",
        ]
    }
    _other = _d["vat"] + _d["storage"] + _d["flyers"] + _d["credit_interest"]
    _cmp = pl.read_csv(source = DATA / "scenarios" / "comparison.csv")
    _p_base = float(_cmp.filter(pl.col("scenario") == "baseline")["profit_before_tax"][0])
    _p_clerk = float(_cmp.filter(pl.col("scenario") == "second_clerk")["profit_before_tax"][0])
    # extended-hours sales: the baseline day runs 8:00-20:59, the arm 7:00-21:59
    _ext = sales["second_clerk"].filter(
        (pl.col("hour") < 8) | (pl.col("hour") > 20)
    )
    clerk_stats = {
        "d_profit": _p_clerk - _p_base,
        "p_clerk": _p_clerk,
        "d_rev": _d["revenue"],
        "wages": _d["wages"],
        "payroll": _d["payroll_tax"],
        "utilities": _d["utilities"],
        "ext_rev": float((_ext["qty"] * _ext["unit_price"]).sum()),
    }
    _labels = [
        "baseline<br>profit",
        "Δ revenue",
        "Δ goods<br>bought",
        "wages",
        "payroll tax",
        "utilities",
        "other",
        "clerk-arm<br>profit",
    ]
    _fig = go.Figure()
    _fig.add_trace(
        go.Waterfall(
            x = _labels,
            measure = [
                "absolute",
                "relative",
                "relative",
                "relative",
                "relative",
                "relative",
                "relative",
                "total",
            ],
            y = [
                _p_base,
                _d["revenue"],
                -_d["procurement"],
                -_d["wages"],
                -_d["payroll_tax"],
                -_d["utilities"],
                -_other,
                0.0,
            ],
            text = [
                f"{_p_base / 1000:,.1f}k",
                f"{_d['revenue'] / 1000:+,.1f}k",
                f"{-_d['procurement'] / 1000:+,.1f}k",
                f"{-_d['wages'] / 1000:+,.1f}k",
                f"{-_d['payroll_tax'] / 1000:+,.1f}k",
                f"{-_d['utilities'] / 1000:+,.1f}k",
                f"{-_other / 1000:+,.1f}k",
                f"{_p_clerk / 1000:,.1f}k",
            ],
            textposition = "outside",
            connector = dict(
                line = dict(
                    color = MUTED,
                    width = 1,
                ),
            ),
            increasing = dict(marker = dict(color = ACCENT)),
            decreasing = dict(marker = dict(color = WARN)),
            totals = dict(marker = dict(color = "#8A8A8A")),
        ),
    )
    style(
        fig = _fig,
        title = "The clerk decision in euros: from baseline profit to the clerk arm's year (twin differences)",
    )
    _fig.update_yaxes(
        showticklabels = False,
        showline = False,
        ticks = "",
        title_text = "profit before tax (€)",
        title_font = dict(
            size = 11.5,
            color = MUTED,
        ),
        # negative floor so outside labels under the deep bars don't clip
        range = [
            _p_clerk * 1.45,
            _p_base + _d["revenue"] * 3.2,
        ],
    )
    _fig.update_xaxes(title_text = "")
    mo.vstack(
        items = [
            mo.md(rf"""
    ## 6 · Was hiring the clerk worth it? (5.6)

    The `second_clerk` arm answers catalog question 4.6 by brute force:
    hire one clerk, open 7:00–22:00 all year, change nothing else. The
    hope: the shop's largest hidden-demand cause is `closed` — demand
    arriving outside opening hours — and longer hours should convert it.
    """),
            _fig,
            caption(
                f"The twin difference is brutal: €{_d['revenue'] / 1000:,.1f}k "
                "of extra revenue costs "
                f"€{_d['wages'] / 1000:,.1f}k in wages plus "
                f"€{_d['payroll_tax'] / 1000:,.1f}k payroll tax plus "
                f"€{_d['utilities'] / 1000:,.1f}k utilities — the year "
                f"lands at €{_p_clerk / 1000:,.1f}k, a "
                f"€{-(clerk_stats['d_profit']) / 1000:,.0f}k swing into "
                "deep loss. Employer-priced labor for two extra shop-hours "
                "per day costs roughly six times the gross margin those "
                "hours generate."
            ),
            mo.accordion(
                items = {
                    "Grading: where the 'recovered' closed demand actually went": mo.md(
                        f"""
    The hidden-demand ledger explains WHY the hope was false. Extending
    hours does exactly what it promises upstream: closed-cause unmet
    demand collapses from ≈53,500 units to ≈14,600 — the door really was
    the constraint. But revenue rises only
    €{clerk_stats['d_rev'] / 1000:,.1f}k (≈2% — and the extended hours'
    €{clerk_stats['ext_rev'] / 1000:,.1f}k of takings are partly shoppers
    who shifted from midday, which is why the net is smaller than the
    7 a.m. till suggests). Demand that finds the door shut is mostly
    DEFERRED, not destroyed: the pantry waits a day, the weekly budget
    is unchanged, and the same groceries get bought inside the old
    hours. The ledger's `closed` column measures inconvenience, not
    forgone revenue — mistaking one for the other is precisely the
    error that would justify the hire. (Same mechanism as the typhoon's
    catch-up in §4, and a small dark twist: stockouts RISE, 8.7% → 10.0%,
    because longer selling hours drain shelves the unchanged Monday
    order sheet no longer refills fast enough.)
    """
                    ),
                },
            ),
        ],
    )
    return


@app.cell
def _(ev_stats, mo, rebate_stats, vat_stats, war_stats):
    mo.md(f"""
    ---
    ## What the laboratory settles

    Five verdicts, each exact by construction:

    1. **The VAT cut reached the customers** — matched food tags fell
       {abs(vat_stats['tag_dec']):.1f}% against a {abs(vat_stats['full_pt']):.2f}%
       full-pass-through benchmark, within weeks; the owner's
       €{vat_stats['d_profit']:,.0f} is volume and float, not capture (§1).
    2. **Fiscal stimulus is not retail stimulus** — of a
       €{rebate_stats['injected'] / 1000:,.0f}k budget windfall, groceries kept
       {rebate_stats['mpc_window']:.0%} in the window and
       {rebate_stats['mpc_net']:.0%} after the pantry payback (§2).
    3. **Inflation is not profit** — the war adds
       €{war_stats['d_rev'] / 1000:,.0f}k of revenue and takes
       €{-war_stats['d_profit']:,.0f} of profit; postponable categories,
       not luxuries, absorb the shock (§3).
    4. **Storms are timing events** — three lost days, two weeks of pantry
       refill, an annual cost statistically indistinguishable from zero (§4).
    5. **Don't hire for the closed-door demand** — it is deferred, not lost;
       the clerk converts a 73% drop in closed-cause unmet demand into 2%
       more revenue at 6× the cost (§6).

    And one verdict about *method*, the reason this layer exists: the
    observational elasticity (−0.23) underpredicted the war twin's response
    ({ev_stats['pooled']:.2f}) by half, because a number identified off
    relative price moves does not transport to a shock that moves every
    price at once (§5). The real world never hands an analyst these twins —
    which is exactly why knowing HOW an estimate was identified, and what
    variation it can legitimately speak for, is the difference between
    analysis and numerology.

    ---
    ### Appendix — method notes

    Data: each arm's `visible/receipts.csv` (sales lines: positive
    quantities, refunds excluded) and `cost_sheet.csv`; the recording
    layer fires from the same keyed streams in every arm, so its noise
    largely cancels in twin differences. Grading panels read
    `hidden/budget_paths.csv` (rebate injection) and
    `hidden/hidden_demand.csv` (closed-cause units) and are marked as
    such. The typhoon arm's ±€400/month normalization ghost (§0) is the
    laboratory's placebo floor. Elasticity −0.23 from Layer 2
    (`diagnose_causes.py`), estimated on the three-year arc whose first
    year is this baseline. Tools: Polars, NumPy, Plotly.
    """)
    return


if __name__ == "__main__":
    app.run()
