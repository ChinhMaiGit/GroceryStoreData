"""Technical report analysis for grocery-sim's project site: the Malm's
Market engagement.

Reproducing this: point DATA below at
`cases/3y_baseline/visible/` (this project's layout; the same `visible/`
folder [`analysis_notebook.py`](https://github.com/ChinhMaiGit/grocery-sim/blob/main/cases/3y_baseline/analysis_notebook.py)
uses to build the stakeholder report), and HIDDEN at the matching
`hidden/` folder (only used once, in Section 3, to grade the "no theft"
claim against ground truth, never to build an estimate). Then run this
script. It writes every table into `results.json`, and every figure as
both a static PNG and an interactive HTML (the one embedded on the site).

This restates `analysis_notebook.py`'s eight sections as a technical
review would expect them: model specifications, coefficient tables with
robust standard errors, confidence intervals, and diagnostics, in place of
the notebook's narrated conclusions. Every regression uses the identical
window, cleaning rule, and covariate set as the notebook it reviews.
Nothing is re-litigated, only restated with the statistics shown in full
(`statsmodels` with HAC-robust errors in place of the notebook's raw
`np.linalg.lstsq`) and, once, checked directly against this run's own
hidden ground truth.
"""

import json
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import statsmodels.api as sm

DATA = "./visible"          # <- the 3y_baseline visible/ folder
HIDDEN = "./hidden"         # <- the matching hidden/ folder (Section 3 only)
FIGDIR = "./figures"
os.makedirs(FIGDIR, exist_ok = True)

INK = "#0b0b0b"
SECONDARY = "#52514e"
MUTED = "#8c8c8c"
GRID = "#e5e5e3"
SURFACE = "#fcfcfb"
BLUE = "#2a78d6"
RED = "#e34948"

PLOT = dict(
    plot_bgcolor = SURFACE,
    paper_bgcolor = SURFACE,
    font = dict(
        color = INK,
        size = 13,
        family = "Helvetica, Arial, sans-serif",
    ),
    margin = dict(
        l = 64,
        r = 28,
        t = 56,
        b = 52,
    ),
)
# no gridlines, a recessive line + a few ticks only -- declutter per the
# Storytelling-with-Data rules, gridlines and heavy axis chrome are chart
# junk that competes with the data for attention
AXIS = dict(
    showgrid = False,
    zeroline = False,
    showline = True,
    linecolor = GRID,
    ticks = "outside",
    tickcolor = GRID,
    tickfont = dict(color = SECONDARY),
    nticks = 6,
)
BAR_AXIS = dict(
    showgrid = False,
    zeroline = False,
    showline = False,
    showticklabels = False,
    ticks = "",
)


def savefig(
    fig,
    name,
    title = None,
    height = 420,
    width = 900,
    showlegend = True,
    hide_value_axis = False,
):
    fig.update_layout(
        **PLOT,
        height = height,
        width = width,
        showlegend = showlegend,
        legend = dict(
            bgcolor = "rgba(0,0,0,0)",
            font = dict(color = SECONDARY, size = 12),
        ),
        title = dict(
            text = title,
            x = 0,
            xanchor = "left",
            font = dict(color = INK, size = 15),
        ) if title else None,
    )
    fig.update_xaxes(**AXIS)
    # column/bar charts hide the value axis and print the value on each bar
    # instead (each figure below already adds those labels directly)
    fig.update_yaxes(**(BAR_AXIS if hide_value_axis else AXIS))
    fig.write_image(
        f"{FIGDIR}/{name}.png",
        scale = 2,
    )
    fig.write_html(
        f"{FIGDIR}/{name}.html",
        include_plotlyjs = "cdn",
        full_html = False,
    )


def takeaway(
    fig,
    text,
    x = 0.02,
    y = 0.98,
    color = BLUE,
    anchor = "left",
):
    """A compact, single-line in-plot annotation carrying the one headline
    reading of the chart -- the caption in the qmd prose below it carries
    the rest (mechanism, caveats), per the annotation/caption split in the
    dataviz style guide."""
    fig.add_annotation(
        text = text,
        x = x,
        y = y,
        xref = "paper",
        yref = "paper",
        xanchor = anchor,
        yanchor = "top",
        showarrow = False,
        font = dict(color = color, size = 12.5),
    )
    return fig


