from sqlalchemy import create_engine, text
from typing import Dict, List, Any


def extract_schema_postgresql(connection_string: str) -> str:
    """
    Connects to a PostgreSQL database and extracts
    all tables, columns, types and foreign keys.
    Returns a formatted DDL-like string.
    """
    engine = create_engine(connection_string)

    schema_parts = []

    with engine.connect() as conn:
        # Get all user-created tables
        # We exclude system tables by filtering out pg_catalog and information_schema
        tables_query = text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = conn.execute(tables_query).fetchall()

        for table_row in tables:
            table_name = table_row[0]
            table_ddl = f"CREATE TABLE {table_name} (\n"
            columns = []

            # Get all columns for this table
            columns_query = text("""
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = :table_name
                ORDER BY ordinal_position
            """)
            col_rows = conn.execute(
                columns_query,
                {"table_name": table_name}
            ).fetchall()

            for col in col_rows:
                col_name = col[0]
                col_type = col[1].upper()
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                columns.append(f"    {col_name} {col_type} {nullable}")

            # Get foreign keys for this table
            fk_query = text("""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table,
                    ccu.column_name AS foreign_column
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = :table_name
            """)
            fk_rows = conn.execute(
                fk_query,
                {"table_name": table_name}
            ).fetchall()

            for fk in fk_rows:
                columns.append(
                    f"    FOREIGN KEY ({fk[0]}) "
                    f"REFERENCES {fk[1]}({fk[2]})"
                )

            table_ddl += ",\n".join(columns)
            table_ddl += "\n);"
            schema_parts.append(table_ddl)

    engine.dispose()
    return "\n\n".join(schema_parts)


def extract_schema_mysql(connection_string: str) -> str:
    """
    Connects to a MySQL database and extracts schema.
    MySQL uses the same INFORMATION_SCHEMA standard
    but with slightly different query structure.
    """
    engine = create_engine(connection_string)
    schema_parts = []

    with engine.connect() as conn:
        # Get database name from connection
        db_name_result = conn.execute(text("SELECT DATABASE()")).fetchone()
        db_name = db_name_result[0]

        # Get all tables
        tables_query = text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :db_name
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = conn.execute(
            tables_query,
            {"db_name": db_name}
        ).fetchall()

        for table_row in tables:
            table_name = table_row[0]
            table_ddl = f"CREATE TABLE {table_name} (\n"
            columns = []

            columns_query = text("""
                SELECT
                    column_name,
                    column_type,
                    is_nullable
                FROM information_schema.columns
                WHERE table_schema = :db_name
                AND table_name = :table_name
                ORDER BY ordinal_position
            """)
            col_rows = conn.execute(
                columns_query,
                {"db_name": db_name, "table_name": table_name}
            ).fetchall()

            for col in col_rows:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                columns.append(f"    {col[0]} {col[1].upper()} {nullable}")

            table_ddl += ",\n".join(columns)
            table_ddl += "\n);"
            schema_parts.append(table_ddl)

    engine.dispose()
    return "\n\n".join(schema_parts)


def extract_schema_sqlite(connection_string: str) -> str:
    """
    Connects to a SQLite database and extracts schema.
    SQLite does not have INFORMATION_SCHEMA — it has
    its own system table called sqlite_master instead.
    """
    engine = create_engine(connection_string)
    schema_parts = []

    with engine.connect() as conn:
        # SQLite stores CREATE TABLE statements directly
        # in the sqlite_master table — we just read them out
        tables_query = text("""
            SELECT name, sql
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = conn.execute(tables_query).fetchall()

        for table_row in tables:
            if table_row[1]:  # sql can be None for virtual tables
                schema_parts.append(table_row[1] + ";")

    engine.dispose()
    return "\n\n".join(schema_parts)


def extract_schema(platform: str, connection_string: str) -> str:
    """
    Main entry point — routes to the correct extractor
    based on the database platform.
    """
    extractors = {
        "postgresql": extract_schema_postgresql,
        "mysql": extract_schema_mysql,
        "sqlite": extract_schema_sqlite,
    }

    extractor = extractors.get(platform.lower())

    if not extractor:
        raise ValueError(
            f"Platform '{platform}' is not supported. "
            f"Supported platforms: {list(extractors.keys())}"
        )

    return extractor(connection_string)