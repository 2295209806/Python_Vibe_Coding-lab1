from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Record
from schemas import PageResponse, RecordCreate, RecordResponse, SummaryResponse


# 启动时自动创建数据表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="记账接口", description="简易记账HTTP服务")


# 1. 新增流水
@app.post("/records", response_model=RecordResponse, status_code=201)
def create_record(record: RecordCreate, db: Session = Depends(get_db)):
    db_record = Record(
        amount=record.amount,
        type=record.type,
        category=record.category,
        date=record.date,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


# 2. 查询流水（筛选+分页）
@app.get("/records", response_model=PageResponse)
def get_records(
    type: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(default=1, ge=1, description="页码，从1开始"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页数量，1-100"),
    db: Session = Depends(get_db),
):
    if type and type not in ("收入", "支出"):
        raise HTTPException(
            status_code=400,
            detail="类型参数只能是「收入」或「支出」",
        )

    query = db.query(Record)

    # 动态条件筛选
    if type:
        query = query.filter(Record.type == type)
    if category:
        query = query.filter(Record.category == category)
    if start_date:
        query = query.filter(Record.date >= start_date)
    if end_date:
        query = query.filter(Record.date <= end_date)

    # 总数统计
    total = query.count()

    # 分页查询
    offset = (page - 1) * page_size
    records = query.offset(offset).limit(page_size).all()

    return PageResponse(
        total=total,
        page=page,
        page_size=page_size,
        data=records,
    )


# 3. 统计汇总
@app.get("/summary", response_model=SummaryResponse)
def get_summary(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    db: Session = Depends(get_db),
):
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")

    # 收入合计
    total_income = (
        db.query(func.sum(Record.amount))
        .filter(
            Record.type == "收入",
            Record.date >= start_date,
            Record.date <= end_date,
        )
        .scalar()
        or 0.0
    )

    # 支出合计
    total_expense = (
        db.query(func.sum(Record.amount))
        .filter(
            Record.type == "支出",
            Record.date >= start_date,
            Record.date <= end_date,
        )
        .scalar()
        or 0.0
    )

    balance = total_income - total_expense

    return SummaryResponse(
        start_date=start_date,
        end_date=end_date,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
