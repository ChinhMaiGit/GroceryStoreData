"""Parameters — the single source of truth (each dict mirrors its document §).

Values live here and only here; no magic numbers hide in function bodies.
Numeric tuples keep their meaning in a comment on the same line (the style
contract's one exception to one-element-per-line).
"""

from __future__ import annotations

import datetime as dt
import math

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data"

CATS = [
    "Alcoholic Beverages",
    "Bakery and Bread",
    "Beverages (Non-Alcoholic)",
    "Dairy and Eggs",
    "Fresh Produce",
    "Frozen Foods",
    "Household and Cleaning Supplies",
    "Meat and Poultry",
    "Pantry Staples and Packaged Goods",
    "Personal Care and Health",
    "Seafood",
    "Snacks and Confectionery",
]

# mean basket-value shares (drive both Dirichlet alpha and demand potential)
BASKET_SHARE = {
    "Fresh Produce": 0.11,
    "Bakery and Bread": 0.09,
    "Dairy and Eggs": 0.12,
    "Meat and Poultry": 0.11,
    "Seafood": 0.04,
    "Frozen Foods": 0.07,
    "Beverages (Non-Alcoholic)": 0.10,
    "Alcoholic Beverages": 0.07,
    "Pantry Staples and Packaged Goods": 0.13,
    "Snacks and Confectionery": 0.08,
    "Personal Care and Health": 0.05,
    "Household and Cleaning Supplies": 0.03,
}

# markup rule m_c: low on perishables, high on household goods (P1 §5)
MARKUP = {
    "Fresh Produce": 0.20,
    "Bakery and Bread": 0.22,
    "Dairy and Eggs": 0.22,
    "Meat and Poultry": 0.24,
    "Seafood": 0.24,
    "Frozen Foods": 0.28,
    "Beverages (Non-Alcoholic)": 0.30,
    "Pantry Staples and Packaged Goods": 0.30,
    "Alcoholic Beverages": 0.32,
    "Snacks and Confectionery": 0.35,
    "Personal Care and Health": 0.42,
    "Household and Cleaning Supplies": 0.45,
}

PHASE1 = {
    "n_locations": 8,
    "quality_beta": (2.0, 2.0),                     # Beta(a, b) location quality
    "households": {
        "base": 250,
        "slope": 400,
        "sd": 30,
    },
    "rent": {
        "base": 500.0,
        "slope": 1800.0,
        "sd": 100.0,
    },
    "setup_cost": {
        "base": 6000.0,
        "sd": 400.0,
    },
    "shelf_capacity_units": {
        "base": 6500,
        "slope": 6500,
    },
    "shelf_slots": {
        "base": 150,
        "slope": 250,
    },
    "customer_participation": 0.6,
    "budget_lognormal": {
        "mu": math.log(85),
        "sigma": 0.35,
    },
    "primary_day_weights": [0.07, 0.07, 0.07, 0.07, 0.12, 0.35, 0.25],  # Mon..Sun
    "adherence_beta": (9.0, 1.5),                   # Beta(a, b)
    "topup_beta": (1.5, 12.0),                      # Beta(a, b)
    "dirichlet_conc": 40.0,
    "price_sens_lognormal": {
        "mu": 0.0,
        "sigma": 0.4,
    },
    "brand_budget_loading": 0.6,
    "card_share": 0.6,
    "p_card": {
        "card": 0.95,
        "cash": 0.10,
    },
    "deviation_prob": 0.05,
    "gamma_brand": 1.0,
    "capital": 40_000.0,
    "hours_per_day": 12,
    "hourly_wage": 14.0,
    "hourly_utility": 6.0,
    "unit_storage": 0.02,
    "listing_fee": 2.5,
    "belief_bias": 0.10,
    "belief_sd": 0.25,
    "rho": 0.05,     # no SKU exceeds 5% of category demand (audit-calibrated)
    "sku_appeal_sd": 0.8,   # latent per-SKU appeal: why one pasta outsells another
    "eta": 0.30,     # safety stock: 0.3 of a MONTH's believed demand
    # store-addressable spend per household per month (participation x capture
    # x mean budget x 30/7), used to build mu_c in value terms — P1 §4
    "addressable_value_hh_month": 0.6 * 0.65 * 90.0 * 30 / 7,
}

