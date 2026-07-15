"""Phase 1 — the world at t = 0 (documents/PHASE1_DETAILS.md).

Locations, customers, the owner's beliefs, and his opening MILP (location,
assortment, quantities, staffing, prices).
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pulp

from datagen.params import BASKET_SHARE, BRAND_LEVEL, CATS, MARKUP, PHASE1, PHASE4, ROOT


def load_skus() -> pd.DataFrame:
    df = pd.read_excel(io = ROOT / "SKUs.xlsx")
    df = df.dropna(subset = ["retail_base_price_EUR"]).reset_index(drop = True)
    df["brand"] = df["brand_level"].map(arg = BRAND_LEVEL)
    df["cost"] = df["retail_base_price_EUR"].astype(dtype = float)
    df["idx"] = np.arange(len(df))
    return df


def gen_locations(rng: np.random.Generator) -> pd.DataFrame:
    p = PHASE1
    q = rng.beta(
        a = p["quality_beta"][0],
        b = p["quality_beta"][1],
        size = p["n_locations"],
    )
    hh_raw = rng.normal(
        loc = p["households"]["base"] + p["households"]["slope"] * q,
        scale = p["households"]["sd"],
    )
    hh = np.round(a = np.maximum(0, hh_raw)).astype(dtype = int)
    rent = rng.normal(
        loc = p["rent"]["base"] + p["rent"]["slope"] * q,
        scale = p["rent"]["sd"],
    )
    setup = np.maximum(
        0,
        rng.normal(
            loc = p["setup_cost"]["base"] * (1 - q),
            scale = p["setup_cost"]["sd"],
        ),
    )
    return pd.DataFrame({
        "location_id": np.arange(p["n_locations"]),
        "quality": q,
        "households": hh,
        "rent": rent,
        "setup_cost": setup,
        "operational_needs": (1 + np.floor(2.4 * q)).astype(dtype = int),
        "shelf_capacity_units": np.rint(p["shelf_capacity_units"]["base"]
                                        + p["shelf_capacity_units"]["slope"] * q).astype(dtype = int),
        "shelf_slots": np.rint(p["shelf_slots"]["base"]
                               + p["shelf_slots"]["slope"] * q).astype(dtype = int),
    })


def demand_and_beliefs(
    rng,
    locs,
    shelf_median,
):
    """True addressable demand D_cl (units/month) and the owner's beliefs.

    mu_c converts the addressable monthly spend per household into units at
    the category's shelf-price scale (P1 §4 guardrail: store-addressable)."""
    value = PHASE1["addressable_value_hh_month"]
    mu = {c: value * BASKET_SHARE[c] / shelf_median[c] for c in CATS}
    delta = {
        c: rng.normal(
            loc = PHASE1["belief_bias"],
            scale = PHASE1["belief_sd"],
        )
        for c in CATS
    }
    rows = []
    for _, L in locs.iterrows():
        for c in CATS:
            D = L["households"] * mu[c]
            rows.append({
                "location_id": int(L["location_id"]),
                "category": c,
                "true_demand": D,
                "believed_demand": D * math.exp(delta[c]),
                "belief_delta": delta[c],
            })
    return pd.DataFrame(rows), mu


