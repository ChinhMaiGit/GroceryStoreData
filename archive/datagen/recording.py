"""The recording layer (Phase 3 §20) — how the books get dirty.

The simulation is reality; only the *documents* err. Every defect is injected
into the visible exports from its own keyed stream, logged to the hidden
ledger, and provably cleanable.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from collections import defaultdict
from datagen.keys import K_DIRT, rng_for
from datagen.params import IMPERFECTIONS


def month_end(d):
    """Last calendar day of d's month (stock counts and posting cutoffs)."""
    nxt = (d.replace(day = 28) + dt.timedelta(days = 4)).replace(day = 1)
    return nxt - dt.timedelta(days = 1)


def dirty_layer(
    world,
    frames,
):
    """Corrupt the documents, one calendar year at a time (P5 §2).

    A real back office runs on yearly binders, and so does this one: each
    365-day block of the exports passes through `_dirty_block` with its own
    per-year keyed streams, so the first block's defects are draw-for-draw
    the published one-year baseline's, whatever the horizon. Book drift
    never crosses a year boundary — the December stock count trues it up."""
    n_years = getattr(world, "n_years", 1)
    if n_years == 1:
        return _dirty_block(
            world = world,
            frames = frames,
            year_key = 0,
        )
    _date_col = {
        "receipts": "date",
        "inventory_eod": "date",
        "procurement": "delivery_date",
        "promotions": "start_date",
        "write_offs": "date",
        "weather": "date",
    }
    y0 = frames["weather"]["date"].iloc[0].year
    out_frames = {name: [] for name in frames}
    ledgers = []
    for y in range(n_years):
        block = {
            name: df[df[_date_col[name]].map(arg = lambda d: d.year) == y0 + y]
            .reset_index(drop = True)
            for name, df in frames.items()
        }
        bframes, bledger = _dirty_block(
            world = world,
            frames = block,
            year_key = y,
        )
        for name in frames:
            out_frames[name].append(bframes[name])
        ledgers.append(bledger)
    return (
        {name: pd.concat(
            objs = parts,
            ignore_index = True,
        ) for name, parts in out_frames.items()},
        pd.concat(
            objs = ledgers,
            ignore_index = True,
        ),
    )