PHASE2 = {
    "start": dt.date(2025, 1, 1),
    "n_days": 365,
    "holidays": {  # name -> date
        "new_year": dt.date(2025, 1, 1),
        "good_friday": dt.date(2025, 4, 18),
        "easter_monday": dt.date(2025, 4, 21),
        "may_day": dt.date(2025, 5, 1),
        "midsummer": dt.date(2025, 6, 21),
        "christmas_eve": dt.date(2025, 12, 24),
        "christmas": dt.date(2025, 12, 25),
        "boxing_day": dt.date(2025, 12, 26),
        "new_years_eve": dt.date(2025, 12, 31),
    },
    "major_holidays": [
        "easter_monday",
        "midsummer",
        "christmas",
    ],
    "closures": [
        dt.date(2025, 1, 1),
        dt.date(2025, 12, 25),
    ],
    "pre_holiday_days": 3,
    "temp": {
        "mean": 12.0,
        "amp": 9.0,
        "peak_day": 200,
        "phi": 0.7,
        "sd": 2.0,
    },
    "rain": {
        "p01": 0.25,
        "p11": 0.55,
        "gamma_shape": 1.4,
        "mean_mm": 5.0,
    },
    "loadings": {  # category -> (a_c, kappa_c, h_c)
        "Beverages (Non-Alcoholic)": (0.18, 0.12, 0.10),
        "Fresh Produce": (0.10, 0.03, 0.05),
        "Frozen Foods": (0.02, 0.04, 0.05),
        "Meat and Poultry": (0.08, 0.05, 0.20),
        "Alcoholic Beverages": (0.08, 0.06, 0.30),
        "Dairy and Eggs": (0.00, 0.00, 0.10),
        "Household and Cleaning Supplies": (0.00, 0.00, 0.00),  # placebo
        "Seafood": (-0.03, 0.00, 0.35),
        "Bakery and Bread": (-0.04, -0.02, 0.15),
        "Snacks and Confectionery": (-0.05, -0.03, 0.25),
        "Personal Care and Health": (-0.06, -0.04, 0.00),
        "Pantry Staples and Packaged Goods": (-0.08, -0.04, 0.10),
    },
    "tilts": {  # product type -> (a, kappa)
        "Ice Cream": (0.55, 0.25),
        "Coffee": (-0.20, -0.08),
        "Tea": (-0.20, -0.08),
    },
    "traffic": {
        "wet": -0.20,
        "pre_holiday": 0.15,
        "daily_shock_sd": 0.18,
        "daily_shock_phi": 0.85,
    },
    "wobble_sd": 0.12,
    "tight_spell": {
        "entry": 0.004,
        "mean_weeks": 6,
        "mult": 0.65,
        "crisis_coupling": 2.0,
    },
    "splurge": {
        "prob": 0.01,
        "mult": 1.5,
    },
    "inflation": 0.025,
    "event_rate": 1.5,
    "event_types": {  # type -> (categories or 'ALL', median log peak)
        "commodity_spike": (
            [
                "Bakery and Bread",
                "Pantry Staples and Packaged Goods",
            ],
            0.10,
        ),
        "import_disruption": (
            [
                "Seafood",
                "Alcoholic Beverages",
            ],
            0.12,
        ),
        "harvest_failure": (
            [
                "Fresh Produce",
            ],
            0.18,
        ),
        "fuel_price_surge": (
            "ALL",
            0.04,
        ),
    },
    "event_sd": 0.3,
    "event_ramp": 14,
    "event_decay": 60,
    "crisis": {
        "start_day": 274,
        "ramp": 14,
        "decay": 90,
        "cats": {
            "Frozen Foods": 0.15,
            "Dairy and Eggs": 0.10,
        },
        "utility_peak": 0.35,
    },
    "wage_raise": {
        "day": 182,
        "pct": 0.04,
    },
}

PHASE3 = {
    "open_hour": 8,
    "close_hour": 20,
    # 24-hour arrival profiles: weekdays peak after work, weekends late morning;
    # ~4% of mass outside opening hours (P3 §1)
    "hour_weights": [
        0.2, 0.1, 0.05, 0.05, 0.05, 0.1, 0.4, 1.0,   # hours 0-7
        4.0, 6.0, 6.5, 5.5, 5.0, 4.5, 4.0, 4.5,      # hours 8-15
        6.0, 9.0, 10.0, 8.0, 3.0, 1.2, 0.6, 0.3,     # hours 16-23
    ],
    "hour_weights_weekend": [
        0.2, 0.1, 0.05, 0.05, 0.05, 0.1, 0.3, 0.8,   # hours 0-7
        4.5, 8.0, 10.0, 10.5, 9.0, 7.0, 5.5, 5.0,    # hours 8-15
        5.0, 5.5, 5.0, 3.5, 2.0, 1.0, 0.5, 0.3,      # hours 16-23
    ],
    "carry_frac": (0.7, 1.0),   # people rarely haul the full shortfall home
    "carry_cap": (8, 16),       # per-trip carrying limit, uniform 8..15 units
    # the passing trade: one-off guests, recorded at the till, profile unknown
    "guests": {
        "base_per_day": 7.0,
        "dow_factor": [0.8, 0.8, 0.9, 1.0, 1.2, 1.5, 1.3],  # Mon..Sun
        "extra_cats_poisson": 1.0,
        "visit_budget": (2.64, 0.5),    # lognormal (ln(14), sd)
        "qty2_prob": 0.35,
        "need_theta": 0.45,
    },
    "flyer_lift": 0.05,
    "deviation_prob": 0.05,      # Phase 1's parameter, acting on visits and impulses
    "pantry_target_days": 10.0,
    "list_threshold": 0.7,
    "topup_threshold_days": 2.0,
    "topup_buy_days": 4.0,      # a top-up is a quick basket, not a stock-up
    "need_alpha": 4.0,
    "capture_target": 0.65,     # calibrates the outside option u0
    "max_units_visit": 12,
    "impulse_prob": 0.05,
    "restock_weekday": 0,       # Monday
    "lead_days": 2,
    "ma_weeks": 4,
    "alloc_smoothing": 1.0,     # Laplace floor keeping listed SKUs alive
    "promo_trigger_cover": 4.0,
    "promo_depths": (
        [0.10, 0.20, 0.30],     # markdown depths
        [0.50, 0.35, 0.15],     # probabilities
    ),
    "promo_days": 14,
    "flyer_cost_week": 40.0,
    "loyalty_depth": 0.05,
    "loyalty_traffic_lift": 0.15,   # the advertised day pulls extra visits
    # refunds (P3 §21): the odd item comes back with its receipt — quality
    # gripes, wrong grabs. Money leaves the till; the item is destroyed, not
    # restocked, so inventory never moves.
    "refund_receipt_rate": 0.006,
    "refund_max_lag_days": 13,
    # menu-cost hysteresis: retailers reprice off a smoothed cost trend, not
    # every noisy invoice, and only when the drift is large enough to bother
    "cost_ewma_alpha": 0.35,
    "reprice_threshold": 0.03,
    "spoilage_weekly": {
        "Bakery and Bread": 0.18,
        "Seafood": 0.18,
        "Fresh Produce": 0.14,
        "Meat and Poultry": 0.09,
        "Dairy and Eggs": 0.06,
        "Frozen Foods": 0.01,
    },
    # daily spoilage responds to the script: (heat loading per +10C vs annual
    # mean, cold-chain strain loading on the energy-crisis trajectory)
    "spoil_response": {
        "Bakery and Bread": (0.5, 0.0),
        "Fresh Produce": (0.6, 0.0),
        "Seafood": (0.3, 0.5),
        "Meat and Poultry": (0.3, 0.5),
        "Dairy and Eggs": (0.25, 0.6),
        "Frozen Foods": (0.1, 0.8),
    },
    "spoil_wobble_sd": 0.25,    # day-level batch luck, lognormal
    "spoil_daily_cap": 0.35,
    "credit_apr": 0.08,
}

