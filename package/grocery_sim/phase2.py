"""Phase 2 — the script of the year (documents/PHASE2_DETAILS.md).

Calendar, weather, demand modifiers and tilts, traffic, budget paths, macro
events, cost and spoilage-factor paths.
"""

from __future__ import annotations

import datetime as dt
import math

import numpy as np
import pandas as pd

from .keys import K_PHASE2, rng_for
from .params import CATS, PHASE1, PHASE2, PHASE3, PHASE5


def gen_calendar(n_years = 1):
    """One row per day. Extra years (P5 §2) pull their holidays from PHASE5;
    the year-suffixed names are stripped so the visible label stays the same
    word ('christmas', not 'christmas_2026'). The week counter runs per
    calendar year — weeks 1-52 with the year's ragged tail folded into week
    52, then offset by 52 per year — so year-one values never move."""
    p = PHASE2
    n_days = 365 * n_years
    days = [p["start"] + dt.timedelta(d) for d in range(n_days)]
    holidays = dict(p["holidays"])
    major = list(p["major_holidays"])
    closures = set(p["closures"])
    if n_years > 1:
        holidays.update(PHASE5["holidays"])
        major += PHASE5["major_holidays"]
        closures |= set(PHASE5["closures"])
    hol_by_date = {d: n.rsplit("_20", 1)[0] for n, d in holidays.items()}
    pre = set()
    for name in major:
        d0 = holidays[name]
        for k in range(1, p["pre_holiday_days"] + 1):
            pre.add(d0 - dt.timedelta(k))
    week = [52 * ((t - 1) // 365) + min(52, ((t - 1) % 365) // 7 + 1)
            for t in range(1, n_days + 1)]
    return pd.DataFrame({
        "t": np.arange(1, n_days + 1),
        "date": days,
        "dow": [d.weekday() for d in days],
        "month": [d.month for d in days],
        "week": week,
        "season": [("winter", "spring", "summer", "autumn")[(d.month % 12) // 3] for d in days],
        "holiday": [hol_by_date.get(d, "") for d in days],
        "pre_holiday": [int(d in pre) for d in days],
        "closed": [int(d in closures) for d in days],
    })


def gen_weather(
    cal,
    n_years = 1,
):
    """Generated in per-year blocks from per-year keyed streams (P5 §2): the
    first block consumes rng_for(K_PHASE2, 0) in exactly the one-year order,
    so year one is draw-for-draw identical to the published baseline; later
    blocks get fresh keys, with the AR(1) anomaly and the rain Markov chain
    continued from the previous block's last state."""
    p = PHASE2["temp"]
    r = PHASE2["rain"]
    t = cal["t"].to_numpy()
    mu = p["mean"] + p["amp"] * np.cos(2 * np.pi * (t - p["peak_day"]) / 365)
    eps = np.empty(len(t))
    wet = np.empty(
        shape = len(t),
        dtype = int,
    )
    mm = np.empty(len(t))
    for y in range(n_years):
        rng = rng_for(K_PHASE2, 0) if y == 0 else rng_for(K_PHASE2, 0, y)
        lo = 365 * y
        if y == 0:
            eps[0] = rng.normal(
                loc = 0,
                scale = p["sd"] / math.sqrt(1 - p["phi"]**2),
            )
        else:
            eps[lo] = p["phi"] * eps[lo - 1] + rng.normal(
                loc = 0,
                scale = p["sd"],
            )
        for i in range(lo + 1, lo + 365):
            eps[i] = p["phi"] * eps[i - 1] + rng.normal(
                loc = 0,
                scale = p["sd"],
            )
        if y == 0:
            wet[0] = rng.random() < r["p01"] / (r["p01"] + 1 - r["p11"])
        else:
            wet[lo] = rng.random() < (r["p11"] if wet[lo - 1] else r["p01"])
        for i in range(lo + 1, lo + 365):
            wet[i] = rng.random() < (r["p11"] if wet[i - 1] else r["p01"])
        amounts = rng.gamma(
            shape = r["gamma_shape"],
            scale = r["mean_mm"] / r["gamma_shape"],
            size = 365,
        )
        mm[lo: lo + 365] = np.where(wet[lo: lo + 365], amounts, 0.0)
    return pd.DataFrame({
        "t": t,
        "temp_C": mu + eps,
        "temp_seasonal": mu,
        "anomaly": eps,
        "z": eps / 2.8,
        "rain_mm": mm,
        "wet": wet,
    })


def gen_events(n_years = 1):
    """The scripted crisis plus the drawn surprises. Extra years draw their
    own surprise sets from per-year keys (P5 §2), appended after year one's
    so the baseline event log stays a prefix of the three-year one."""
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
    for y in range(n_years):
        rng = rng_for(K_PHASE2, 1) if y == 0 else rng_for(K_PHASE2, 1, y)
        for _ in range(rng.poisson(lam = p["event_rate"])):
            typ = list(p["event_types"])[rng.integers(low = len(p["event_types"]))]
            cats, med = p["event_types"][typ]
            zeta = rng.lognormal(
                mean = math.log(med),
                sigma = p["event_sd"],
            )
            events.append({
                "event_id": len(events),
                "type": typ,
                "start": 365 * y + float(rng.uniform(
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


def _norm_by_year(
    x,
    n_years,
):
    """Mean-one per 365-day block (P5 §2): year one's normalization never
    sees the later years, and the later years carry no normalization trend —
    growth lives in the panel, not in the modifiers (P5 §11)."""
    out = np.empty_like(x)
    for y in range(n_years):
        lo = 365 * y
        out[lo: lo + 365] = x[lo: lo + 365] / x[lo: lo + 365].mean()
    return out


def gen_paths(
    cal,
    wx,
    events,
    n_years = 1,
):
    """Demand modifiers, tilts, traffic, cost paths, rates, spoilage factors —
    all mean-one normalized where the documents say so (per year-block, P5
    §2). Random draws come in per-year blocks from per-year keyed streams,
    each block drawing in the one-year order (traffic AR first, then the six
    spoilage wobble vectors), so year one is draw-for-draw the baseline."""
    p = PHASE2
    t = cal["t"].to_numpy()
    cyc = np.cos(2 * np.pi * (t - p["temp"]["peak_day"]) / 365)
    z, H = wx["z"].to_numpy(), cal["pre_holiday"].to_numpy()

    M = {}
    for c in CATS:
        a, k, h = p["loadings"][c]
        M[c] = _norm_by_year(
            x = np.exp(a * cyc + k * z + h * H),
            n_years = n_years,
        )
    psi = {}
    for ptype, (a, k) in p["tilts"].items():
        psi[ptype] = _norm_by_year(
            x = np.exp(a * cyc + k * z),
            n_years = n_years,
        )

    # traffic: rain, holidays, plus the unmodeled residue of local life —
    # roadworks, a market day, a lingering local mood (an AR(1) daily shock,
    # not i.i.d.: real daily footfall persists day to day, just as the
    # temperature anomaly of Section 2 does)
    _sd = p["traffic"]["daily_shock_sd"]
    _phi = p["traffic"]["daily_shock_phi"]
    _innov_sd = _sd * math.sqrt(1 - _phi**2)
    _eps_traffic = np.empty(len(t))
    _wobbles = {c: np.empty(len(t)) for c in PHASE3["spoil_response"]}
    for y in range(n_years):
        rng = rng_for(K_PHASE2, 2) if y == 0 else rng_for(K_PHASE2, 2, y)
        lo = 365 * y
        if y == 0:
            _eps_traffic[0] = rng.normal(
                loc = 0,
                scale = _sd,
            )
        else:
            _eps_traffic[lo] = _phi * _eps_traffic[lo - 1] + rng.normal(
                loc = 0,
                scale = _innov_sd,
            )
        for _i in range(lo + 1, lo + 365):
            _eps_traffic[_i] = _phi * _eps_traffic[_i - 1] + rng.normal(
                loc = 0,
                scale = _innov_sd,
            )
        # the spoilage batch-luck wobbles are drawn AFTER the block's traffic
        # shocks, mirroring the one-year draw order stream-for-stream
        for c in PHASE3["spoil_response"]:
            _wobbles[c][lo: lo + 365] = rng.normal(
                loc = 0,
                scale = PHASE3["spoil_wobble_sd"],
                size = 365,
            )
    lam_raw = np.exp(p["traffic"]["wet"] * wx["wet"].to_numpy()
                     + p["traffic"]["pre_holiday"] * H
                     + _eps_traffic)
    open_mask = cal["closed"].to_numpy() == 0
    lam = np.empty(len(t))
    for y in range(n_years):
        _sl = slice(365 * y, 365 * y + 365)
        _open = open_mask[_sl]
        lam[_sl] = np.where(_open, lam_raw[_sl] / lam_raw[_sl][_open].mean(), 0.0)

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
    wage = PHASE1["hourly_wage"] * (1 + p["wage_raise"]["pct"] * (t >= p["wage_raise"]["day"]))
    utility = PHASE1["hourly_utility"] * infl * np.exp(g_energy)
    if n_years > 1:
        # the lumpy contract steps (P5 §5): statutory July wage revisions
        # and January utility-tariff resets, on top of the smooth drift
        for _day, _pct in PHASE5["contracts"]["wage_raises"]:
            wage = wage * (1 + _pct * (t >= _day))
        for _day, _mult in PHASE5["contracts"]["utility_tariff"]:
            utility = utility * np.where(t >= _day, _mult, 1.0)
    rates = pd.DataFrame({
        "t": t,
        "utility_rate": utility,
        "wage_rate": wage,
        "storage_rate": PHASE1["unit_storage"] * infl,
    })
    # crisis trajectory normalized to peak one -> weekly, for budget coupling
    gbar = _traj(
        t = t,
        start = p["crisis"]["start_day"],
        ramp = p["crisis"]["ramp"],
        decay = p["crisis"]["decay"],
    )
    _wk = cal["week"].to_numpy()
    gbar_w = np.array(object = [gbar[_wk == w].mean() for w in range(1, 52 * n_years + 1)])

    # spoilage factor paths: heat + cold-chain strain + batch luck, mean one
    temp_dev = (wx["temp_C"].to_numpy() - PHASE2["temp"]["mean"]) / 10.0
    spoilf = {}
    for c, (kT, kE) in PHASE3["spoil_response"].items():
        spoilf[c] = _norm_by_year(
            x = np.exp(kT * temp_dev + kE * gbar + _wobbles[c]),
            n_years = n_years,
        )
    return M, psi, lam, cost_mult, rates, gbar_w, spoilf


def gen_budget_paths(
    customers,
    gbar_w,
):
    p = PHASE2
    n, W = len(customers), len(gbar_w)
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
