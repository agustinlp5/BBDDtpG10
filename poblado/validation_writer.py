from __future__ import annotations

from datetime import date
from pathlib import Path


DEFAULT_TEMPLATE_PATH = Path("templates/validaciones_populado.sql.tpl")


def write_validations_sql(
    output_path: Path,
    reference_date: date,
    template_path: Path = DEFAULT_TEMPLATE_PATH,
) -> None:
    """Renderiza el SQL de validaciones usando la fecha lógica de referencia."""
    template = template_path.read_text(encoding="utf-8")
    rendered = template.format(reference_date=reference_date.isoformat())
    output_path.write_text(rendered, encoding="utf-8")
