from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import date
from typing import Optional, List


class RecordCreate(BaseModel):
    amount: float = Field(gt=0, description="金额必须大于0")
    type: str = Field(description="类型：收入 或 支出")
    category: str = Field(min_length=1, description="分类不能为空")
    date: date

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in ("收入", "支出"):
            raise ValueError("类型只能是「收入」或「支出」")
        return v


class RecordResponse(BaseModel):
    id: int
    amount: float
    type: str
    category: str
    date: date

    model_config = ConfigDict(from_attributes=True)


class PageResponse(BaseModel):
    total: int
    page: int
    page_size: int
    data: List[RecordResponse]


class SummaryResponse(BaseModel):
    start_date: date
    end_date: date
    total_income: float
    total_expense: float
    balance: float
