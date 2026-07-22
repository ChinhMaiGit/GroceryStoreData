"""Technical report analysis for grocery-sim's project site.

Reproducing this:

1. Generate the data with `grocery_sim` (see advanced-methods.qmd's own
   "Generating this run's data" section for the exact settings used):

    from grocery_sim import GroceryStoreSimulation

    sim = GroceryStoreSimulation()
    sim.setup(dict(
        basic = dict(
            name = "Technical Report Shop",
            random_seed = 5501,
            year = 3,
            retain_earning = True,
            retain_earning_from = "2026-01",
        ),
        events = dict(
            war = ["2025-03-01", "2026-09-01"],
            typhoon = "2025-07-15",
            food_vat_cut = "2025-05-01",
            tax_cut = "2026-02-01",
            competitor = "2026-06-01",
            operational_hazard = "2027-04-01",
        ),
        potential_investment = dict(
            more_staff = True,
            bigger_store = True,
            upgrade_infrastructure = True,
        ),
    ))
    sim.simulate()
    data = sim.data()
    for name in data.keys():
        data[name].to_parquet(f"<DATA>/{name}.parquet")

2. Point DATA below at that folder, FIGDIR at wherever figures should land,
   and run this script. It writes every figure plus results.json, the
   single source every number in advanced-methods.qmd is transcribed from.

3. Dependencies beyond the package itself: statsmodels, scikit-learn,
   pymc, arviz, plotly, kaleido, openpyxl. On Windows, pm.sample() needs
   cores=1 (already set below). The multiprocessing spawn backend
   otherwise re-imports this module in each worker and crashes without a
   `if __name__ == "__main__":` guard.

Runs GLM (NB regression + a difference-in-differences pass-through
design), ML (gradient-boosting demand forecast + a stock-out classifier),
and a hierarchical Bayesian partial-pooling model, against a real
three-year grocery_sim run. Every number quoted in the report prose is in
this script's own printed output / results.json -- nothing is hand-typed
from a notebook that could have drifted.
"""

import json
import os
import warnings

import numpy as np
import pandas as pd
import plotly.graph_objects as go

warnings.filterwarnings("ignore")

DATA = "./tech_report_data"       # <- point at the exported parquet folder (step 1 above)
FIGDIR = "./figures"              # <- where figures + results.json are written
os.makedirs(FIGDIR, exist_ok = True)

# --------------------------------------------------- palette (dataviz skill)
# validated: node scripts/validate_palette.js "#2a78d6,#e34948" --mode light
# -> ALL CHECKS PASS (lightness band, chroma floor, CVD sep 21.6, normal-
# vision floor 32.3, contrast). Fixed roles held across every chart in this
# report: blue = the model/processed estimate, red = the raw/unpooled/cost
# comparison, ink = actual observed data, muted = a de-emphasized baseline.
INK = "#0b0b0b"
SECONDARY = "#52514e"
MUTED = "#8c8c8c"
GRID = "#e5e5e3"
SURFACE = "#fcfcfb"
BLUE = "#2a78d6"       # slot 1 -- model / processed / pooled estimate
BLUE_WASH = "rgba(42,120,214,0.12)"
RED = "#e34948"        # slot 8 -- raw / unpooled / cost comparison

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
AXIS = dict(
    showgrid = True,
    gridcolor = GRID,
    gridwidth = 1,
    zeroline = False,
    showline = True,
    linecolor = GRID,
    ticks = "outside",
    tickcolor = GRID,
    tickfont = dict(color = SECONDARY),
)


