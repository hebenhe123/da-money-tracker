# Workflow Design

## 项目目标

从上市公司募集资金相关公告的PDF文件中，自动识别并抽取与募集资金使用、投资项目变更、项目延期相关的目标章节，为后续LLM结构化信息抽取提供高质量输入数据。

## 总流程图

```
Crawl -> Parse -> Route -> Extract -> Validate -> Aggregate -> Report
```

## 节点表

| 节点 | 输入 | 输出 | 成功标准 | 失败处理 | 日志 |
|------|------|------|----------|----------|------|
| **Crawl** | 巨潮查询接口、股票代码列表 | `data/metadata/metadata.csv` + `data/pdf/*.pdf` | 字段完整（doc_id, company_code, pdf_url等），PDF下载成功 | 记录失败原因，跳过该记录 | 成功/失败数量、耗时 |
| **Parse** | `data/pdf/*.pdf` | `data/markdown/*.md` 或 `data/parsed/parsed_docs_sample.jsonl` | Markdown字符数>100，表格结构完整 | 记录解析失败原因，重试或跳过 | 解析成功/失败数、平均耗时 |
| **Route** | 解析后的Markdown + `configs/section_rules.yaml` | `data/routed/*_sections.json` | 至少识别到一个目标章节 | 标记无目标章节的文档 | 章节识别数、各类型分布 |
| **Extract** | 目标章节文本 + `prompts/prompt_final.md` | `outputs/results/final_results.csv` | 字段完整、evidence_text非空 | 记录抽取失败，标记人工复核 | 抽取成功/失败数、置信度分布 |
| **Validate** | 抽取结果 + Pydantic Schema | `outputs/results/final_results.csv`（校验后） | 数据类型正确、字段格式符合要求 | 记录校验失败原因 | 校验通过/失败数、错误类型分布 |
| **Aggregate** | 校验后的记录 | `outputs/results/final_results.csv` | 汇总数据完整、去重正确 | 记录汇总错误 | 总记录数、去重后数 |
| **Report** | 所有中间结果 | `outputs/reports/eval_report_final.md`, `fin/final_report.md` | 报告生成成功、评估指标完整 | 记录报告生成失败 | 报告路径、生成时间 |

## 人工检查点

| 检查点 | 位置 | 检查内容 | 频率 |
|--------|------|----------|------|
| 数据质量抽查 | Crawl阶段后 | 随机抽查10%的PDF文件完整性 | 每次运行 |
| 章节识别抽查 | Route阶段后 | 随机抽查10%的章节分类正确性 | 每次运行 |
| 抽取质量抽查 | Extract阶段后 | 随机抽查5%的抽取结果与原文比对 | 每次运行 |
| 最终结果审核 | Report阶段前 | 人工审核关键数据准确性 | 最终提交前 |

## 配置文件

- `configs/workflow.yaml` - 工作流步骤配置
- `configs/crawl_config.yaml` - 爬虫配置
- `configs/model_config.yaml` - LLM模型配置
- `configs/section_rules.yaml` - 章节规则配置

## 最小运行命令

```bash
# 完整流程
python pipeline_run.py --config configs/workflow.yaml --step all

# 单独运行某个步骤
python pipeline_run.py --config configs/workflow.yaml --step crawl
python pipeline_run.py --config configs/workflow.yaml --step parse
python pipeline_run.py --config configs/workflow.yaml --step evaluate

# 强制重新执行（跳过产物检查）
python pipeline_run.py --config configs/workflow.yaml --step all --force
```

## 工作流模式说明

### 1. 顺序流水线
```
metadata -> parse -> route -> extract -> validate -> aggregate -> report
```
适合基础项目，每份PDF独立处理。

### 2. 条件分支
```python
if section_found:
    extract_fields()
else:
    mark_for_manual_review()
```
若没有找到目标章节，进入人工复核列表。

### 3. 失败重试
```python
parse_pdf() -> if failed retry 2 times -> log_failure()
```
对不稳定节点进行有限重试（如MinerU API超时）。

### 4. Reviewer-Revise
```python
extract() -> review_schema_and_evidence() -> revise_or_accept()
```
检查evidence_text是否支持抽取结果，必要时修正。

### 5. Human-in-the-loop
```python
route_sections() -> sample_check_by_human() -> update_rules() -> continue()
```
章节路由后人工抽样确认，更新规则后继续。

## 输出文件清单

| 文件路径 | 说明 | 生成阶段 | 实际存在 |
|----------|------|----------|----------|
| `data/metadata/metadata.csv` | 公告元数据 | Crawl | ✅ |
| `data/pdf/*.pdf` | 下载的PDF文件（100个） | Crawl | ✅ |
| `data/markdown/*.md` | 解析后的Markdown文件 | Parse | ❌ (未生成) |
| `data/parsed/parsed_docs_sample.jsonl` | 解析样本JSONL | Parse | ✅ (仅样本) |
| `data/routed/*_sections.json` | 章节路由结果（99个） | Route | ✅ |
| `outputs/reports/dataset_audit.csv` | 数据集审计报告 | Audit | ✅ |
| `outputs/reports/section_check_report.csv` | 章节检查报告 | Route | ✅ |
| `outputs/results/final_results.csv` | 最终汇总结果 | Aggregate | ✅ |
| `outputs/results/Listed_Companies_Fundraising_Analysis.csv` | 结构化分析结果 | Extract | ✅ |
| `outputs/reports/eval_report_final.md` | 评估报告 | Report | ✅ |
| `fin/final_report.md` | 最终报告 | Report | ✅ |
| `outputs/logs/run_log.jsonl` | 运行日志 | 所有阶段 | ✅ |
| `fin/ai_usage_statement.md` | AI使用声明 | 人工撰写 | ✅ |
| `fin/ai_worklog_all.md` | AI工作日志 | 人工撰写 | ✅ |

## 实际项目数据统计

- **PDF文件总数**：100份
- **章节路由成功**：99份
- **有项目信息记录**：18份
- **有变更记录**：19份
- **无项目公告**：87份
- **最终输出行数**：18行

## 样本公司分布

| 股票代码 | 公司名称 | PDF数量 |
|----------|----------|---------|
| 300014 | 亿纬锂能 | 25 |
| 300274 | 阳光电源 | 35 |
| 300750 | 宁德时代 | 18 |
| 300760 | 医学之声 | 4 |
| 601012 | 隆基绿能 | 14 |
| 603259 | 药明康德 | 4 |

## 时间范围

- **数据发布时间**：2024-02-06 至 2025-06-24
- **项目实施时间**：2026年
