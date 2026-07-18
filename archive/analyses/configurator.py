import marimo

__generated_with = "0.23.14"
app = marimo.App(width="full", app_title="Scenario Configurator")


@app.cell
def _():
    import subprocess
    import sys
    import time

    import marimo as mo

    from pathlib import Path

    ROOT = Path(__file__).resolve().parent.parent.parent
    ARCHIVE = ROOT / "archive"
    DATA = ROOT / "data" / "scenarios"
    if str(ARCHIVE) not in sys.path:
        sys.path.insert(0, str(ARCHIVE))

    from datagen.scenarios import SCENARIOS  # noqa: E402 (needs ARCHIVE on sys.path)

    # ---- what a generated arm looks like, and which notebook(s) already
    # target it. This tool does NOT parameterize the notebooks below — each
    # was written and graded against one specific arm (mostly 3y_baseline,
    # or a named twin pair), so "opening the graded notebook" only makes
    # sense for the arms this table actually lists. Picking anything else
    # still generates real, gradeable data — there just isn't a full-depth
    # notebook pointed at it yet (see documents/ANALYSIS_CATALOG.md, whose
    # Layers 0-4 and 6 are written to apply to ANY arm; adapting one of the
    # notebooks below to a new arm is a data-path edit, not a rewrite).
    NOTEBOOKS = {
        "baseline": [
            "archive/analyses/catalog_walkthrough.py",
        ],
        "3y_baseline": [
            "archive/analyses/analysis_workbook.py",
            "archive/analyses/clean_and_describe.py",
            "archive/analyses/diagnose_causes.py",
            "archive/analyses/predict_and_warn.py",
            "archive/analyses/prescribe.py",
            "archive/analyses/learn_structure.py",
            "archive/analyses/three_year_review.py",
        ],
        "3y_no_competitor": [
            "archive/analyses/competitor_entry_study.py",
        ],
        "3y_no_expansion": [
            "archive/analyses/expansion_review.py",
        ],
        "food_vat_cut_july": [
            "archive/analyses/policy_lab.py",
        ],
        "tax_rebate_spring": [
            "archive/analyses/policy_lab.py",
        ],
        "war_june": [
            "archive/analyses/policy_lab.py",
        ],
        "typhoon_september": [
            "archive/analyses/policy_lab.py",
        ],
        "second_clerk": [
            "archive/analyses/policy_lab.py",
        ],
    }
    # some notebooks read a SECOND arm besides the one the user picked (a
    # CRN-twin comparison) — that arm must also exist on disk before the
    # notebook will run
    COREQUISITES = {
        "3y_no_competitor": ["3y_baseline"],
        "3y_no_expansion": ["3y_baseline"],
        "food_vat_cut_july": ["baseline"],
        "tax_rebate_spring": ["baseline"],
        "war_june": ["baseline"],
        "typhoon_september": ["baseline"],
        "second_clerk": ["baseline"],
    }
    ALL_ARMS = ["baseline"] + sorted(SCENARIOS)
    return (
        ALL_ARMS,
        COREQUISITES,
        DATA,
        NOTEBOOKS,
        ROOT,
        SCENARIOS,
        mo,
        subprocess,
        sys,
        time,
    )


@app.cell
def _(mo):
    mo.md(r"""
    # Scenario configurator

    Pick a scenario, generate its data, and jump straight to the notebook
    that already analyzes it — one flow instead of three manual steps.

    This tool does not invent new analysis: it drives the existing
    `generate_dataset.py` CLI and points you at the existing graded
    notebooks (`analyses/*.py`), which were each written and graded against
    one specific arm. If you pick an arm with no notebook listed below,
    generation still works — you're just the first to analyze it, starting
    from `documents/ANALYSIS_CATALOG.md`, whose Layers 0–4 and 6 are
    written to apply to any arm.
    """)
    return


@app.cell
def _(ALL_ARMS, DATA, NOTEBOOKS, SCENARIOS, mo):
    def _status(name):
        _visible = DATA / name / "visible"
        if not _visible.exists():
            return "not generated"
        _n = len(list(_visible.glob("*.csv")))
        return f"generated ({_n} files)"

    _rows = [
        {
            "arm": _name,
            "description": "the one-year reference arm" if _name == "baseline"
                           else SCENARIOS[_name]["description"],
            "status": _status(_name),
            "notebooks": ", ".join(
                _p.split("/")[-1] for _p in NOTEBOOKS.get(_name, [])
            ) or "(none yet — see the catalog)",
        }
        for _name in ALL_ARMS
    ]
    mo.ui.table(
        data = _rows,
        selection = None,
        label = "Every reference arm, its generation status, and its dedicated notebook(s)",
    )
    return


