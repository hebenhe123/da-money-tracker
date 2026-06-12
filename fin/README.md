# 上市公司募集资金用途与变更跟踪的结构化抽取研究

## 项目简介

本项目旨在从上市公司募集资金相关公告的PDF文件中，自动识别并抽取与募集资金使用、投资项目变更、项目延期相关的目标章节，为后续LLM结构化信息抽取提供高质量输入数据。

## 金融问题

上市公司募集资金的使用情况是投资者和监管机构关注的重点信息。传统的人工阅读方式效率低下，难以大规模跟踪分析。本项目通过自动化技术，从巨潮资讯网等公开渠道获取募集资金相关公告，提取关键信息，实现：

- **募集资金使用情况跟踪**：自动识别募投项目的投资进度、资金使用情况
- **项目变更监控**：检测募投项目的变更、延期、终止等状态变化
- **结构化数据抽取**：将非结构化PDF文本转换为可分析的结构化数据

## 数据来源与公告范围

- **数据来源**：巨潮资讯网（www.cninfo.com.cn）
- **公告类型**：
  - 募集资金使用情况专项报告
  - 募投项目变更公告
  - 募投项目延期公告
  - 募集资金存放与使用情况鉴证报告
- **时间范围**：2024-2025年（最早2024-02-06，最晚2025-06-24）
- **样本数量**：100份公告PDF文件
- **股票代码**：
  - 300014（亿纬锂能）- 25份
  - 300274（阳光电源）- 35份
  - 300750（宁德时代）- 18份
  - 300760（迈瑞医疗）- 4份
  - 601012（隆基绿能）- 14份
  - 603259（药明康德）- 4份

## 目录结构

```
C:\Users\Aurora\Desktop\aa\
├── README.md                          # 项目说明文档
├── requirements.txt                   # Python依赖包
├── .env.example                       # 环境变量示例
├── AGENTS.md                          # 成员分工说明
├── summary_report.md                  # 项目总结报告
├── topic_proposal.md                  # 课题提案
├── workflow_design.md                 # 工作流设计
├── ai_usage_statement.md              # AI使用声明
├── ai_worklog_all.md                  # AI工作日志
│
├── configs/                           # 配置文件目录
│   ├── task.yaml                      # 任务配置
│   ├── workflow.yaml                  # 工作流配置
│   ├── crawl_config.yaml              # 爬虫配置
│   ├── model_config.yaml              # 模型配置
│   └── section_rules.yaml             # 章节规则配置
│
├── data/                              # 数据目录
│   ├── metadata/
│   │   └── metadata.csv               # 元数据文件（100条记录）
│   ├── pdf/                           # PDF文件（100份）
│   │   ├── 300014_*.pdf              # 亿纬锂能公告
│   │   ├── 300274_*.pdf              # 阳光电源公告
│   │   ├── 300750_*.pdf              # 宁德时代公告
│   │   ├── 300760_*.pdf              # 医学之声公告
│   │   ├── 601012_*.pdf              # 隆基绿能公告
│   │   └── 603259_*.pdf              # 药明康德公告
│   ├── routed/                        # 章节路由结果（99条）
│   │   └── *_sections.json           # 路由后的章节JSON
│   └── evaluation/                    # 评估数据
│       ├── ground_truth.jsonl         # 真值数据
│       └── sample_list.csv           # 评估样本列表
│
├── prompts/                           # 提示词目录
│   ├── basic_info_prompt.yaml         # 基本信息抽取提示词
│   └── ...                            # 其他提示词文件
│
├── schemas/                           # 数据模型目录
│   └── basic_info_schema.json        # 基本信息抽取Schema
│
├── scripts/                           # 脚本目录
│   └── crawl_metadata.py             # 元数据爬取脚本
│
├── src/                               # 源代码目录
│   ├── cninfo/                        # 巨潮资讯爬虫
│   ├── llm/                           # LLM相关代码
│   │   ├── client.py                 # LLM客户端
│   │   └── schemas.py                # Pydantic数据模型
│   ├── mineru/                        # MinerU解析器
│   ├── workflow/                      # 工作流管理
│   │   └── section_router.py         # 章节路由器
│   └── evaluation/                    # 评估工具
│       └── evaluator.py               # 评估器
│
├── outputs/                           # 输出目录
│   ├── logs/
│   │   ├── validation_errors.jsonl   # 验证错误日志
│   │   └── extract_all.log           # 抽取运行日志
│   ├── reports/
│   │   └── eval_report_final.md      # 评估报告
│   ├── results/
│   │   ├── final_results.jsonl       # 最终抽取结果
│   │   └── final_results_bak.jsonl   # 结果备份
│   ├── Listed_Companies_Fundraising_Analysis.csv  # 结构化分析结果
│   ├── change_type_pie_chart.png      # 变更类型饼图
│   ├── change_reason_bar_chart.png    # 变更原因柱状图
│   └── change_trend_stacked_chart.png # 变更趋势堆积图
│
├── fin/                               # 工作流子目录
│   ├── pipeline_run.py               # 主运行脚本
│   ├── demo_script.md                 # 演示脚本
│   ├── requirements.txt              # Python依赖包
│   ├── .env.example                  # 环境变量示例
│   ├── configs/                      # 配置文件
│   ├── data/                         # 数据目录
│   ├── src/                          # 源代码
│   ├── prompts/                      # 提示词
│   ├── outputs/                      # 输出目录
│   └── ...
│
└── [其他Python脚本文件]                # 辅助脚本
```

