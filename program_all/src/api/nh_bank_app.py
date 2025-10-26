# -*- coding: utf-8 -*-
"""
NhBank FastAPI App (CRUD + timestamp + UPSERT)
"""
from typing import Optional, List, Union, Literal
from fastapi import FastAPI, HTTPException, Query, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.db.nh_bank.nh_bank_repository import NhBankTxRepository

# ---------- Schemas ----------
class TxIn(BaseModel):
    id: str
    type: str
    name: str
    date: int
    real_date: str
    balanceAfterTransaction: int
    amount: int

class TxPatch(BaseModel):
    type: Optional[str] = None
    name: Optional[str] = None
    date: Optional[int] = None
    real_date: Optional[str] = None
    balanceAfterTransaction: Optional[int] = Field(default=None, alias="balanceAfterTransaction")
    amount: Optional[int] = None

class TxOut(BaseModel):
    id: str
    type: str
    name: str
    date: int
    real_date: str
    balanceAfterTransaction: int
    amount: int

def create_app(repo: NhBankTxRepository, api_key: str) -> FastAPI:
    app = FastAPI(title="NhBank Transactions API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def _auth(x_api_key: Optional[str]):
        if x_api_key != api_key:
            raise HTTPException(status_code=401, detail="Unauthorized")


    @app.get("/nhbank/transactions/by-timestamp", response_model=TxOut)
    def get_transactions_by_timestamp(
            ts: int = Query(..., description="date 필드(unix timestamp, 초 단위)"),
            x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
    ):
        _auth(x_api_key)
        rows = repo.get_by_timestamp(ts)
        if not rows:
            raise HTTPException(status_code=404, detail="No transactions found at given timestamp")
        return rows[0]


    # ★ 전체 조회 API
    @app.get("/nhbank/transactions", response_model=List[TxOut])
    def list_transactions(
            limit: Optional[int] = Query(None, ge=1, le=10000, description="가져올 최대 건수(없으면 전체)"),
            offset: int = Query(0, ge=0, description="페이징 오프셋"),
            order: Literal["asc", "desc"] = Query("desc", description="정렬: asc|desc"),
            x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    ):
        """
        전체 거래내역 조회 (옵션: limit/offset/order).
        기본은 최신순(desc).
        """
        _auth(x_api_key)
        rows = repo.list_all(limit=limit, offset=offset, order=order.upper())
        return rows

    return app