def style(
    fig,
    title = None,
    height = 420,
    width = 920,
    showlegend = True,
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
    fig.update_xaxes(**AXIS, title_font = dict(color = SECONDARY))
    fig.update_yaxes(**AXIS, title_font = dict(color = SECONDARY))
    return fig


def savefig(
    fig,
    name,
    height = 420,
    width = 920,
    showlegend = True,
    title = None,
):
    style(
        fig,
        title = title,
        height = height,
        width = width,
        showlegend = showlegend,
    )
    fig.write_image(f"{FIGDIR}/{name}.png", scale = 2)


results = {}

# ==================================================================== load
receipts = pd.read_parquet(f"{DATA}/receipts.parquet")
weather = pd.read_parquet(f"{DATA}/weather.parquet")
calendar = pd.read_parquet(f"{DATA}/calendar.parquet")
cost_sheet = pd.read_parquet(f"{DATA}/cost_sheet.parquet")
procurement = pd.read_parquet(f"{DATA}/procurement.parquet")
price_history = pd.read_parquet(f"{DATA}/price_history.parquet")
inventory_eod = pd.read_parquet(f"{DATA}/inventory_eod.parquet")
skus = pd.read_excel("SKUs.xlsx")  # ships inside package/grocery_sim/SKUs.xlsx

uid_cat = skus.set_index("uid")["category"]
receipts["category"] = receipts["uid"].map(uid_cat)
procurement["category"] = procurement["uid"].map(uid_cat)
price_history["category"] = price_history["uid"].map(uid_cat)
inventory_eod["category"] = (
    inventory_eod["uid"].map(uid_cat) if "uid" in inventory_eod.columns else None
)

for df in (receipts, weather, calendar, procurement, price_history, inventory_eod):
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])

print("loaded:", receipts.shape, weather.shape, calendar.shape, cost_sheet.shape)

# ============================================================ GLM section
import statsmodels.api as sm
import statsmodels.formula.api as smf

sales = receipts[receipts["qty"] > 0].copy()
daily_units = sales.groupby("date")["qty"].sum().rename("units").to_frame()
daily = daily_units.join(weather.set_index("date")).join(calendar.set_index("date"))
daily = daily[daily["closed"] == 0].copy()
daily["t"] = (daily.index - daily.index.min()).days
daily["dow"] = daily.index.dayofweek
daily["is_weekend"] = (daily["dow"] >= 5).astype(int)
daily["is_pre_holiday"] = daily["pre_holiday"].astype(int)
temp_seasonal = daily.groupby(daily.index.dayofyear)["temp_C"].transform("mean")
daily["temp_anom"] = daily["temp_C"] - temp_seasonal

glm_df = daily.dropna(subset = ["units", "temp_anom", "rain_mm", "wet"]).copy()

nb_model = smf.glm(
    formula = "units ~ temp_anom + rain_mm + wet + is_weekend + is_pre_holiday + t",
    data = glm_df,
    family = sm.families.NegativeBinomial(),
).fit(
    cov_type = "HAC",
    cov_kwds = dict(maxlags = 7),
)

glm_table = pd.DataFrame(dict(
    coef = nb_model.params,
    IRR = np.exp(nb_model.params),
    se_HAC = nb_model.bse,
    p_value = nb_model.pvalues,
    ci_low = np.exp(nb_model.conf_int()[0]),
    ci_high = np.exp(nb_model.conf_int()[1]),
))
print(glm_table.round(4))
results["glm_demand"] = dict(
    n_obs = int(nb_model.nobs),
    pseudo_r2 = float(1 - nb_model.deviance / nb_model.null_deviance),
    table = glm_table.round(4).to_dict(orient = "index"),
)

# fitted vs actual plot (7-day rolling mean, so weekly cycle doesn't dominate)
glm_df["fitted"] = nb_model.fittedvalues
roll = glm_df[["units", "fitted"]].rolling(7, min_periods = 1).mean()
fig = go.Figure()
fig.add_trace(go.Scatter(
    x = roll.index,
    y = roll["units"],
    name = "actual (7-day mean)",
    mode = "lines",
    line = dict(color = INK, width = 2),
))
fig.add_trace(go.Scatter(
    x = roll.index,
    y = roll["fitted"],
    name = "GLM fitted",
    mode = "lines",
    line = dict(color = BLUE, width = 2),
))
fig.update_yaxes(title = "units/day")
savefig(fig, "01_glm_fitted_vs_actual", title = "Negative-binomial demand GLM: fitted vs. actual")

# temperature partial-effect plot
temp_grid = np.linspace(glm_df["temp_anom"].min(), glm_df["temp_anom"].max(), 60)
base = glm_df[["rain_mm", "wet", "is_weekend", "is_pre_holiday", "t"]].mean()
pred_df = pd.DataFrame(dict(
    temp_anom = temp_grid,
    **{k: base[k] for k in base.index},
))
pred = nb_model.get_prediction(pred_df).summary_frame()
fig = go.Figure()
fig.add_trace(go.Scatter(
    x = np.concatenate([temp_grid, temp_grid[::-1]]),
    y = np.concatenate([pred["mean_ci_upper"], pred["mean_ci_lower"][::-1]]),
    fill = "toself",
    fillcolor = BLUE_WASH,
    line = dict(width = 0),
    showlegend = False,
    hoverinfo = "skip",
))
fig.add_trace(go.Scatter(
    x = temp_grid,
    y = pred["mean"],
    mode = "lines",
    line = dict(color = BLUE, width = 2),
    showlegend = False,
))
fig.update_xaxes(title = "temperature anomaly vs. day-of-year normal (°C)")
fig.update_yaxes(title = "predicted units/day")
savefig(
    fig,
    "02_glm_temp_partial_effect",
    title = "Partial effect of temperature anomaly on demand (other covariates at their mean)",
    showlegend = False,
)