def solve_milp(
    skus,
    locs,
    beliefs,
):
    """The owner's opening decision (P1 §8, with the audit amendments:
    purchase-side no-dominance cap, hired-staff overhead, gapRel solve)."""
    p = PHASE1
    Dhat = {(r["category"], r["location_id"]): r["believed_demand"]
            for _, r in beliefs.iterrows()}
    uid = list(skus["uid"])
    cost = dict(zip(skus["uid"], skus["cost"]))
    scat = dict(zip(skus["uid"], skus["category"]))
    nl = len(locs)

    prob = pulp.LpProblem(
        name = "owner_t0",
        sense = pulp.LpMaximize,
    )
    y = pulp.LpVariable.dicts(
        name = "y",
        indices = range(nl),
        cat = "Binary",
    )
    x = pulp.LpVariable.dicts(
        name = "x",
        indices = uid,
        cat = "Binary",
    )
    q = pulp.LpVariable.dicts(
        name = "q",
        indices = uid,
        lowBound = 0,
    )
    u = pulp.LpVariable.dicts(
        name = "u",
        indices = uid,
        lowBound = 0,
    )
    Eh = pulp.LpVariable(
        name = "hired",
        lowBound = 0,
    )   # owner works unpaid (P1 §7)

    H0 = p["hours_per_day"] * 30
    revenue = pulp.lpSum(vector = ((1 + MARKUP[scat[s]]) * cost[s] * u[s] for s in uid))
    total = (pulp.lpSum(vector = (y[l] * (locs.rent[l] + locs.setup_cost[l]) for l in range(nl)))
             + pulp.lpSum(vector = (cost[s] * q[s] for s in uid))
             + p["unit_storage"] * pulp.lpSum(vector = (q[s] for s in uid))
             + p["listing_fee"] * pulp.lpSum(vector = (x[s] for s in uid))
             # hiring is costed at the FULL employer price: wage plus payroll
             # contributions — the one tax every real owner prices in (P4 §2)
             + Eh * p["hourly_wage"] * (1 + PHASE4["payroll_rate"]) * H0
             + p["hourly_utility"] * H0)
    prob += revenue - total
    prob += pulp.lpSum(vector = (y[l] for l in range(nl))) == 1
    for s in uid:
        prob += u[s] <= q[s]
    for c in CATS:
        S = [s for s in uid if scat[s] == c]
        dl = pulp.lpSum(vector = (y[l] * Dhat[(c, l)] for l in range(nl)))
        prob += pulp.lpSum(vector = (u[s] for s in S)) <= dl
        prob += pulp.lpSum(vector = (q[s] for s in S)) >= p["eta"] * dl
        Ms = p["rho"] * max(Dhat[(c, l)] for l in range(nl))
        for s in S:
            prob += u[s] <= p["rho"] * dl
            prob += q[s] <= p["rho"] * dl      # tightened purchase cap (audit)
            prob += q[s] <= Ms * x[s]
    prob += pulp.lpSum(vector = (q[s] for s in uid)) \
        <= pulp.lpSum(vector = (y[l] * locs.shelf_capacity_units[l] for l in range(nl)))
    prob += pulp.lpSum(vector = (x[s] for s in uid)) \
        <= pulp.lpSum(vector = (y[l] * locs.shelf_slots[l] for l in range(nl)))
    prob += Eh >= pulp.lpSum(vector = (y[l] * locs.operational_needs[l] for l in range(nl))) - 1
    prob += total <= p["capital"]
    prob.solve(
        solver = pulp.PULP_CBC_CMD(
            msg = 0,
            gapRel = 0.005,
            timeLimit = 120,
        ),
    )
    assert pulp.LpStatus[prob.status] == "Optimal", pulp.LpStatus[prob.status]

    loc = next(l for l in range(nl) if y[l].value() > 0.5)
    dec = pd.DataFrame({
        "uid": uid,
        "listed": [int((x[s].value() or 0) > 0.5) for s in uid],
        "q0": [round(max(0.0, q[s].value() or 0.0)) for s in uid],   # relax-and-round
        "believed_sales": [max(0.0, u[s].value() or 0.0) for s in uid],
    })
    return {
        "location": loc,
        "hired": round(Eh.value() or 0),
        "believed_profit": pulp.value(prob.objective),
        "spend": pulp.value(total),
        "decision": dec,
    }


def gen_customers(
    rng,
    n_households,
):
    p = PHASE1
    n = rng.binomial(
        n = n_households,
        p = p["customer_participation"],
    )
    budget = rng.lognormal(
        mean = p["budget_lognormal"]["mu"],
        sigma = p["budget_lognormal"]["sigma"],
        size = n,
    )
    z = (np.log(budget) - p["budget_lognormal"]["mu"]) / p["budget_lognormal"]["sigma"]
    nu = rng.normal(
        loc = 0,
        scale = 1,
        size = n,
    )
    lam = p["brand_budget_loading"]
    brand_aff = 1 / (1 + np.exp(-(lam * z + math.sqrt(1 - lam**2) * nu)))
    alpha = np.array(object = [BASKET_SHARE[c] for c in CATS]) * p["dirichlet_conc"]
    frame = pd.DataFrame({
        "customer_id": np.arange(n),
        "weekly_budget": budget,
        "primary_day": rng.choice(
            a = 7,
            size = n,
            p = p["primary_day_weights"],
        ),
        "adherence": rng.beta(
            a = p["adherence_beta"][0],
            b = p["adherence_beta"][1],
            size = n,
        ),
        "topup_rate": rng.beta(
            a = p["topup_beta"][0],
            b = p["topup_beta"][1],
            size = n,
        ),
        "price_sens": rng.lognormal(
            mean = p["price_sens_lognormal"]["mu"],
            sigma = p["price_sens_lognormal"]["sigma"],
            size = n,
        ),
        "brand_affinity": brand_aff,
        "card_type": rng.random(size = n) < p["card_share"],
    })
    weights = pd.DataFrame(
        data = rng.dirichlet(
            alpha = alpha,
            size = n,
        ),
        columns = [f"w{ci}" for ci in range(len(CATS))],
    )
    return frame.join(other = weights)
