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
- **时间范围**：2020-2024年
- **样本数量**：100份公告PDF文件
- **股票代码**：300014（亿纬锂能）、300274（阳光电源）、300750（宁德时代）、601012（隆基绿能）、603259（药明康德）等

## 目录结构

```
public_repo/
├── README.md                          # 项目说明文档
├── requirements.txt                   # Python依赖包
├── .env.example                       # 环境变量示例
├── AGENTS.md                          # 成员分工说明
├── configs/                           # 配置文件目录
│   ├── task.yaml                      # 任务配置
│   ├── workflow.yaml                  # 工作流配置
│   ├── crawl_config.yaml              # 爬虫配置
│   ├── model_config.yaml              # 模型配置
│   └── section_rules.yaml             # 章节规则配置
├── data/                              # 数据目录
│   ├── metadata/
│   │   └── metadata.csv               # 元数据文件
│   └── parsed/
│       └── parsed_docs_sample.jsonl   # 解析样本数据
├── prompts/                           # 提示词目录
│   ├── prompt_v1.md                   # 初始版本提示词
│   └── prompt_final.md                # 最终版本提示词
├── src/                               # 源代码目录
│   ├── cninfo/                        # 巨潮资讯爬虫
│   ├── llm/                           # LLM相关代码
│   ├── mineru/                        # MinerU解析器
│   ├── workflow/                      # 工作流管理
│   └── evaluation/                    # 评估工具
├── outputs/                           # 输出目录
│   ├── logs/
│   │   └── sample_run_log.jsonl       # 运行日志
│   ├── results/
│   │   └── final_results.csv          # 最终结果
│   └── reports/
│       └── eval_report_final.md       # 评估报告
├── tests/                             # 测试目录
├── pipeline_run.py                    # 主运行脚本
├── final_report.md                    # 最终报告
├── demo_script.md                     # 演示脚本
├── final_slides.pdf                   # 演示幻灯片
├── ai_usage_statement.md              # AI使用声明
└── ai_worklog_all.md                  # AI工作日志
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
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入真实的API密钥
```

## .env.example 变量说明

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `LLM_PROVIDER` | LLM服务提供商 | openai / deepseek / qwen |
| `LLM_BASE_URL` | LLM API基础URL | https://api.openai.com/v1 |
| `LLM_API_KEY` | LLM API密钥 | sk-xxxxxxxxxxxxxxxx |
| `LLM_MODEL` | 使用的模型名称 | gpt-4o / deepseek-chat |
| `MINERU_API_KEY` | MinerU API密钥（可选） | your_mineru_key_here |

## 最小运行命令

### 完整流程运行

```bash
python pipeline_run.py --mode full
```

### 单步运行

```bash
# 1. 仅解析PDF
python pipeline_run.py --mode parse

# 2. 仅章节路由
python pipeline_run.py --mode route

# 3. 仅信息抽取
python pipeline_run.py --mode extract
```

### 指定文件运行

```bash
python pipeline_run.py --input data/pdf/sample.pdf --output outputs/results/
```

## 输出文件说明

### 主要输出文件

| 文件路径 | 说明 | 格式 |
|----------|------|------|
| `outputs/results/final_results.csv` | 最终结构化结果 | CSV |
| `outputs/reports/eval_report_final.md` | 评估报告 | Markdown |
| `outputs/logs/sample_run_log.jsonl` | 运行日志 | JSONL |
| `data/parsed/parsed_docs_sample.jsonl` | 解析样本数据 | JSONL |

### 输出字段说明

**final_results.csv** 主要字段：

- `doc_id`: 文档唯一标识
- `company_code`: 股票代码
- `company_name`: 公司名称
- `announcement_type`: 公告类型
- `section_type`: 章节类型
- `project_name`: 项目名称
- `investment_amount`: 投资金额
- `progress`: 投资进度
- `change_reason`: 变更原因
- `evidence`: 证据文本片段
- `extraction_confidence`: 抽取置信度

## 评估结果摘要

### 整体性能

| 指标 | 数值 |
|------|------|
| **文档总数** | 100 |
| **目标文档数** | 99 |
| **Section Router成功率** | 99% |
| **章节提取准确率** | 95% |
| **字段抽取准确率** | 88% |

### 章节分类统计

| 章节类型 | 数量 | 占比 |
|----------|------|------|
| basic_info | 64 | 64.6% |
| usage | 43 | 43.4% |
| change | 12 | 12.1% |
| delay | 8 | 8.1% |
| termination | 3 | 3.0% |

### 错误分类

| 错误类型 | 数量 | 占比 |
|----------|------|------|
| 章节定位错误 | 3 | 3.0% |
| 字段抽取错误 | 8 | 8.1% |
| 格式解析错误 | 1 | 1.0% |

## 主要局限

1. **PDF格式多样性**：不同公司公告的PDF格式差异较大，部分复杂表格解析效果不佳
2. **章节标题不规范**：部分公告章节标题使用非标准表述，导致章节定位失败
3. **LLM幻觉问题**：在信息抽取环节，LLM可能生成不存在的信息
4. **样本覆盖不足**：当前样本主要集中在新能源行业，其他行业覆盖有限
5. **时间成本**：完整流程处理100份文档约需2-3小时，大规模应用需优化性能

## 快速开始

### 演示单个文档处理

```bash
# 使用示例PDF进行演示
python pipeline_run.py --input data/pdf/300014_sample.pdf --demo
```

### 查看演示脚本

```bash
cat demo_script.md
```

### 运行测试

```bash
python -m pytest tests/
```

## 引用

如果您使用了本项目，请引用：

```bibtex
@software{fund_usage_extraction,
  title={上市公司募集资金用途与变更跟踪的结构化抽取研究},
  author={Your Team},
  year={2024},
  url={https://github.com/your-username/fund-usage-extraction}
}
```

## 许可证

MIT License

