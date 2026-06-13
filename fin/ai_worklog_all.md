# AI Worklog

## 秦艺嘉：ai_worklog

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

---

## 朱怡诺

## 项目目标
从上市公司募集资金相关公告的PDF文件中，自动识别并抽取与募集资金使用、投资项目变更、项目延期相关的目标章节，为后续LLM结构化信息抽取提供高质量输入数据。

---

# AI Usage Log

| 序号 | 任务描述 | 指令类型 |
|------|---------|---------|
| 1 | 修改 `pipeline_run.py`，添加环境变量加载、绝对路径处理，实现 `try_mineru_parse()` 和 `try_pdfplumber_parse()` 函数 | 代码修改 |
| 2 | 修改 `section_router.py`，添加Scorer类、`clean_title()` 函数、`deduplicate_and_merge_sections()` 函数，调整 `section_rules.yaml` 配置 | 代码修改 |
| 3 | 重新编写 `section_router.py`，支持Markdown标题识别、正文关键词辅助分类、contract类型、空文件跳过、重复内容去重、命令行参数 | 代码编写 |
| 4 | 修改 `save_sections_to_json()` 函数输出dict结构，添加CLI参数 `-o`，新增 `build_extraction_tasks()` 函数 | 代码修改 |
| 5 | 修改classify_document_type函数，新增排除关键词检查，扩展section_router.py关键词配置，修复文档标题过滤规则 | 代码修改 |
| 6 | 运行section_router.py批量处理所有文档，扩展关键词配置，修复"的"字差异匹配问题，生成parse_quality_check.csv质量检查报告 | 代码编写 |
| 7 | 实现cleanup_bb.py脚本，清理临时文件和过时脚本，生成清理报告 | 代码编写 |
| 8 | 编写 `pipeline_run.py`，包含 `run_pipeline()`、`parse_pdf()`、`route_markdown()`、`save_log()` 函数，添加argparse支持和断点续跑逻辑 | 代码编写 |
| 9 | 编写 `generate_quality_report.py`，遍历JSON文件提取质量检查信息，统计质量问题类型分布 | 代码编写 |
| 10 | 编写 `generate_manual_validation_set.py`，使用固定随机种子42，生成人工验证集 | 代码编写 |
| 11 | 修改 `section_router.py` 中的 SECTION_CONFIG，扩展关键词配置，修复文档标题过滤规则 | 代码修改 |
| 12 | 分析人工检查发现的问题（wrong_section、incomplete），整理错误案例和修复方案 | 文档编写 |

---

## 何易欣

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
| 25 | 建立核心数据清洗与合并模块 merge_to_excel.py，实现多源大模型输出数据的结构化规整 | 代码编写 | 
| 26 | 在 merge_to_excel.py 中加入金额单位换算逻辑，将文本中的万元与元进行标准化统一对齐 | 代码修改 | 
| 27 | 设计噪声数据拦截机制，编写代码自动识别并拦截39条临时购买理财与滚动定存的干扰数据 | 代码编写 | 
| 28 | 引入 Pydantic 框架，针对 change_type 和 board_resolution 等基础字段定义严格的强校验 Schema 约束 | 代码编写 | 
| 29 | 开发自定义前置校验器 @field_validator，将模型输出的非标准文本（如“审议通过”）自动归一化为标准枚举值 | 代码修改 | 
| 30 | 编写字段评估核心脚本 evaluate_basic_fields.py，实现自动化字段提取准确率统计与数据质检 | 代码编写 | 
| 31 | 编写可视化分析脚本 visualize_analysis.py，用于读取清洗校准后的最终数据集 final_results.jsonl | 代码编写 | 
| 32 | 在 visualize_analysis.py 中利用 matplotlib 自动绘制募集资金变更类型分布饼图 change_type_pie_chart.png | 代码编写 | 
| 33 | 撰写人工质检盲测大报告 eval_report_final.md，对大模型生成的幻觉进行多维度深度错误分类与率值统计 | 文档编写 | 
| 34 | 提炼关键字段的原始证据文本 evidence_text 追溯解释，并将其整合进答辩演示脚本 demo_script.md 中 | 文档编写 |
