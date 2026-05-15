"""Rebuild and seed the local demo SQLite database from scratch.

This script is intended for development recovery after deleting `sql_app.db`.
It:

1. Optionally deletes the existing database file.
2. Regenerates the CPWD guideline seed JSON.
3. Runs Alembic migrations up to head (which includes baseline + guideline seeding).
4. Verifies guideline framework and section-index view data were ingested.
"""

from __future__ import annotations

import argparse
import configparser
import logging
import sqlite3
import subprocess
import sys
from pathlib import Path

LOGGER = logging.getLogger("restore_demo_database")


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_db_path(backend_root: Path) -> Path:
    config = configparser.ConfigParser()
    config.read(backend_root / "alembic.ini")
    db_url = config["alembic"]["sqlalchemy.url"]
    if db_url.startswith("sqlite:///./"):
        return backend_root / db_url.removeprefix("sqlite:///./")
    if db_url.startswith("sqlite:///"):
        return Path(db_url.removeprefix("sqlite:///"))
    if db_url.startswith("sqlite://"):
        raise RuntimeError("Unsupported sqlite URL format for this restore helper")
    raise RuntimeError(f"Unsupported SQLAlchemy URL: {db_url}")


def _run(cmd: list[str], cwd: Path, *, env: dict[str, str] | None = None) -> None:
    LOGGER.info("Running: %s", " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd), check=True, env=env)


def _verify_demo_data(db_path: Path) -> None:
    if not db_path.exists():
        raise RuntimeError(f"Database not found at {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()

        def _count(query: str, params: dict | tuple | None = None) -> int:
            if params is None:
                params = ()
            row = cur.execute(query, params).fetchone()
            return int(row[0]) if row else 0

        has_view = _count(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='view' AND name='v_guideline_section_index'"
        )
        framework_count = _count(
            "SELECT COUNT(*) FROM guideline_frameworks WHERE slug = :slug",
            {"slug": "cpwd-v1"},
        )
        section_count = _count(
            "SELECT COUNT(*) FROM guideline_sections gs "
            "JOIN guideline_frameworks gf ON gf.id = gs.framework_id "
            "WHERE gf.slug = :slug",
            {"slug": "cpwd-v1"},
        )
        catalog_count = _count(
            "SELECT COUNT(*) FROM guideline_catalog_entries gce "
            "JOIN guideline_frameworks gf ON gf.id = gce.framework_id "
            "WHERE gf.slug = :slug",
            {"slug": "cpwd-v1"},
        )
        framework_index_rows = _count(
            "SELECT COUNT(*) FROM v_guideline_section_index WHERE framework_slug = :slug",
            {"slug": "cpwd-v1"},
        )

        LOGGER.info("Verification snapshot:")
        LOGGER.info(" - v_guideline_section_index exists: %s", bool(has_view))
        LOGGER.info(" - CPWD framework rows: %s", framework_count)
        LOGGER.info(" - CPWD sections rows: %s", section_count)
        LOGGER.info(" - CPWD catalog entries: %s", catalog_count)
        LOGGER.info(" - CPWD section-index rows: %s", framework_index_rows)

        if not framework_count:
            raise RuntimeError("cpwd-v1 framework was not ingested")
        if not section_count:
            raise RuntimeError("cpwd-v1 guideline sections were not ingested")
        if not catalog_count:
            raise RuntimeError("cpwd-v1 guideline catalog entries were not ingested")
        if not framework_index_rows or not has_view:
            raise RuntimeError(
                "Guideline section-index view/rows are missing; migration may not have run correctly."
            )

        LOGGER.info("Demo data verification passed.")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rebuild backend SQLite database and ingest seeded demo data."
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not delete an existing database file before migrations.",
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Skip regenerating cpwd_guideline_v1.json before migration.",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip final database verification step.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG logging.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    backend_root = _backend_root()
    db_path = _load_db_path(backend_root)
    alembic_ini = backend_root / "alembic.ini"

    if db_path.exists() and not args.no_clean:
        LOGGER.warning("Removing existing database at %s", db_path)
        db_path.unlink()
    elif db_path.exists():
        LOGGER.warning("Keeping existing database due to --no-clean")

    if not args.skip_seed:
        _run([sys.executable, str(backend_root / "scripts" / "build_cpwd_guideline_seed.py")], cwd=backend_root)

    _run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(alembic_ini),
            "upgrade",
            "head",
        ],
        cwd=backend_root,
    )

    if args.skip_verify:
        return

    _verify_demo_data(db_path)
    LOGGER.info("Restore complete.")


if __name__ == "__main__":
    main()
