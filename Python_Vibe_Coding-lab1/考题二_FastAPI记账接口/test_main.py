import pytest
from fastapi.testclient import TestClient
from main import app
from database import Base, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 使用独立测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_accounting.db"
engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


# 每个测试用例自动重置数据库：开始前建表，结束后删表
@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


# 重写数据库依赖，使用测试库会话
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_create_record_success():
    """正常用例：新增流水成功"""
    payload = {
        "amount": 100.5,
        "type": "收入",
        "category": "工资",
        "date": "2024-01-15"
    }
    response = client.post("/records", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 100.5
    assert data["type"] == "收入"
    assert "id" in data


def test_create_invalid_amount():
    """异常用例1：金额<=0"""
    payload = {"amount": -50, "type": "支出", "category": "餐饮", "date": "2024-01-16"}
    response = client.post("/records", json=payload)
    assert response.status_code == 422
    assert "detail" in response.json()


def test_create_invalid_type():
    """异常用例2：类型非法"""
    payload = {"amount": 50, "type": "消费", "category": "餐饮", "date": "2024-01-16"}
    response = client.post("/records", json=payload)
    assert response.status_code == 422
    assert "类型只能是" in str(response.json()["detail"])


def test_create_invalid_date():
    """异常用例3：日期格式错误"""
    payload = {"amount": 50, "type": "支出", "category": "餐饮", "date": "2024/01/16"}
    response = client.post("/records", json=payload)
    assert response.status_code == 422


def test_get_records_filter_page():
    """正常用例：筛选+分页查询"""
    # 插入15条测试数据
    for i in range(15):
        client.post("/records", json={
            "amount": 10 + i,
            "type": "支出" if i % 2 == 0 else "收入",
            "category": "餐饮" if i % 2 == 0 else "工资",
            "date": f"2024-01-{10 + i}"
        })

    # 按类型筛选+分页
    response = client.get("/records?type=支出&page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 8
    assert len(data["data"]) == 5
    assert all(item["type"] == "支出" for item in data["data"])

    # 日期区间筛选
    response = client.get("/records?start_date=2024-01-10&end_date=2024-01-12")
    assert response.status_code == 200
    assert response.json()["total"] == 3


def test_get_records_invalid_type():
    """异常用例：查询参数类型非法"""
    response = client.get("/records?type=错误类型")
    assert response.status_code == 400
    assert "类型参数只能是" in response.json()["detail"]


def test_summary_correct():
    """正常用例：统计汇总计算正确"""
    client.post("/records", json={"amount": 1000, "type": "收入", "category": "工资", "date": "2024-01-10"})
    client.post("/records", json={"amount": 300, "type": "支出", "category": "房租", "date": "2024-01-15"})
    client.post("/records", json={"amount": 200, "type": "支出", "category": "餐饮", "date": "2024-01-20"})
    client.post("/records", json={"amount": 500, "type": "收入", "category": "奖金", "date": "2024-02-01"})

    response = client.get("/summary?start_date=2024-01-01&end_date=2024-01-31")
    assert response.status_code == 200
    data = response.json()
    assert data["total_income"] == 1000
    assert data["total_expense"] == 500
    assert data["balance"] == 500


def test_summary_date_error():
    """异常用例：日期区间颠倒"""
    response = client.get("/summary?start_date=2024-02-01&end_date=2024-01-01")
    assert response.status_code == 400
    assert "开始日期不能晚于结束日期" in response.json()["detail"]