def month_dummies(mm, reference = 1):
    """Fixed-category month dummies (January is the reference by default),
    built the same way whether this frame will later be used to fit or to
    predict out of sample. `pd.get_dummies` drops whichever category
    happens to be *first in this particular frame*, which silently drops
    the wrong reference column (and zeroes out a real coefficient) once a
    held-out period doesn't happen to start in January -- so every month
    dummy in this script goes through this function instead, never
    `pd.get_dummies` directly."""
    months = [k for k in range(1, 13) if k != reference]
    return pd.DataFrame(
        {f"m_{k}": (mm.to_numpy() == k).astype(float) for k in months},
        index = mm.index,
    )


results = {}

# ================================================================ load
receipts_raw = pd.read_csv(
    f"{DATA}/receipts.csv",
    dtype = dict(
        customer_id = str,
        ref_receipt_id = str,
    ),
)
cost_sheet = pd.read_csv(f"{DATA}/cost_sheet.csv")
tax_statement = pd.read_csv(f"{DATA}/tax_statement.csv")
write_offs = pd.read_csv(f"{DATA}/write_offs.csv")
procurement = pd.read_csv(f"{DATA}/procurement.csv")
skus = pd.read_excel("SKUs.xlsx")[["uid", "category"]]

# ==================================================== 1. dedup receipts
# identical to analysis_notebook.py's own rule: a POS retry re-posts every
# line of a receipt byte-identical, so group by the FULL row (qty
# included) and check whether every one of a receipt's distinct rows
# repeats an even number of times -- that receipt's quantities get halved
full_key = [
    "receipt_id",
    "hour",
    "payment",
    "customer_id",
    "uid",
    "qty",
    "unit_price",
    "promo",
    "date",
    "ref_receipt_id",
]
counts = receipts_raw.groupby(full_key, dropna = False).size().reset_index(name = "n")
is_retry = counts.groupby("receipt_id")["n"].apply(lambda s: (s % 2 == 0).all())
counts["is_retry"] = counts["receipt_id"].map(is_retry)
counts["qty_clean"] = np.where(
    counts["is_retry"],
    counts["qty"] * (counts["n"] // 2),
    counts["qty"] * counts["n"],
)
group_cols = [
    "receipt_id",
    "hour",
    "payment",
    "customer_id",
    "uid",
    "unit_price",
    "date",
    "ref_receipt_id",
]
receipts = counts.groupby(group_cols, dropna = False)["qty_clean"].sum().reset_index(name = "qty")
receipts = receipts[receipts["qty"] != 0].copy()
n_flagged = int(counts.loc[counts["is_retry"], "receipt_id"].nunique())

results["dedup"] = dict(n_flagged_receipts = n_flagged)
print(f"1. dedup: {n_flagged} receipts carry the re-upload signature")

# grading the blind flag against this arm's own hidden answer key, loaded
# once, here, never used to build the estimate above -- only to check it
hidden_imp = pd.read_csv(f"{HIDDEN}/imperfections.csv")
true_dup_receipts = set(hidden_imp.loc[hidden_imp["kind"] == "dup_receipt", "key"].astype(int))
blind_flagged_receipts = set(counts.loc[counts["is_retry"], "receipt_id"].unique())
false_positives = blind_flagged_receipts - true_dup_receipts
results["dedup"]["true_dup_receipts"] = len(true_dup_receipts)
results["dedup"]["blind_minus_true"] = sorted(false_positives)
results["dedup"]["blind_minus_true_is_the_traced_double_scans"] = None  # filled in after Section 1's own trace, below
print(
    f"true dup_receipt count: {len(true_dup_receipts)}, "
    f"blind flagged: {len(blind_flagged_receipts)}, "
    f"false positives: {sorted(false_positives)}"
)

# --------------------------------------- till-to-ledger reconciliation
receipts["yy"] = receipts["date"].str.slice(0, 4).astype(int)
till_by_year = receipts.groupby("yy").apply(
    lambda d: (d["qty"] * d["unit_price"]).sum(),
    include_groups = False,
).rename("till_revenue")
ledger_by_year = cost_sheet.groupby("year")["revenue"].sum().rename("ledger_revenue")
tie = pd.concat(
    [till_by_year, ledger_by_year.rename_axis("yy")],
    axis = 1,
)
tie["gap"] = tie["till_revenue"] - tie["ledger_revenue"]

print(tie.round(2))
results["reconciliation"] = dict(
    table = tie.round(2).reset_index().to_dict(orient = "records"),
    max_abs_gap = round(float(tie["gap"].abs().max()), 2),
)

# trace the residual gap to a specific, named cause: a single item scanned
# in two identical lines on one receipt (not a re-upload, since a re-upload
# duplicates every distinct line, not just one)
lines = receipts_raw.groupby(
    ["receipt_id", "date", "uid", "qty", "unit_price"],
).size().reset_index(name = "n_dup")
distinct = lines.groupby("receipt_id").size().rename("n_distinct")
lines = lines.join(distinct, on = "receipt_id")
suspects = lines[(lines["n_distinct"] == 1) & (lines["n_dup"] == 2)].copy()
suspects["true_value"] = (suspects["qty"] * suspects["unit_price"]).round(2)
gaps = [round(g, 2) for g in tie["gap"].abs().tolist() if abs(g) > 0.5]
found = suspects[suspects["true_value"].isin(gaps)]
print(found[["receipt_id", "date", "uid", "qty", "unit_price", "true_value"]])
results["reconciliation"]["traced_receipts"] = found[
    ["receipt_id", "date", "uid", "qty", "unit_price", "true_value"]
].to_dict(orient = "records")

# confirm the false positives above are exactly these two traced receipts,
# not a coincidence of counts
traced_ids = set(found["receipt_id"])
results["dedup"]["blind_minus_true_is_the_traced_double_scans"] = (false_positives == traced_ids)
print(f"blind false positives equal the traced double-scan receipts: {false_positives == traced_ids}")

# ========================================= 2. trend + seasonal decomposition
sales = receipts[(receipts["qty"] > 0) & receipts["ref_receipt_id"].isna()].copy()
sales["mm"] = sales["date"].str.slice(5, 7).astype(int)
monthly = sales.groupby(["yy", "mm"]).apply(
    lambda d: (d["qty"] * d["unit_price"]).sum(),
    include_groups = False,
).rename("rev").reset_index()
monthly["t"] = (monthly["yy"] - 2025) * 12 + monthly["mm"]
monthly = monthly.sort_values("t")

# January 2025 excluded (t=1): the owner's own account says it was
# pantry-filling, not ordinary trade, exactly as the notebook excludes it
train = monthly[monthly["t"] != 1].copy()
X = sm.add_constant(pd.concat(
    [train[["t"]], month_dummies(train["mm"])],
    axis = 1,
))
y = np.log(train["rev"])
trend_model = sm.OLS(y, X).fit(
    cov_type = "HAC",
    cov_kwds = dict(maxlags = 3),
)

trend_pct_yr = (np.exp(trend_model.params["t"] * 12) - 1) * 100
trend_ci = trend_model.conf_int().loc["t"]
trend_ci_pct = (np.exp(trend_ci * 12) - 1) * 100

print(trend_model.summary().tables[1])
results["trend"] = dict(
    n_obs = int(trend_model.nobs),
    r2 = round(float(trend_model.rsquared), 4),
    trend_coef_monthly_log = round(float(trend_model.params["t"]), 5),
    trend_se_hac = round(float(trend_model.bse["t"]), 5),
    trend_pvalue = float(trend_model.pvalues["t"]),
    trend_pct_per_year = round(float(trend_pct_yr), 2),
    trend_pct_per_year_ci = [
        round(float(trend_ci_pct.iloc[0]), 2),
        round(float(trend_ci_pct.iloc[1]), 2),
    ],
)

# volume / price / basket decomposition, 2025 vs 2027
sales["yy"] = sales["date"].str.slice(0, 4).astype(int)
yearly = sales.groupby("yy").apply(
    lambda d: pd.Series(dict(
        rev = (d["qty"] * d["unit_price"]).sum(),
        units = d["qty"].sum(),
        cards = d.loc[d["customer_id"].notna(), "customer_id"].nunique(),
        trips = d["receipt_id"].nunique(),
    )),
    include_groups = False,
)
yearly["avg_price"] = yearly["rev"] / yearly["units"]
yearly["basket"] = yearly["rev"] / yearly["trips"]
growth = dict(
    unit_growth_pct = round(float(yearly["units"].iloc[-1] / yearly["units"].iloc[0] - 1) * 100, 1),
    price_growth_pct = round(float(yearly["avg_price"].iloc[-1] / yearly["avg_price"].iloc[0] - 1) * 100, 1),
    basket_growth_pct = round(float(yearly["basket"].iloc[-1] / yearly["basket"].iloc[0] - 1) * 100, 1),
    trips_growth_pct = round(float(yearly["trips"].iloc[-1] / yearly["trips"].iloc[0] - 1) * 100, 1),
)
results["trend"]["decomposition"] = growth
print(growth)

fig = go.Figure()
fig.add_trace(go.Bar(
    x = train["t"],
    y = train["rev"],
    marker = dict(color = MUTED),
    name = "actual monthly revenue",
))
fig.add_trace(go.Scatter(
    x = train["t"],
    y = np.exp(trend_model.fittedvalues),
    mode = "lines",
    line = dict(color = BLUE, width = 2),
    name = "trend + season (fitted)",
))
fig.update_yaxes(title = "revenue (EUR/month)")
fig.update_xaxes(title = "month (Feb 2025 = 2)")
takeaway(fig, f"net of season, growth ≈{trend_pct_yr:+.1f}%/year")
savefig(fig, "02_trend_season", title = "Monthly revenue: fitted trend + seasonal OLS (HAC SEs)")

# ============================================== 3. write-off decomposition
proc_dedup = procurement.drop_duplicates(
    subset = ["uid", "qty", "unit_cost", "order_date", "delivery_date"],
)
median_cost = proc_dedup.groupby("uid")["unit_cost"].median().rename("mc")
woc = write_offs.join(median_cost, on = "uid")
woc["eur"] = woc["units"] * woc["mc"]
by_reason = woc.groupby("reason").agg(
    units = ("units", "sum"),
    eur = ("eur", "sum"),
).sort_values("eur", ascending = False)
total_eur = float(by_reason["eur"].sum())
rev_3y = float(yearly["rev"].sum())

print(by_reason)
results["writeoffs"] = dict(
    table = by_reason.reset_index().round(2).to_dict(orient = "records"),
    total_eur = round(total_eur, 2),
    pct_of_revenue = round(total_eur / rev_3y * 100, 2),
)

# trace the largest stock_count correction month to a specific duplicated
# delivery, exactly as the notebook does
woc["ym"] = woc["date"].str.slice(0, 7)
sc_monthly = woc[woc["reason"] == "stock_count"].groupby("ym")["units"].sum().sort_values(ascending = False)
worst_month = sc_monthly.index[0]
dupe = procurement.groupby(
    ["uid", "qty", "unit_cost", "order_date", "delivery_date"],
).size().reset_index(name = "n")
dupe = dupe[dupe["n"] > 1].copy()
dupe["delivery_month"] = dupe["delivery_date"].str.slice(0, 7)
dupe["extra_units"] = (dupe["n"] - 1) * dupe["qty"]
dupe_that_month = dupe[dupe["delivery_month"] == worst_month]
extra = int(dupe_that_month["extra_units"].sum())
correction = int(sc_monthly.iloc[0])

results["writeoffs"]["worst_month"] = worst_month
results["writeoffs"]["worst_month_correction_units"] = correction
results["writeoffs"]["worst_month_duplicate_units"] = extra
print(f"worst stock_count month {worst_month}: {correction} units, {extra} traced to duplicate deliveries")

# grading the "no theft" claim against the same hidden answer key loaded
# in Section 1, reused here, never used to build the estimate above
results["writeoffs"]["ground_truth_defect_families"] = hidden_imp["kind"].value_counts().to_dict()
results["writeoffs"]["ground_truth_has_theft_family"] = bool(
    hidden_imp["kind"].isin(["theft", "shrinkage_theft"]).any(),
)
print("hidden defect families this run:", hidden_imp["kind"].value_counts().to_dict())
print("a theft-labeled defect family exists in ground truth:", results["writeoffs"]["ground_truth_has_theft_family"])

reason_labels = dict(
    spoilage = "spoiled on the shelf",
    stock_count = "month-end count correction",
    damage = "the freezer accident",
)
fig = go.Figure(go.Bar(
    x = [reason_labels[r] for r in by_reason.index],
    y = by_reason["eur"].tolist(),
    marker = dict(color = [RED if r == "damage" else BLUE for r in by_reason.index]),
    text = [f"€{v:,.0f}" for v in by_reason["eur"]],
    textposition = "outside",
    textfont = dict(color = INK, size = 12.5),
))
fig.update_yaxes(
    title = "EUR over 3 years",
    range = [0, float(by_reason["eur"].max()) * 1.2],
)
takeaway(fig, f"{total_eur / rev_3y * 100:.1f}% of revenue, almost all spoilage")
savefig(
    fig,
    "03_writeoffs",
    title = "Write-offs by reason, at invoice cost",
    showlegend = False,
    height = 420,
    hide_value_axis = True,
)

print("Sections 1-3 done")

# =============================================== 4. competitor counterfactual
def fit_and_project(df_train, df_post, col):
    X_ = sm.add_constant(pd.concat(
        [df_train[["t"]], month_dummies(df_train["mm"])],
        axis = 1,
    ))
    y_ = np.log(df_train[col])
    m = sm.OLS(y_, X_).fit(
        cov_type = "HAC",
        cov_kwds = dict(maxlags = 3),
    )
    Xp = sm.add_constant(
        pd.concat([df_post[["t"]], month_dummies(df_post["mm"])], axis = 1),
        has_constant = "add",
    )
    pred = np.exp(m.predict(Xp))
    resid_sigma = float(np.sqrt(m.mse_resid))
    return pred, m, resid_sigma


units_monthly = sales.groupby(["yy", "mm"]).apply(
    lambda d: pd.Series(dict(units = d["qty"].sum(), trips = d["receipt_id"].nunique())),
    include_groups = False,
).reset_index()
units_monthly["t"] = (units_monthly["yy"] - 2025) * 12 + units_monthly["mm"]
monthly_full = monthly.merge(units_monthly[["t", "units", "trips"]], on = "t")
train4 = monthly_full[(monthly_full["t"] >= 2) & (monthly_full["t"] <= 26)].copy()
post4 = monthly_full[monthly_full["t"] >= 27].copy()

pred_rev, rev_model, sigma_rev = fit_and_project(train4, post4, "rev")
pred_units, _, _ = fit_and_project(train4, post4, "units")
pred_trips, _, _ = fit_and_project(train4, post4, "trips")

gap_rev = float(post4["rev"].sum() - pred_rev.sum())
results["competitor"] = dict(
    pred_rev = round(float(pred_rev.sum()), 0),
    act_rev = round(float(post4["rev"].sum()), 0),
    gap_rev = round(gap_rev, 0),
    gap_units_pct = round(float(post4["units"].sum() / pred_units.sum() - 1) * 100, 2),
    gap_trips_pct = round(float(post4["trips"].sum() / pred_trips.sum() - 1) * 100, 2),
    resid_sigma_log = round(sigma_rev, 4),
    pre_period_r2 = round(float(rev_model.rsquared), 4),
    pre_period_n = int(rev_model.nobs),
)
print(results["competitor"])

# category-level difference-in-differences on the shelves the owner
# discounted (his own May 2027 price cut is the treatment date, since
# that is the response actually visible in the tag file)
EXPOSED = [
    "Beverages (Non-Alcoholic)",
    "Snacks and Confectionery",
    "Household and Cleaning Supplies",
]
cat_sales = sales.merge(skus, on = "uid")
cat_sales["exposed"] = cat_sales["category"].isin(EXPOSED)
cat_sales["yy"] = cat_sales["date"].str.slice(0, 4).astype(int)
cat_monthly = cat_sales.groupby(["yy", "mm", "exposed"]).apply(
    lambda d: (d["qty"] * d["unit_price"]).sum(),
    include_groups = False,
).rename("rev").reset_index()
cat_monthly["t"] = (cat_monthly["yy"] - 2025) * 12 + cat_monthly["mm"]
cat_monthly["exposed_i"] = cat_monthly["exposed"].astype(int)
cat_monthly["post"] = (cat_monthly["t"] >= 29).astype(int)   # May 2027 = t 29
cat_monthly["did"] = cat_monthly["exposed_i"] * cat_monthly["post"]

Xd = sm.add_constant(pd.concat(
    [cat_monthly[["t", "exposed_i", "post", "did"]], month_dummies(cat_monthly["mm"])],
    axis = 1,
))
yd = np.log(cat_monthly["rev"])
did_model = sm.OLS(yd, Xd).fit(
    cov_type = "HAC",
    cov_kwds = dict(maxlags = 4),
)

did_pct = (np.exp(did_model.params["did"]) - 1) * 100
did_ci = (np.exp(did_model.conf_int().loc["did"]) - 1) * 100
print(did_model.summary().tables[1])
results["competitor"]["did"] = dict(
    coef_log = round(float(did_model.params["did"]), 4),
    pct = round(float(did_pct), 2),
    ci_pct = [
        round(float(did_ci.iloc[0]), 2),
        round(float(did_ci.iloc[1]), 2),
    ],
    pvalue = float(did_model.pvalues["did"]),
    n_obs = int(did_model.nobs),
)
print(results["competitor"]["did"])

fig = go.Figure()
fig.add_trace(go.Scatter(
    x = post4["t"],
    y = pred_rev,
    mode = "lines",
    line = dict(color = MUTED, width = 2, dash = "dash"),
    name = "expected (pre-entry trend)",
))
fig.add_trace(go.Scatter(
    x = post4["t"],
    y = post4["rev"],
    mode = "lines+markers",
    line = dict(color = BLUE, width = 2),
    name = "actual",
))
fig.update_yaxes(title = "revenue (EUR/month)")
fig.update_xaxes(title = "month (March 2027 = 27)")
takeaway(fig, f"10-month gap ≈ €{gap_rev:+,.0f}, not distinguishable from noise")
savefig(fig, "04_competitor", title = "Actual vs. pre-entry-trend-predicted revenue since the competitor opened")

print("Section 4 done")

# =========================================================== 5. expansion
cs = cost_sheet.copy()
cs["t"] = (cs["year"] - 2025) * 12 + cs["month"]
post5 = cs[cs["t"] >= 23]
train5 = cs[(cs["t"] >= 2) & (cs["t"] <= 22)]


def fit_and_project_cs(df_train, df_post, col):
    X_ = sm.add_constant(pd.concat(
        [df_train[["t"]], month_dummies(df_train["month"])],
        axis = 1,
    ))
    y_ = np.log(df_train[col])
    m = sm.OLS(y_, X_).fit(
        cov_type = "HAC",
        cov_kwds = dict(maxlags = 3),
    )
    Xp = sm.add_constant(
        pd.concat([df_post[["t"]], month_dummies(df_post["month"])], axis = 1),
        has_constant = "add",
    )
    return np.exp(m.predict(Xp)), m


pred_rev5, rev_model5 = fit_and_project_cs(train5, post5, "revenue")
pred_util5, _ = fit_and_project_cs(train5, post5, "utilities")

wages = float(post5["wages"].sum())
payroll = float(post5["payroll_tax"].sum())
extra_util = max(0.0, float(post5["utilities"].sum() - pred_util5.sum()))
capex = 14_000.0
total_cost = wages + payroll + extra_util + capex
extra_rev = float(post5["revenue"].sum() - pred_rev5.sum())
gm = 1 - float(cs["procurement"].sum()) / float(cs["revenue"].sum())
extra_gross_profit = extra_rev * gm
net = extra_gross_profit - total_cost

results["expansion"] = dict(
    months = int(len(post5)),
    wages = round(wages, 0),
    payroll_tax = round(payroll, 0),
    extra_utilities = round(extra_util, 0),
    capex = capex,
    total_cost = round(total_cost, 0),
    extra_revenue = round(extra_rev, 0),
    gross_margin = round(gm, 4),
    extra_gross_profit = round(extra_gross_profit, 0),
    net = round(net, 0),
    revenue_needed_for_wage_bill = round((wages + payroll) / gm, 0),
    pre_period_r2 = round(float(rev_model5.rsquared), 4),
)
print(results["expansion"])

waterfall_values = [extra_gross_profit, -wages, -payroll, -extra_util, -capex]
fig = go.Figure(go.Waterfall(
    x = ["extra gross profit", "wages", "payroll tax", "extra utilities", "fit-out"],
    measure = ["relative"] * 5,
    y = waterfall_values,
    text = [f"{'+' if v >= 0 else ''}{v:,.0f}" for v in waterfall_values],
    textposition = "outside",
    textfont = dict(color = INK, size = 12.5),
    connector = dict(line = dict(color = MUTED, width = 1)),
    increasing = dict(marker = dict(color = BLUE)),
    decreasing = dict(marker = dict(color = RED)),
))
fig.update_yaxes(
    title = "EUR",
    range = [net * 1.15, extra_gross_profit * 3],
)
takeaway(
    fig,
    f"net so far: ≈€{net:,.0f}",
    x = 0.98,
    y = 0.9,
    color = RED,
    anchor = "right",
)
savefig(
    fig,
    "05_expansion",
    title = "Expansion cost/benefit waterfall",
    showlegend = False,
    hide_value_axis = True,
)

print("Section 5 done")

# =============================================================== 6. churn
card_sales = sales[sales["customer_id"].notna() & sales["ref_receipt_id"].isna()]
visits = card_sales.groupby("customer_id").agg(
    n = ("receipt_id", "nunique"),
    first = ("date", "min"),
    last = ("date", "max"),
)
regulars = visits[visits["n"] >= 10].copy()
regulars["first_dt"] = pd.to_datetime(regulars["first"])
regulars["last_dt"] = pd.to_datetime(regulars["last"])

year_ends = [
    ("2025-12-31", 2025),
    ("2026-12-31", 2026),
    ("2027-12-31", 2027),
]
rows = []
for year_end, label in year_ends:
    ye = pd.Timestamp(year_end)
    eligible = regulars[regulars["first_dt"] <= ye]
    silent = eligible[(ye - eligible["last_dt"]).dt.days >= 90]
    new_that_year = regulars[regulars["first_dt"].dt.year == label]
    rows.append(dict(
        year = label,
        regulars_established_by_year_end = int(len(eligible)),
        gone_quiet_90d_plus = int(len(silent)),
        newly_established_that_year = int(len(new_that_year)),
    ))
churn_table = pd.DataFrame(rows)
print(churn_table)
results["churn"] = dict(
    total_regulars = int(len(regulars)),
    table = churn_table.to_dict(orient = "records"),
)

fig = go.Figure()
fig.add_trace(go.Bar(
    x = churn_table["year"],
    y = churn_table["newly_established_that_year"],
    name = "newly established",
    marker = dict(color = BLUE),
    text = churn_table["newly_established_that_year"],
    textposition = "outside",
))
fig.add_trace(go.Bar(
    x = churn_table["year"],
    y = -churn_table["gone_quiet_90d_plus"],
    name = "gone quiet 90d+ (cumulative)",
    marker = dict(color = RED),
    text = churn_table["gone_quiet_90d_plus"],
    textposition = "outside",
))
fig.update_yaxes(title = "customers (tokens)")
takeaway(
    fig,
    "a flow, not a leak: new faces roughly keep pace with the quiet ones",
    x = 0.5,
    y = 0.85,
)
savefig(
    fig,
    "06_churn",
    title = "New regulars vs. regulars gone quiet, by year",
    hide_value_axis = True,
)

print("Section 6 done")

# ============================================================== 7. forecast
train7 = monthly[monthly["t"] >= 2].copy()
train7["post_ind"] = (train7["t"] >= 23).astype(int)
X7 = sm.add_constant(pd.concat(
    [train7[["t", "post_ind"]], month_dummies(train7["mm"])],
    axis = 1,
))
y7 = np.log(train7["rev"])
fc_model = sm.OLS(y7, X7).fit(
    cov_type = "HAC",
    cov_kwds = dict(maxlags = 3),
)
sigma7 = float(np.sqrt(fc_model.mse_resid))

future = pd.DataFrame(dict(
    t = np.arange(37, 49),
    mm = np.arange(1, 13),
))
future["post_ind"] = 1
Xf = sm.add_constant(
    pd.concat([future[["t", "post_ind"]], month_dummies(future["mm"])], axis = 1),
    has_constant = "add",
)
point_log = fc_model.predict(Xf)
pred28 = np.exp(point_log)
lo28 = np.exp(point_log - 1.2816 * sigma7)
hi28 = np.exp(point_log + 1.2816 * sigma7)

rev2026 = cs[cs["year"] == 2026].sort_values("month")["revenue"].to_numpy()
rev2027 = cs[cs["year"] == 2027].sort_values("month")["revenue"].to_numpy()
naive_wmape = float(np.abs(rev2027 - rev2026).sum() / rev2027.sum()) * 100
model_wmape = float(np.abs(train7["rev"] - np.exp(fc_model.fittedvalues)).sum() / train7["rev"].sum()) * 100

y2027 = cs[cs["year"] == 2027]
rev27 = float(y2027["revenue"].sum())
proc_rate = float(y2027["procurement"].sum()) / rev27
vat_rate = float(y2027["vat"].sum()) / rev27
fixed_cols = ["rent", "wages", "payroll_tax", "utilities", "storage", "flyers", "credit_interest", "repairs"]
fixed_2027 = float(y2027[fixed_cols].sum().sum())


def profit_at(rev):
    return rev * (1 - proc_rate - vat_rate) - fixed_2027


results["forecast"] = dict(
    point = round(float(pred28.sum()), 0),
    lo = round(float(lo28.sum()), 0),
    hi = round(float(hi28.sum()), 0),
    naive_wmape_pct = round(naive_wmape, 2),
    model_wmape_pct = round(model_wmape, 2),
    profit_point = round(profit_at(float(pred28.sum())), 0),
    profit_lo = round(profit_at(float(lo28.sum())), 0),
    profit_hi = round(profit_at(float(hi28.sum())), 0),
    r2 = round(float(fc_model.rsquared), 4),
    n_obs = int(fc_model.nobs),
)
print(results["forecast"])

fig = go.Figure()
fig.add_trace(go.Scatter(
    x = list(future["t"]) + list(future["t"][::-1]),
    y = list(hi28) + list(lo28[::-1]),
    fill = "toself",
    fillcolor = "rgba(42,120,214,0.12)",
    line = dict(width = 0),
    showlegend = False,
    hoverinfo = "skip",
))
fig.add_trace(go.Scatter(
    x = monthly[monthly["t"] >= 25]["t"],
    y = monthly[monthly["t"] >= 25]["rev"],
    mode = "lines",
    line = dict(color = MUTED, width = 2),
    name = "actual (2027)",
))
fig.add_trace(go.Scatter(
    x = future["t"],
    y = pred28,
    mode = "lines+markers",
    line = dict(color = BLUE, width = 2),
    name = "2028 forecast",
))
fig.update_yaxes(title = "revenue (EUR/month)")
fig.update_xaxes(title = "month (Jan 2027 = 25)")
takeaway(
    fig,
    f"point €{pred28.sum() / 1000:,.0f}k, range €{lo28.sum() / 1000:,.0f}k-€{hi28.sum() / 1000:,.0f}k",
    y = 0.15,
)
savefig(fig, "07_forecast", title = "2028 revenue forecast with an 80% interval, structural break at the expansion")

print("Section 7 done")

# =============================================== 8. synthesis: rent review
rent_2026 = float(cs.loc[cs["year"] == 2026, "rent"].iloc[0])
rent_2027 = float(cs.loc[cs["year"] == 2027, "rent"].iloc[0])
rent_review_cost = (rent_2027 - rent_2026) * 12
results["synthesis"] = dict(
    rent_2026_monthly = round(rent_2026, 2),
    rent_2027_monthly = round(rent_2027, 2),
    rent_pct_increase = round((rent_2027 / rent_2026 - 1) * 100, 1),
    rent_review_annual_cost = round(rent_review_cost, 2),
    expansion_annualized_cost = round(total_cost / len(post5) * 12, 0),
)
print(
    f"rent review: {results['synthesis']['rent_pct_increase']}% increase, "
    f"{rent_review_cost:,.2f} extra cost per year"
)
# -> 12.0% increase, 1,671.35 extra cost per year

with open(f"{FIGDIR}/results.json", "w") as f:
    json.dump(results, f, indent = 2, default = str)
print("wrote results.json")
