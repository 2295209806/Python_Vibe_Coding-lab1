import pytest
import pandas as pd
import os
from sales_report import generate_report, REQUIRED_COLUMNS


def create_test_excel(path, data):
    """创建测试用Excel文件"""
    df = pd.DataFrame(data)
    df.to_excel(path, index=False, engine="openpyxl")


def test_normal_case(tmp_path):
    """测试正常场景：数据清洗+统计结果正确"""
    input_path = tmp_path / "sales_raw.xlsx"
    output_path = tmp_path / "report.xlsx"

    test_data = {
        "日期": ["2024-01-01", "2024-01-02", "2024-01-02", "2024-01-03"],
        "销售员": ["张三", "李四", "李四", "王五"],
        "产品": ["A", "B", "B", "C"],
        "数量": [10, 5, 5, -2],
        "单价": [100, 200, 200, 50],
        "地区": ["华北", "华东", "华东", "华南"]
    }
    create_test_excel(input_path, test_data)

    generate_report(str(input_path), str(output_path))

    # 验证输出文件存在
    assert os.path.exists(output_path)

    # 读取各sheet校验
    with pd.ExcelFile(output_path, engine="openpyxl") as xls:
        # 明细：去重+剔除负数量，剩余2行
        df_detail = pd.read_excel(xls, sheet_name="明细清洗后")
        assert len(df_detail) == 2
        assert "销售额" in df_detail.columns
        assert list(df_detail["销售额"]) == [1000, 1000]

        # 按销售员汇总
        df_seller = pd.read_excel(xls, sheet_name="按销售员")
        seller_sum = dict(zip(df_seller["销售员"], df_seller["销售额合计"]))
        assert seller_sum["张三"] == 1000
        assert seller_sum["李四"] == 1000

        # 按地区汇总
        df_region = pd.read_excel(xls, sheet_name="按地区")
        region_sum = dict(zip(df_region["地区"], df_region["销售额合计"]))
        assert region_sum["华北"] == 1000
        assert region_sum["华东"] == 1000

        # 总览
        df_overview = pd.read_excel(xls, sheet_name="总览")
        assert df_overview.loc[0, "金额"] == 2000


def test_file_not_exist(tmp_path):
    """边界用例1：输入文件不存在"""
    input_path = tmp_path / "not_exist.xlsx"
    output_path = tmp_path / "report.xlsx"

    with pytest.raises(FileNotFoundError) as exc_info:
        generate_report(str(input_path), str(output_path))
    assert "不存在" in str(exc_info.value)


def test_missing_columns(tmp_path):
    """边界用例2：缺少必要字段"""
    input_path = tmp_path / "bad_cols.xlsx"
    output_path = tmp_path / "report.xlsx"

    bad_data = {
        "日期": ["2024-01-01"],
        "销售员": ["张三"],
        "产品": ["A"],
        "数量": [10],
        "单价": [100]
    }
    create_test_excel(input_path, bad_data)

    with pytest.raises(ValueError) as exc_info:
        generate_report(str(input_path), str(output_path))
    assert "缺少必要字段" in str(exc_info.value)
    assert "地区" in str(exc_info.value)


def test_empty_after_clean(tmp_path):
    """边界用例3：清洗后无有效数据"""
    input_path = tmp_path / "all_invalid.xlsx"
    output_path = tmp_path / "report.xlsx"

    invalid_data = {
        "日期": ["2024-01-01", "2024-01-02"],
        "销售员": ["张三", "李四"],
        "产品": ["A", "B"],
        "数量": [0, -5],
        "单价": [100, 200],
        "地区": ["华北", "华东"]
    }
    create_test_excel(input_path, invalid_data)

    with pytest.raises(ValueError) as exc_info:
        generate_report(str(input_path), str(output_path))
    assert "无有效数据" in str(exc_info.value)


def test_empty_file(tmp_path):
    """边界用例4：空文件/损坏文件"""
    input_path = tmp_path / "empty.xlsx"
    output_path = tmp_path / "report.xlsx"

    with open(input_path, "wb") as f:
        f.write(b"")

    with pytest.raises(RuntimeError) as exc_info:
        generate_report(str(input_path), str(output_path))
    assert "读取输入文件失败" in str(exc_info.value)