# ---------------------------------------------- pass-through: DiD design
# events.food_vat_cut halves VAT on the reduced-rate (food) group on one
# exact date -- but a naive before/after event study on a food category
# alone is confounded here by the concurrent events.war cost shock
# (started 2025-03-01, ~120-day decay, hits every category), which by
# itself pushes the realized cost step to ~-8% against a theoretical
# -4.55%. A standard-VAT category (unaffected by the VAT cut, but equally
# exposed to the war shock) lets that common trend be differenced out --
# a difference-in-differences design, not just a cleaner window.
treated_cat = "Pantry Staples and Packaged Goods"   # reduced VAT -> cut
control_cat = "Household and Cleaning Supplies"      # standard VAT -> unaffected
vat_cut_date = pd.Timestamp("2025-05-01")

all_weeks = pd.period_range(
    price_history["date"].min(),
    price_history["date"].max(),
    freq = "W",
).start_time


def weekly_price_level(cat):
    """A proper held-price index: price_history only logs a row when a
    price *changes* (menu-cost hysteresis means most SKUs reprice only a
    few times a year), so naively averaging whatever rows exist in a
    given week means some weeks are an average of 1-2 SKUs that happened
    to reprice, not the category's actual shelf level that week. Forward-
    fill each SKU's last known price onto every week instead, so the
    weekly average is always across the category's full SKU set."""
    ph_cat = price_history[price_history["category"] == cat].copy()
    ph_cat["week"] = ph_cat["date"].dt.to_period("W").dt.start_time
    panel = ph_cat.pivot_table(
        index = "week",
        columns = "uid",
        values = "price",
        aggfunc = "last",
    )
    panel = panel.reindex(all_weeks).ffill()
    return panel.mean(axis = 1).rename("price")


def weekly_cost_index(cat):
    proc_cat = procurement[procurement["category"] == cat].copy()
    proc_cat["week"] = pd.to_datetime(proc_cat["delivery_date"]).dt.to_period("W").dt.start_time
    return proc_cat.groupby("week")["unit_cost"].mean().reindex(all_weeks).ffill().rename("cost")


def weekly_index(cat):
    df = pd.concat([weekly_price_level(cat), weekly_cost_index(cat)], axis = 1).dropna()
    df["weeks_since"] = (df.index - vat_cut_date).days // 7
    return df[(df["weeks_since"] >= -8) & (df["weeks_since"] <= 8)].copy()


treated = weekly_index(treated_cat)
control = weekly_index(control_cat)


def pre_post_means(df):
    pre = df[df["weeks_since"] < 0][["price", "cost"]].mean()
    post = df[(df["weeks_since"] >= 0) & (df["weeks_since"] <= 7)][["price", "cost"]].mean()
    return pre, post


t_pre, t_post = pre_post_means(treated)
c_pre, c_post = pre_post_means(control)

d_cost_treated = np.log(t_post["cost"]) - np.log(t_pre["cost"])
d_cost_control = np.log(c_post["cost"]) - np.log(c_pre["cost"])
did_cost = d_cost_treated - d_cost_control  # the VAT-cut-specific cost move

d_price_treated = np.log(t_post["price"]) - np.log(t_pre["price"])
d_price_control = np.log(c_post["price"]) - np.log(c_pre["price"])
did_price = d_price_treated - d_price_control  # the VAT-cut-specific price move

did_pass_through = did_price / did_cost

print("naive treated-only cost drop:", np.exp(d_cost_treated) - 1, "(confounded by the war shock)")
print("control-category cost move (the common trend):", np.exp(d_cost_control) - 1)
print("DiD cost move (VAT-cut-specific):", np.exp(did_cost) - 1, "vs theoretical", 1.05 / 1.10 - 1)
print("DiD price move (VAT-cut-specific):", np.exp(did_price) - 1)
print("DiD pass-through (uninformative -- see report):", did_pass_through)

