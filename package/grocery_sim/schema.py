"""A heuristic entity-relationship diagram over one run's exported tables.

There is no declared foreign-key schema anywhere upstream (the tables are
plain CSVs written by export.py) — this module infers likely relationships
from shared "key-like" column names across tables, and picks the table whose
name best matches the key as the "one" side. It is a readable approximation
for orientation, not an enforced schema; treat the diagram as a starting
point for exploring the tables, not a ground truth about referential
integrity.
"""

from __future__ import annotations

# key column -> the table name that most plausibly "owns" that key (its
# primary key); every other table containing the same column is drawn as
# referencing it. Extend this as new tables/columns are added.
_KEY_OWNER = {
    "uid": "price_history",
    "customer_id": "customers",
    "location_id": "locations",
    "category": "category_loadings",
    "receipt_id": "receipts",
}


def mermaid_erd(columns: dict[str, list[str]]) -> str:
    """columns: {table_name: [column names]}. Returns a Mermaid `erDiagram`
    block (renders natively in the artifact/Markdown viewers this project
    already uses)."""
    lines = ["erDiagram"]

    for table, cols in sorted(columns.items()):
        lines.append(f"    {table} {{")
        for col in cols[:12]:
            lines.append(f"        string {col}")
        if len(cols) > 12:
            lines.append(f"        string more_columns_{len(cols) - 12}")
        lines.append("    }")

    for key, owner in _KEY_OWNER.items():
        if owner not in columns:
            continue
        referencing = [t for t, cols in columns.items() if t != owner and key in cols]
        for t in sorted(referencing):
            lines.append(f'    {owner} ||--o{{ {t} : "{key}"')

    return "\n".join(lines)
