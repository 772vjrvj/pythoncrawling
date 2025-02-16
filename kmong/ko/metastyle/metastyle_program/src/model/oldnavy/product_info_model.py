from dataclasses import dataclass
from typing import Optional

@dataclass
class ProductInfoModel:
    no: Optional[int]
    pno: int
    cid: str
    category: str
    pid: str
    product: str
    description: str
    page_no: int
    product_no: int
    img_list: str
    success_yn: str
    main_url: str
    detail_url: str
    error_message: Optional[str]
    reg_date: str
    deleted_yn: str

    # DAO에서 사용할 공통 컬럼 리스트
    COLUMNS = [
        "no", "pno", "cid", "category", "pid", "product", "description", "page_no",
        "product_no", "img_list", "success_yn", "main_url", "detail_url",
        "error_message", "reg_date", "deleted_yn"
    ]