PHASE4 = {
    # VAT (P4 §2): differential rates embedded in every gross price; the
    # reduced rate covers food, the standard rate the non-food categories
    "vat_reduced": 0.10,
    "vat_standard": 0.20,
    "vat_standard_categories": [
        "Alcoholic Beverages",
        "Household and Cleaning Supplies",
        "Personal Care and Health",
    ],
    # employer contributions on gross wages — zero while the owner works alone,
    # real money the moment a staffing scenario hires
    "payroll_rate": 0.25,
    # small-business flat rate on positive realized annual profit; accrued at
    # the year's close, paid the following January (no cash movement in-year)
    "profit_tax_rate": 0.20,
}

# ============================================================================
# The recording layer (Phase 3 §20) — rates of document defects
# ============================================================================
IMPERFECTIONS = {
    # D1: a POS retry re-posts an entire receipt (same id, every line twice)
    "dup_receipt_rate": 0.002,
    # D2: a POS clock glitch stamps hour = 0 on all of a receipt's lines
    "hour_glitch_rate": 0.004,
    # D3: hand-keyed / terminal-batch label variants for the payment method
    "payment_variant_rate": 0.012,
    "payment_variants": {
        "card": [
            "Card",
            "CARD",
        ],
        "cash": [
            "Cash",
            "CASH",
            "cash ",
        ],
    },
    # D4: a supplier invoice entered twice, days apart
    "dup_invoice_rate": 0.004,
    # D5: deliveries received but never entered
    "n_missing_invoices": 6,
    # D6: entry lag of the invoice clerk — one lag per delivery (the paperwork
    #     is entered as a batch), plus a few straggler lines entered later
    "posting_lag": (
        [0, 1, 2, 3, 5, 7, 9],                          # lag days
        [0.70, 0.15, 0.10, 0.02, 0.01, 0.01, 0.01],     # probabilities
    ),
    "posting_straggler_rate": 0.04,
    # D7: stock tossed without being logged — the dominant shrinkage source
    "unrecorded_spoilage_rate": 0.025,
    # D8: digit slips in one night's on_hand, self-corrected the next day
    "n_snapshot_typos": 24,
    # D9: weather-sensor outages (spells of 1-3 days)
    "n_weather_outages": 3,
    "outage_max_days": 3,
    # D10: the classic confectionery misspelling in the promotions log
    "promo_typo": (
        "Snacks and Confectionery",
        "Snacks and Confectionary",
    ),
    "n_promo_typos": 2,
    # D11: mis-rings — the cashier scans the wrong item and voids it on the
    #      spot; the till tape keeps both lines, netting to zero
    "void_pair_rate": 0.006,
}

BRAND_LEVEL = {
    "common": 0.15,
    "intermediate": 0.50,
    "premium": 0.85,
}

# most shelf tags end .x9, but a real price list is not uniform: some SKUs
# live on .x5 endings and some on round dimes (deli, produce, multibuy habits)
PRICE_ENDINGS = (
    [9, 5, 0],              # endings (cents digit)
    [0.86, 0.09, 0.05],     # probabilities
)
