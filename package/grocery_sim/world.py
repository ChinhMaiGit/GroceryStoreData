"""The World — everything the daily loop needs, precomputed as arrays.

Assembles Phase 1 (the world at t = 0) and Phase 2 (the script of the year)
and calibrates the outside option so realized capture hits its target.
"""

from __future__ import annotations

import datetime as dt
import math
import time

import numpy as np
import pandas as pd

from .keys import K_PANEL, K_PHASE1, K_PHASE2, rng_for
from .params import CATS, MARKUP, PHASE1, PHASE2, PHASE3, PHASE4, PHASE5, PRICE_ENDINGS
from .scenarios import vat_base_rates
from .phase1 import (
    demand_and_beliefs,
    gen_customers,
    gen_locations,
    gen_newcomer,
    load_skus,
    solve_milp,
)
from .phase2 import (
    gen_budget_paths,
    gen_calendar,
    gen_events,
    gen_paths,
    gen_weather,
)


class World:
    """Everything the daily loop needs, precomputed as arrays.

    `scenario` (P4 §3) is a declarative spec of edits to the exogenous script
    and the owner's policy knobs — never to an RNG key — so a scenario World
    shares every keyed draw with the baseline (CRN)."""

    def __init__(
        self,
        scenario = None,
    ):
        t0 = time.time()
        self.scenario = scenario or {}
        # Phase 5 (P5 §1): a scenario spec carrying a "phase5" key runs the
        # three-year horizon; the key's dict shallow-overrides PHASE5, which
        # is how the twin arms switch single mechanisms off (P5 §9)
        _p5_spec = self.scenario.get("phase5")
        self.p5 = None if _p5_spec is None else {
            **PHASE5,
            **_p5_spec,
        }
        self.n_years = PHASE5["horizon_years"] if self.p5 else 1
        self.n_days = 365 * self.n_years
        self.n_weeks = 52 * self.n_years
        self.skus = load_skus()
        rng1 = rng_for(K_PHASE1, 0)
        self.locs = gen_locations(rng = rng1)
        shelf_median = {
            c: float(self.skus.loc[self.skus.category == c, "cost"].median()) * (1 + MARKUP[c])
            for c in CATS
        }
        self.beliefs, self.mu = demand_and_beliefs(
            rng = rng1,
            locs = self.locs,
            shelf_median = shelf_median,
        )
        self.milp = solve_milp(
            skus = self.skus,
            locs = self.locs,
            beliefs = self.beliefs,
        )
        L = self.milp["location"]
        self.customers = gen_customers(
            rng = rng_for(K_PHASE1, 1),
            n_households = int(self.locs.households[L]),
        )
        self.n0 = len(self.customers)
        if self.p5:
            self._build_panel_flow()
        print(f"  phase 1: location {L} (Q={self.locs.quality[L]:.2f}), "
              f"{int(self.milp['decision'].listed.sum())} SKUs, "
              f"{len(self.customers)} customers, believed profit "
              f"{self.milp['believed_profit']:,.0f}  [{time.time()-t0:.1f}s]")

        self.cal = gen_calendar(n_years = self.n_years)
        self.wx = gen_weather(
            cal = self.cal,
            n_years = self.n_years,
        )
        if self.p5:
            # the 2026 heatwave (P5 §7) edits the weather script BEFORE the
            # paths are built, so demand modifiers and spoilage feel the heat.
            # The anomaly ramps in and out over ramp_days: heat builds and
            # breaks over days, never at midnight (P5 audit amendment)
            _hw = self.p5["heatwave"]
            _t_all = self.wx["t"].to_numpy()
            _profile = _hw["temp_delta"] * np.clip(
                a = np.minimum(
                    (_t_all - _hw["t_from"] + 1) / _hw["ramp_days"],
                    (_hw["t_to"] - _t_all + 1) / _hw["ramp_days"],
                ),
                a_min = 0.0,
                a_max = 1.0,
            )
            self.wx["temp_C"] = self.wx["temp_C"] + _profile
            self.wx["anomaly"] = self.wx["anomaly"] + _profile
            self.wx["z"] = self.wx["anomaly"] / 2.8
        # scenario weather edits are script overwrites BEFORE the paths are
        # built, so demand modifiers and spoilage factors feel the storm too
        for _we in self.scenario.get("weather_edit", []):
            _sl = self.wx.index[(self.wx["t"] >= _we["t_from"]) & (self.wx["t"] <= _we["t_to"])]
            self.wx.loc[_sl, "temp_C"] = self.wx.loc[_sl, "temp_C"] + _we["temp_delta"]
            self.wx.loc[_sl, "anomaly"] = self.wx.loc[_sl, "anomaly"] + _we["temp_delta"]
            self.wx.loc[_sl, "z"] = self.wx.loc[_sl, "anomaly"] / 2.8
            self.wx.loc[_sl, "rain_mm"] = _we["rain_mm"]
            self.wx.loc[_sl, "wet"] = _we["wet"]
        self.events = gen_events(n_years = self.n_years)
        _events_add = list(self.scenario.get("events_add", []))
        if self.p5:
            # the scripted supply shocks of years two and three (P5 §7-8)
            # ride the ordinary event machinery — nothing special downstream
            _events_add.append(self.p5["avian_flu"])
            _events_add.append(self.p5["commodity"])
        for _ev in _events_add:
            _cats = _ev.get("cats")
            if _cats is None:
                _cats = {c: _ev["zeta_all"] for c in CATS}
            self.events.append({
                "event_id": len(self.events),
                "type": _ev["type"],
                "start": _ev["start"],
                "ramp": _ev["ramp"],
                "decay": _ev["decay"],
                "cats": dict(_cats),
                "utility_peak": _ev["utility_peak"],
            })
        self.M, self.psi, self.lam, self.cost_mult, self.rates, gbar_w, self.spoilf = \
            gen_paths(
                cal = self.cal,
                wx = self.wx,
                events = self.events,
                n_years = self.n_years,
            )
        for _tm in self.scenario.get("traffic_mult", []):
            self.lam[_tm["t_from"] - 1: _tm["t_to"]] = \
                self.lam[_tm["t_from"] - 1: _tm["t_to"]] * _tm["mult"]
        # VAT rate paths (P4 §2): scenarios change rates from a date; the
        # gross invoice factor (1+r_t)/(1+r_0) rides the cost-path channel,
        # so tags follow through the same menu-cost hysteresis as any shock
        _base_r = vat_base_rates()
        _n_days = len(self.cal)
        self.vat_rate = {c: np.full(
            shape = _n_days,
            fill_value = _base_r[c],
        ) for c in CATS}
        for _vs in self.scenario.get("vat_schedule", []):
            if "categories" in _vs:
                _targets = _vs["categories"]
            elif _vs.get("group") == "reduced":
                _targets = [c for c in CATS if _base_r[c] == PHASE4["vat_reduced"]]
            else:
                _targets = [c for c in CATS if _base_r[c] == PHASE4["vat_standard"]]
            for c in _targets:
                self.vat_rate[c][_vs["t_from"] - 1:] = _vs["rate"]
        for c in CATS:
            _vfac = (1 + self.vat_rate[c]) / (1 + _base_r[c])
            self.cost_mult[c] = self.cost_mult[c] * _vfac
        # events.tax_raise (grocery_sim's own addition): a flat rate on
        # gross revenue, zero unless a scenario schedules one. Unlike VAT
        # this never touches shelf prices — it is a direct cash cost to the
        # owner, read at the monthly close in phase3.py.
        self.revenue_tax_rate = np.full(shape = _n_days, fill_value = 0.0)
        for _rs in self.scenario.get("revenue_tax_schedule", []):
            self.revenue_tax_rate[_rs["t_from"] - 1:] = _rs["rate"]
        self.budgets, self.spells = gen_budget_paths(
            customers = self.customers,
            gbar_w = gbar_w,
        )
        for _bm in self.scenario.get("budget_mult", []):
            self.budgets[:, _bm["w_from"] - 1: _bm["w_to"]] = \
                self.budgets[:, _bm["w_from"] - 1: _bm["w_to"]] * _bm["mult"]
        # policy knobs (P4 §3): staffing and opening hours
        _pol = self.scenario.get("policy", {})
        self.hired = self.milp["hired"] + _pol.get("hired_extra", 0)
        self.open_hour = _pol.get("open_hour", PHASE3["open_hour"])
        self.close_hour = _pol.get("close_hour", PHASE3["close_hour"])
        print(f"  phase 2: {len(self.events)} events "
              f"({', '.join(e['type'] for e in self.events)})")

        # --- static lookups for the loop ---
        s = self.skus
        self.listed = s.index[self.milp["decision"].listed == 1].to_numpy()
        self.cat_listed = {c: [i for i in self.listed if s.category[i] == c] for c in CATS}
        self.cat_of = s.category.to_dict()
        self.ptype = s.product_type.to_dict()
        self.brand = s.brand.to_numpy()
        self.base_cost = s.cost.to_numpy()
        self.uid = s.uid.to_dict()
        self.markup = np.array(object = [MARKUP[s.category[i]] for i in range(len(s))])
        self.shelf_median = {
            c: float(np.median(a = [(1 + MARKUP[c]) * self.base_cost[i]
                                    for i in self.cat_listed[c]]))
            for c in CATS
        }
        lam_w = PHASE3["spoilage_weekly"]
        self.spoil_daily = np.array(object = [1 - (1 - lam_w.get(s.category[i], 0.0)) ** (1 / 7)
                                              for i in range(len(s))])
        # latent per-SKU appeal: the thousand unmodeled reasons one product
        # outsells its shelf-neighbor; unknown to the owner, hidden from analyst
        self.appeal = rng_for(K_PHASE1, 2).normal(
            loc = 0,
            scale = PHASE1["sku_appeal_sd"],
            size = len(s),
        )
        # each SKU's habitual price ending, fixed at listing time (see charm())
        _ends, _endp = PRICE_ENDINGS
        self.price_end = rng_for(K_PHASE1, 3).choice(
            a = np.array(object = _ends),
            p = _endp,
            size = len(s),
        )
        cust = self.customers
        self.w_ic = cust[[f"w{ci}" for ci in range(len(CATS))]].to_numpy()
        # drain rate r_ic (units/day) — P3 §3; value-consistent with budgets
        self.r_ic = (self.w_ic * cust.weekly_budget.to_numpy()[:, None]
                     / np.array(object = [self.shelf_median[c] for c in CATS])[None, :] / 7.0)
        self.target = PHASE3["pantry_target_days"] * self.r_ic
        if self.p5:
            self._build_phase5_paths()
        self.u0 = self._calibrate_u0()
        print(f"  calibrated outside option u0 = {self.u0:.2f}")

    def _build_panel_flow(self):
        """The panel flow (P5 §3): persistence types for the opening panel,
        monthly departure hazards for transients, replacement arrivals, the
        growth trickle, and the 2026 apartment block. Every draw is keyed by
        stable identity under K_PANEL, and nothing draws before month 13, so
        year one is untouched (P5 §2)."""
        p5p = self.p5["panel"]
        start = PHASE2["start"]
        n_months = 12 * self.n_years

        def _month_first_t(m):
            d = dt.date(
                start.year + (m - 1) // 12,
                (m - 1) % 12 + 1,
                1,
            )
            return (d - start).days + 1

        def _month_last_t(m):
            return _month_first_t(m = m + 1) - 1 if m < n_months else self.n_days

        def _month_of_t(t):
            d = start + dt.timedelta(int(t) - 1)
            return (d.year - start.year) * 12 + d.month

        def _departure_month(
            idx,
            first_month,
        ):
            g = rng_for(K_PANEL, 1, idx)
            for m in range(max(p5p["churn_start_month"], first_month), n_months + 1):
                if g.random() < p5p["transient_monthly_hazard"]:
                    return m
            return None

        gp = rng_for(K_PANEL, 0)
        _trans0 = gp.random(size = self.n0) < p5p["transient_share"]
        persistence = ["transient" if x else "rooted" for x in _trans0]
        departure_t = [np.nan] * self.n0
        new_rows = []
        pending_repl = []      # (departure month, departing index) — chronological
        for i in range(self.n0):
            if _trans0[i]:
                m = _departure_month(
                    idx = i,
                    first_month = 1,
                )
                if m is not None:
                    departure_t[i] = float(_month_last_t(m = m))
                    pending_repl.append((m, i))

        def _add_newcomer(
            arr_month = None,
            arr_t = None,
        ):
            idx = self.n0 + len(new_rows)
            g = rng_for(K_PANEL, 5, idx)
            row = gen_newcomer(rng = g)
            _trans = g.random() < p5p["newcomer_transient_share"]
            a_t = int(arr_t) if arr_t is not None else _month_first_t(m = arr_month)
            a_m = _month_of_t(t = a_t)
            row["customer_id"] = idx
            row["arrival_t"] = a_t
            row["departure_t"] = np.nan
            row["persistence"] = "transient" if _trans else "rooted"
            if _trans:
                m = _departure_month(
                    idx = idx,
                    first_month = a_m + 1,
                )
                if m is not None:
                    row["departure_t"] = float(_month_last_t(m = m))
                    pending_repl.append((m, idx))
            new_rows.append(row)

        # the apartment block fills (P5 §7): a scripted arrival surge
        _blk = p5p["apartment_block"]
        gb = rng_for(K_PANEL, 4)
        _blk_days = sorted(int(x) for x in gb.integers(
            low = _blk["t_from"],
            high = _blk["t_from"] + _blk["ramp_days"],
            size = _blk["n_new"],
        ))
        for _d in _blk_days:
            _add_newcomer(arr_t = _d)
        # the slow growth trickle: the neighborhood does not boom, but it
        # does not hold its breath through year one either
        for y in range(self.n_years):
            gt = rng_for(K_PANEL, 3, y)
            _n_extra = gt.poisson(lam = p5p["growth_trickle_per_year"])
            _months = sorted(int(x) for x in gt.integers(
                low = 12 * y + 1,
                high = 12 * y + 13,
                size = _n_extra,
            ))
            for _m in _months:
                _add_newcomer(arr_month = _m)
        # each departure re-lets the flat: replacements arrive with a lag,
        # and a transient replacement may itself depart and be replaced
        _k_repl = 0
        while pending_repl:
            pending_repl.sort()
            m_dep, _ = pending_repl.pop(0)
            gr = rng_for(K_PANEL, 2, _k_repl)
            _k_repl += 1
            _arr_m = m_dep + int(gr.geometric(p = p5p["replacement_delay_p"]))
            if _arr_m <= n_months:
                _add_newcomer(arr_month = _arr_m)

        cust = self.customers.assign(
            arrival_t = 1,
            departure_t = departure_t,
            persistence = persistence,
        )
        self.customers = pd.concat(
            objs = [
                cust,
                pd.DataFrame(new_rows),
            ],
            ignore_index = True,
        )[list(cust.columns)]

    def _build_phase5_paths(self):
        """Per-day activity mask, the guest-intensity path, and the
        discounter's heterogeneous defection multipliers (P5 §3, §8)."""
        p5 = self.p5
        n = len(self.customers)
        arr = self.customers["arrival_t"].to_numpy()
        dep = self.customers["departure_t"].to_numpy()
        self.arrival_t_arr = arr.astype(dtype = int)
        days = np.arange(1, self.n_days + 1)
        self.active = (arr[None, :] <= days[:, None]) \
            & (np.isnan(dep)[None, :] | (days[:, None] <= dep[None, :]))
        n_active = self.active.sum(axis = 1)
        # guests scale with the neighborhood (P5 §3), get a permanent bump
        # from the block, a fortnight of festival, and the discounter's dent
        gm = n_active / float(self.n0)
        _blk = p5["panel"]["apartment_block"]
        gm = gm * np.where(days >= _blk["t_from"], _blk["guest_mult"], 1.0)
        _fst = p5["festival"]
        gm = gm * np.where((days >= _fst["t_from"]) & (days <= _fst["t_to"]),
                           _fst["guest_mult"], 1.0)
        comp = p5["competitor"]
        if comp is not None:
            self.comp_ramp = np.clip(
                a = (days - comp["t"]) / comp["ramp_days"],
                a_min = 0.0,
                a_max = 1.0,
            )
            gm = gm * (1 - (1 - comp["guest_mult"]) * self.comp_ramp)
            # chi solves E[exp(-chi s k)] = 1 - drop over the panel: the
            # price-hunters defect first, rooted residents less (P5 §8)
            ps = self.customers["price_sens"].to_numpy()
            _stilde = (np.argsort(np.argsort(ps)) + 1) / n
            _k = np.where(self.customers["persistence"].to_numpy() == "transient",
                          1.0, comp["rooted_factor"])
            _lo, _hi = 0.0, 10.0
            for _ in range(60):
                _mid = (_lo + _hi) / 2
                if float(np.mean(np.exp(-_mid * _stilde * _k))) > 1 - comp["target_visit_drop"]:
                    _lo = _mid
                else:
                    _hi = _mid
            _chi = (_lo + _hi) / 2
            self.comp_mult = np.exp(-_chi * _stilde * _k)
        else:
            self.comp_ramp = np.zeros(self.n_days)
            self.comp_mult = np.ones(n)
        self.guest_mult_t = gm

    def _calibrate_u0(self):
        """Bisect u0 so the mean inside-choice probability at a typical
        mid-shop need (shortfall 60%) hits the capture target (P3 §4)."""
        g = rng_for(K_PHASE1, 99)
        # sample the OPENING panel only: panel-flow newcomers (P5 §3) must
        # not move the bisection, or year one would desync (P5 §2)
        sample_i = g.choice(
            a = self.n0,
            size = min(200, self.n0),
            replace = False,
        )
        prices0 = (1 + self.markup) * self.base_cost

        def capture(u0):
            probs = []
            for i in sample_i:
                for ci, c in enumerate(CATS):
                    idx = self.cat_listed[c]
                    U = (PHASE3["need_alpha"] * 0.6 + self.appeal[idx]
                         + PHASE1["gamma_brand"] * (1 - np.abs(self.customers.brand_affinity.iloc[i]
                                                               - self.brand[idx]))
                         - self.customers.price_sens.iloc[i] * prices0[idx] / self.shelf_median[c])
                    m = max(U.max(), u0)
                    inside = np.exp(U - m).sum()
                    probs.append(inside / (inside + math.exp(u0 - m)))
            return float(np.mean(a = probs))

        lo, hi = -5.0, 8.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if capture(u0 = mid) > PHASE3["capture_target"]:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