## 环境安装方法

### 1. 克隆仓库

```bash
git clone https://github.com/your-username/fund-usage-extraction.git
cd fund-usage-extraction
```

### 2. 创建虚拟环境

```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
copy .env.example .env
# 编辑 .env 文件，填入真实的API密钥
```

## .env.example 变量说明

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `LLM_PROVIDER` | LLM服务提供商 | openai / deepseek / qwen |
| `LLM_BASE_URL` | LLM API基础URL | https://api.siliconflow.cn/v1 |
| `LLM_API_KEY` | LLM API密钥 | sk-xxxxxxxxxxxxxxxx |
| `LLM_MODEL` | 使用的模型名称 | deepseek-ai/DeepSeek-R1 / gpt-4o |
| `MINERU_API_KEY` | MinerU API密钥（可选） | your_mineru_key_here |
| `MINERU_BASE_URL` | MinerU API基础URL | https://openapi.htmlchecker.com/api/v1 |
| `CNINFO_BASE_URL` | 巨潮资讯基础URL | http://www.cninfo.com.cn |
| `MAX_WORKERS` | 最大并发数 | 4 |
| `BATCH_SIZE` | 批处理大小 | 10 |
| `MAX_RECORDS` | 最大处理记录数 | 100 |

## 核心数据目录

| 目录 | 说明 |
|------|------|
| `data/pdf/` | PDF文件存储目录（100份公告） |
| `data/routed/` | 章节路由结果（99条记录） |
| `data/metadata/` | 元数据文件 |
| `outputs/` | 输出结果目录 |

## 输出文件说明

### 主要输出文件

| 文件路径 | 说明 | 格式 |
|----------|------|------|
| `outputs/Listed_Companies_Fundraising_Analysis.csv` | 结构化分析结果 | CSV |
| `outputs/final_results.jsonl` | 最终抽取结果 | JSONL |
| `outputs/reports/eval_report_final.md` | 评估报告 | Markdown |
| `outputs/logs/validation_errors.jsonl` | 验证错误日志 | JSONL |

### Listed_Companies_Fundraising_Analysis.csv 主要字段

- `股票代码`: 股票代码
- `文档ID`: 文档唯一标识
- `是否变更`: 是/否
- `变动具体分类`: 变更类型
- `核心变动原因`: 变更原因
- `政策或环境影响说明`: 环境影响说明
- `大模型抓取证据(原文)`: 原文证据

## 实际数据分析结果

### 处理统计

| 指标 | 数值 |
|------|------|
| **PDF文件总数** | 100 |
| **章节路由成功** | 99 |
| **有项目信息记录** | 18 |
| **有变更记录** | 19 |
| **无项目公告** | 87 |
| **最终输出行数** | 18 |

### 变更类型分布

| 变更类型 | 说明 |
|----------|------|
| 募投项目效益未达预期 | 项目未达到预计效益 |
| 部分闲置资金现金管理 | 闲置资金进行现金管理 |
| 其他类型 | 待扩展 |

### 主要变更原因

- **宏观经济波动/行业周期调整**：受宏观环境、行业周期影响
- **市场环境变化及项目推进调整**：市场需求变化
- **项目效益未达预期**：实际收益低于预期

### 样本公司分布

| 股票代码 | 公司名称 | PDF数量 |
|----------|----------|---------|
| 300014 | 亿纬锂能 | 25 |
| 300274 | 阳光电源 | 35 |
| 300750 | 宁德时代 | 18 |
| 300760 | 医学之声 | 4 |
| 601012 | 隆基绿能 | 14 |
| 603259 | 药明康德 | 4 |

## 主要局限

1. **PDF格式多样性**：不同公司公告的PDF格式差异较大，部分复杂表格解析效果不佳
2. **章节标题不规范**：部分公告章节标题使用非标准表述，导致章节定位失败
3. **LLM幻觉问题**：在信息抽取环节，LLM可能生成不存在的信息
4. **样本覆盖不足**：当前样本主要集中在新能源和医药行业，其他行业覆盖有限
5. **时间成本**：完整流程处理100份文档需要较长时间，大规模应用需优化性能

## 快速开始

### 使用项目已有数据

```bash
# 查看已有分析结果
type outputs\Listed_Companies_Fundraising_Analysis.csv

# 查看抽取结果
type outputs\final_results.jsonl
```

### 运行抽取流程

```bash
cd fin
python pipeline_run.py --mode full
```

### 查看演示脚本

```bash
type fin\demo_script.md
```

## 引用

如果您使用了本项目，请引用：

```bibtex
@software{fund_usage_extraction,
  title={上市公司募集资金用途与变更跟踪的结构化抽取研究},
  author={Your Team},
  year={2026},
  url={https://github.com/your-username/fund-usage-extraction}
}
```

## 许可证

MIT License