import pandas as pd
import os
from typing import Tuple


# 必要关键字段
REQUIRED_COLUMNS = ["日期", "销售员", "产品", "数量", "单价", "地区"]


def generate_report(input_file: str, output_file: str) -> None:
    """
    读取原始销售Excel，完成数据清洗与统计，输出报表文件
    :param input_file: 原始Excel文件路径
    :param output_file: 输出报表文件路径
    """
    # 1. 检查输入文件是否存在
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"错误：输入文件 {input_file} 不存在，请检查路径。")

    # 2. 读取原始文件（只读，不修改原文件）
    try:
        df_raw = pd.read_excel(input_file, engine="openpyxl")
    except Exception as e:
        raise RuntimeError(f"错误：读取输入文件失败，文件可能为空或格式损坏。详情：{str(e)}")

    # 3. 检查必要字段是否完整
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df_raw.columns]
    if missing_cols:
        raise ValueError(f"错误：输入文件缺少必要字段：{', '.join(missing_cols)}")

    # 4. 数据清洗
    # 4.1 删除关键字段缺失的行
    df_clean = df_raw.dropna(subset=REQUIRED_COLUMNS).copy()

    # 4.2 转换数量、单价为数值类型，无法转换的行剔除
    df_clean["数量"] = pd.to_numeric(df_clean["数量"], errors="coerce")
    df_clean["单价"] = pd.to_numeric(df_clean["单价"], errors="coerce")
    df_clean = df_clean.dropna(subset=["数量", "单价"])

    # 4.3 剔除数量 <= 0 的异常行
    df_clean = df_clean[df_clean["数量"] > 0]

    # 4.4 按全字段去重
    df_clean = df_clean.drop_duplicates(subset=REQUIRED_COLUMNS)

    # 5. 检查清洗后是否有有效数据
    if df_clean.empty:
        raise ValueError("错误：数据清洗后无有效数据，请检查原始文件内容。")

    # 6. 计算销售额
    df_clean["销售额"] = df_clean["数量"] * df_clean["单价"]

    # 7. 统计汇总
    # 7.1 按销售员汇总
    sales_by_seller = df_clean.groupby("销售员")["销售额"].sum().reset_index()
    sales_by_seller.columns = ["销售员", "销售额合计"]

    # 7.2 按地区汇总
    sales_by_region = df_clean.groupby("地区")["销售额"].sum().reset_index()
    sales_by_region.columns = ["地区", "销售额合计"]

    # 7.3 总览：月度总额
    total_amount = df_clean["销售额"].sum()
    df_overview = pd.DataFrame({"指标": ["月度销售总额"], "金额": [total_amount]})

    # 8. 写入输出Excel（不影响原始文件）
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df_clean.to_excel(writer, sheet_name="明细清洗后", index=False)
        sales_by_seller.to_excel(writer, sheet_name="按销售员", index=False)
        sales_by_region.to_excel(writer, sheet_name="按地区", index=False)
        df_overview.to_excel(writer, sheet_name="总览", index=False)

    print(f"报表生成成功，已保存至：{output_file}")


if __name__ == "__main__":
    # 默认运行示例
    try:
        generate_report("sample_data/sales_raw.xlsx", "report.xlsx")
    except Exception as e:
        print(e)
