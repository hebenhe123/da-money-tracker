# AI Worklog

## 项目：上市公司募集资金用途与变更跟踪的结构化抽取与动态分析研究

---

### 任务列表

| 序号 | 任务描述 | 指令类型 |
|------|---------|---------|
| 1 | 完成 crawl_spec.md 抓取规格说明文件，包含股票池、时间范围、公告关键词、公告类型、数据量目标、多公告匹配、限速和失败记录方式 | 文档编写 |
| 2 | 修改 crawl_spec.md，将时间范围扩展到2025年6月，只保留专项报告和年度报告，删除变更公告和临时公告 | 文档修改 |
| 3 | 修改 crawl_spec.md，增加辅助公司（新能源和医药生物行业），目标PDF文件数不少于80份 | 文档修改 |
| 4 | 修改配置文件 max_records 调整为 80-100 份 | 配置修改 |
| 5 | 生成元数据抓取模块 scripts/crawl_metadata.py，读取配置文件生成 metadata.csv | 代码编写 |
| 6 | 生成 PDF 下载模块 src/download_pdfs.py，支持限速、重试、跳过已存在文件 | 代码编写 |
| 7 | 生成数据检查模块 src/check_dataset.py，检查数据集完整性生成报告 | 代码编写 |
| 8 | 在 crawl_metadata.py 中添加抓取数量限制，达到 max_records 停止抓取 | 代码修改 |
| 9 | 修改配置文件 max_records 为 100 | 配置修改 |
| 10 | 修改 crawl_metadata.py 适配巨潮资讯网最新接口，更新 URL、请求参数、返回结构、时间戳处理、PDF 链接拼接 | 代码修改 |
| 11 | 修改 crawl_metadata.py 清理标题 HTML 标签、修正 url 字段、添加分页日志 | 代码修改 |
| 12 | 修改配置文件关键词，将"募投项目"改为"募集资金" | 配置修改 |
| 13 | 更新配置文件，新增5家公司（比亚迪、阳光电源、亿纬锂能、恒瑞医药、迈瑞医疗） | 配置修改 |
| 14 | 删除比亚迪和恒瑞医药两家公司 | 配置修改 |
| 15 | 编写中央总控脚本 pipeline_run.py，实现一键串联数据采集全流程，支持断点续跑、日志记录、命令行参数 | 代码编写 |
| 16 | 修改 pipeline_run.py 修复跳过逻辑、修正模块导入路径、增强无人值守支持 | 代码修改 |
| 17 | 生成 JSON Schema 文件 schemas/basic_info_schema.json，定义基础信息字段 | 文档编写 |
| 18 | 生成 Prompt 模板文件 prompts/basic_info_prompt.yaml，用于大模型抽取基础信息字段 | 文档编写 |
| 19 | 创建 prompts/basic_info_prompt.yaml 文件 | 文件创建 |
| 20 | 编写 filter_samples.py 脚本，从 metadata.csv 中筛选指定的30条记录 | 代码编写 |
| 21 | 创建 data/evaluation/ground_truth.jsonl 文件，包含30条标准答案 | 文件创建 |
| 22 | 编写 evaluate_basic_fields.py 评估脚本，评估基础信息字段抽取准确率 | 代码编写 |
| 23 | 创建 evaluate_basic_fields.py 文件 | 文件创建 |
| 24 | 生成 AI Worklog 文件，记录所有任务指令 | 文档编写 |

---

**生成日期**：2026-06-05
**项目路径**：`c:\Users\Qin Ming\Desktop\aa`