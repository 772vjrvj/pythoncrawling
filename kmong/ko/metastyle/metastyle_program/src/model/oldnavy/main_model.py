from dataclasses import dataclass
from typing import Optional

@dataclass
class MainModel:
    no: Optional[int]  # PRIMARY KEY AUTOINCREMENT
    now_category: str
    now_page_no: int
    now_product_no: int
    total_page_cnt: int
    total_product_cnt: int
    completed_yn: str
    update_date: str
    reg_date: str
    deleted_yn: str

    # DAO에서 사용할 공통 컬럼 리스트
    COLUMNS = [
        "no", "now_category", "now_page_no", "now_product_no",
        "total_page_cnt", "total_product_cnt", "completed_yn",
        "update_date", "reg_date", "deleted_yn"
    ]
