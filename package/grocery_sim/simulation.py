"""GroceryStoreSimulation — the standalone-library entry point.

Wraps the phase1 -> phase2 -> phase3 -> recording -> export pipeline
(originally orchestrated by generate_dataset.py) behind the object interface:

    sim = GroceryStoreSimulation()
    sim.setup(settings)
    sim.simulate()
    sim.data()             # in-memory tables
    sim.db()                # duckdb connection over the same tables
    sim.erd()                # Mermaid ER diagram string
    sim.describe()          # the business-case brief
    sim.settings             # the resolved settings dict (JSON-serializable)
    sim.create_analysis(path=...)
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pandas as pd

from . import events as _events
from . import keys as _keys
from .export import export as _export
from .phase3 import run_year
from .settings import resolve as _resolve_settings
from .validate import validate as _validate
from .world import World


class ValidationError(RuntimeError):
    """Raised by .simulate() when a structural invariant fails — see
    validate.py's module docstring for what "structural" means and why
    only this tier is ever fatal."""


class SimulationData:
    """Attribute-style access to one arm's tables (`sim.data().receipts`),
    plus a compact schema summary as its repr."""

    def __init__(self, tables: dict[str, pd.DataFrame]):
        self._tables = tables
        for name, df in tables.items():
            setattr(self, name, df)

    def __getitem__(self, name: str) -> pd.DataFrame:
        return self._tables[name]

    def __iter__(self):
        return iter(self._tables)

    def keys(self):
        return self._tables.keys()

    def __repr__(self) -> str:
        lines = [f"{'table':<20}{'rows':>10}   columns"]
        for name, df in sorted(self._tables.items()):
            cols = ", ".join(df.columns[:6]) + (", ..." if len(df.columns) > 6 else "")
            lines.append(f"{name:<20}{len(df):>10}   {cols}")
        return "\n".join(lines)


class GroceryStoreSimulation:

    def __init__(self):
        self.settings: dict | None = None
        self.validation: dict | None = None
        self._world = None
        self._base = None
        self._oracle = None
        self._out_dir: Path | None = None
        self._own_tmp = False

    # ------------------------------------------------------------------ setup
    def setup(self, settings: dict | None = None) -> "GroceryStoreSimulation":
        """Validate and resolve `settings` against the schema in settings.py.
        Does not run anything — call .simulate() next."""
        self.settings = _resolve_settings(settings)
        return self

    # --------------------------------------------------------------- simulate
    def simulate(self, out_dir: str | Path | None = None) -> "GroceryStoreSimulation":
        if self.settings is None:
            raise RuntimeError("call .setup(settings) before .simulate()")
        s = self.settings

        # The randomness discipline is a process-global module constant
        # (keys.MASTER_SEED); scope it to this run. Not safe for two
        # differently-seeded simulations running concurrently in one
        # process — sequential use is fine.
        _keys.MASTER_SEED = s["basic"]["random_seed"]

        scenario = _events.compose(
            basic = s["basic"],
            events = s["events"],
            potential_investment = s["potential_investment"],
        )

        print(f"=== simulating: {s['basic']['name']} ===")
        self._world = World(scenario = scenario)
        self._base = run_year(world = self._world, oracle = False)
        self._oracle = run_year(world = self._world, oracle = True)

        if out_dir is None:
            self._out_dir = Path(tempfile.mkdtemp(prefix = "grocery_sim_"))
            self._own_tmp = True
        else:
            self._out_dir = Path(out_dir)
            self._own_tmp = False
        dirt = _export(
            world = self._world,
            base = self._base,
            oracle = self._oracle,
            out = self._out_dir,
        )
        _relabel_dates(
            out_dir = self._out_dir,
            year_shift = int(s["basic"]["year_start"].split("-")[0]) - 2025,
        )

        self.validation = _validate(
            world = self._world,
            base = self._base,
            oracle = self._oracle,
            dirt = dirt,
        )
        if not self.validation["structural_ok"]:
            failed = [c["name"] for c in self.validation["checks"]
                      if c["tier"] == "structural" and not c["pass"]]
            raise ValidationError(
                "structural invariant(s) failed — this is a generator bug, "
                f"not an expected consequence of the settings: {failed}. "
                "See sim.validation for the full report."
            )
        return self

    # -------------------------------------------------------------------- data
    def data(self, include_hidden: bool = False) -> SimulationData:
        self._require_simulated()
        tables = _read_csvs(self._out_dir / "visible")
        if include_hidden:
            tables.update({f"hidden_{k}": v for k, v in _read_csvs(self._out_dir / "hidden").items()})
        return SimulationData(tables)

    # ---------------------------------------------------------------------- db
    def db(
        self,
        path: str | Path | None = None,
        include_hidden: bool = False,
    ):
        """A duckdb connection with every visible table (and, optionally,
        the hidden answer-key tables under a hidden_ prefix) loaded from the
        exported CSVs. `path=None` -> an in-memory database."""
        self._require_simulated()
        import duckdb

        con = duckdb.connect(database = str(path) if path else ":memory:")
        for csv in sorted((self._out_dir / "visible").glob("*.csv")):
            con.execute(
                f"CREATE OR REPLACE TABLE {csv.stem} AS "
                f"SELECT * FROM read_csv_auto(?, all_varchar=false)",
                [str(csv)],
            )
        if include_hidden:
            for csv in sorted((self._out_dir / "hidden").glob("*.csv")):
                con.execute(
                    f"CREATE OR REPLACE TABLE hidden_{csv.stem} AS "
                    f"SELECT * FROM read_csv_auto(?, all_varchar=false)",
                    [str(csv)],
                )
        return con

    # --------------------------------------------------------------------- erd
    def erd(self, include_hidden: bool = False) -> str:
        """A Mermaid `erDiagram` string, built from the hand-declared
        relationships in schema.py (duckdb/CSV tables carry no FK metadata
        of their own to introspect)."""
        self._require_simulated()
        from .schema import mermaid_erd

        tables = self.data(include_hidden = include_hidden)
        columns = {name: list(tables[name].columns) for name in tables.keys()}
        return mermaid_erd(columns = columns)

    # ---------------------------------------------------------------- describe
    def describe(self) -> str:
        self._require_simulated()
        from .describe import build_brief

        text = build_brief(settings = self.settings)
        print(text)
        return text

    # --------------------------------------------------------------- analysis
    def create_analysis(
        self,
        path: str | Path,
        mode: str = "student",
    ) -> Path:
        """Write a marimo notebook (.py, marimo's native format) scaffolded
        around this run's own tables. mode='student' leaves the case
        questions as prompts; mode='instructor' also fills in a worked
        first pass. See analysis.py for exactly what each mode generates —
        this is a scaffold, not a substitute for reviewing the analysis."""
        self._require_simulated()
        from .analysis import write_notebook

        return write_notebook(
            path = Path(path),
            settings = self.settings,
            db_path = self._out_dir / "simulation.duckdb",
            out_dir = self._out_dir,
            mode = mode,
        )

    # ----------------------------------------------------------------- export
    def export_settings(self, path: str | Path) -> None:
        """Dump the resolved settings to JSON for later reuse:
        GroceryStoreSimulation().setup(json.load(open(path)))."""
        Path(path).write_text(json.dumps(self.settings, indent = 2))

    def cleanup(self) -> None:
        """Remove the temp export directory, if simulate() created one
        (out_dir=None). Safe to call even if nothing was ever simulated."""
        if self._own_tmp and self._out_dir and self._out_dir.exists():
            shutil.rmtree(self._out_dir)

    # ------------------------------------------------------------------- misc
    def _require_simulated(self):
        if self._out_dir is None:
            raise RuntimeError("call .simulate() first")


def _read_csvs(folder: Path) -> dict[str, pd.DataFrame]:
    return {csv.stem: pd.read_csv(csv) for csv in sorted(folder.glob("*.csv"))}


_DATE_COL_HINTS = ("date",)


def _relabel_dates(out_dir: Path, year_shift: int) -> None:
    """Shift every date-like column in every exported CSV by `year_shift`
    years, so a run with basic.year_start='2027' shows 2027 dates rather
    than the internal, fixed 2025 epoch. Day-of-week alignment follows the
    *internal* 2025 calendar, not the real target year's — a documented
    simplification (see events.py's module docstring)."""
    if year_shift == 0:
        return
    for csv in list((out_dir / "visible").glob("*.csv")) + list((out_dir / "hidden").glob("*.csv")):
        df = pd.read_csv(csv)
        touched = False
        for col in df.columns:
            if any(h in col.lower() for h in _DATE_COL_HINTS):
                parsed = pd.to_datetime(df[col], errors = "coerce")
                if parsed.notna().any():
                    shifted = parsed + pd.DateOffset(years = year_shift)
                    df[col] = shifted.dt.strftime("%Y-%m-%d").where(parsed.notna(), df[col])
                    touched = True
        if touched:
            df.to_csv(csv, index = False)
