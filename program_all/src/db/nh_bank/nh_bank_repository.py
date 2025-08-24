# -*- coding: utf-8 -*-
"""
NhBank SQLite Repository (CRUD + timestamp + UPSERT)
"""
import os
import sqlite3
import threading
from typing import Iterable, Optional, List, Dict, Any

_DIR = os.path.dirname(__file__)
_DB_DIR = os.path.join(_DIR, "data")
os.makedirs(_DB_DIR, exist_ok=True)

DB_PATH = os.path.join(_DB_DIR, "nh_bank.db")

_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS NH_BANK (
    id TEXT PRIMARY KEY,                          -- {in|ex}_{branchId}_{timestamp}
    type TEXT NOT NULL,                           -- '입금' | '출금'
    name TEXT NOT NULL,                           -- 거래기록사항
    date INTEGER NOT NULL,                        -- unix timestamp (sec)
    real_date TEXT NOT NULL,                      -- "YYYY-MM-DD HH:mm:ss"
    balance_after INTEGER NOT NULL,               -- 잔액
    amount INTEGER NOT NULL,                      -- 거래금액
    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

CREATE INDEX IF NOT EXISTS idx_tx_date ON NH_BANK(date);
CREATE INDEX IF NOT EXISTS idx_tx_type ON NH_BANK(type);
CREATE INDEX IF NOT EXISTS idx_tx_name ON NH_BANK(name);
"""

class NhBankTxRepository:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        with self._lock, self._conn:
            self._conn.executescript(_SCHEMA)

    def upsert_many(self, txs: Iterable[Dict[str, Any]]) -> int:
        q = """
        INSERT INTO NH_BANK (id, type, name, date, real_date, balance_after, amount, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, strftime('%s','now'), strftime('%s','now'))
        ON CONFLICT(id) DO UPDATE SET
            type          = excluded.type,
            name          = excluded.name,
            date          = excluded.date,
            real_date     = excluded.real_date,
            balance_after = excluded.balance_after,
            amount        = excluded.amount,
            updated_at    = strftime('%s','now');
        """
        rows = [
            (
                t["id"], t["type"], t["name"], int(t["date"]), t["real_date"],
                int(t["balanceAfterTransaction"]), int(t["amount"])
            )
            for t in txs
        ]
        if not rows:
            return 0
        with self._lock, self._conn:
            cur = self._conn.executemany(q, rows)
            return cur.rowcount


    def get_by_timestamp(self, ts: int) -> List[Dict[str, Any]]:
        """
        특정 date 타임스탬프(ts)와 정확히 일치하는 거래내역 반환.
        여러 건이 있을 수 있으므로 List[Dict] 로 리턴.
        """
        sql = """SELECT id, type, name, date, real_date,
                        balance_after AS balanceAfterTransaction, amount
                 FROM NH_BANK
                 WHERE date = ?"""
        with self._lock, self._conn:
            cur = self._conn.execute(sql, (int(ts),))
            return [dict(r) for r in cur.fetchall()]


    def list_all(
            self,
            limit: Optional[int] = None,
            offset: int = 0,
            order: str = "DESC",
    ) -> List[Dict[str, Any]]:
        """
        전체 거래내역 조회 (옵션: limit/offset/pagination, 정렬)
        order: "ASC" | "DESC"
        """
        order_norm = "DESC" if str(order).upper() != "ASC" else "ASC"

        base_sql = """SELECT id, type, name, date, real_date,
                             balance_after AS balanceAfterTransaction, amount
                      FROM NH_BANK
                      ORDER BY date {}""".format(order_norm)

        with self._lock, self._conn:
            if limit is None:
                cur = self._conn.execute(base_sql)
            else:
                cur = self._conn.execute(base_sql + " LIMIT ? OFFSET ?", (int(limit), int(offset)))
            return [dict(r) for r in cur.fetchall()]



    def close(self):
        with self._lock:
            self._conn.close()
