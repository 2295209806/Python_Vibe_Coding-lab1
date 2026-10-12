import pandas as pd
import os

if __name__ == "__main__":
    # 生成包含脏数据的示例原始文件
    data = {
        "日期": ["2024-01-05", "2024-01-06", "2024-01-06", "2024-01-07", "2024-01-08", None, "2024-01-10"],
        "销售员": ["张三", "李四", "李四", "王五", "赵六", "孙七", "周八"],
        "产品": ["笔记本电脑", "鼠标", "鼠标", "键盘", "显示器", "耳机", "笔记本电脑"],
        "数量": [2, 10, 10, -3, 5, 8, 1],
        "单价": [5000, 80, 80, 150, 1200, 200, 4800],
        "地区": ["北京", "上海", "上海", "广州", "深圳", "杭州", "北京"]
    }

    os.makedirs("sample_data", exist_ok=True)
    df = pd.DataFrame(data)
    df.to_excel("sample_data/sales_raw.xlsx", index=False, engine="openpyxl")
    print("示例数据已生成：sample_data/sales_raw.xlsx")
