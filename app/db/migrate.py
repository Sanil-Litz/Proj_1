from pathlib import Path

from sqlalchemy import text

from app.db.session import engine


def run_migration() -> None:
    schema_file = Path(__file__).resolve().parents[2] / "sql" / "schema.sql"
    ddl = schema_file.read_text(encoding="utf-8")
    with engine.begin() as conn:
        for statement in [s.strip() for s in ddl.split(";") if s.strip()]:
            conn.execute(text(statement))


if __name__ == "__main__":
    run_migration()
