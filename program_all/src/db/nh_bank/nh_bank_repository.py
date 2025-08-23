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

DB_PATH = os.path.join(_DB_DIR, "nh_bank_transactions.db")

_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS transactions (
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

CREATE INDEX IF NOT EXISTS idx_tx_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_tx_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_tx_name ON transactions(name);
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
        INSERT INTO transactions (id, type, name, date, real_date, balance_after, amount, created_at, updated_at)
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
                 FROM transactions
                 WHERE date = ?"""
        with self._lock, self._conn:
            cur = self._conn.execute(sql, (int(ts),))
            return [dict(r) for r in cur.fetchall()]


    def close(self):
        with self._lock:
            self._conn.close()