results["pass_through"] = dict(
    treated_category = treated_cat,
    control_category = control_cat,
    theoretical_cost_drop = round(1.05 / 1.10 - 1, 4),
    naive_treated_cost_drop = round(float(np.exp(d_cost_treated) - 1), 4),
    control_cost_move = round(float(np.exp(d_cost_control) - 1), 4),
    did_cost_drop = round(float(np.exp(did_cost) - 1), 4),
    did_price_drop = round(float(np.exp(did_price) - 1), 4),
    did_pass_through = round(float(did_pass_through), 3),
)

for df in (treated, control):
    df["cost_idx100"] = 100 * np.exp(
        np.log(df["cost"]) - np.log(df.loc[df["weeks_since"] < 0, "cost"]).mean()
    )
    df["price_idx100"] = 100 * np.exp(
        np.log(df["price"]) - np.log(df.loc[df["weeks_since"] < 0, "price"]).mean()
    )

from plotly.subplots import make_subplots

fig = make_subplots(
    rows = 1,
    cols = 2,
    shared_yaxes = True,
    subplot_titles = (f"{treated_cat} (treated: VAT cut)", f"{control_cat} (control: no VAT change)"),
    horizontal_spacing = 0.06,
)
for col, df in enumerate((treated, control), start = 1):
    show = col == 1
    fig.add_trace(
        go.Scatter(
            x = df["weeks_since"],
            y = df["cost_idx100"],
            name = "invoice cost",
            mode = "lines+markers",
            line = dict(color = RED, width = 2),
            marker = dict(size = 8, line = dict(color = SURFACE, width = 2)),
            legendgroup = "cost",
            showlegend = show,
        ),
        row = 1,
        col = col,
    )
    fig.add_trace(
        go.Scatter(
            x = df["weeks_since"],
            y = df["price_idx100"],
            name = "shelf price",
            mode = "lines+markers",
            line = dict(color = BLUE, width = 2),
            marker = dict(size = 8, line = dict(color = SURFACE, width = 2)),
            legendgroup = "price",
            showlegend = show,
        ),
        row = 1,
        col = col,
    )
    fig.add_vline(x = 0, line = dict(color = MUTED, width = 1, dash = "dash"), row = 1, col = col)
    fig.update_xaxes(title = "weeks since the food-VAT cut", row = 1, col = col, **AXIS)
fig.update_yaxes(title = "index (pre-event mean = 100)", row = 1, col = 1, **AXIS)
fig.update_yaxes(row = 1, col = 2, **AXIS)
for ann in fig.layout.annotations:
    ann.font = dict(color = INK, size = 13)
fig.update_layout(
    **PLOT,
    height = 440,
    width = 980,
    legend = dict(
        bgcolor = "rgba(0,0,0,0)",
        font = dict(color = SECONDARY, size = 12),
        x = 0.01,
        y = 0.02,
    ),
    title = dict(
        text = "Cost pass-through, difference-in-differences design",
        x = 0,
        xanchor = "left",
        font = dict(color = INK, size = 15),
    ),
)
fig.write_image(f"{FIGDIR}/03_pass_through_did.png", scale = 2)

print("GLM section done")

# ===================================================================== ML
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import average_precision_score, mean_absolute_error, mean_squared_error, precision_recall_curve

forecast_cat = "Dairy and Eggs"
cat_sales = sales[sales["category"] == forecast_cat].copy()
weekly = cat_sales.groupby(pd.Grouper(key = "date", freq = "W"))["qty"].sum().rename("units").to_frame()
weekly = weekly.join(weather.set_index("date").resample("W").mean()[["temp_C", "rain_mm"]])
cal_w = calendar.set_index("date")
weekly["holiday_week"] = cal_w["holiday"].notna().resample("W").sum().reindex(weekly.index, fill_value = 0)
weekly["week_of_year"] = weekly.index.isocalendar().week.astype(int)
weekly["month"] = weekly.index.month
for lag in (1, 2, 52):
    weekly[f"lag_{lag}"] = weekly["units"].shift(lag)
weekly["roll4"] = weekly["units"].shift(1).rolling(4).mean()
weekly = weekly.dropna()

