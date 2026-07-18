"""Generates a marimo notebook (.py, marimo's native format) scaffolded
around one simulation run's own duckdb database.

This is a condensed, first-pass version of documents/ANALYSIS_CATALOG.md's
question layers — not the full catalog — meant to give an analyst a running
start, not a finished worked answer. mode='instructor' adds one starter
query per question; mode='student' leaves an empty cell with just the
question as a prompt.
"""

from __future__ import annotations

from pathlib import Path

# A condensed slice of documents/ANALYSIS_CATALOG.md, layer -> [(question,
# starter SQL against the duckdb tables export() writes)]. Extend this list
# rather than the class's method surface when adding coverage.
_CATALOG = [
    ("Layer 0 — Clean the records", [
        ("Do the receipts reconcile to the ledger's revenue line?",
         "SELECT SUM(qty * unit_price) AS till_revenue FROM receipts;"),
        ("Does book stock reconcile against deliveries, sales, and write-offs?",
         "SELECT * FROM inventory_eod LIMIT 20;"),
    ]),
    ("Layer 1 — Describe the business", [
        ("Where does the money come from and go?",
         "SELECT * FROM cost_sheet ORDER BY month;"),
        ("When do people shop?",
         "SELECT date, COUNT(*) AS lines FROM receipts GROUP BY date ORDER BY date;"),
    ]),
    ("Layer 2 — Diagnose causes", [
        ("Does weather move revenue once the calendar is controlled for?",
         "SELECT r.date, w.temp_C, w.rain_mm, SUM(r.qty * r.unit_price) AS revenue "
         "FROM receipts r JOIN weather w USING (date) GROUP BY r.date, w.temp_C, w.rain_mm;"),
    ]),
    ("Layer 3 — Predict", [
        ("What will next week sell, benchmarked against a seasonal-naive forecast?",
         "SELECT * FROM cost_sheet ORDER BY month;"),
    ]),
    ("Layer 4 — Prescribe", [
        ("What is better analytics worth here, in euros?",
         "-- compare against the profit triptych once you have hidden/ access"),
    ]),
]


def write_notebook(
    path: Path,
    settings: dict,
    db_path: Path,
    out_dir: Path,
    mode: str = "student",
) -> Path:
    if mode not in ("student", "instructor"):
        raise ValueError("mode must be 'student' or 'instructor'")

    path = Path(path)
    path.parent.mkdir(parents = True, exist_ok = True)

    cells = [_cell_setup(out_dir = out_dir)]
    for layer_title, questions in _CATALOG:
        cells.append(_cell_layer(layer_title, questions, mode))

    body = "\n\n".join(cells)
    title = settings["basic"]["name"]
    notebook = f'''import marimo

__generated_with = "0.23.14"
app = marimo.App(width="full", app_title={title!r})


{body}

if __name__ == "__main__":
    app.run()
'''
    path.write_text(notebook, encoding = "utf-8")
    return path


def _cell_setup(out_dir: Path) -> str:
    visible_dir = str((out_dir / "visible").resolve()).replace("\\", "/")
    return f'''@app.cell
def _():
    from pathlib import Path

    import duckdb
    import marimo as mo
    import pandas as pd

    VISIBLE = Path({visible_dir!r})

    con = duckdb.connect(database = ":memory:")
    for csv in sorted(VISIBLE.glob("*.csv")):
        con.execute(
            f"CREATE OR REPLACE TABLE {{csv.stem}} AS SELECT * FROM read_csv_auto('{{csv.as_posix()}}')"
        )

    mo.md("# Analysis — tables loaded into `con` (duckdb)")
    return con, mo, pd
'''


def _cell_layer(title: str, questions: list[tuple[str, str]], mode: str) -> str:
    fn = "_" + "".join(c for c in title.lower() if c.isalnum())
    md_lines = [f"## {title}"] + [f"- {q}" for q, _ in questions]
    md_literal = repr("\n".join(md_lines))
    body = [
        "@app.cell",
        f"def {fn}(con, mo):",
        f"    mo.md({md_literal})",
    ]
    for _q, sql in (questions if mode == "instructor" else []):
        if sql.strip().startswith("--"):
            body.append(f"    print({sql!r})    # no runnable starter query yet")
        else:
            body.append(f"    con.sql({sql!r}).df()")
    if mode == "student":
        body.append("    # your queries here")
    body.append("    return")
    return "\n".join(body)
