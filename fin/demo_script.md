# 演示脚本

## 项目概述

本演示展示如何从上市公司募集资金公告中自动抽取结构化信息。

**项目目标**：从上市公司公告中抽取募集资金的存放、使用、变更等信息，构建结构化数据集。

**处理流程**：PDF解析 → 章节路由 → 信息抽取 → 质量评估

---

## 演示流程

### 步骤1：PDF解析

**输入**：PDF文件
```
data/pdf/300014_0d32b1f7651539af1c4d612792e8c2c4.pdf
```

**处理**：使用MinerU解析PDF
```python
from src.mineru.parser import PDFParser

parser = PDFParser(primary="mineru")
markdown_text = parser.parse(pdf_path)
```

**输出**：Markdown文件
```
data/markdown/300014_0d32b1f7651539af1c4d612792e8c2c4.md
```

**示例输出**：
```markdown
# 募集资金年度存放与使用情况鉴证报告
惠州亿纬锂能股份有限公司

## 一、募集资金基本情况

### （1）2019年非公开发行股票
经中国证券监督管理委员会出具的《关于核准惠州亿纬锂能股份有限公司非公开发行股票的批复》（证监许可[2019]106号）核准，公司非公开发行人民币普通股（A股）114,995,400股，发行价格为21.74元/股，募集资金总额2,499,999,996.00元，扣除各项发行费用32,750,475.35元后，实际募集资金净额为人民币2,467,249,520.65元。

### （2）2020年向特定对象发行股票
经中国证券监督管理委员会出具的《关于同意惠州亿纬锂能股份有限公司向特定对象发行股票注册的批复》（[2020]1980号文）的同意注册，公司采用增发方式向特定对象发行了人民币普通股（A股）48,440,224股，发行价格为51.61元/股，募集资金总额为人民币2,499,999,960.64元。

## 四、变更募集资金投资项目的资金使用情况
2020年11月10日和2020年11月26日，公司分别召开第五届董事会第十六次会议和2020年第五次临时股东大会审议通过了《关于变更部分募集资金用途的议案》，同意公司将2019年非公开发行募集资金投资项目"荆门亿纬创能储能动力锂离子电池项目"调出募集资金90,000万元用于组建全自动化圆柱三元锂离子电池生产线。
```

---

### 步骤2：章节路由

**输入**：Markdown文本

**处理**：识别目标章节
```python
from src.workflow.section_router import SectionRouter

router = SectionRouter(config_path="configs/section_rules.yaml")
sections = router.route(markdown_text)
```

**输出**：章节列表
```json
[
  {
    "section_type": "basic_info",
    "title": "一、募集资金基本情况",
    "content": "### （1）2019年非公开发行股票...实际募集资金净额为人民币2,467,249,520.65元。"
  },
  {
    "section_type": "change",
    "title": "四、变更募集资金投资项目的资金使用情况",
    "content": "2020年11月10日和2020年11月26日，公司分别召开第五届董事会第十六次会议和2020年第五次临时股东大会审议通过了《关于变更部分募集资金用途的议案》，同意公司将2019年非公开发行募集资金投资项目\"荆门亿纬创能储能动力锂离子电池项目\"调出募集资金90,000万元用于组建全自动化圆柱三元锂离子电池生产线。"
  }
]
```

---

### 步骤3：信息抽取

**输入**：目标章节

**处理**：提取结构化信息
```python
from src.llm.client import LLMClient

client = LLMClient()
prompt = f"""
请从以下文本中提取募集资金变更信息：

{section['content']}

请提取以下字段：
- change_date: 变更日期（董事会决议日期）
- project_name: 原项目名称
- change_amount: 变更金额（万元）
- new_usage: 变更后用途
- board_resolution: 董事会决议情况
- shareholder_approval: 股东大会审议情况
"""

result = client.extract_structured_data(prompt, schema)
```

**输出**：结构化数据
```json
{
  "company_code": "300014",
  "company_name": "亿纬锂能",
  "doc_id": "300014_0d32b1f7651539af1c4d612792e8c2c4",
  "change_date": "2020年11月10日",
  "project_name": "荆门亿纬创能储能动力锂离子电池项目",
  "change_amount": 90000,
  "new_usage": "组建全自动化圆柱三元锂离子电池生产线",
  "board_resolution": "审议通过",
  "shareholder_approval": "2020年第五次临时股东大会审议通过",
  "evidence_text": "2020年11月10日和2020年11月26日，公司分别召开第五届董事会第十六次会议和2020年第五次临时股东大会审议通过了《关于变更部分募集资金用途的议案》，同意公司将2019年非公开发行募集资金投资项目\"荆门亿纬创能储能动力锂离子电池项目\"调出募集资金90,000万元用于组建全自动化圆柱三元锂离子电池生产线。",
  "extraction_confidence": 0.95
}
```

---

### 步骤4：数据校验

**输入**：抽取结果

**处理**：使用Pydantic进行数据校验和文本归一化
```python
from src.llm.schemas import FundChange
from pydantic import ValidationError

try:
    validated = FundChange(**result)
    print(f"校验通过: {validated.dict()}")
except ValidationError as e:
    print(f"校验失败: {e}")
```