train = weekly[weekly.index.year < 2027]
test = weekly[weekly.index.year == 2027]
features = [
    "temp_C",
    "rain_mm",
    "holiday_week",
    "week_of_year",
    "month",
    "lag_1",
    "lag_2",
    "lag_52",
    "roll4",
]

gbm = HistGradientBoostingRegressor(
    max_depth = 3,
    learning_rate = 0.08,
    max_iter = 200,
    random_state = 0,
)
gbm.fit(train[features], train["units"])
pred_gbm = gbm.predict(test[features])

naive_pred = test["lag_52"].values  # seasonal-naive: same week last year

mae_gbm = mean_absolute_error(test["units"], pred_gbm)
mae_naive = mean_absolute_error(test["units"], naive_pred)
rmse_gbm = mean_squared_error(test["units"], pred_gbm) ** 0.5
rmse_naive = mean_squared_error(test["units"], naive_pred) ** 0.5

print(f"GBM  MAE={mae_gbm:.1f} RMSE={rmse_gbm:.1f}")
print(f"naive MAE={mae_naive:.1f} RMSE={rmse_naive:.1f}")
print("MAE improvement over naive:", 1 - mae_gbm / mae_naive)

results["ml_forecast"] = dict(
    category = forecast_cat,
    n_train = int(len(train)),
    n_test = int(len(test)),
    mae_gbm = round(float(mae_gbm), 1),
    mae_naive = round(float(mae_naive), 1),
    rmse_gbm = round(float(rmse_gbm), 1),
    rmse_naive = round(float(rmse_naive), 1),
    mae_improvement_pct = round(float(1 - mae_gbm / mae_naive) * 100, 1),
    feature_importance = {},
)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x = test.index,
    y = test["units"],
    name = "actual",
    mode = "lines+markers",
    line = dict(color = INK, width = 2),
    marker = dict(size = 7, line = dict(color = SURFACE, width = 1.5)),
))
fig.add_trace(go.Scatter(
    x = test.index,
    y = pred_gbm,
    name = "gradient boosting",
    mode = "lines+markers",
    line = dict(color = BLUE, width = 2),
    marker = dict(size = 7, line = dict(color = SURFACE, width = 1.5)),
))
fig.add_trace(go.Scatter(
    x = test.index,
    y = naive_pred,
    name = "seasonal-naive (52-wk lag)",
    mode = "lines",
    line = dict(color = MUTED, width = 2, dash = "dash"),
))
fig.update_yaxes(title = "units/week")
savefig(fig, "04_ml_forecast_holdout", title = f"2027 holdout forecast: {forecast_cat}")

# permutation-free importance from the trained HGB via built-in feature contribution proxy:
# HistGradientBoostingRegressor has no feature_importances_, so use permutation importance
from sklearn.inspection import permutation_importance

perm = permutation_importance(
    gbm,
    test[features],
    test["units"],
    n_repeats = 30,
    random_state = 0,
)
imp = pd.Series(perm.importances_mean, index = features).sort_values()
results["ml_forecast"]["feature_importance"] = imp.round(3).to_dict()
print(imp)

fig = go.Figure(go.Bar(
    x = imp.values,
    y = imp.index,
    orientation = "h",
    marker = dict(color = BLUE),
))
fig.update_xaxes(title = "permutation importance (MAE increase when shuffled)")
savefig(
    fig,
    "05_ml_feature_importance",
    title = "What the forecaster actually relies on",
    height = 440,
    showlegend = False,
)

print("ML forecast section done")

# ---------------------------------------------------- stockout classifier
stockout_days = inventory_eod[inventory_eod["on_hand"] == 0][["uid", "date"]].copy()
stockout_days["week"] = stockout_days["date"].dt.to_period("W").dt.start_time
stockout_weeks = stockout_days.groupby(["uid", "week"]).size().reset_index(name = "n")
stockout_weeks["stockout"] = 1

inv = inventory_eod.copy()
inv["week"] = inv["date"].dt.to_period("W").dt.start_time
weekly_inv = inv.groupby(["uid", "week"])["on_hand"].mean().rename("avg_on_hand").reset_index()

sales_by_sku_week = sales.copy()
sales_by_sku_week["week"] = sales_by_sku_week["date"].dt.to_period("W").dt.start_time
weekly_demand = sales_by_sku_week.groupby(["uid", "week"])["qty"].sum().rename("weekly_units").reset_index()

