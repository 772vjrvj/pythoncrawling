from dataclasses import dataclass
from typing import Optional

@dataclass
class CategoryListModel:
    no: Optional[int]
    pno: int
    cid: str
    category: str
    input_start_page: int
    input_end_page: int
    real_start_page: int
    real_end_page: int
    total_page_cnt: int
    total_product_cnt: int
    now_page_no: int
    now_product_no: int
    completed_yn: str
    update_date: str
    reg_date: str
    deleted_yn: str

    # 컬럼 리스트를 공통화
    COLUMNS = [
        "no", "pno", "cid", "category", "input_start_page", "input_end_page",
        "real_start_page", "real_end_page", "total_page_cnt", "total_product_cnt",
        "now_page_no", "now_product_no", "completed_yn", "update_date", "reg_date", "deleted_yn"
    ]