**输出**：校验结果
```json
{
  "company_code": "300014",
  "company_name": "亿纬锂能",
  "doc_id": "300014_0d32b1f7651539af1c4d612792e8c2c4",
  "change_date": "2020-11-10",
  "project_name": "荆门亿纬创能储能动力锂离子电池项目",
  "change_amount": 900000000,
  "change_amount_unit": "元",
  "new_usage": "组建全自动化圆柱三元锂离子电池生产线",
  "board_resolution": "passed",
  "shareholder_approval": true,
  "evidence_text": "2020年11月10日和2020年11月26日...",
  "extraction_confidence": 0.95
}
```

---

### 步骤5：质量评估

**输入**：抽取结果

**处理**：验证准确性
```python
from src.evaluation.evaluator import FieldEvaluator

evaluator = FieldEvaluator(ground_truth_path="data/evaluation/ground_truth.jsonl")
metrics = evaluator.evaluate_fields(result, doc_id)
```

**输出**：评估指标
```json
{
  "accuracy": 1.0,
  "field_accuracy": {
    "company_code": 1.0,
    "company_name": 1.0,
    "change_date": 1.0,
    "project_name": 1.0,
    "change_amount": 1.0,
    "board_resolution": 1.0
  },
  "correct": 6,
  "total": 6
}
```

---

## 完整证据链

### 文档信息

| 字段 | 值 |
|------|-----|
| 文档ID | 300014_0d32b1f7651539af1c4d612792e8c2c4 |
| 股票代码 | 300014 |
| 公司名称 | 惠州亿纬锂能股份有限公司 |
| 公告类型 | 募集资金年度存放与使用情况专项报告 |
| 公告日期 | 2025-04-17 |

### 处理结果

| 步骤 | 状态 | 时间 | 置信度 |
|------|------|------|--------|
| PDF解析 | 成功 | 5秒 | 0.95 |
| 章节路由 | 成功 | 2秒 | 0.91 |
| 信息抽取 | 成功 | 3秒 | 0.95 |
| 数据校验 | 成功 | 1秒 | 1.00 |
| 质量评估 | 成功 | 1秒 | 1.00 |

### 最终输出

```csv
doc_id,company_code,company_name,announcement_type,section_type,change_date,project_name,change_amount,new_usage,board_resolution,evidence_text,extraction_confidence
300014_0d32b1f7651539af1c4d612792e8c2c4,300014,亿纬锂能,募集资金年度存放与使用情况专项报告,change,2020-11-10,荆门亿纬创能储能动力锂离子电池项目,900000000,组建全自动化圆柱三元锂离子电池生产线,passed,2020年11月10日和2020年11月26日，公司分别召开第五届董事会第十六次会议和2020年第五次临时股东大会审议通过了《关于变更部分募集资金用途的议案》，同意公司将2019年非公开发行募集资金投资项目"荆门亿纬创能储能动力锂离子电池项目"调出募集资金90,000万元用于组建全自动化圆柱三元锂离子电池生产线。,0.95
```

---

## 运行演示

### 单文档演示

```bash
cd fin
python pipeline_run.py --input data/pdf/300014_0d32b1f7651539af1c4d612792e8c2c4.pdf --demo
```

### 批量处理演示

```bash
cd fin
python pipeline_run.py --mode full --input data/pdf/ --output outputs/results/
```

### 查看运行日志

```bash
tail -f outputs/logs/run_log.jsonl
```

---

## 项目文件结构

```
fin/
├── data/
│   ├── pdf/                    # PDF公告文件
│   ├── markdown/               # 解析后的Markdown文件
│   └── metadata/               # 元数据文件
├── src/
│   ├── mineru/parser.py        # PDF解析模块
│   ├── workflow/section_router.py  # 章节路由模块
│   ├── llm/client.py           # LLM客户端
│   ├── llm/schemas.py          # Pydantic数据模型
│   ├── evaluation/evaluator.py # 评估模块
│   └── config.py               # 配置管理
├── configs/
│   └── section_rules.yaml      # 章节路由规则
├── outputs/
│   ├── logs/                   # 运行日志
│   ├── reports/                # 报告文件
│   └── results/                # 抽取结果
└── pipeline_run.py             # 主运行脚本
```

---

## 支持的公告类型

| 公告类型 | 说明 | 示例 |
|---------|------|------|
| 募集资金年度专项报告 | 年度存放与使用情况 | 亿纬锂能2024年度报告 |
| 募集资金变更公告 | 变更募集资金用途 | 项目变更、地点变更 |
| 募集资金延期公告 | 项目延期 | 原计划日期延期 |
| 募集资金使用进展公告 | 阶段性进展 | 投资进度公告 |

---

## 核心字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| company_code | string | 股票代码 |
| company_name | string | 公司名称 |
| doc_id | string | 文档唯一标识 |
| announcement_type | string | 公告类型 |
| change_date | date | 变更日期 |
| project_name | string | 项目名称 |
| change_amount | int | 变更金额（元） |
| change_amount_unit | string | 金额单位 |
| new_usage | string | 变更后用途 |
| board_resolution | enum | 董事会决议（passed/failed） |
| shareholder_approval | bool | 股东大会是否通过 |
| evidence_text | string | 原始证据文本 |
| extraction_confidence | float | 抽取置信度 |