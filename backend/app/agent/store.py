"""Report store: in-memory index backed by one JSON file per report (atomic writes)."""

from __future__ import annotations

import logging
import os
import re
import tempfile
import threading
from pathlib import Path

from .report import IncidentReport

log = logging.getLogger(__name__)
_ID = re.compile(r"^rpt_[0-9a-f]{32}$")


class ReportStore:
    def __init__(self, directory: str | Path) -> None:
        self._dir = Path(directory) / "reports"
        self._lock = threading.Lock()

    def _path(self, report_id: str) -> Path:
        if not _ID.match(report_id):
            raise KeyError(report_id)
        return self._dir / f"{report_id}.json"

    def save(self, report: IncidentReport) -> None:
        with self._lock:
            self._dir.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=self._dir, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(report.model_dump_json(indent=2))
                os.replace(tmp, self._path(report.id))
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)

    def get(self, report_id: str) -> IncidentReport | None:
        try:
            path = self._path(report_id)
        except KeyError:
            return None
        if not path.exists():
            return None
        return IncidentReport.model_validate_json(path.read_text(encoding="utf-8"))

    def list(self) -> list[IncidentReport]:
        if not self._dir.exists():
            return []
        out: list[IncidentReport] = []
        for p in self._dir.glob("rpt_*.json"):
            try:
                out.append(IncidentReport.model_validate_json(p.read_text(encoding="utf-8")))
            except Exception:  # noqa: BLE001 - a corrupt file must not break the list
                log.warning("Skipping unreadable report file %s", p.name)
        return sorted(out, key=lambda r: r.created_at, reverse=True)
