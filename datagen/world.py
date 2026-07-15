"""The World — everything the daily loop needs, precomputed as arrays.

Assembles Phase 1 (the world at t = 0) and Phase 2 (the script of the year)
and calibrates the outside option so realized capture hits its target.
"""

from __future__ import annotations

import math
import time

import numpy as np

from datagen.keys import K_PHASE1, K_PHASE2, rng_for
from datagen.params import CATS, MARKUP, PHASE1, PHASE3, PHASE4, PRICE_ENDINGS
from datagen.scenarios import vat_base_rates
from datagen.phase1 import (
    demand_and_beliefs,
    gen_customers,
    gen_locations,
    load_skus,
    solve_milp,
)
from datagen.phase2 import (
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
        print(f"  phase 1: location {L} (Q={self.locs.quality[L]:.2f}), "
              f"{int(self.milp['decision'].listed.sum())} SKUs, "
              f"{len(self.customers)} customers, believed profit "
              f"{self.milp['believed_profit']:,.0f}  [{time.time()-t0:.1f}s]")

        self.cal = gen_calendar()
        self.wx = gen_weather(
            rng = rng_for(K_PHASE2, 0),
            cal = self.cal,
        )
        # scenario weather edits are script overwrites BEFORE the paths are
        # built, so demand modifiers and spoilage factors feel the storm too
        for _we in self.scenario.get("weather_edit", []):
            _sl = self.wx.index[(self.wx["t"] >= _we["t_from"]) & (self.wx["t"] <= _we["t_to"])]
            self.wx.loc[_sl, "temp_C"] = self.wx.loc[_sl, "temp_C"] + _we["temp_delta"]
            self.wx.loc[_sl, "anomaly"] = self.wx.loc[_sl, "anomaly"] + _we["temp_delta"]
            self.wx.loc[_sl, "z"] = self.wx.loc[_sl, "anomaly"] / 2.8
            self.wx.loc[_sl, "rain_mm"] = _we["rain_mm"]
            self.wx.loc[_sl, "wet"] = _we["wet"]
        self.events = gen_events(rng = rng_for(K_PHASE2, 1))
        for _ev in self.scenario.get("events_add", []):
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
                rng = rng_for(K_PHASE2, 2),
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
        self.u0 = self._calibrate_u0()
        print(f"  calibrated outside option u0 = {self.u0:.2f}")

    def _calibrate_u0(self):
        """Bisect u0 so the mean inside-choice probability at a typical
        mid-shop need (shortfall 60%) hits the capture target (P3 §4)."""
        g = rng_for(K_PHASE1, 99)
        sample_i = g.choice(
            a = len(self.customers),
            size = min(200, len(self.customers)),
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
