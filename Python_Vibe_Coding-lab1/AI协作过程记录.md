# AI协作过程记录
## 考题一：Excel报表生成脚本
### 关键对话摘要
1. **初始框架生成**
   - 指令：写Python脚本读取sales_raw.xlsx，做数据清洗，输出4个sheet的report.xlsx
   - AI输出：基础pandas读写脚本，包含简单去重和分组统计
   - 人工修正：明确关键字段范围，补充数值类型校验，增加异常处理分支

2. **边界能力补强**
   - 指令：增加空文件、缺失字段、全无效数据的报错，全程不能修改原始文件
   - AI输出：补充文件存在性检查和try-except捕获
   - 人工审查：确认所有IO操作仅读取原始文件，写入仅针对输出文件

3. **测试用例生成**
   - 指令：生成pytest用例，覆盖正常场景+至少2个边界异常场景
   - AI输出：基础测试函数框架
   - 人工优化：使用临时文件隔离测试数据，补充统计结果数值断言

### 核心代码变更diff
```diff
- df = pd.read_excel("sales_raw.xlsx")
+ if not os.path.exists(input_file):
+     raise FileNotFoundError(f"错误：输入文件 {input_file} 不存在")
+ try:
+     df_raw = pd.read_excel(input_file, engine="openpyxl")
+ except Exception as e:
+     raise RuntimeError(f"读取文件失败：{str(e)}")

- df = df.drop_duplicates()
+ df_clean = df_raw.dropna(subset=REQUIRED_COLUMNS).copy()
+ df_clean["数量"] = pd.to_numeric(df_clean["数量"], errors="coerce")
+ df_clean = df_clean[df_clean["数量"] > 0]
+ df_clean = df_clean.drop_duplicates(subset=REQUIRED_COLUMNS)
