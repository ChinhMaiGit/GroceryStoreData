"""Export — writes data/visible/ (through the recording layer) and
data/hidden/ (the answer key). See documents/ACCOUNTING.md for what each
artifact records and the reconciliation contract between them.
"""

from __future__ import annotations

import pandas as pd

from datagen.keys import token
from datagen.params import CATS, OUT, PHASE2
from datagen.recording import dirty_layer


def export(
    world,
    base,
    oracle,
    out = OUT,
):
    vis, hid = out / "visible", out / "hidden"
    vis.mkdir(
        parents = True,
        exist_ok = True,
    )
    hid.mkdir(
        parents = True,
        exist_ok = True,
    )
    w = world

    # --- visible: the analyst's dataset, passed through the recording layer ---
    rec = base["receipts"].copy()
    date_of = dict(zip(w.cal.t, w.cal.date))
    rec["date"] = rec["t"].map(arg = date_of)
    rec.loc[rec.customer_id == "", "customer_id"] = pd.NA
    rec["ref_receipt_id"] = rec["ref_receipt_id"].astype(dtype = "Int64")
    rec = rec.drop(columns = "t")
    inv = base["inventory"].copy()
    inv["date"] = inv["t"].map(arg = date_of)
    inv = inv.drop(columns = "t")
    pr = base["procurement"].copy()
    pr["order_date"] = pr["order_t"].map(arg = date_of)
    pr["delivery_date"] = pr["delivery_t"].map(arg = date_of)
    pr = pr.drop(columns = [
        "order_t",
        "delivery_t",
    ])
    pm = base["promotions"].copy()
    if len(pm):
        pm["start_date"] = pm["start_t"].map(arg = date_of)
        pm["end_date"] = pm["end_t"].map(arg = lambda x: date_of.get(x, w.cal.date.iloc[-1]))
        pm = pm.drop(columns = [
            "start_t",
            "end_t",
        ])
    wo = base["write_offs"].copy()
    if len(wo):
        wo["date"] = wo["t"].map(arg = date_of)
        wo = wo.drop(columns = "t")
    wxv = w.wx.copy()
    wxv["date"] = wxv["t"].map(arg = date_of)
    _wx_cols = [
        "date",
        "temp_C",
        "rain_mm",
        "wet",
    ]
    frames, ledger = dirty_layer(
        world = w,
        frames = {
            "receipts": rec,
            "inventory_eod": inv,
            "procurement": pr,
            "promotions": pm,
            "write_offs": wo,
            "weather": wxv[_wx_cols],
        },
    )
    for _name, _df in frames.items():
        _df.to_csv(
            path_or_buf = vis / f"{_name}.csv",
            index = False,
        )
    ph = base["price_history"].copy()
    ph["date"] = ph["t"].map(arg = date_of)
    ph.drop(columns = "t").to_csv(
        path_or_buf = vis / "price_history.csv",
        index = False,
    )
    base["cost_sheet"].to_csv(
        path_or_buf = vis / "cost_sheet.csv",
        index = False,
    )
    # the annual tax statement (P4 §2): VAT, payroll, and the profit-tax
    # accrual — what the accountant files after the year closes
    _cs = base["cost_sheet"]
    pd.DataFrame([{
        "year": 2025,
        "vat_remitted": float(_cs["vat"].sum()),
        "payroll_tax": float(_cs["payroll_tax"].sum()),
        "profit_before_tax": base["realized_profit"],
        "profit_tax": base["profit_tax"],
        "profit_after_tax": base["realized_after_tax"],
    }]).to_csv(
        path_or_buf = vis / "tax_statement.csv",
        index = False,
    )
    w.cal.drop(columns = "t").to_csv(
        path_or_buf = vis / "calendar.csv",
        index = False,
    )
    w.locs.drop(columns = [
        "quality",
        "households",
    ]).to_csv(
        path_or_buf = vis / "locations.csv",
        index = False,
    )
    ledger.to_csv(
        path_or_buf = hid / "imperfections.csv",
        index = False,
    )

    # --- hidden: the answer key ---
    w.locs.to_csv(
        path_or_buf = hid / "locations_full.csv",
        index = False,
    )
    w.beliefs.to_csv(
        path_or_buf = hid / "location_category.csv",
        index = False,
    )
    w.customers.assign(
        token = [token(
            kind = 0,
            n = int(i),
        ) for i in w.customers.customer_id],
    ).to_csv(
        path_or_buf = hid / "customers.csv",
        index = False,
    )
    base["guests"].to_csv(
        path_or_buf = hid / "guests.csv",
        index = False,
    )
    w.milp["decision"].to_csv(
        path_or_buf = hid / "decision_t0.csv",
        index = False,
    )
    base["hidden"].to_csv(
        path_or_buf = hid / "hidden_demand.csv",
        index = False,
    )
    base["forecasts"].to_csv(
        path_or_buf = hid / "owner_forecasts.csv",
        index = False,
    )
    pd.DataFrame({
        "t": w.cal.t,
        **{f"M_{c}": w.M[c] for c in CATS},
        "traffic": w.lam,
    }).to_csv(
        path_or_buf = hid / "demand_modifiers.csv",
        index = False,
    )
    pd.DataFrame({
        "t": w.cal.t,
        **{f"psi_{k}": v for k, v in w.psi.items()},
    }).to_csv(
        path_or_buf = hid / "tilts.csv",
        index = False,
    )
    pd.DataFrame({
        "t": w.cal.t,
        **{f"cost_{c}": w.cost_mult[c] for c in CATS},
    }).join(other = w.rates.drop(columns = "t")).to_csv(
        path_or_buf = hid / "cost_paths.csv",
        index = False,
    )
    pd.DataFrame({
        "t": w.cal.t,
        **{f"spoilf_{c}": v for c, v in w.spoilf.items()},
    }).to_csv(
        path_or_buf = hid / "spoil_factors.csv",
        index = False,
    )
    pd.DataFrame(
        data = w.budgets,
        columns = [f"w{k}" for k in range(1, 53)],
    ).assign(customer_id = w.customers.customer_id).to_csv(
        path_or_buf = hid / "budget_paths.csv",
        index = False,
    )
    pd.DataFrame(
        data = w.spells,
        columns = [f"w{k}" for k in range(1, 53)],
    ).assign(customer_id = w.customers.customer_id).to_csv(
        path_or_buf = hid / "spell_flags.csv",
        index = False,
    )
    pd.DataFrame([{
        **{k: v for k, v in e.items() if k != "cats"},
        "categories": "|".join(e["cats"]),
        "peaks": "|".join(f"{z:.3f}" for z in e["cats"].values()),
    } for e in w.events]).to_csv(
        path_or_buf = hid / "event_log.csv",
        index = False,
    )
    pd.DataFrame([{
        "category": c,
        "a": a,
        "kappa": k,
        "h": h,
    } for c, (a, k, h) in PHASE2["loadings"].items()]).to_csv(
        path_or_buf = hid / "category_loadings.csv",
        index = False,
    )
    pd.DataFrame([{
        "believed_profit_month1": w.milp["believed_profit"],
        "realized_profit_year": base["realized_profit"],
        "realized_after_tax": base["realized_after_tax"],
        "oracle_profit_year": oracle["realized_profit"],
        "oracle_after_tax": oracle["realized_after_tax"],
    }]).to_csv(
        path_or_buf = hid / "profit_triptych.csv",
        index = False,
    )
    wxv.to_csv(
        path_or_buf = hid / "weather_full.csv",
        index = False,
    )
    return frames, ledger
