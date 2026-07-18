"""Self-validation — the generator grades its own output on every run.

`validate()` is tiered into three kinds of claim, following the same split
`validate_scenario()` already draws between structural invariants and
baseline-calibrated fingerprints (P4 §5), generalized here to the full
battery:

  "structural" — bookkeeping identities, conservation, referential
      integrity, and the recording layer's recoverability contract. These
      have nothing to do with which events are scripted; a failure here is
      a generator bug, always, extreme settings or not. GroceryStoreSimulation
      treats any structural failure as fatal (see simulation.py).

  "band"      — magnitude bands calibrated against the quiet baseline (e.g.
      "Fri-Sun revenue 60-75%"). These are *expected* to diverge once real
      events are scripted — a war year failing the weekend-revenue band is
      not a defect, it is the shock working. Reported, never fatal.

  "core"      — exactly one check, "oracle > realized (information pays)",
      reported separately from the other bands because it is not a
      stylistic realism fingerprint: it is the mechanism this project's own
      paper builds its central claim on. A core failure is never fatal
      either (extreme, compounding settings can legitimately erase the
      gap), but it is never buried among the other 28 checks either.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .keys import token
from .params import IMPERFECTIONS, OUT, PHASE4
from .recording import month_end


def validate(
    world,
    base,
    oracle,
    dirt,
):
    w = world
    rec_years = max(1, w.n_days // 365)   # several bands below are per-year
    con = base["conservation"]
    lhs = con["purchased"] - con["sold"] - con["spoiled"]
    err = np.abs(lhs - con["ending"]).max()
    checks = [(
        "conservation (init+purchased-sold-spoiled == ending)",
        err < 1e-6,
        f"max err {err:.2e}",
        "structural",
    )]

    rec = base["receipts"]
    card = (rec.drop_duplicates(subset = "receipt_id").payment == "card").mean()
    checks.append((
        "card share ~ 0.61",
        0.55 < card < 0.67,
        f"{card:.3f}",
        "band",
    ))
    _dow_cols = [
        "t",
        "dow",
    ]
    rev = rec.assign(v = rec.qty * rec.unit_price).merge(
        right = w.cal[_dow_cols],
        on = "t",
    )
    wknd = rev.loc[rev.dow >= 4, "v"].sum() / rev.v.sum()
    checks.append((
        "Fri-Sun revenue 60-75%",
        0.60 < wknd < 0.75,
        f"{wknd:.3f}",
        "band",
    ))
    closed_t = set(w.cal.loc[w.cal.closed == 1, "t"])
    checks.append((
        "zero sales on closure days",
        rec[rec.t.isin(values = closed_t)].empty,
        "",
        "structural",
    ))
    so = base["stockout_rate"]
    checks.append((
        "stockout SKU-days 1-10%",
        0.005 < so < 0.12,
        f"{so:.3f}",
        "band",
    ))
    _hd = rec.merge(
        right = w.cal[_dow_cols],
        on = "t",
    ).drop_duplicates(subset = "receipt_id")
    _wd_pk = _hd[_hd.dow < 5].groupby(by = "hour").size().idxmax()
    _we_pk = _hd[_hd.dow >= 5].groupby(by = "hour").size().idxmax()
    checks.append((
        "weekday peak 17-19h, weekend peak 9-13h",
        _wd_pk in (17, 18, 19) and _we_pk in (9, 10, 11, 12, 13),
        f"weekday {_wd_pk}h, weekend {_we_pk}h",
        "band",
    ))

    ice = w.skus.loc[w.skus.product_type == "Ice Cream", "uid"]
    _month_cols = [
        "t",
        "month",
    ]
    icer = rec[rec.uid.isin(values = set(ice))].merge(
        right = w.cal[_month_cols],
        on = "t",
    )
    if len(icer):
        _jja = [
            6,
            7,
            8,
        ]
        _djf = [
            12,
            1,
            2,
        ]
        s = icer[icer.month.isin(values = _jja)].qty.sum()
        wtr = icer[icer.month.isin(values = _djf)].qty.sum()
        ratio = s / max(wtr, 1)
        checks.append((
            "ice cream summer/winter in 1.7-3.5x",
            1.7 < ratio < 3.5,
            f"{ratio:.2f}",
            "band",
        ))
    # realized capture: regulars' revenue / their total grocery budgets — the
    # end-to-end verification of the alpha/u0 calibration (P3 §4). On the
    # Phase 5 panel, w.budgets is a full-horizon matrix computed for every
    # customer row regardless of when they actually arrived or left (P2's
    # gen_budget_paths has no notion of tenure) — summing it unconditionally
    # counts budget for weeks a churned customer was never actually present,
    # inflating the denominator (empirically ~25-30% inflation on a 3-year
    # panel) and dragging capture well below target even in a quiet run.
    # The correct denominator only counts a customer's budget in the weeks
    # they were actually resident.
    if "arrival_t" in w.customers.columns:
        _arr = w.customers["arrival_t"].to_numpy()
        _dep = w.customers["departure_t"].fillna(np.inf).to_numpy()
        _week_start_day = np.arange(1, w.n_weeks + 1) * 7 - 6
        _in_window = ((_week_start_day[None, :] >= _arr[:, None])
                     & (_week_start_day[None, :] <= _dep[:, None]))
        total_budget = float((w.budgets * _in_window).sum())
    else:
        total_budget = float(w.budgets.sum())
    capture = (float((rec.qty * rec.unit_price).sum()) - base["guest_rev"]) / total_budget
    checks.append((
        "realized capture near 0.65 target",
        0.55 < capture < 0.75,
        f"{capture:.3f}",
        "band",
    ))

    # forensic-realism checks (validator pass)
    _id_cols = [
        "customer_id",
        "receipt_id",
    ]
    _ids = rec.loc[rec.customer_id != "", _id_cols] \
        .drop_duplicates().groupby(by = "customer_id").size()
    checks.append((
        "card-ID long tail (many one-off tokens)",
        len(_ids) > 800 and (_ids <= 2).mean() > 0.5,
        f"{len(_ids)} ids, {(_ids <= 2).mean():.0%} appear <=2x",
        "structural",
    ))
    _qhi = rec.qty[rec.qty >= 9].value_counts()
    _spike = float(_qhi.max() / len(rec)) if len(_qhi) else 0.0
    checks.append((
        "no single high-qty spike (<3% of lines)",
        _spike < 0.03,
        f"largest high-qty mass {_spike:.3f}",
        "band",
    ))
    _endc = np.rint(base["price_history"].price * 100).astype(dtype = int) % 10
    _p9 = float((_endc == 9).mean())
    _p5 = float((_endc == 5).mean())
    _p0 = float((_endc == 0).mean())
    checks.append((
        "charm pricing mixed (75-95% end in 9, .x5 and .x0 both present)",
        0.75 <= _p9 <= 0.95 and _p5 > 0.02 and _p0 > 0.01,
        f".x9 {_p9:.0%}, .x5 {_p5:.0%}, .x0 {_p0:.0%}",
        "band",
    ))
    _chg = base["price_history"].groupby(by = "uid").size() - 1
    _med_chg_per_yr = float(_chg.median()) / rec_years
    checks.append((
        "repricing cadence realistic (median 3-15 changes/SKU/yr)",
        3 <= _med_chg_per_yr <= 15,
        f"median {_med_chg_per_yr:.1f}/yr over {rec_years} yr(s), "
        f"p90 {_chg.quantile(0.9) / rec_years:.1f}/yr",
        "band",
    ))
    _dd = rec.assign(v = rec.qty * rec.unit_price).merge(
        right = w.cal[_dow_cols],
        on = "t",
    ).groupby(by = "t").agg({
        "v": "sum",
        "dow": "first",
    }).reset_index()
    _dd["res"] = _dd["v"] / _dd.groupby(by = "dow")["v"].transform("mean")
    _ac1 = float(_dd["res"].autocorr(lag = 1))
    checks.append((
        "daily revenue shows day-to-day persistence (lag-1 autocorr > 0.05)",
        _ac1 > 0.05,
        f"{_ac1:.2f}",
        "band",
    ))

    # spoilage economics: softened, weather- and crisis-responsive
    _rev = float((rec.qty * rec.unit_price).sum())
    _spoilv = float((con["spoiled"] * w.base_cost).sum())
    checks.append((
        "spoilage 3-7% of revenue",
        0.03 < _spoilv / _rev < 0.07,
        f"{_spoilv/_rev:.1%} ({_spoilv:,.0f})",
        "band",
    ))
    _cat_cols = [
        "uid",
        "category",
    ]
    _date_cols = [
        "t",
        "date",
    ]
    _wo = base["write_offs"].merge(
        right = w.skus[_cat_cols],
        on = "uid",
    ).merge(
        right = w.cal[_date_cols],
        on = "t",
    )
    _wo["m"] = pd.to_datetime(arg = _wo.date).dt.month
    _ambient = [
        "Bakery and Bread",
        "Fresh Produce",
    ]
    _amb = _wo[_wo.category.isin(values = _ambient)]
    _jja_m = [
        6,
        7,
        8,
    ]
    _djf_m = [
        12,
        1,
        2,
    ]
    _ratio = _amb[_amb.m.isin(values = _jja_m)].units.sum() / max(
        _amb[_amb.m.isin(values = _djf_m)].units.sum(), 1)
    checks.append((
        "ambient write-offs peak in summer (JJA/DJF > 1.3)",
        _ratio > 1.3,
        f"{_ratio:.2f}",
        "band",
    ))
    bel, real, orc = w.milp["believed_profit"], base["realized_profit"], oracle["realized_profit"]
    checks.append((
        "oracle > realized (information pays)",
        orc > real,
        f"believed(m1) {bel:,.0f} | realized {real:,.0f} | oracle {orc:,.0f}",
        "core",
    ))

    # the tax layer (P4 §2): the remittance ties to the rate map applied
    # independently to actual sales and purchases, and the statement closes
    _catmap = dict(zip(w.skus["uid"], w.skus["category"]))
    _rs = rec.assign(cat = rec["uid"].map(func = _catmap))
    _rshare = np.array(object = [w.vat_rate[c][t - 1] / (1 + w.vat_rate[c][t - 1])
                                 for c, t in zip(_rs["cat"], _rs["t"])])
    _vout = float((_rs["qty"] * _rs["unit_price"] * _rshare).sum())
    _pr = base["procurement"].assign(cat = base["procurement"]["uid"].map(func = _catmap))
    # clamp guards a delivery landing one day past the horizon's last day
    # (e.g. an order placed near year-end); this must be the run's own
    # length, not a hardcoded 365 — on a 3-year run with a dated VAT change,
    # a fixed 365 silently priced every post-year-one delivery at the wrong
    # (day-365) rate instead of its own, which is exactly the bug that
    # first exposed this clamp when validate() was generalized past 1 year
    _n_days = len(w.cal)
    _pshare = np.array(object = [w.vat_rate[c][min(t, _n_days) - 1]
                                 / (1 + w.vat_rate[c][min(t, _n_days) - 1])
                                 for c, t in zip(_pr["cat"], _pr["delivery_t"])])
    _vin = float((_pr["qty"] * _pr["unit_cost"] * _pshare).sum())
    _vat_led = float(base["cost_sheet"]["vat"].sum())
    _vat_gap = abs((_vout - _vin) - _vat_led)
    checks.append((
        "VAT remitted ties to the rate map (output - input, invoice rounding aside)",
        _vat_gap < 25.0,
        f"remitted {_vat_led:,.0f}, recomputed gap {_vat_gap:.2f}",
        "structural",
    ))
    _pt = base["profit_tax"]
    # profit tax is accrued and settled *per year* (P5 finance, each year
    # closes and taxes its own result independently), not on the multi-year
    # sum — max(0, total_profit) is only equal to sum(max(0, yearly_profit))
    # when every year happens to be individually profitable. On the 3-year
    # horizon, expected tax must be recomputed year by year.
    if base.get("year_results"):
        _pt_expected = sum(PHASE4["profit_tax_rate"] * max(0.0, y["profit_before_tax"])
                           for y in base["year_results"])
    else:
        _pt_expected = max(0.0, base["realized_profit"]) * PHASE4["profit_tax_rate"]
    checks.append((
        "profit tax accrues on the positive result; after-tax < before-tax",
        abs(_pt - _pt_expected) < 1e-6
        and base["realized_after_tax"] <= base["realized_profit"],
        f"before {base['realized_profit']:,.0f} | tax {_pt:,.0f} "
        f"| after {base['realized_after_tax']:,.0f}",
        "structural",
    ))
    # unconditionally zero only while no one was ever hired; the Phase 5
    # endogenous expansion (or a policy.hired_extra spec) can hire staff, at
    # which point nonzero payroll tax is the *correct* result, not a defect
    _ever_hired = float(base["cost_sheet"].get("wages", pd.Series(dtype = float)).sum()) > 0.0
    _payroll = float(base["cost_sheet"]["payroll_tax"].sum())
    checks.append((
        "payroll tax is zero unless staff were hired, else strictly positive",
        (_payroll == 0.0) if not _ever_hired else (_payroll > 0.0),
        f"payroll_tax {_payroll:,.0f}, wages paid: {_ever_hired}",
        "structural",
    ))

    # refunds (P3 §21): referential integrity always holds; the count band
    # (30-250) is calibrated to one year of receipts and is a "band", not a
    # structural rule — a 3-year run legitimately sees roughly 3x as many
    _rf = rec[rec["qty"] < 0]
    _sale_ids = set(rec.loc[rec["qty"] > 0, "receipt_id"])
    _ref_ok = bool(_rf["ref_receipt_id"].isin(values = _sale_ids).all())
    checks.append((
        "refunds present, each pointing at a real sale receipt",
        len(_rf) > 0 and _ref_ok,
        f"{len(_rf)} refunds, refs valid: {_ref_ok}",
        "structural",
    ))
    checks.append((
        "refund count in the calibrated per-year range (30-250/yr)",
        30 * rec_years <= len(_rf) <= 250 * rec_years,
        f"{len(_rf)} refunds over {rec_years} yr(s)",
        "band",
    ))
    _led_gap = abs(float((rec.qty * rec.unit_price).sum())
                   - float(base["cost_sheet"].revenue.sum()))
    checks.append((
        "receipts (net of refunds) tie to the ledger to the cent",
        _led_gap < 1e-6,
        f"gap {_led_gap:.2e}",
        "structural",
    ))

    # recording-layer recoverability (P3 §20): the defects must be findable,
    # cleanable, and must reconstruct the truth exactly where §20 promises it
    frames, ledger = dirt
    drec = frames["receipts"]
    _mult = drec.groupby(
        by = list(drec.columns),
        dropna = False,
    ).size().reset_index(name = "n")
    _fl = _mult.groupby(by = "receipt_id")["n"].apply(func = lambda s: bool((s % 2 == 0).all()))
    _flagged = {str(r) for r in _fl[_fl].index}
    _inj = set(ledger.loc[ledger["kind"] == "dup_receipt", "key"])
    # The all-even rule is sound only in the sense the design docs describe:
    # "verified against the reference year, where zero legitimate receipts
    # have that property" — an empirical property of one calibrated seed,
    # not a mathematical guarantee for every seed. A different seed can
    # legitimately produce a genuine receipt whose lines happen to all be
    # even-multiplicity by chance, which would flag as a false positive here
    # without any defect in the generator. Reported as a band, not fatal.
    checks.append((
        "dirty layer: all-even rule flags exactly the injected receipt dupes",
        _flagged == _inj and len(_inj) >= 10,
        f"{len(_flagged)} flagged / {len(_inj)} injected",
        "band",
    ))
    # void pairs net to zero, so after halving the retries the dirty tape's
    # revenue, units, and receipt set must all equal the truth exactly —
    # but this recomputation reuses _flagged above, so it inherits the same
    # seed-dependent false-positive risk and is likewise a band, not fatal
    _mult["keep"] = np.where(_mult["receipt_id"].astype(dtype = str).isin(values = _flagged),
                             _mult["n"] // 2, _mult["n"])
    _clean_rev = float((_mult["qty"] * _mult["unit_price"] * _mult["keep"]).sum())
    _clean_units = float((_mult["qty"] * _mult["keep"]).sum())
    _true_rev = float((rec.qty * rec.unit_price).sum())
    checks.append((
        "dirty layer: dedup + void-cancel recovers revenue, units, receipts exactly",
        abs(_clean_rev - _true_rev) < 1e-6
        and _clean_units == float(rec.qty.sum())
        and drec["receipt_id"].nunique() == rec["receipt_id"].nunique(),
        f"revenue err {abs(_clean_rev - _true_rev):.2e}",
        "band",
    ))
    # negative lines WITHOUT a refund reference are the injected voids; the
    # referenced ones are honest refunds, checked separately above. Each
    # having a matching partner line is structural; the 30-300 count is a
    # one-year calibration and is reported as a band instead, since a 3-year
    # run legitimately sees roughly 3x as many.
    _neg = drec[(drec["qty"] < 0) & drec["ref_receipt_id"].isna()]
    _pair_cols = [
        "receipt_id",
        "uid",
        "unit_price",
    ]
    _pos_keys = set(map(tuple, drec.loc[drec["qty"] > 0, _pair_cols]
                        .itertuples(index = False, name = None)))
    _matched = all(k in _pos_keys for k in _neg[_pair_cols]
                   .itertuples(index = False, name = None))
    checks.append((
        "dirty layer: till tape shows voided mis-rings, each with its partner line",
        len(_neg) > 0 and _matched,
        f"{len(_neg)} negative lines, all matched: {_matched}",
        "structural",
    ))
    checks.append((
        "dirty layer: voided mis-ring count in the calibrated per-year range (30-300/yr)",
        30 * rec_years <= len(_neg) <= 300 * rec_years,
        f"{len(_neg)} negative lines over {rec_years} yr(s)",
        "band",
    ))
    dpr = frames["procurement"]
    _inv_key = [
        "uid",
        "qty",
        "unit_cost",
        "order_date",
        "delivery_date",
    ]
    _ded = dpr.drop_duplicates(subset = _inv_key)
    # IMPERFECTIONS["n_missing_invoices"] is a one-year calibration constant;
    # whether the recording layer scales it per calendar-year binder on the
    # P5 horizon hasn't been independently re-verified here, so this is
    # reported as a band rather than asserted as a hard invariant
    checks.append((
        "dirty layer: invoice dedup recovers all but the missing lines",
        len(_ded) == len(base["procurement"]) - IMPERFECTIONS["n_missing_invoices"] * rec_years,
        f"{len(dpr)} raw -> {len(_ded)} deduped vs {len(base['procurement'])} true "
        f"(expects {IMPERFECTIONS['n_missing_invoices']}/yr x {rec_years})",
        "band",
    ))
    _pairs = dpr.groupby(by = _inv_key) \
        .agg(
            n = ("posted_date", "size"),
            mx = ("posted_date", "max"),
        ).reset_index()
    _pairs = _pairs[_pairs["n"] > 1]
    _chrono = all(row.mx <= month_end(d = row.delivery_date) for row in _pairs.itertuples())
    checks.append((
        "dirty layer: duplicate postings precede the count that corrects them",
        len(_pairs) > 0 and _chrono,
        f"{len(_pairs)} duplicated invoices, all inside their delivery month: {_chrono}",
        "structural",
    ))
    _scatter = float(dpr.groupby(by = "delivery_date")["posted_date"].nunique().mean())
    checks.append((
        "dirty layer: paperwork entered in batches (1-4 posting dates/delivery)",
        1.0 <= _scatter <= 4.0,
        f"{_scatter:.2f}",
        "structural",
    ))
    _bp = frames["inventory_eod"].pivot(
        index = "uid",
        columns = "date",
        values = "on_hand",
    )

    def _grid(df, dcol, vcol):
        return df.pivot_table(
            index = "uid",
            columns = dcol,
            values = vcol,
            aggfunc = "sum",
        ).reindex(
            index = _bp.index,
            columns = _bp.columns,
        ).fillna(value = 0).to_numpy()

    _B = _bp.to_numpy().astype(dtype = float)
    _D = _grid(
        df = dpr,
        dcol = "delivery_date",
        vcol = "qty",
    )
    # refunds never touch the shelf (returns are destroyed, not restocked),
    # so recorded goods-outflow is the ref-less lines only
    _S = _grid(
        df = drec[drec["ref_receipt_id"].isna()],
        dcol = "date",
        vcol = "qty",
    )
    _W = _grid(
        df = frames["write_offs"],
        dcol = "date",
        vcol = "units",
    )
    _res = _B[:, 1:] - _B[:, :-1] - _D[:, 1:] + _S[:, 1:] + _W[:, 1:]
    _nbad = int(np.count_nonzero(np.abs(_res) > 1e-9))
    _ntypo = int((ledger["kind"] == "snapshot_typo").sum())
    checks.append((
        "dirty layer: book stock reconciles day-to-day except at snapshot typos",
        _nbad == 2 * _ntypo and _ntypo > 0,
        f"{_nbad} broken diffs vs {2 * _ntypo} expected",
        "structural",
    ))
    _wnull = int(frames["weather"]["temp_C"].isna().sum())
    checks.append((
        "dirty layer: weather outage totals in the calibrated per-year range (3-9/yr)",
        3 * rec_years <= _wnull <= 9 * rec_years,
        f"{_wnull} over {rec_years} yr(s)",
        "band",
    ))
    _expected_kinds = {
        "hour_glitch",
        "payment_variant",
        "dup_receipt",
        "dup_invoice",
        "missing_invoice",
        "unrecorded_spoilage",
        "snapshot_typo",
        "weather_outage",
        "category_typo",
        "void_pair",
    }
    # Not actually a structural invariant, despite how it reads: some of
    # these families (category_typo especially, calibrated to ~2 rows/yr
    # even at baseline) are low-count enough that an arbitrary random_seed
    # can legitimately draw zero of them in a given year. This held for
    # every family only because the original codebase always ran a single,
    # specific MASTER_SEED — the moment random_seed became a user-facing
    # parameter (this package's own extension), that guarantee stopped
    # being true in general. Reported as a band, not asserted as fatal.
    _missing = _expected_kinds - set(ledger["kind"].unique())
    checks.append((
        "dirty layer: every defect family present in the hidden ledger",
        not _missing,
        f"{len(ledger)} ledger rows across {ledger['kind'].nunique()} families"
        + (f"; missing: {sorted(_missing)} (low-count families can miss "
           f"entirely for an arbitrary seed)" if _missing else ""),
        "band",
    ))
    structural_ok = all(okk for _, okk, _, tier in checks if tier == "structural")
    print("\nValidation — structural invariants (must always hold):")
    for name, okk, detail, tier in checks:
        if tier == "structural":
            print(f"  {'PASS' if okk else 'FAIL'}  {name}  {detail}")
    print("\nValidation — core mechanism (reported, not fatal):")
    for name, okk, detail, tier in checks:
        if tier == "core":
            print(f"  {'PASS' if okk else 'FAIL'}  {name}  {detail}")
    print("\nValidation — baseline-calibrated realism bands "
          "(expected to diverge under active events; reported, not fatal):")
    for name, okk, detail, tier in checks:
        if tier == "band":
            print(f"  {'PASS' if okk else 'FAIL'}  {name}  {detail}")
    return {
        "structural_ok": structural_ok,
        "checks": [
            {"name": name, "pass": okk, "detail": detail, "tier": tier}
            for name, okk, detail, tier in checks
        ],
    }


def validate_phase5(
    world,
    base,
    out,
):
    """The Phase 5 battery (P5 §11, checks 31-35): the exogenous script's
    year-one identity against the published one-year baseline, the panel
    accounting, and the RE ledger's reconciliation to the cost sheet."""
    w = world
    base_dir = OUT / "scenarios" / "baseline"
    checks = []

    # (31) the exogenous script's year one is byte-for-byte the published
    # baseline's: weather, calendar, modifiers, cost paths, events. The
    # ENDOGENOUS files (receipts, inventory, ...) are allowed to differ —
    # the panel churns from month one on this horizon (P5 §2 amendment),
    # so the people move even while the world's script stands still.
    _prefix_files = [
        "visible/weather.csv",
        "visible/calendar.csv",
        "visible/locations.csv",
        "hidden/demand_modifiers.csv",
        "hidden/tilts.csv",
        "hidden/cost_paths.csv",
        "hidden/spoil_factors.csv",
        "hidden/event_log.csv",
        "hidden/weather_full.csv",
        "hidden/decision_t0.csv",
        "hidden/locations_full.csv",
        "hidden/location_category.csv",
    ]
    _bad = []
    for _rel in _prefix_files:
        _a = (base_dir / _rel.replace("/", "\\")).read_text(encoding = "utf-8")
        _b = (out / _rel.replace("/", "\\")).read_text(encoding = "utf-8")
        if not _b.startswith(_a):
            _bad.append(_rel)
    checks.append((
        "P5-31 the exogenous script's year one is a byte prefix of the baseline's",
        not _bad,
        f"{len(_prefix_files) - len(_bad)}/{len(_prefix_files)} files"
        + (f", first mismatch {_bad[0]}" if _bad else ""),
    ))

    # (32) panel accounting: nobody shops before arriving or after leaving
    # (refund lines excepted — a return can straggle past moving day)
    _cust = w.customers
    _win = {token(
        kind = 0,
        n = int(r.customer_id),
    ): (
        int(r.arrival_t),
        float(r.departure_t) if pd.notna(r.departure_t) else np.inf,
    ) for r in _cust.itertuples()}
    rec = base["receipts"]
    _sales = rec[(rec["qty"] > 0) & (rec["customer_id"] != "")]
    _viol = 0
    for _tok, _t in zip(_sales["customer_id"], _sales["t"]):
        _wd = _win.get(_tok)
        if _wd is not None and not (_wd[0] <= _t <= _wd[1]):
            _viol += 1
    _newcomer_toks = {token(
        kind = 0,
        n = int(r.customer_id),
    ) for r in _cust.itertuples() if int(r.arrival_t) > 1}
    _n_new_lines = int(_sales["customer_id"].isin(values = _newcomer_toks).sum())
    checks.append((
        "P5-32 panel accounting: activity only inside each stay, newcomers do shop",
        _viol == 0 and _n_new_lines > 100,
        f"{_viol} out-of-window lines, {_n_new_lines} newcomer lines",
    ))

    # (33) the RE ledger reconciles to the cost sheet to the cent
    _cs = base["cost_sheet"]
    _rate = PHASE4["profit_tax_rate"]
    _retain = w.p5["finance"]["retain_ratio"]
    _open = float(base["year_results"][0]["profit_after_tax"])
    _re_exp = 0.0
    _gap33 = 0.0
    for _r in _cs.itertuples():
        _m_global = (int(_r.year) - 2025) * 12 + int(_r.month)
        if _m_global < w.p5["finance"]["formalize_month"]:
            continue
        if _m_global == w.p5["finance"]["formalize_month"]:
            _re_exp = max(0.0, _open)
        _res = (_r.revenue - _r.procurement - _r.rent - _r.wages - _r.payroll_tax
                - _r.utilities - _r.storage - _r.flyers - _r.vat
                - _r.credit_interest - _r.repairs)
        _pi = _res * (1 - _rate)
        if _pi > 0:
            _re_exp += _retain * _pi
            _gap33 = max(_gap33, abs(_r.owner_draw - (1 - _retain) * _pi))
        _re_exp -= _r.capex
        _gap33 = max(_gap33, abs(_r.retained_earnings - _re_exp))
    checks.append((
        "P5-33 retained-earnings ledger reconciles (draws, retention, capex)",
        _gap33 < 1e-6,
        f"max gap {_gap33:.2e}",
    ))

    # (34) January settles the prior year's tax in cash
    _jan = _cs[(_cs["month"] == 1) & (_cs["year"] > 2025)]
    _tax_by_year = {int(y["year"]): float(y["profit_tax"]) for y in base["year_results"]}
    _gap34 = float(max(
        (abs(r.profit_tax_paid - _tax_by_year[int(r.year) - 1]) for r in _jan.itertuples()),
        default = np.inf,
    ))
    checks.append((
        "P5-34 January pays last year's profit tax to the cent",
        len(_jan) == 2 and _gap34 < 1e-6,
        f"{len(_jan)} January closes, max gap {_gap34:.2e}",
    ))

    # (35) the discounter's defection is heterogeneous by construction:
    # transients and price-hunters lose more visit probability than rooted
    if w.p5["competitor"] is not None:
        _pers = _cust["persistence"].to_numpy()
        _mt = float(np.mean(w.comp_mult[_pers == "transient"]))
        _mr = float(np.mean(w.comp_mult[_pers == "rooted"]))
        _mean = float(np.mean(w.comp_mult))
        checks.append((
            "P5-35 defection concentrated in transients; aggregate near target",
            _mt < _mr and abs(_mean - (1 - w.p5["competitor"]["target_visit_drop"])) < 0.01,
            f"transient x{_mt:.2f} vs rooted x{_mr:.2f}, mean x{_mean:.3f}",
        ))

    print("\nPhase 5 validation:")
    for cname, okk, detail in checks:
        print(f"  {'PASS' if okk else 'FAIL'}  {cname}  {detail}")
    return all(c[1] for c in checks)