@app.cell
def _(ALL_ARMS, mo):
    arm_picker = mo.ui.dropdown(
        options = ALL_ARMS,
        value = "3y_baseline",
        label = "Scenario to generate",
    )
    arm_picker
    return (arm_picker,)


@app.cell
def _(COREQUISITES, arm_picker, mo):
    _coreq = COREQUISITES.get(arm_picker.value, [])
    _coreq_note = (
        mo.md(
            f"**This notebook's comparison needs `{_coreq[0]}` on disk too** "
            "— check the box below to generate it in the same run if it "
            "isn't already there."
        )
        if _coreq
        else mo.md("")
    )
    include_coreq = mo.ui.checkbox(
        value = bool(_coreq),
        label = f"also generate {_coreq[0]}" if _coreq else "",
        disabled = not _coreq,
    )
    mo.vstack(items = [_coreq_note, include_coreq]) if _coreq else mo.md("")
    return (include_coreq,)


@app.cell
def _(mo):
    generate_button = mo.ui.run_button(label = "Generate this arm")
    generate_button
    return (generate_button,)


@app.cell
def _(
    COREQUISITES,
    ROOT,
    arm_picker,
    generate_button,
    include_coreq,
    mo,
    subprocess,
    sys,
    time,
):
    # ---- run generate_dataset.py for the picked arm (+ its co-requisite) ---
    # `generate_dataset.py` always (re)generates the one-year baseline on
    # every invocation, so picking "baseline" alone needs no --scenario flag
    # at all; anything else is passed as a repeatable --scenario NAME.
    _log = mo.md("*Click \"Generate this arm\" above to run the generator.*")
    if generate_button.value:
        _names = []
        if arm_picker.value != "baseline":
            _names.append(arm_picker.value)
        if include_coreq.value:
            for _c in COREQUISITES.get(arm_picker.value, []):
                if _c != "baseline" and _c not in _names:
                    _names.append(_c)
        _cmd = [sys.executable, "generate_dataset.py"]
        for _n in _names:
            _cmd += ["--scenario", _n]
        _t0 = time.time()
        _result = subprocess.run(
            args = _cmd,
            cwd = str(ARCHIVE),
            capture_output = True,
            text = True,
            timeout = 900,
        )
        _elapsed = time.time() - _t0
        _tail = "\n".join(_result.stdout.strip().splitlines()[-25:])
        _log = mo.vstack(
            items = [
                mo.md(
                    f"**{'Done' if _result.returncode == 0 else 'FAILED'}** "
                    f"in {_elapsed:.0f}s — `{' '.join(_cmd)}`"
                ),
                mo.plain_text(_tail or _result.stderr[-2000:]),
            ],
        )
    _log
    return


@app.cell
def _(NOTEBOOKS, arm_picker, mo):
    _lines = [
        f"- `{_p}` — run `uv run marimo edit {_p}`"
        for _p in NOTEBOOKS.get(arm_picker.value, [])
    ]
    _list_md = "\n".join(_lines) or "No dedicated notebook targets this arm yet."
    mo.md(
        f"""
    ## Open the graded notebook for `{arm_picker.value}`

    {_list_md}

    Copy the command into your terminal, or use the launcher below to start
    it from here (opens as its own `marimo edit` server; this configurator
    keeps running independently).
    """
    )
    return


@app.cell
def _(NOTEBOOKS, arm_picker, mo):
    launch_picker = mo.ui.dropdown(
        options = NOTEBOOKS.get(arm_picker.value, []) or ["(none available)"],
        label = "Notebook to launch",
    )
    launch_button = mo.ui.run_button(label = "Open in marimo edit")
    mo.hstack(items = [launch_picker, launch_button])
    return launch_button, launch_picker


@app.cell
def _(ROOT, launch_button, launch_picker, mo, subprocess, sys):
    _msg = mo.md("")
    if launch_button.value and launch_picker.value and launch_picker.value != "(none available)":
        # detached, non-blocking: this app keeps running while the chosen
        # notebook opens in its own marimo server / browser tab
        subprocess.Popen(
            args = [sys.executable, "-m", "marimo", "edit", launch_picker.value],
            cwd = str(ROOT),
        )
        _msg = mo.md(f"Launching `{launch_picker.value}` in a new marimo server…")
    _msg
    return


if __name__ == "__main__":
    app.run()
