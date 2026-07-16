"""Phase 3 — the play, performed (documents/PHASE3_DETAILS.md).

The daily market loop: visits, pantries, softmax choices, stockouts, the
hidden-demand ledger, guests, refunds, the owner's weekly restock,
promotions, spoilage, the monthly ledger — plus the oracle counterfactual
replay via `oracle = True`.
"""

from __future__ import annotations

import datetime as dt
import math

import numpy as np
import pandas as pd

from collections import defaultdict
from datagen.keys import (
    K_COST,
    K_CUSTDAY,
    K_GUEST,
    K_OWNERWK,
    K_REFUND,
    K_SKUDAY,
    charm,
    rng_for,
    token,
)
from datagen.params import BASKET_SHARE, CATS, PHASE1, PHASE3, PHASE4
from datagen.world import World


def run_year(
    world: World,
    oracle: bool = False,
):
    """The daily loop (P3 §12). `oracle=True` replays the identical scripted
    year with the owner's forecast replaced by true seasonal demand,
    censoring undone and spoilage priced in (P3 §14). Customer-side draws are
    keyed by (customer, day), so both worlds share their randomness (CRN)."""
    w, p3 = world, PHASE3
    p5 = w.p5
    n_sku, n_cust = len(w.skus), len(w.customers)
    n_days = len(w.cal)
    dec = w.milp["decision"]

    inv = dec.q0.to_numpy().astype(dtype = float)
    price = charm(
        p = (1 + w.markup) * w.base_cost,
        ending = w.price_end,
    )    # opening pass-through, charm-priced (gross = net x (1 + VAT) at t0)
    # the owner prices on NET margin (P4 §2): he knows the VAT is not his
    # money, so the smoothed cost trend he tracks is tax-exclusive and the
    # day's rate is re-applied on top of the markup. At constant rates this
    # is identical to marking up the gross invoice; when a rate changes, the
    # new rate reaches his target price immediately and exactly.
    _r0 = np.array(object = [w.vat_rate[w.cat_of[i]][0] for i in range(n_sku)])
    cost_ewma = w.base_cost / (1 + _r0)   # the smoothed NET cost trend
    pantry = np.empty(shape = (n_cust, len(CATS)))
    for i in range(n_cust):
        g = rng_for(K_CUSTDAY, i, 0)
        pantry[i] = g.uniform(
            low = 0,
            high = w.target[i],
        )
    cash = PHASE1["capital"] - w.milp["spend"] \
        + w.locs.rent[w.milp["location"]] \
        + (w.milp["hired"] * PHASE1["hourly_wage"] * (1 + PHASE4["payroll_rate"])
           + PHASE1["hourly_utility"]) * 12 * 30
    # ^ the MILP budgeted month-1 rent/wages(+payroll)/utilities; the ledger
    #   charges them at the monthly close instead, so they are returned here.
    credit = 0.0
    hired = w.hired
    open_hour = w.open_hour
    close_hour = w.close_hour
    clerk_hours = None      # None -> staff are paid for all open hours
    shelf_mult = 1.0
    base_rent = float(w.locs.rent[w.milp["location"]])
    # year-one one-offs, needed early for the January tax settlement (P5 §4)
    setup_oneoffs = float(w.locs.setup_cost[w.milp["location"]]) \
        + PHASE1["listing_fee"] * len(w.listed)
    initial_restock = float((dec.q0.to_numpy() * w.base_cost).sum())
    # Phase 5 finance state (P5 §4): the RE ledger, the January tax
    # settlement, and the one possible expansion
    re_balance = 0.0
    y1_after_tax = 0.0
    pending_tax = 0.0
    year_results = []
    expanded = False
    expansion_t = None
    promo_cover = p3["promo_trigger_cover"]
    _resp = None
    if p5 and p5["response"] is not None and p5["competitor"] is not None:
        # the owner's competitive response is scheduled off the entry script,
        # never off realized revenue, so the no-competitor twin stays clean
        # (P5 §13.3) — no entry, no response
        _resp = p5["response"]
        _resp_cats = set(_resp["cut_cats"])

    def vat_share(
        cat,
        day_ix,
    ):
        """The VAT fraction of a gross amount: r/(1+r) at that day's rate."""
        r = w.vat_rate[cat][day_ix]
        return r / (1 + r)

    # owner forecast state: 4 pseudo-weeks seeded from beliefs (x 7/30)
    L = w.milp["location"]
    bel = {r["category"]: r["believed_demand"]
           for _, r in w.beliefs[w.beliefs.location_id == L].iterrows()}
    sales_hist = {c: [bel[c] * 7 / 30] * p3["ma_weeks"] for c in CATS}
    sku_hist = defaultdict(lambda: [0.0] * p3["ma_weeks"])
    week_sales_c = defaultdict(float)
    week_sales_s = defaultdict(float)
    # oracle extras: uncensored demand accumulators, seeded with the TRUTH
    week_demand_s = defaultdict(float)
    demand_hist = defaultdict(lambda: [0.0] * p3["ma_weeks"])
    true_D = {r["category"]: r["true_demand"]
              for _, r in w.beliefs[w.beliefs.location_id == L].iterrows()}
    cat_demand_hist = {c: [true_D[c] * 7 / 30] * p3["ma_weeks"] for c in CATS}

    pending = defaultdict(list)                    # arrival day -> [(sku, qty, unit_cost)]
    pending_refunds = defaultdict(list)            # return day -> queued refund events

    def schedule_refund(
        rid,
        t0,
        r_lines,
        payment,
        cust_id,
    ):
        """P3 §21: with small probability one line of this receipt comes back
        days later — a quality gripe or a wrong grab. Keyed by receipt id so
        counterfactual replays stay CRN-valid. The item is destroyed, not
        restocked, so the refund moves money only."""
        gr = rng_for(K_REFUND, rid)
        if gr.random() >= p3["refund_receipt_rate"]:
            return
        _j, _q, _up, _fl = r_lines[int(gr.integers(len(r_lines)))]
        _q_ret = 1 if _q <= 1 else int(gr.integers(
            low = 1,
            high = min(2, int(_q)) + 1,
        ))
        _t_r = t0 + int(gr.integers(
            low = 1,
            high = p3["refund_max_lag_days"] + 1,
        ))
        if _t_r > len(w.cal):
            return                     # the year's records close first
        _h_r = int(gr.integers(
            low = 9,
            high = 20,
        ))
        pending_refunds[_t_r].append(
            (rid, _h_r, payment, cust_id, _j, _q_ret, round(float(_up), 2), int(_fl)))
    promo_until = np.zeros(n_sku)
    promo_depth = np.zeros(n_sku)
    flyer_until = 0
    spent_week = np.zeros(n_cust)
    cur_week = 1

    receipts = []
    hidden = []
    proc = []
    promos_log = []
    price_log = []
    invsnap = []
    writeoffs = []
    costsheet = []
    fc_log = []
    guest_log = []
    guest_rev = 0.0
    guest_counter = 0
    for i0 in w.listed:
        price_log.append({
            "uid": w.uid[i0],
            "t": 1,
            "price": round(price[i0], 2),
        })
    month_acc = defaultdict(float)
    receipt_id = 0
    total_spoiled = np.zeros(n_sku)
    purchased = dec.q0.to_numpy().astype(dtype = float).copy()
    sold_total = np.zeros(n_sku)
    hour_wd = np.array(
        object = p3["hour_weights"],
        dtype = float,
    )
    hour_wd /= hour_wd.sum()
    hour_we = np.array(
        object = p3["hour_weights_weekend"],
        dtype = float,
    )
    hour_we /= hour_we.sum()
    guest_share = np.array(object = [BASKET_SHARE[c] for c in CATS])

    # last Sundays (loyalty days) — grouped by calendar month of each year
    _last_sunday = {}
    for d in w.cal.itertuples():
        if d.dow == 6:
            _last_sunday[(d.date.year, d.date.month)] = d.t
    loyalty_days = set(_last_sunday.values())

    stockout_sku_days = 0
    listed_days = 0
    # the prudent owner's tax jar (P4 §2): the profit tax accruing on the
    # year-to-date result is set aside mentally — that money never counts
    # as ordering headroom, even though it only leaves in January
    ytd_result = 0.0
    tax_reserve = 0.0

    for day in w.cal.itertuples():
        t = day.t
        week = day.week
        if week != cur_week:
            spent_week[:] = 0.0
            cur_week = week

        if p5:
            # a newcomer's first morning (P5 §3): a freshly stocked pantry —
            # they moved in with boxes, not with empty cupboards
            for i in np.flatnonzero(w.arrival_t_arr == t):
                g = rng_for(K_CUSTDAY, int(i), 0)
                pantry[i] = g.uniform(
                    low = 0,
                    high = w.target[i],
                )
            # the expansion executes on the first of the month (P5 §4.2)
            if expansion_t == t:
                _exp = p5["finance"]["expansion"]
                cash -= p5["finance"]["expansion_capex"]
                re_balance -= p5["finance"]["expansion_capex"]
                month_acc["capex"] += p5["finance"]["expansion_capex"]
                hired += _exp["hired_extra"]
                clerk_hours = _exp["clerk_hours_per_day"]
                open_hour = _exp["open_hour"]
                close_hour = _exp["close_hour"]
                shelf_mult = _exp["shelf_mult"]
                expanded = True
            # the freezer dies overnight (P5 §7): the frozen aisle and part
            # of the dairy case go in the bin at opening, the repairman bills
            if t == p5["freezer"]["t"]:
                _fz = p5["freezer"]
                for i in w.listed:
                    _frac = _fz["frozen_loss"] if w.cat_of[i] == "Frozen Foods" \
                        else _fz["dairy_loss"] if w.cat_of[i] == "Dairy and Eggs" else 0.0
                    _units = int(inv[i]) if _frac >= 1.0 else int(round(_frac * inv[i]))
                    if _frac > 0 and _units > 0:
                        inv[i] -= _units
                        total_spoiled[i] += _units
                        writeoffs.append({
                            "t": t,
                            "uid": w.uid[i],
                            "units": _units,
                            "reason": "damage",
                        })
                cash -= _fz["repair_cost"]
                month_acc["repairs"] += _fz["repair_cost"]

        # ---- morning: overnight spoilage, deliveries, prices -------------
        for i in w.listed:
            if w.spoil_daily[i] > 0 and inv[i] > 0:
                g = rng_for(K_SKUDAY, int(i), t)
                _lam_eff = min(p3["spoil_daily_cap"],
                               w.spoil_daily[i] * w.spoilf[w.cat_of[i]][t - 1])
                sp = g.binomial(
                    n = int(inv[i]),
                    p = _lam_eff,
                )
                if sp:
                    inv[i] -= sp
                    total_spoiled[i] += sp
                    writeoffs.append({
                        "t": t,
                        "uid": w.uid[i],
                        "units": int(sp),
                    })
        for sku_i, qty, ucost in pending.pop(t, []):
            inv[sku_i] += qty
            purchased[sku_i] += qty
            # the shelf tracks a smoothed cost trend (an EWMA of invoice
            # costs), not each noisy invoice, and only reprices once the
            # drift clears a threshold — menu-cost hysteresis, the way real
            # retailers actually manage price lists
            alpha = p3["cost_ewma_alpha"]
            _r_day = w.vat_rate[w.cat_of[sku_i]][t - 1]
            cost_ewma[sku_i] = alpha * (ucost / (1 + _r_day)) + (1 - alpha) * cost_ewma[sku_i]
            _mk = w.markup[sku_i]
            if _resp is not None and t >= _resp["t"] and w.cat_of[sku_i] in _resp_cats:
                # the price fight-back (P5 §8): thinner margins on the
                # price-visible categories, passed through at each delivery
                _mk = _mk - _resp["markup_cut"]
            candidate = float(charm(
                p = (1 + _mk) * cost_ewma[sku_i] * (1 + _r_day),
                ending = w.price_end[sku_i],
            ))
            if abs(candidate / price[sku_i] - 1) > p3["reprice_threshold"]:
                price[sku_i] = candidate
                price_log.append({
                    "uid": w.uid[sku_i],
                    "t": t,
                    "price": candidate,
                })

        eff_price = price.copy()
        live_promo = promo_until >= t
        eff_price[live_promo] = charm(
            p = price[live_promo] * (1 - promo_depth[live_promo]),
            ending = w.price_end[live_promo],
        )
        if t in loyalty_days:   # storewide % off is taken at the till, not the tag
            eff_price = np.minimum(eff_price, np.round(
                a = price * (1 - p3["loyalty_depth"]),
                decimals = 2,
            ))

        # ---- trading ------------------------------------------------------
        if day.closed and t in pending_refunds:
            # the shop is shut; the would-be returner comes back tomorrow
            pending_refunds[t + 1].extend(pending_refunds.pop(t))
        if not day.closed:
            # morning returners first: a refund is its own till transaction,
            # negative quantity, pointing back at the original receipt
            for _orig, _h_r, _pay_r, _cid_r, _j, _q_ret, _up_r, _fl_r in pending_refunds.pop(t, []):
                receipt_id += 1
                receipts.append({
                    "receipt_id": receipt_id,
                    "t": t,
                    "hour": _h_r,
                    "payment": _pay_r,
                    "customer_id": _cid_r,
                    "uid": w.uid[_j],
                    "qty": -_q_ret,
                    "unit_price": _up_r,
                    "promo": _fl_r,
                    "ref_receipt_id": _orig,
                })
                month_acc["revenue"] -= _q_ret * _up_r
                month_acc["vat_out"] -= _q_ret * _up_r * vat_share(
                    cat = w.cat_of[_j],
                    day_ix = t - 1,
                )
                cash -= _q_ret * _up_r
            lam_t = w.lam[t - 1] * (1 + p3["flyer_lift"] * (flyer_until >= t)) \
                * (1 + p3["loyalty_traffic_lift"] * (t in loyalty_days))
            hour_w = hour_we if day.dow >= 5 else hour_wd
            _act = w.active[t - 1] if p5 else None
            _ramp = w.comp_ramp[t - 1] if p5 else 0.0
            arrivals = []
            for i in range(n_cust):
                if _act is not None and not _act[i]:
                    continue    # not living here (yet, or anymore) — P5 §3
                g = rng_for(K_CUSTDAY, i, t)
                base = (w.customers.adherence.iloc[i] if day.dow == w.customers.primary_day.iloc[i]
                        else w.customers.topup_rate.iloc[i])
                if _ramp > 0.0:
                    # the discounter's pull (P5 §8): the outside option got
                    # better, and more so for the price-sensitive
                    base = base * (1 - (1 - w.comp_mult[i]) * _ramp)
                visit = g.random() < min(1.0, base * lam_t)
                if g.random() < PHASE1["deviation_prob"]:
                    visit = not visit
                if visit:
                    arrivals.append((
                        int(g.choice(
                            a = 24,
                            p = hour_w,
                        )),
                        i,
                        g,
                    ))
            # the passing trade: one-off guests, keyed by day (CRN-safe)
            gg = rng_for(K_GUEST, t)
            _gp = p3["guests"]
            _guest_lam = _gp["base_per_day"] * _gp["dow_factor"][day.dow] * lam_t
            if p5:
                # guests scale with the neighborhood, feel the block, the
                # festival fortnight, and the discounter (P5 §3, §8)
                _guest_lam = _guest_lam * w.guest_mult_t[t - 1]
            _n_guest = gg.poisson(lam = _guest_lam)
            for _ in range(_n_guest):
                arrivals.append((
                    int(gg.choice(
                        a = 24,
                        p = hour_w,
                    )),
                    -1,
                    gg,
                ))
            arrivals.sort(key = lambda a: a[0])

            for hour, i, g in arrivals:
                if i == -1:  # ---- a guest: small basket, no pantry, no profile
                    if hour < open_hour or hour >= close_hour:
                        continue
                    _budget_g = g.lognormal(
                        mean = _gp["visit_budget"][0],
                        sigma = _gp["visit_budget"][1],
                    )
                    _beta_g = g.lognormal(
                        mean = 0,
                        sigma = 0.4,
                    )
                    _b_g = g.beta(
                        a = 2,
                        b = 2,
                    )
                    _cats_g = set(g.choice(
                        a = len(CATS),
                        size = 1 + g.poisson(lam = _gp["extra_cats_poisson"]),
                        p = guest_share,
                    ))
                    _lines_g = []
                    for _ci in _cats_g:
                        _c = CATS[_ci]
                        _idx = [j for j in w.cat_listed[_c] if inv[j] >= 1]
                        if not _idx:
                            continue
                        _arr = np.array(object = _idx)
                        _tilt = np.array(object = [math.log(w.psi[w.ptype[j]][t - 1])
                                                   if w.ptype[j] in w.psi else 0.0
                                                   for j in _idx])
                        _U = (p3["need_alpha"] * _gp["need_theta"]
                              + math.log(w.M[_c][t - 1]) + w.appeal[_arr] + _tilt
                              + PHASE1["gamma_brand"] * (1 - np.abs(_b_g - w.brand[_arr]))
                              - _beta_g * eff_price[_arr] / w.shelf_median[_c])
                        _m = max(_U.max(), w.u0)
                        _e = np.exp(np.append(
                            arr = _U,
                            values = w.u0,
                        ) - _m)
                        _pick = int(g.choice(
                            a = len(_e),
                            p = _e / _e.sum(),
                        ))
                        if _pick == len(_idx):
                            continue        # outside option: window-shopped
                        _j = _idx[_pick]
                        _q = 1 + (g.random() < _gp["qty2_prob"])
                        _q = min(_q, int(inv[_j]), int(_budget_g // eff_price[_j]))
                        if _q < 1:
                            continue
                        inv[_j] -= _q
                        sold_total[_j] += _q
                        _budget_g -= _q * eff_price[_j]
                        week_sales_s[_j] += _q
                        week_sales_c[_c] += _q
                        week_demand_s[_j] += _q
                        _lines_g.append((
                            _j,
                            _q,
                            eff_price[_j],
                            bool(live_promo[_j] or t in loyalty_days),
                        ))
                    if _lines_g:
                        _by_card = g.random() < (PHASE1["p_card"]["card"]
                                                 if g.random() < PHASE1["card_share"]
                                                 else PHASE1["p_card"]["cash"])
                        guest_counter += 1
                        _tok = token(
                            kind = 1,
                            n = guest_counter,
                        ) if _by_card else ""
                        receipt_id += 1
                        _val = 0.0
                        for _j, _q, _up, _fl in _lines_g:
                            receipts.append({
                                "receipt_id": receipt_id,
                                "t": t,
                                "hour": hour,
                                "payment": "card" if _by_card else "cash",
                                "customer_id": _tok,
                                "uid": w.uid[_j],
                                "qty": _q,
                                "unit_price": round(_up, 2),
                                "promo": int(_fl),
                            })
                            month_acc["revenue"] += _q * _up
                            month_acc["vat_out"] += _q * _up * vat_share(
                                cat = w.cat_of[_j],
                                day_ix = t - 1,
                            )
                            cash += _q * _up
                            _val += _q * _up
                        guest_rev += _val
                        schedule_refund(
                            rid = receipt_id,
                            t0 = t,
                            r_lines = _lines_g,
                            payment = "card" if _by_card else "cash",
                            cust_id = _tok,
                        )
                        guest_log.append({
                            "t": t,
                            "token": _tok or None,
                            "payment": "card" if _by_card else "cash",
                            "value": round(_val, 2),
                        })
                    continue

                Mrow = np.array(object = [w.M[c][t - 1] for c in CATS])
                shortfall = np.maximum(0.0, w.target[i] - pantry[i])
                ratio = np.divide(shortfall, w.target[i],
                                  out = np.zeros_like(shortfall),
                                  where = w.target[i] > 0)
                primary = day.dow == w.customers.primary_day.iloc[i]
                if hour < open_hour or hour >= close_hour:
                    for ci in np.argsort(a = -ratio):
                        if ratio[ci] > (1 - p3["list_threshold"] if primary else 1 - 0.2):
                            hidden.append({
                                "t": t,
                                "hour": hour,
                                "customer_id": i,
                                "category": CATS[ci],
                                "uid": "",
                                "qty": math.ceil(shortfall[ci]),
                                "cause": "closed",
                            })
                    continue

                if primary:
                    listed_c = [ci for ci in range(len(CATS))
                                if pantry[i][ci] < p3["list_threshold"] * w.target[i][ci]]
                else:
                    listed_c = [ci for ci in range(len(CATS))
                                if pantry[i][ci] < p3["topup_threshold_days"] * w.r_ic[i][ci]]
                order = sorted(listed_c, key = lambda ci: -ratio[ci])
                budget_left = w.budgets[i, week - 1] - spent_week[i]
                lines = []
                broke = False

                for ci in order:
                    c = CATS[ci]
                    if broke:
                        hidden.append({
                            "t": t,
                            "hour": hour,
                            "customer_id": i,
                            "category": c,
                            "uid": "",
                            "qty": math.ceil(shortfall[ci]),
                            "cause": "budget",
                        })
                        continue
                    # people rarely haul the whole shortfall home in one trip,
                    # and how much they *can* carry varies trip to trip
                    _carry = g.uniform(
                        low = p3["carry_frac"][0],
                        high = p3["carry_frac"][1],
                    )
                    _cap = int(g.integers(
                        low = p3["carry_cap"][0],
                        high = p3["carry_cap"][1],
                    ))
                    need_units = min(math.ceil(shortfall[ci] * _carry), _cap)
                    if not primary:
                        need_units = min(need_units, math.ceil(p3["topup_buy_days"] * w.r_ic[i][ci]))
                    if need_units <= 0:
                        continue
                    theta = p3["need_alpha"] * ratio[ci] + math.log(Mrow[ci])
                    exclude = set()
                    remaining = need_units
                    while remaining > 0:
                        idx = [j for j in w.cat_listed[c] if j not in exclude and inv[j] >= 1]
                        if idx:
                            arr = np.array(object = idx)
                            tilt = np.array(object = [math.log(w.psi[w.ptype[j]][t - 1])
                                                      if w.ptype[j] in w.psi else 0.0
                                                      for j in idx])
                            U = (theta + w.appeal[arr]
                                 + PHASE1["gamma_brand"] * (1 - np.abs(
                                     w.customers.brand_affinity.iloc[i] - w.brand[arr]))
                                 + tilt
                                 - w.customers.price_sens.iloc[i] * eff_price[arr] / w.shelf_median[c])
                            m = max(U.max(), w.u0)
                            e = np.exp(np.append(
                                arr = U,
                                values = w.u0,
                            ) - m)
                            pick = int(g.choice(
                                a = len(e),
                                p = e / e.sum(),
                            ))
                        else:
                            pick = -1          # only the outside option remains
                        if pick == -1 or (idx and pick == len(idx)):
                            # outside option: they buy elsewhere — pantry refills,
                            # budget is spent there too (P3 §4 stability rule)
                            spend = min(remaining * w.shelf_median[c], budget_left)
                            units = int(spend // w.shelf_median[c])
                            if units > 0:
                                hidden.append({
                                    "t": t,
                                    "hour": hour,
                                    "customer_id": i,
                                    "category": c,
                                    "uid": "",
                                    "qty": units,
                                    "cause": "outside",
                                })
                                pantry[i][ci] += units
                                budget_left -= units * w.shelf_median[c]
                                spent_week[i] += units * w.shelf_median[c]
                            remaining = 0
                            break
                        j = idx[pick]
                        afford = int(budget_left // eff_price[j])
                        take = min(remaining, int(inv[j]), afford)
                        if afford == 0:
                            broke = True
                            hidden.append({
                                "t": t,
                                "hour": hour,
                                "customer_id": i,
                                "category": c,
                                "uid": w.uid[j],
                                "qty": remaining,
                                "cause": "budget",
                            })
                            remaining = 0
                            break
                        if take > 0:
                            inv[j] -= take
                            sold_total[j] += take
                            pantry[i][ci] += take
                            val = take * eff_price[j]
                            budget_left -= val
                            spent_week[i] += val
                            week_sales_s[j] += take
                            week_sales_c[c] += take
                            week_demand_s[j] += take
                            lines.append((
                                j,
                                take,
                                eff_price[j],
                                bool(live_promo[j] or t in loyalty_days),
                            ))
                            remaining -= take
                        if remaining > 0:      # stockout on the remainder
                            hidden.append({
                                "t": t,
                                "hour": hour,
                                "customer_id": i,
                                "category": c,
                                "uid": w.uid[j],
                                "qty": remaining,
                                "cause": "stockout",
                            })
                            week_demand_s[j] += remaining
                            exclude.add(j)

                # impulse item (P3 §4)
                if lines and g.random() < p3["impulse_prob"]:
                    j = int(g.choice(a = w.listed))
                    if inv[j] >= 1 and budget_left >= eff_price[j]:
                        inv[j] -= 1
                        sold_total[j] += 1
                        budget_left -= eff_price[j]
                        spent_week[i] += eff_price[j]
                        week_sales_s[j] += 1
                        week_sales_c[w.cat_of[j]] += 1
                        pantry[i][CATS.index(w.cat_of[j])] += 1
                        lines.append((
                            j,
                            1,
                            eff_price[j],
                            bool(live_promo[j] or t in loyalty_days),
                        ))

                if lines:
                    ptype = w.customers.card_type.iloc[i]
                    by_card = g.random() < (PHASE1["p_card"]["card"] if ptype
                                            else PHASE1["p_card"]["cash"])
                    receipt_id += 1
                    for j, qty, up, fl in lines:
                        receipts.append({
                            "receipt_id": receipt_id,
                            "t": t,
                            "hour": hour,
                            "payment": "card" if by_card else "cash",
                            "customer_id": token(
                                kind = 0,
                                n = i,
                            ) if by_card else "",
                            "uid": w.uid[j],
                            "qty": qty,
                            "unit_price": round(up, 2),
                            "promo": int(fl),
                        })
                        month_acc["revenue"] += qty * up
                        month_acc["vat_out"] += qty * up * vat_share(
                            cat = w.cat_of[j],
                            day_ix = t - 1,
                        )
                        cash += qty * up            # revenue reaches the till daily
                    schedule_refund(
                        rid = receipt_id,
                        t0 = t,
                        r_lines = lines,
                        payment = "card" if by_card else "cash",
                        cust_id = token(
                            kind = 0,
                            n = i,
                        ) if by_card else "",
                    )

        # ---- evening: pantry drain, snapshot ------------------------------
        Mrow = np.array(object = [w.M[c][t - 1] for c in CATS])
        pantry = np.maximum(0.0, pantry - w.r_ic * Mrow[None, :])
        for i in w.listed:
            invsnap.append({
                "t": t,
                "uid": w.uid[i],
                "on_hand": int(inv[i]),
            })
            listed_days += 1
            if inv[i] < 1:
                stockout_sku_days += 1

        # ---- weekly owner ops (Monday) ------------------------------------
        if day.dow == p3["restock_weekday"]:
            for c in CATS:
                sales_hist[c].append(week_sales_c.get(c, 0.0))
                cat_demand_hist[c].append(
                    sum(week_demand_s.get(j, 0.0) for j in w.cat_listed[c]))
            for j in w.listed:
                sku_hist[j].append(week_sales_s.get(j, 0.0))
                demand_hist[j].append(week_demand_s.get(j, 0.0))
            week_sales_c.clear()
            week_sales_s.clear()
            week_demand_s.clear()

            gw = rng_for(K_OWNERWK, week)
            cover_mult = (7 + p3["lead_days"]) / 7 + PHASE1["eta"] * 30 / 7
            order = []
            Dw_total = 0.0
            for c in CATS:
                if oracle:
                    # censoring undone (uncensored demand MA) + true seasonal
                    # anticipation via the known modifier path (P3 §14)
                    M = w.M[c]
                    m_next = float(M[t - 1: min(t + 8, n_days)].mean())
                    m_past = float(M[max(0, t - 29): t - 1].mean()) if t > 2 else 1.0
                    Dw = float(np.mean(a = cat_demand_hist[c][-p3["ma_weeks"]:])) * m_next / m_past
                    hist = demand_hist
                else:
                    Dw = float(np.mean(a = sales_hist[c][-p3["ma_weeks"]:]))
                    hist = sku_hist
                fc_log.append({
                    "week": week,
                    "category": c,
                    "forecast_weekly": Dw,
                    "oracle": int(oracle),
                })
                Dw_total += Dw
                idx = w.cat_listed[c]
                recent = np.array(object = [np.mean(a = hist[j][-p3["ma_weeks"]:]) for j in idx])
                share = (recent + p3["alloc_smoothing"]) \
                    / (recent.sum() + p3["alloc_smoothing"] * len(idx))
                # spoilage priced in: the oracle shrinks the safety buffer in
                # proportion to how fast the category dies — balancing waste
                # against stockouts instead of applying one flat cover
                if oracle:
                    lam_w = PHASE3["spoilage_weekly"].get(c, 0.0)
                    cm = (7 + p3["lead_days"]) / 7 \
                        + PHASE1["eta"] * 30 / 7 * max(0.0, 1 - 4 * lam_w)
                else:
                    cm = cover_mult
                # while the freezer is being repaired (P5 §7) only half the
                # frozen shelf exists — the owner orders to what he can store
                _fz_scale = 1.0
                if p5 and c == "Frozen Foods":
                    _fz = p5["freezer"]
                    if _fz["t"] <= t < _fz["t"] + _fz["cap_days"]:
                        _fz_scale = _fz["frozen_cap_mult"]
                for j, sh in zip(idx, share):
                    tgt = cm * Dw * sh
                    need = tgt - inv[j] - sum(qq for dd, lst in pending.items()
                                              for jj, qq, _ in lst if jj == j)
                    need = need * _fz_scale
                    if need >= 1:
                        order.append((j, int(round(need))))
            # invoice costs: category path times idiosyncratic per-line noise —
            # real supplier invoices never move in perfect unison
            ucost = {
                j: w.base_cost[j]
                * w.cost_mult[w.cat_of[j]][min(t + p3["lead_days"], n_days) - 1]
                * math.exp(rng_for(K_COST, int(j), t).normal(
                    loc = 0,
                    scale = 0.025,
                ))
                for j, _ in order
            }
            bill = sum(q_ * ucost[j] for j, q_ in order)
            # cash + credit line room, minus the tax jar
            headroom = cash + 20_000 - credit - tax_reserve
            scale = min(1.0, headroom / bill) if bill > 0 else 1.0
            # shelf capacity cap (P3 §8): physical stock peaks just after the
            # Wednesday delivery — project on-hand then, using his own forecast
            shelf_cap = float(w.locs.shelf_capacity_units[w.milp["location"]]) * shelf_mult
            at_delivery = max(0.0, float(inv[w.listed].sum())
                              - p3["lead_days"] * Dw_total / 7) \
                + sum(qq for lst in pending.values() for _, qq, _ in lst)
            order_total = sum(q_ for _, q_ in order)
            if order_total > 0:
                scale = min(scale, max(0.0, shelf_cap - at_delivery) / order_total)
            for j, q_ in order:
                q2 = int(q_ * scale)
                if q2 >= 1:
                    pending[t + p3["lead_days"]].append((j, q2, ucost[j]))
                    proc.append({
                        "order_t": t,
                        "delivery_t": t + p3["lead_days"],
                        "uid": w.uid[j],
                        "qty": q2,
                        "unit_cost": round(ucost[j], 4),
                    })
                    cash -= q2 * ucost[j]
                    month_acc["procurement"] += q2 * ucost[j]
                    month_acc["vat_in"] += q2 * ucost[j] * vat_share(
                        cat = w.cat_of[j],
                        day_ix = min(t + p3["lead_days"], n_days) - 1,
                    )

            # markdown trigger (P3 §9); the P5 §8 response loosens the cover
            if _resp is not None and t >= _resp["t"]:
                promo_cover = _resp["promo_trigger_cover"]
            for c in CATS:
                Dw = float(np.mean(a = sales_hist[c][-p3["ma_weeks"]:]))
                on = sum(inv[j] for j in w.cat_listed[c])
                if Dw > 0 and on / Dw > promo_cover:
                    idx = sorted(w.cat_listed[c],
                                 key = lambda j: np.mean(a = sku_hist[j][-p3["ma_weeks"]:]))
                    slow = idx[: max(1, len(idx) // 3)]
                    depths, probs = p3["promo_depths"]
                    d = float(gw.choice(
                        a = depths,
                        p = probs,
                    ))
                    for j in slow:
                        promo_until[j] = t + p3["promo_days"]
                        promo_depth[j] = d
                    flyer_until = max(flyer_until, t + p3["promo_days"])
                    promos_log.append({
                        "start_t": t,
                        "end_t": t + p3["promo_days"],
                        "type": "markdown",
                        "category": c,
                        "depth": d,
                        "n_skus": len(slow),
                        "flyer_cost": p3["flyer_cost_week"] * 2,
                    })
                    cash -= p3["flyer_cost_week"] * 2
                    month_acc["flyers"] += p3["flyer_cost_week"] * 2

        # ---- monthly close --------------------------------------------------
        nxt = day.date + dt.timedelta(1)
        if nxt.month != day.date.month or t == n_days:
            days_in_m = day.date.day
            rate = w.rates[w.rates.t == t].iloc[0]
            open_hours = close_hour - open_hour
            # the P5 §4.2 hire works a fixed part-time shift; every other
            # staffing arrangement (P4 policy arms) covers the open hours
            _paid_h = clerk_hours if clerk_hours is not None else open_hours
            wages = hired * rate.wage_rate * _paid_h * days_in_m
            payroll = wages * PHASE4["payroll_rate"]
            utils = rate.utility_rate * open_hours * days_in_m
            storage = float(inv[w.listed].sum()) * rate.storage_rate
            rent = base_rent
            if p5 and t >= p5["contracts"]["rent_mult_from_t"][0]:
                # the two-year contract renews (P5 §5): the landlord watched
                # the shop succeed and reprices to market
                rent = base_rent * p5["contracts"]["rent_mult_from_t"][1]
            # VAT collected at the till, minus VAT paid on invoices, leaves
            # the till at the monthly close (P4 §2) — real cash, like rent
            vat_due = month_acc["vat_out"] - month_acc["vat_in"]
            cash -= wages + payroll + utils + storage + rent + vat_due
            interest = credit * PHASE3["credit_apr"] / 12
            cash -= interest
            month_result = (month_acc["revenue"] - month_acc["procurement"]
                            - rent - wages - payroll - utils - storage
                            - month_acc["flyers"] - vat_due - interest
                            - month_acc["repairs"])
            draw = 0.0
            profit_tax_paid = 0.0
            if p5:
                _fin = p5["finance"]
                _m_global = (day.date.year - 2025) * 12 + day.date.month
                if _m_global == _fin["formalize_month"]:
                    # the books formalize (P5 §4.1): the first year's surplus
                    # is declared the opening retained-earnings balance
                    re_balance = y1_after_tax
                if _m_global >= _fin["formalize_month"]:
                    # the owner pays himself out of good months only; the
                    # retained share stays in the till, earmarked for growth
                    _pi = month_result * (1 - PHASE4["profit_tax_rate"])
                    if _pi > 0:
                        draw = (1 - _fin["retain_ratio"]) * _pi
                        re_balance += _fin["retain_ratio"] * _pi
                        cash -= draw
                if day.date.month == 1 and pending_tax > 0:
                    # last year's profit tax leaves the till in January —
                    # cash-basis now, not the P4 accrual idealization (P5 §4.1)
                    profit_tax_paid = pending_tax
                    cash -= pending_tax
                    pending_tax = 0.0
            if cash < 0:                        # draw on the credit line
                credit += -cash
                cash = 0.0
            elif credit > 0:                    # repay when possible
                pay = min(credit, cash)
                credit -= pay
                cash -= pay
            ytd_result += month_result
            if p5 and day.date.month == 12:
                # the year closes: settle the taxable result (year one also
                # absorbs the opening one-offs), accrue the January bill
                _oneoffs = setup_oneoffs + initial_restock if day.date.year == 2025 else 0.0
                _taxable = ytd_result - _oneoffs
                _tax = PHASE4["profit_tax_rate"] * max(0.0, _taxable)
                year_results.append({
                    "year": day.date.year,
                    "profit_before_tax": _taxable,
                    "profit_tax": _tax,
                    "profit_after_tax": _taxable - _tax,
                })
                if day.date.year == 2025:
                    y1_after_tax = max(0.0, _taxable - _tax)
                pending_tax = _tax
                ytd_result = 0.0
            tax_reserve = PHASE4["profit_tax_rate"] * max(0.0, ytd_result) + pending_tax
            if (p5 and not expanded and expansion_t is None
                    and p5["finance"]["expansion_threshold"] is not None
                    and re_balance >= p5["finance"]["expansion_threshold"]
                    and cash - tax_reserve >= p5["finance"]["expansion_capex"]):
                # enough capital, honestly counted — the expansion goes ahead
                # on the first of next month (P5 §4.2)
                expansion_t = t + 1
            row = {
                "month": day.date.month,
                "revenue": month_acc["revenue"],
                "procurement": month_acc["procurement"],
                "rent": rent,
                "wages": wages,
                "payroll_tax": payroll,
                "utilities": utils,
                "storage": storage,
                "flyers": month_acc["flyers"],
                "vat": vat_due,
                "credit_interest": interest,
                "credit_balance": credit,
                "cash": cash,
            }
            if p5:
                # the capital-flow columns (P5 §4.1); the one-year baseline
                # keeps its published schema untouched
                row["year"] = day.date.year
                row["repairs"] = month_acc["repairs"]
                row["owner_draw"] = draw
                row["retained_earnings"] = re_balance
                row["capex"] = month_acc["capex"]
                row["profit_tax_paid"] = profit_tax_paid
            costsheet.append(row)
            month_acc = defaultdict(float)

    cs = pd.DataFrame(costsheet)
    _cost_cols = [
        "procurement",
        "rent",
        "wages",
        "payroll_tax",
        "utilities",
        "storage",
        "flyers",
        "vat",
        "credit_interest",
    ]
    if p5:
        _cost_cols.append("repairs")
    realized = float(cs.revenue.sum() - cs[_cost_cols].sum().sum()
                     - w.locs.setup_cost[w.milp["location"]]
                     - PHASE1["listing_fee"] * len(w.listed)
                     - initial_restock)
    # profit tax (P4 §2): accrued on the positive result at the year's close;
    # under Phase 5 each year settles separately and January pays it in cash
    if p5:
        profit_tax = float(sum(y["profit_tax"] for y in year_results))
    else:
        profit_tax = max(0.0, realized) * PHASE4["profit_tax_rate"]
    return {
        "profit_tax": profit_tax,
        "realized_after_tax": realized - profit_tax,
        "year_results": year_results,
        "receipts": pd.DataFrame(receipts),
        "hidden": pd.DataFrame(hidden),
        "procurement": pd.DataFrame(proc),
        "promotions": pd.DataFrame(promos_log),
        "price_history": pd.DataFrame(price_log),
        "inventory": pd.DataFrame(invsnap),
        "write_offs": pd.DataFrame(writeoffs),
        "cost_sheet": cs,
        "forecasts": pd.DataFrame(fc_log),
        "guests": pd.DataFrame(guest_log),
        "guest_rev": guest_rev,
        "realized_profit": realized,
        "conservation": {
            "purchased": purchased,
            "sold": sold_total,
            "spoiled": total_spoiled,
            "ending": inv,
        },
        "stockout_rate": stockout_sku_days / max(1, listed_days),
    }
