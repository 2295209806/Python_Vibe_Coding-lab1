from sqlalchemy import Column, Integer, Float, String, Date
from database import Base


class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False, comment="金额")
    type = Column(String(10), nullable=False, comment="类型：收入/支出")
    category = Column(String(50), nullable=False, comment="分类")
    date = Column(Date, nullable=False, comment="日期")
