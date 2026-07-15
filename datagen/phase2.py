"""Phase 2 — the script of the year (documents/PHASE2_DETAILS.md).

Calendar, weather, demand modifiers and tilts, traffic, budget paths, macro
events, cost and spoilage-factor paths.
"""

from __future__ import annotations

import datetime as dt
import math

import numpy as np
import pandas as pd

from datagen.keys import K_PHASE2, rng_for
from datagen.params import CATS, PHASE1, PHASE2, PHASE3


def gen_calendar():
    p = PHASE2
    days = [p["start"] + dt.timedelta(d) for d in range(p["n_days"])]
    hol_by_date = {d: n for n, d in p["holidays"].items()}
    pre = set()
    for name in p["major_holidays"]:
        d0 = p["holidays"][name]
        for k in range(1, p["pre_holiday_days"] + 1):
            pre.add(d0 - dt.timedelta(k))
    return pd.DataFrame({
        "t": np.arange(1, p["n_days"] + 1),
        "date": days,
        "dow": [d.weekday() for d in days],
        "month": [d.month for d in days],
        "week": [min(52, (t - 1) // 7 + 1) for t in range(1, p["n_days"] + 1)],
        "season": [("winter", "spring", "summer", "autumn")[(d.month % 12) // 3] for d in days],
        "holiday": [hol_by_date.get(d, "") for d in days],
        "pre_holiday": [int(d in pre) for d in days],
        "closed": [int(d in p["closures"]) for d in days],
    })


def gen_weather(
    rng,
    cal,
):
    p = PHASE2["temp"]
    n = len(cal)
    t = cal["t"].to_numpy()
    mu = p["mean"] + p["amp"] * np.cos(2 * np.pi * (t - p["peak_day"]) / 365)
    eps = np.empty(n)
    eps[0] = rng.normal(
        loc = 0,
        scale = p["sd"] / math.sqrt(1 - p["phi"]**2),
    )
    for i in range(1, n):
        eps[i] = p["phi"] * eps[i - 1] + rng.normal(
            loc = 0,
            scale = p["sd"],
        )
    r = PHASE2["rain"]
    wet = np.empty(
        shape = n,
        dtype = int,
    )
    wet[0] = rng.random() < r["p01"] / (r["p01"] + 1 - r["p11"])
    for i in range(1, n):
        wet[i] = rng.random() < (r["p11"] if wet[i - 1] else r["p01"])
    amounts = rng.gamma(
        shape = r["gamma_shape"],
        scale = r["mean_mm"] / r["gamma_shape"],
        size = n,
    )
    mm = np.where(wet, amounts, 0.0)
    return pd.DataFrame({
        "t": t,
        "temp_C": mu + eps,
        "temp_seasonal": mu,
        "anomaly": eps,
        "z": eps / 2.8,
        "rain_mm": mm,
        "wet": wet,
    })


def gen_events(rng):
    p = PHASE2
    events = [{
        "event_id": 0,
        "type": "energy_crisis",
        "start": p["crisis"]["start_day"],
        "ramp": p["crisis"]["ramp"],
        "decay": p["crisis"]["decay"],
        "cats": dict(p["crisis"]["cats"]),
        "utility_peak": p["crisis"]["utility_peak"],
    }]
    for k in range(rng.poisson(lam = p["event_rate"])):
        typ = list(p["event_types"])[rng.integers(low = len(p["event_types"]))]
        cats, med = p["event_types"][typ]
        zeta = rng.lognormal(
            mean = math.log(med),
            sigma = p["event_sd"],
        )
        events.append({
            "event_id": k + 1,
            "type": typ,
            "start": float(rng.uniform(
                low = 1,
                high = 365,
            )),
            "ramp": p["event_ramp"],
            "decay": p["event_decay"],
            "cats": {c: zeta for c in (CATS if cats == "ALL" else cats)},
            "utility_peak": 0.0,
        })
    return events


def _traj(
    t,
    start,
    ramp,
    decay,
):
    x = np.clip(
        a = (t - start) / ramp,
        a_min = 0,
        a_max = 1,
    ) * np.exp(-np.clip(
        a = t - start - ramp,
        a_min = 0,
        a_max = None,
    ) / decay)
    return np.where(t >= start, x, 0.0)


def gen_paths(
    cal,
    wx,
    events,
    rng,
):
    """Demand modifiers, tilts, traffic, cost paths, rates, spoilage factors —
    all mean-one normalized where the documents say so."""
    p = PHASE2
    t = cal["t"].to_numpy()
    cyc = np.cos(2 * np.pi * (t - p["temp"]["peak_day"]) / 365)
    z, H = wx["z"].to_numpy(), cal["pre_holiday"].to_numpy()

    M = {}
    for c in CATS:
        a, k, h = p["loadings"][c]
        m = np.exp(a * cyc + k * z + h * H)
        M[c] = m / m.mean()
    psi = {}
    for ptype, (a, k) in p["tilts"].items():
        s = np.exp(a * cyc + k * z)
        psi[ptype] = s / s.mean()

    # traffic: rain, holidays, plus the unmodeled residue of local life —
    # roadworks, a market day, a lingering local mood (an AR(1) daily shock,
    # not i.i.d.: real daily footfall persists day to day, just as the
    # temperature anomaly of Section 2 does)
    _sd = p["traffic"]["daily_shock_sd"]
    _phi = p["traffic"]["daily_shock_phi"]
    _innov_sd = _sd * math.sqrt(1 - _phi**2)
    _eps_traffic = np.empty(len(t))
    _eps_traffic[0] = rng.normal(
        loc = 0,
        scale = _sd,
    )
    for _i in range(1, len(t)):
        _eps_traffic[_i] = _phi * _eps_traffic[_i - 1] + rng.normal(
            loc = 0,
            scale = _innov_sd,
        )
    lam = np.exp(p["traffic"]["wet"] * wx["wet"].to_numpy()
                 + p["traffic"]["pre_holiday"] * H
                 + _eps_traffic)
    open_mask = cal["closed"].to_numpy() == 0
    lam = np.where(open_mask, lam / lam[open_mask].mean(), 0.0)

    infl = np.exp(p["inflation"] * t / 365)
    cost_mult = {c: infl.copy() for c in CATS}
    g_energy = np.zeros(len(t))
    for ev in events:
        g = _traj(
            t = t,
            start = ev["start"],
            ramp = ev["ramp"],
            decay = ev["decay"],
        )
        for c, zeta in ev["cats"].items():
            cost_mult[c] = cost_mult[c] * np.exp(zeta * g)
        if ev["utility_peak"] > 0:
            g_energy = ev["utility_peak"] * g
    rates = pd.DataFrame({
        "t": t,
        "utility_rate": PHASE1["hourly_utility"] * infl * np.exp(g_energy),
        "wage_rate": PHASE1["hourly_wage"] * (1 + p["wage_raise"]["pct"] * (t >= p["wage_raise"]["day"])),
        "storage_rate": PHASE1["unit_storage"] * infl,
    })
    # crisis trajectory normalized to peak one -> weekly, for budget coupling
    gbar = _traj(
        t = t,
        start = p["crisis"]["start_day"],
        ramp = p["crisis"]["ramp"],
        decay = p["crisis"]["decay"],
    )
    gbar_w = np.array(object = [gbar[cal["week"].to_numpy() == w].mean() for w in range(1, 53)])

    # spoilage factor paths: heat + cold-chain strain + batch luck, mean one
    temp_dev = (wx["temp_C"].to_numpy() - PHASE2["temp"]["mean"]) / 10.0
    spoilf = {}
    for c, (kT, kE) in PHASE3["spoil_response"].items():
        f = np.exp(kT * temp_dev + kE * gbar
                   + rng.normal(
                       loc = 0,
                       scale = PHASE3["spoil_wobble_sd"],
                       size = len(t),
                   ))
        spoilf[c] = f / f.mean()
    return M, psi, lam, cost_mult, rates, gbar_w, spoilf


def gen_budget_paths(
    customers,
    gbar_w,
):
    p = PHASE2
    n, W = len(customers), 52
    B = np.empty(shape = (n, W))
    spell_flag = np.zeros(
        shape = (n, W),
        dtype = int,
    )
    for i in range(n):
        g = rng_for(K_PHASE2, 10, i)
        in_spell = False
        left = 0
        entry = p["tight_spell"]["entry"] * (1 + p["tight_spell"]["crisis_coupling"] * gbar_w)
        for w in range(W):
            if not in_spell and g.random() < entry[w]:
                in_spell = True
                left = g.geometric(p = 1 / p["tight_spell"]["mean_weeks"])
            s = p["tight_spell"]["mult"] if in_spell else 1.0
            spell_flag[i, w] = int(in_spell)
            if in_spell:
                left -= 1
                if left <= 0:
                    in_spell = False
            gk = p["splurge"]["mult"] if g.random() < p["splurge"]["prob"] else 1.0
            wobble = g.normal(
                loc = 0,
                scale = p["wobble_sd"],
            )
            B[i, w] = customers.weekly_budget.iloc[i] * math.exp(wobble) * s * gk
    return B, spell_flag