panel = weekly_inv.merge(weekly_demand, on = ["uid", "week"], how = "left").fillna(dict(weekly_units = 0))
panel["category"] = panel["uid"].map(uid_cat)
panel = panel.sort_values(["uid", "week"])
panel["avg_daily_demand_lag"] = panel.groupby("uid")["weekly_units"].shift(1) / 7.0
panel["cover_days"] = panel["avg_on_hand"] / panel["avg_daily_demand_lag"].replace(0, np.nan)
panel["next_week"] = panel.groupby("uid")["week"].shift(-1)
panel = panel.merge(
    stockout_weeks[["uid", "week", "stockout"]].rename(columns = dict(week = "next_week")),
    on = ["uid", "next_week"],
    how = "left",
)
panel["stockout"] = panel["stockout"].fillna(0).astype(int)
panel["month"] = panel["week"].dt.month
panel = panel.dropna(subset = ["cover_days"])
panel = panel[np.isfinite(panel["cover_days"])]
panel["cat_code"] = panel["category"].astype("category").cat.codes

cls_features = ["cover_days", "avg_daily_demand_lag", "month", "cat_code"]
panel_train = panel[panel["week"].dt.year < 2027]
panel_test = panel[panel["week"].dt.year == 2027]

clf = HistGradientBoostingClassifier(
    max_depth = 4,
    learning_rate = 0.08,
    max_iter = 150,
    random_state = 0,
)
clf.fit(panel_train[cls_features], panel_train["stockout"])
proba = clf.predict_proba(panel_test[cls_features])[:, 1]

pr_auc = average_precision_score(panel_test["stockout"], proba)
base_rate = panel_test["stockout"].mean()
precision, recall, thresh = precision_recall_curve(panel_test["stockout"], proba)

print("stockout base rate (test):", base_rate, "PR-AUC:", pr_auc)
results["ml_stockout"] = dict(
    n_train = int(len(panel_train)),
    n_test = int(len(panel_test)),
    base_rate_test = round(float(base_rate), 4),
    pr_auc = round(float(pr_auc), 4),
)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x = recall,
    y = precision,
    name = "classifier",
    mode = "lines",
    line = dict(color = BLUE, width = 2),
))
fig.add_trace(go.Scatter(
    x = [0, 1],
    y = [base_rate, base_rate],
    name = f"random baseline (base rate = {base_rate:.3f})",
    mode = "lines",
    line = dict(color = MUTED, width = 2, dash = "dash"),
))
fig.update_xaxes(title = "recall", range = [0, 1])
fig.update_yaxes(title = "precision", range = [0, 1.02])
savefig(
    fig,
    "06_ml_stockout_pr_curve",
    title = f"Stockout-risk classifier: PR curve (AUC = {pr_auc:.3f})",
    height = 460,
    width = 640,
)

print("ML section done")

# ============================================================ Bayesian
# hierarchical partial pooling of the weekend demand effect, by category.
# Deliberately restricted to the first 90 trading days (not the full three
# years): with three years of data every category's own OLS estimate is
# already precise enough that pooling barely changes anything, which would
# make a weak demonstration. A new shop's first quarter is exactly when a
# real analyst faces this problem for real -- some categories have enough
# volume to trust on their own, others don't yet, and partial pooling is
# the honest way to use what the whole shop knows to steady the ones that
# don't.
early = sales[sales["date"] < sales["date"].min() + pd.Timedelta(days = 90)].copy()
early_cal = calendar.set_index("date")
daily_cat = early.groupby(["category", "date"])["qty"].sum().rename("units").reset_index()
daily_cat["is_weekend"] = daily_cat["date"].map(early_cal["dow"]).ge(5).astype(int)
daily_cat["log_units"] = np.log1p(daily_cat["units"])

cats = sorted(daily_cat["category"].unique())
unpooled = []
for c in cats:
    sub = daily_cat[daily_cat["category"] == c]
    m = smf.ols(formula = "log_units ~ is_weekend", data = sub).fit()
    unpooled.append(dict(
        category = c,
        n_days = int(len(sub)),
        beta = float(m.params["is_weekend"]),
        se = float(m.bse["is_weekend"]),
    ))
unpooled = pd.DataFrame(unpooled).sort_values("se").reset_index(drop = True)
print(unpooled)

import pymc as pm