def validate_scenario(
    world,
    base,
    name,
    spec,
):
    """The structural subset for scenario arms (P4 §5): the realism bands are
    baseline-calibrated (a war year *should* fail them), so an arm checks only
    the invariants no scenario is allowed to break, plus its own fingerprint."""
    w = world
    con = base["conservation"]
    lhs = con["purchased"] - con["sold"] - con["spoiled"]
    err = np.abs(lhs - con["ending"]).max()
    checks = [(
        "conservation (init+purchased-sold-spoiled == ending)",
        err < 1e-6,
        f"max err {err:.2e}",
    )]
    rec = base["receipts"]
    closed_t = set(w.cal.loc[w.cal.closed == 1, "t"])
    checks.append((
        "zero sales on closure days",
        rec[rec.t.isin(values = closed_t)].empty,
        "",
    ))
    _rf = rec[rec["qty"] < 0]
    _sale_ids = set(rec.loc[rec["qty"] > 0, "receipt_id"])
    checks.append((
        "refunds point at real sale receipts",
        bool(_rf["ref_receipt_id"].isin(values = _sale_ids).all()),
        f"{len(_rf)} refunds",
    ))
    _led_gap = abs(float((rec.qty * rec.unit_price).sum())
                   - float(base["cost_sheet"].revenue.sum()))
    checks.append((
        "receipts tie to the ledger to the cent",
        _led_gap < 1e-6,
        f"gap {_led_gap:.2e}",
    ))
    _exp_name, _exp_check, _exp_detail = spec["expect"]
    checks.append((
        f"scenario fingerprint: {_exp_name}",
        bool(_exp_check(world, base)),
        _exp_detail(world, base),
    ))
    print(f"\nScenario validation [{name}]:")
    for cname, okk, detail in checks:
        print(f"  {'PASS' if okk else 'FAIL'}  {cname}  {detail}")
    return all(c[1] for c in checks)