def _dirty_block(
    world,
    frames,
    year_key,
):
    """Corrupt the *documents*, never the physics (Phase 3 §20).

    The simulation is reality and is already finished when this runs; every
    defect below is injected into the visible exports only, from its own
    keyed stream, so the CRN discipline and the oracle replay are untouched.
    Book inventory drifts away from true stock exactly as far as the
    document defects imply, and monthly stock counts true it up through
    `stock_count` write-off rows — the familiar shape of retail shrinkage.
    Returns the corrupted frames plus a ledger of every injected defect
    (the hidden answer key for the data-cleaning grade)."""
    imp = IMPERFECTIONS

    def _g(stream):
        # year one consumes the original keys (P5 §2); later binders their own
        return rng_for(K_DIRT, stream) if year_key == 0 else rng_for(K_DIRT, stream, year_key)

    ledger = []
    events = []      # (uid, date, book-minus-true delta) from document defects

    # ---- receipts: D11 voided mis-rings, D2 placeholder hours, D3 label
    # ---- drift, D1 duplicates --------------------------------------------
    rec = frames["receipts"].copy()
    rids = rec["receipt_id"].unique()
    rid_date = dict(zip(
        rec.drop_duplicates(subset = "receipt_id")["receipt_id"],
        rec.drop_duplicates(subset = "receipt_id")["date"],
    ))

    # D11 first, so the void lines inherit any later per-receipt mutation.
    # The wrong item is a real product at that day's real shelf price (drawn
    # from another receipt of the same day); +q then -q nets to zero, so
    # there is no economic or inventory effect — only till-tape noise.
    g11 = _g(stream = 11)
    vids = g11.choice(
        a = rids,
        size = round(len(rids) * imp["void_pair_rate"]),
        replace = False,
    )
    _pool_cols = [
        "uid",
        "unit_price",
        "promo",
    ]
    _day_pool = {d: sub[_pool_cols].reset_index(drop = True)
                 for d, sub in rec.groupby(by = "date")}
    _void_rows = []
    for r in vids:
        _host = rec[rec["receipt_id"] == r].iloc[0]
        _pool = _day_pool[_host["date"]]
        _don = _pool.iloc[int(g11.integers(len(_pool)))]
        _q = int(g11.integers(
            low = 1,
            high = 3,
        ))
        for _sgn in (1, -1):
            _void_rows.append({
                "receipt_id": _host["receipt_id"],
                "hour": _host["hour"],
                "payment": _host["payment"],
                "customer_id": _host["customer_id"],
                "uid": _don["uid"],
                "qty": _sgn * _q,
                "unit_price": _don["unit_price"],
                "promo": _don["promo"],
                "date": _host["date"],
            })
        ledger.append({
            "kind": "void_pair",
            "table": "receipts",
            "key": str(r),
            "date": rid_date[r],
            "delta": _q,
            "note": f"mis-ring of {_don['uid']} voided at the till",
        })
    rec = pd.concat(
        objs = [rec, pd.DataFrame(_void_rows)],
        ignore_index = True,
    )

    g2 = _g(stream = 2)
    glitch = g2.choice(
        a = rids,
        size = round(len(rids) * imp["hour_glitch_rate"]),
        replace = False,
    )
    rec.loc[rec["receipt_id"].isin(values = set(glitch)), "hour"] = 0
    ledger += [{
        "kind": "hour_glitch",
        "table": "receipts",
        "key": str(r),
        "date": rid_date[r],
        "delta": 0,
        "note": "hour overwritten with the 0 placeholder",
    } for r in glitch]

    g3 = _g(stream = 3)
    vic = g3.choice(
        a = rids,
        size = round(len(rids) * imp["payment_variant_rate"]),
        replace = False,
    )
    pay_of = dict(zip(
        rec.drop_duplicates(subset = "receipt_id")["receipt_id"],
        rec.drop_duplicates(subset = "receipt_id")["payment"],
    ))
    var_map = {}
    for r in vic:
        opts = imp["payment_variants"][pay_of[r]]
        var_map[r] = opts[int(g3.integers(len(opts)))]
    rec["payment"] = rec["receipt_id"].map(arg = var_map).fillna(value = rec["payment"])
    ledger += [{
        "kind": "payment_variant",
        "table": "receipts",
        "key": str(r),
        "date": rid_date[r],
        "delta": 0,
        "note": f"'{pay_of[r]}' recorded as '{var_map[r]}'",
    } for r in vic]

    # D1 last, so the retry's copies inherit any D2/D3 mutation and stay
    # byte-identical to their originals. The dedup rule the analyst needs —
    # "every distinct line's multiplicity is even" — is only sound if no
    # legitimate receipt already has that property, so such receipts are
    # excluded from the candidate pool (the reference year has none).
    g1 = _g(stream = 1)
    _cols = list(rec.columns)
    _mult = rec.groupby(
        by = _cols,
        dropna = False,
    ).size().reset_index(name = "n")
    _nat = _mult.groupby(by = "receipt_id")["n"].apply(func = lambda s: bool((s % 2 == 0).all()))
    pool = np.array([r for r in rids if not _nat[r]])
    dup = g1.choice(
        a = pool,
        size = round(len(rids) * imp["dup_receipt_rate"]),
        replace = False,
    )
    _dup_lines = rec[rec["receipt_id"].isin(values = set(dup))]
    for row in _dup_lines.itertuples():
        # refund lines are financial only (no goods movement), so a
        # duplicated refund shifts no book stock
        if pd.isna(row.ref_receipt_id):
            events.append((row.uid, row.date, -float(row.qty)))
    rec = pd.concat(
        objs = [rec, _dup_lines],
        ignore_index = True,
    )
    ledger += [{
        "kind": "dup_receipt",
        "table": "receipts",
        "key": str(r),
        "date": rid_date[r],
        "delta": int((_dup_lines["receipt_id"] == r).sum()),
        "note": "POS retry re-posted the whole receipt",
    } for r in dup]
    # the till journal is chronological: a retry's copies land right after
    # the original, not in a batch at the end of the year's file
    rec = rec.sort_values(
        by = "receipt_id",
        kind = "stable",
        ignore_index = True,
    )

    # ---- procurement: D6 posting lag, D4 double postings, D5 missing lines --
    pr = frames["procurement"].copy()
    g6 = _g(stream = 6)
    lags, probs = imp["posting_lag"]
    # one lag per delivery: the clerk keys a delivery's paperwork in one
    # sitting, with the odd straggler line entered a few days later
    _batch_lag = {d: int(g6.choice(
        a = lags,
        p = probs,
    )) for d in sorted(pr["delivery_date"].unique())}
    _lag = np.array([_batch_lag[d] for d in pr["delivery_date"]])
    _strag = g6.random(size = len(pr)) < imp["posting_straggler_rate"]
    _lag = _lag + np.where(_strag, g6.integers(
        low = 1,
        high = 3,
        size = len(pr),
    ), 0)
    pr["posted_date"] = [d + dt.timedelta(int(l)) for d, l in zip(pr["delivery_date"], _lag)]

    # a duplicate must be keyed in before the month-end count that will
    # correct it, or the paper trail runs backwards in time
    g4 = _g(stream = 4)
    _room = np.array([(month_end(d = d) - p).days
                      for d, p in zip(pr["delivery_date"], pr["posted_date"])])
    _elig4 = np.flatnonzero(_room >= 2)
    di = sorted(g4.choice(
        a = _elig4,
        size = round(len(pr) * imp["dup_invoice_rate"]),
        replace = False,
    ))
    dup_inv = pr.iloc[di].copy()
    _extra = [int(g4.integers(
        low = 1,
        high = min(7, r) + 1,
    )) for r in _room[di]]
    dup_inv["posted_date"] = [d + dt.timedelta(x) for d, x in zip(dup_inv["posted_date"], _extra)]
    for row in dup_inv.itertuples():
        events.append((row.uid, row.delivery_date, float(row.qty)))
        ledger.append({
            "kind": "dup_invoice",
            "table": "procurement",
            "key": row.uid,
            "date": row.delivery_date,
            "delta": int(row.qty),
            "note": "invoice posted twice",
        })

    g5 = _g(stream = 5)
    mi = sorted(g5.choice(
        a = np.array([i for i in range(len(pr)) if i not in set(di)]),
        size = imp["n_missing_invoices"],
        replace = False,
    ))
    for i in mi:
        row = pr.iloc[i]
        events.append((row["uid"], row["delivery_date"], -float(row["qty"])))
        ledger.append({
            "kind": "missing_invoice",
            "table": "procurement",
            "key": row["uid"],
            "date": row["delivery_date"],
            "delta": -int(row["qty"]),
            "note": "delivery received but never entered",
        })
    pr = pd.concat(
        objs = [pr.drop(index = pr.index[mi]), dup_inv],
        ignore_index = True,
    )

    # ---- write-offs: D7 unrecorded tosses, plus the reason label ------------
    wo = frames["write_offs"].copy()
    if "reason" in wo.columns:
        # the freezer failure's rows (P5 §7) arrive labeled "damage" from the
        # simulation; everything unlabeled is the ordinary nightly toss
        wo["reason"] = wo["reason"].fillna(value = "spoilage")
    else:
        wo["reason"] = "spoilage"
    g7 = _g(stream = 7)
    ui = sorted(g7.choice(
        a = len(wo),
        size = round(len(wo) * imp["unrecorded_spoilage_rate"]),
        replace = False,
    ))
    for row in wo.iloc[ui].itertuples():
        events.append((row.uid, row.date, float(row.units)))
        ledger.append({
            "kind": "unrecorded_spoilage",
            "table": "write_offs",
            "key": row.uid,
            "date": row.date,
            "delta": int(row.units),
            "note": "tossed without being logged",
        })
    wo = wo.drop(index = wo.index[ui]).reset_index(drop = True)

    # ---- inventory: book drift, monthly stock counts, D8 snapshot typos -----
    inv = frames["inventory_eod"].copy()
    days = sorted(inv["date"].unique())
    tix = {d: i for i, d in enumerate(days)}
    n_days = len(days)
    per_uid = defaultdict(lambda: np.zeros(n_days))
    for uid, d, delta in events:
        per_uid[uid][tix[d]:] += delta
    count_ix = [i for i, d in enumerate(days)
                if i == n_days - 1 or days[i + 1].month != d.month]
    adj_rows = []
    book_delta = {}
    for uid, arr in per_uid.items():
        adjcum = np.zeros(n_days)
        prior = 0.0
        for c in count_ix:
            a = arr[c] - prior
            if a != 0:
                adj_rows.append({
                    "uid": uid,
                    "units": int(a),
                    "date": days[c],
                    "reason": "stock_count",
                })
                adjcum[c:] += a
                prior = arr[c]
        book_delta[uid] = arr - adjcum
    _di = inv["date"].map(arg = tix).to_numpy()
    on = inv["on_hand"].to_numpy().astype(dtype = float)
    for uid, bd in book_delta.items():
        m = (inv["uid"] == uid).to_numpy()
        on[m] += bd[_di[m]]
    on = np.rint(on).astype(dtype = int)
    if adj_rows:
        wo = pd.concat(
            objs = [wo, pd.DataFrame(adj_rows)],
            ignore_index = True,
        )

    g8 = _g(stream = 8)
    _elig = np.flatnonzero((on >= 10) & (_di >= 1) & (_di <= n_days - 2))
    _cand = g8.choice(
        a = _elig,
        size = min(len(_elig), 5 * imp["n_snapshot_typos"]),
        replace = False,
    )
    # keep typos apart: no two on the same SKU within one day of each other,
    # so each breaks the perpetual identity on exactly two consecutive diffs
    _kept = []
    _seen = set()
    for i in _cand:
        uid, dd = inv["uid"].iat[int(i)], int(_di[int(i)])
        if all((uid, dd + s) not in _seen for s in (-1, 0, 1)):
            _kept.append(int(i))
            _seen.add((uid, dd))
        if len(_kept) == imp["n_snapshot_typos"]:
            break
    for i in _kept:
        old = int(on[i])
        s = str(old)
        new = old + 10 if len(s) < 2 or s[-1] == s[-2] else int(s[:-2] + s[-1] + s[-2])
        on[i] = new
        ledger.append({
            "kind": "snapshot_typo",
            "table": "inventory_eod",
            "key": inv["uid"].iat[i],
            "date": inv["date"].iat[i],
            "delta": new - old,
            "note": f"on_hand {old} keyed in as {new}",
        })
    inv["on_hand"] = on

    # ---- weather: D9 sensor outages ------------------------------------------
    wx = frames["weather"].copy()
    g9 = _g(stream = 9)
    starts = sorted(g9.choice(
        a = np.arange(5, len(wx) - 5),
        size = imp["n_weather_outages"],
        replace = False,
    ))
    _dark_cols = [
        "temp_C",
        "rain_mm",
        "wet",
    ]
    for s in starts:
        ln = int(g9.integers(
            low = 1,
            high = imp["outage_max_days"] + 1,
        ))
        wx.loc[wx.index[s:s + ln], _dark_cols] = np.nan
        ledger.append({
            "kind": "weather_outage",
            "table": "weather",
            "key": "",
            "date": wx["date"].iat[s],
            "delta": ln,
            "note": f"sensor dark for {ln} day(s)",
        })

    # ---- promotions: D10 the category typo ----------------------------------
    pm = frames["promotions"].copy()
    good, bad = imp["promo_typo"]
    _rows = pm.index[pm["category"] == good].to_numpy()
    g10 = _g(stream = 10)
    pick = g10.choice(
        a = _rows,
        size = min(imp["n_promo_typos"], len(_rows)),
        replace = False,
    ) if len(_rows) else np.array(
        object = [],
        dtype = int,
    )
    pm.loc[pick, "category"] = bad
    ledger += [{
        "kind": "category_typo",
        "table": "promotions",
        "key": str(i),
        "date": pm["start_date"].loc[i],
        "delta": 0,
        "note": f"'{good}' logged as '{bad}'",
    } for i in pick]

    frames = {
        **frames,
        "receipts": rec,
        "procurement": pr,
        "write_offs": wo,
        "inventory_eod": inv,
        "weather": wx,
        "promotions": pm,
    }
    return frames, pd.DataFrame(ledger)
