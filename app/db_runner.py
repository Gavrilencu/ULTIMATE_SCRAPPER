# -*- coding: utf-8 -*-
import re
from app.models import DatabaseConnection, JobVariable


def get_connection(db_conn: DatabaseConnection):
    if db_conn.db_type == "sqlite":
        import sqlite3
        path = db_conn.extra or db_conn.database or ":memory:"
        return sqlite3.connect(path)
    if db_conn.db_type == "postgres":
        try:
            import psycopg2
        except ImportError:
            raise ValueError("Instalați psycopg2-binary: pip install psycopg2-binary")
        return psycopg2.connect(
            host=db_conn.host,
            port=db_conn.port or 5432,
            dbname=db_conn.database,
            user=db_conn.username,
            password=db_conn.password,
        )
    if db_conn.db_type == "mysql":
        import pymysql
        return pymysql.connect(
            host=db_conn.host,
            port=db_conn.port or 3306,
            database=db_conn.database,
            user=db_conn.username,
            password=db_conn.password,
        )
    if db_conn.db_type == "oracle":
        try:
            import oracledb
        except ImportError:
            raise ValueError("Instalați oracledb: pip install oracledb")
        dsn = db_conn.extra
        if not dsn:
            host = db_conn.host or "localhost"
            port = db_conn.port or 1521
            svc = db_conn.database or "ORCL"
            dsn = f"{host}:{port}/{svc}"
        return oracledb.connect(user=db_conn.username, password=db_conn.password, dsn=dsn)
    raise ValueError(f"Unsupported database type: {db_conn.db_type}")


def format_for_db(value: str, db_type: str, as_date: bool = False) -> str:
    if value is None or value == "":
        return "NULL"
    escaped = value.replace("'", "''")
    if as_date:
        if db_type == "oracle":
            return f"TO_DATE('{escaped}', 'YYYY-MM-DD HH24:MI:SS')"
        if db_type in ("postgres", "mysql"):
            return f"'{escaped}'"
        return f"'{escaped}'"
    return f"'{escaped}'"


def substitute_variables(sql: str, variables: dict) -> str:
    out = sql
    for k, v in variables.items():
        safe = (v or "").replace("'", "''")
        out = re.sub(rf"\{{{k}\}}", safe, out, flags=re.IGNORECASE)
    return out


def run_count_query(conn, sql: str, variables: dict) -> int:
    sql = substitute_variables(sql, variables)
    cur = conn.cursor()
    try:
        cur.execute(sql)
        row = cur.fetchone()
        return int(row[0]) if row else 0
    finally:
        cur.close()


def run_insert(conn, sql: str, variables: dict):
    sql = substitute_variables(sql, variables)
    cur = conn.cursor()
    try:
        cur.execute(sql)
        conn.commit()
    finally:
        cur.close()
