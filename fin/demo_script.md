# 演示脚本

## 项目概述

本演示展示如何从上市公司募集资金公告中自动抽取结构化信息。

## 演示流程

### 步骤1：PDF解析

**输入**：PDF文件
```
data/pdf/300014_0d32b1f7651539af1c4d612792e8c2c4.pdf
```

**处理**：使用MinerU解析PDF
```python
from src.mineru.parser import PDFParser

parser = PDFParser()
markdown_text = parser.parse(pdf_path)
```

**输出**：Markdown文件
```
data/markdown/300014_0d32b1f7651539af1c4d612792e8c2c4.md
```

**示例输出**：
```markdown
# 亿纬锂能关于部分募投项目延期的公告

## 一、募集资金投资项目延期情况

公司"年产10GWh动力储能电池建设项目"原计划达到预定可使用状态日期为2024年3月31日，现延期至2024年12月31日。

延期原因：受宏观经济环境影响，下游需求增速放缓，公司根据市场情况调整了项目建设进度。
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
    "section_type": "delay",
    "title": "一、募集资金投资项目延期情况",
    "content": "公司\"年产10GWh动力储能电池建设项目\"原计划达到预定可使用状态日期为2024年3月31日，现延期至2024年12月31日。延期原因：受宏观经济环境影响，下游需求增速放缓，公司根据市场情况调整了项目建设进度。"
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
请从以下文本中提取募投项目延期信息：

{section['content']}

请提取以下字段：
- project_name: 项目名称
- original_date: 原计划日期
- new_date: 延期后日期
- delay_reason: 延期原因
"""

result = client.extract_structured_data(prompt, schema)
```

**输出**：结构化数据
```json
{
  "project_name": "年产10GWh动力储能电池建设项目",
  "original_date": "2024年3月31日",
  "new_date": "2024年12月31日",
  "delay_reason": "受宏观经济环境影响，下游需求增速放缓，公司根据市场情况调整了项目建设进度",
  "evidence": "公司\"年产10GWh动力储能电池建设项目\"原计划达到预定可使用状态日期为2024年3月31日，现延期至2024年12月31日。延期原因：受宏观经济环境影响，下游需求增速放缓，公司根据市场情况调整了项目建设进度。"
}
```

---

### 步骤4：质量评估

**输入**：抽取结果

**处理**：验证准确性
```python
from src.evaluation.evaluator import FieldEvaluator

evaluator = FieldEvaluator(ground_truth_path="tests/ground_truth.json")
metrics = evaluator.evaluate_fields(result, doc_id)
```

**输出**：评估指标
```json
{
  "accuracy": 1.0,
  "field_accuracy": {
    "project_name": 1.0,
    "original_date": 1.0,
    "new_date": 1.0,
    "delay_reason": 1.0
  },
  "correct": 4,
  "total": 4
}
```

---

## 完整证据链

### 文档信息

| 字段 | 值 |
|------|-----|
| 文档ID | 300014_0d32b1f7651539af1c4d612792e8c2c4 |
| 股票代码 | 300014 |
| 公司名称 | 亿纬锂能 |
| 公告类型 | 募投项目延期公告 |
| 公告日期 | 2024-03-15 |

### 处理结果

| 步骤 | 状态 | 时间 | 置信度 |
|------|------|------|--------|
| PDF解析 | 成功 | 5秒 | 0.95 |
| 章节路由 | 成功 | 2秒 | 0.91 |
| 信息抽取 | 成功 | 3秒 | 0.88 |
| 质量评估 | 成功 | 1秒 | 1.00 |

### 最终输出

```csv
doc_id,company_code,company_name,announcement_type,section_type,project_name,original_date,new_date,delay_reason,evidence,extraction_confidence
300014_0d32b1f7651539af1c4d612792e8c2c4,300014,亿纬锂能,募投项目延期公告,delay,年产10GWh动力储能电池建设项目,2024年3月31日,2024年12月31日,受宏观经济环境影响，下游需求增速放缓，公司根据市场情况调整了项目建设进度,公司"年产10GWh动力储能电池建设项目"原计划达到预定可使用状态日期为2024年3月31日，现延期至2024年12月31日。延期原因：受宏观经济环境影响，下游需求增速放缓，公司根据市场情况调整了项目建设进度。,0.88
```

---

## 运行演示

### 单文档演示

```bash
python pipeline_run.py --input data/pdf/300014_0d32b1f7651539af1c4d612792e8c2c4.pdf --demo
```

### 批量处理演示

```bash
python pipeline_run.py --mode full --input data/pdf/ --output outputs/results/
```

---