with pm.Model() as hier:
    mu = pm.Normal("mu", 0, 1)
    tau = pm.HalfNormal("tau", 0.5)
    beta_true = pm.Normal("beta_true", mu, tau, shape = len(unpooled))
    pm.Normal("obs", beta_true, unpooled["se"].values, observed = unpooled["beta"].values)
    # cores=1: avoids the Windows multiprocessing spawn crash (see module
    # docstring) -- fine here, the model is tiny (12 observations)
    idata = pm.sample(
        2000,
        tune = 1500,
        chains = 4,
        cores = 1,
        target_accept = 0.95,
        random_seed = 0,
        progressbar = False,
    )

post_mean = idata.posterior["beta_true"].mean(dim = ("chain", "draw")).values
post_lo = idata.posterior["beta_true"].quantile(0.025, dim = ("chain", "draw")).values
post_hi = idata.posterior["beta_true"].quantile(0.975, dim = ("chain", "draw")).values
global_mu = float(idata.posterior["mu"].mean())
rhat_max = float(pm.summary(idata, var_names = ["mu", "tau"])["r_hat"].max())

unpooled["pooled_mean"] = post_mean
unpooled["pooled_lo"] = post_lo
unpooled["pooled_hi"] = post_hi
print(unpooled)
print("global mu:", global_mu, "max r_hat:", rhat_max)

results["bayes_hierarchical"] = dict(
    n_days_used = 90,
    n_categories = len(cats),
    global_weekend_effect_log = round(global_mu, 3),
    global_weekend_effect_pct = round((np.exp(global_mu) - 1) * 100, 1),
    max_rhat = round(rhat_max, 4),
    table = unpooled.round(3).to_dict(orient = "records"),
)

y_labels = [f"{c}  (n={n})" for c, n in zip(unpooled["category"], unpooled["n_days"])]
y = np.arange(len(unpooled))
fig = go.Figure()
for i in range(len(unpooled)):
    fig.add_trace(go.Scatter(
        x = [unpooled["pooled_lo"].iloc[i], unpooled["pooled_hi"].iloc[i]],
        y = [y[i] - 0.15, y[i] - 0.15],
        mode = "lines",
        line = dict(color = BLUE, width = 6),
        opacity = 0.25,
        showlegend = False,
        hoverinfo = "skip",
    ))
    fig.add_trace(go.Scatter(
        x = [unpooled["beta"].iloc[i], unpooled["pooled_mean"].iloc[i]],
        y = [y[i] + 0.15, y[i] - 0.15],
        mode = "lines",
        line = dict(color = MUTED, width = 1),
        showlegend = False,
        hoverinfo = "skip",
    ))
fig.add_trace(go.Scatter(
    x = unpooled["beta"],
    y = y + 0.15,
    name = "unpooled (per-category OLS)",
    mode = "markers",
    marker = dict(color = RED, size = 10, line = dict(color = SURFACE, width = 2)),
))
fig.add_trace(go.Scatter(
    x = unpooled["pooled_mean"],
    y = y - 0.15,
    name = "partial-pooled (hierarchical posterior mean)",
    mode = "markers",
    marker = dict(color = BLUE, size = 10, line = dict(color = SURFACE, width = 2)),
))
fig.add_vline(x = global_mu, line = dict(color = INK, width = 1, dash = "dash"))
fig.update_yaxes(tickmode = "array", tickvals = list(y), ticktext = y_labels, title = None)
fig.update_xaxes(title = "weekend effect on log(units), first 90 days")
plot_kwargs = dict(PLOT)
plot_kwargs["margin"] = dict(l = 230, r = 28, t = 80, b = 52)
fig.update_layout(
    **plot_kwargs,
    height = 560,
    width = 980,
    legend = dict(
        bgcolor = "rgba(0,0,0,0)",
        font = dict(color = SECONDARY, size = 12),
        orientation = "h",
        y = 1.1,
        x = 0,
    ),
    title = dict(
        text = "Partial pooling shrinks noisy category estimates toward the shop-wide mean",
        x = 0,
        xanchor = "left",
        font = dict(color = INK, size = 14),
    ),
)
fig.update_xaxes(**AXIS)
fig.update_yaxes(**AXIS, tickmode = "array", tickvals = list(y), ticktext = y_labels)
fig.write_image(f"{FIGDIR}/07_bayes_shrinkage.png", scale = 2)

print("Bayesian section done")

with open(f"{FIGDIR}/results.json", "w") as f:
    json.dump(results, f, indent = 2, default = str)
print("wrote results.json")
