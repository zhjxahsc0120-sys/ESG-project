from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

import pymysql
from pymysql.cursors import DictCursor


MYSQL_CONFIG = {
    "host": os.getenv("LUOYI_MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("LUOYI_MYSQL_PORT", "3307")),
    "user": os.getenv("LUOYI_MYSQL_USER", "luoyi_app"),
    "password": os.getenv("LUOYI_MYSQL_PASSWORD", ""),
    "database": os.getenv("LUOYI_MYSQL_DATABASE", "luoyi_esg"),
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    "autocommit": True,
    "connect_timeout": 3,
    "read_timeout": 10,
    "write_timeout": 10,
}


def mysql_enabled() -> bool:
    return os.getenv("LUOYI_DB_MODE", "mysql").lower() in {"mysql", "auto"}


@contextmanager
def mysql_connect() -> Iterator[pymysql.connections.Connection]:
    conn = pymysql.connect(**MYSQL_CONFIG)
    try:
        yield conn
    finally:
        conn.close()


def mysql_ping() -> dict:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION() AS version, DATABASE() AS database_name")
            row = cur.fetchone()
    return {
        "ok": True,
        "engine": "mysql",
        "host": MYSQL_CONFIG["host"],
        "port": MYSQL_CONFIG["port"],
        "database": row["database_name"],
        "version": row["version"],
    }
