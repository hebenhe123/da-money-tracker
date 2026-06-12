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


## 使用的工具
TRAE / ChatGPT / Gemini

---

# Project Overview

## 项目题目
上市公司募集资金用途与变更跟踪的结构化抽取研究

## 项目目标
从上市公司募集资金相关公告的PDF文件中，自动识别并抽取与募集资金使用、投资项目变更、项目延期相关的目标章节，为后续LLM结构化信息抽取提供高质量输入数据。

## 成员分工
| 成员 | 职责 |
|------|------|
| Member B | PDF Parsing（MinerU）、Section Checking、Environment & Git |

---

# AI Usage Log

## MinerU Parsing

### 问题
- MinerU 调用方式不统一，不同环境下命令格式不同
- 路径配置使用相对路径，在不同目录结构下运行失败
- 缺少备选解析方案，MinerU不可用时无法处理PDF

### AI建议
- 使用环境变量 `MINERU_CMD` 配置MinerU命令
- 使用 `Path(__file__).resolve().parent` 获取绝对路径
- 添加 pdfplumber 作为备选PDF解析方案
- 增加PDF→Markdown转换功能，自动识别标题层级

### 实施方案
- 修改 `pipeline_run.py`，添加环境变量加载
- 使用 `ROOT_DIR = Path(__file__).resolve().parent` 获取项目根目录
- 实现 `try_mineru_parse()` 和 `try_pdfplumber_parse()` 函数
- 实现 `convert_text_to_markdown()` 函数自动识别标题层级

### 验证方式
- 运行 `python pipeline_run.py` 检查是否能正确解析PDF
- 检查 `data/markdown/` 目录是否生成Markdown文件
- 验证Markdown文件是否包含正确的标题格式

### 最终结果
- 成功解析100个PDF文件
- 生成100个Markdown文件到 `data/markdown/` 目录
- 支持MinerU和pdfplumber两种解析方式
- 自动识别标题层级并添加Markdown格式

---

## Section Router

### 问题
- 章节分类错误："变更募集资金投资项目"被分类为fund_investment而非fund_change
- 关键词评分算法存在缺陷，短关键词重复计分导致错误分类
- 父章节和子章节重复匹配，内容冗余

### AI建议
- 重构评分逻辑，引入Scorer类实现语义评分
- 实现Priority Keywords机制（重要关键词高分）
- 实现Negative Keywords机制（排除关键词扣分）
- 实现Longest Keyword Wins策略
- 修改去重策略：保留父章节，删除同类型子章节

### 实施方案
- 修改 `section_router.py`，添加Scorer类
- 实现 `clean_title()` 函数去除标题编号前缀
- 修改 `deduplicate_and_merge_sections()` 函数保留父章节
- 调整 `section_rules.yaml` 配置关键词权重

### 验证方式
- 使用真实公告文件测试：`python section_router.py ../output/宁德时代.md -o result.json`
- 验证场景：
  - "募集资金投资项目情况" → fund_investment
  - "变更募集资金投资项目情况" → fund_change  
  - "部分募集资金投资项目延期" → project_delay

### 最终结果
- 成功正确分类各类章节
- 解决了"变更募集资金投资项目"分类错误问题
- 实现父子章节智能去重，保留完整业务章节
- 输出JSON结构支持批量处理

---

## Section Router V2 - 增强版章节路由器

### 问题
- 大量章节被归为other，特别是合同条款、账户操作、保荐机构条款等
- 重复章节问题：同一年度或同类条款被重复发现
- 空文件处理：许多文件提取章节数为0
- 分类精度问题：部分可识别类型能正确分类，但仍有标题模糊或正文关键内容未被检测
- "续"章节继承逻辑需要优化

### AI建议
- 正文关键词辅助分类：对于other类章节，扫描正文前几行内容检测关键词
- 合同类或银行操作章节单独标注：新增contract类型
- 空文件过滤：在read_markdown后加空内容判断，跳过无内容文件
- 重复章节处理：增加去重逻辑，按上下文合并重复章节
- 分类规则可扩展：标题+正文前N行+关键词表，实现更精准分类

### 实施方案
- 重新编写 `section_router.py`，实现以下功能：
  - 支持Markdown标题识别（#开头）
  - 建立关键词字典：basic_info、storage、usage、project、change、extra、idle、problem、other
  - "续"章节继承父章节类型逻辑
  - 正文关键词辅助分类机制
  - 新增contract类型分类合同/协议类章节
  - 空文件自动跳过
  - 重复内容去重
  - 命令行参数支持（--input、--input-dir、--output）

### 验证方式
- 运行 `python section_router.py` 批量处理 `data/markdown/` 目录
- 检查输出目录 `output/sections/` 是否生成JSON文件
- 验证章节分类准确性：basic_info、storage、usage、project、change、extra、idle、problem、contract、other
- 检查各section字数统计日志

### 最终结果
- 成功处理100个Markdown文件
- 新增contract类型，有效分离合同/协议类章节
- 空文件自动跳过，避免错误
- 正文关键词辅助分类提升分类精度
- "续"章节正确继承父章节类型
- 支持单文件处理和批量处理两种模式
- 输出结构化JSON，便于后续分析或建模

---

## Section Router - 输出接口优化

### 问题
- 原始输出为list结构，不便于批量处理和LLM抽取
- 缺少source_file和route_version字段，不利于错误排查和版本追踪

### AI建议
- 将sections从list改为dict结构，支持直接索引访问
- 添加source_file字段记录源文件路径
- 添加route_version字段记录路由规则版本
- 实现 `build_extraction_tasks()` 函数，为LLM抽取做准备

### 实施方案
- 修改 `save_sections_to_json()` 函数输出dict结构
- 添加CLI参数 `-o` 支持指定输出路径
- 新增 `build_extraction_tasks()` 函数构建LLM抽取任务列表

### 验证方式
- 运行 `python section_router.py test.md -o output.json` 检查输出格式
- 验证JSON结构是否包含doc_id、source_file、route_version字段
- 测试 `build_extraction_tasks()` 输出是否符合LLM输入格式

### 最终结果
- JSON结构改为dict，支持 `data["sections"]["fund_change"]["content"]` 直接访问
- 新增source_file和route_version字段，便于错误排查和版本追踪
- 实现LLM抽取任务生成接口，支持后续结构化抽取流程

---

## Document Classifier

### 问题
- 原分类器将大量非目标文档错误分类为fund_usage_report
- 现金管理公告、理财产品公告被误认为目标文档
- 募集资金监管协议、专户注销公告也被错误分类
- 导致后续处理大量无效文档，浪费计算资源
- 鉴证报告类型文档被错误过滤

### AI建议
- 新增排除关键词规则，优先排除非目标文档
- 明确目标文档定义，包含8种类型（新增募集资金使用计划公告）
- 将鉴证报告从排除列表中移除，纳入目标文档
- 增加置信度评分和匹配规则记录
- 对分类结果进行人工审计和修正

### 实施方案
- 修改classify_document_type函数，新增排除关键词检查
- 排除关键词：现金管理、理财产品、购买理财产品、结构性存款、募集资金专户、监管协议、专户注销、审计报告、核查意见、专项说明、专项核查
- 目标文档：募集资金存放与使用情况专项报告、前次募集资金使用情况专项报告、前次募集资金使用情况鉴证报告、募集资金用途变更公告、募投项目延期公告、募投项目调整公告、募投项目实施进展公告、募集资金使用计划公告
- 扩展section_router.py中的关键词配置，添加"募集资金的基本情况"、"延期实施"、"前次募集资金使用情况"等变体关键词
- 修复文档标题过滤规则，允许"鉴证报告"类型文档通过

### 验证方式
- 运行section_router.py批量处理所有文档
- 检查分类结果统计：目标文档99篇，非目标文档1篇
- 验证鉴证报告是否被正确识别
- 检查output/sections_v2/目录是否生成完整的JSON文件

### 最终结果
- 成功修正分类错误，目标文档从10个提升到99个
- 仅1个文档因无Markdown标题格式无法解析
- 正确识别鉴证报告等重要文档类型
- Section Router成功率：99%（99/100）
- 提取章节总数：293
- 章节类型分布：basic_info=64, usage=43, change=28, problem=32, idle=32, extra=1, other=53

---

## Quality Control & Audit

### 问题
- 原分类结果中包含大量非目标文档
- 需要对分类结果进行人工审计
- 需要生成质量控制报告
- 部分文档因关键词不匹配被错误过滤

### AI建议
- 统计分类结果，生成分类统计表
- 分析过滤原因，明确各类别占比
- 生成质量控制报告，记录分类规则和统计结果
- 扩展关键词配置，提高文档识别率

### 实施方案
- 运行section_router.py批量处理所有文档
- 分析各类别数量和占比
- 扩展关键词配置，修复"的"字差异等匹配问题
- 生成parse_quality_check.csv质量检查报告

### 验证方式
- 检查分类统计：初始100篇，目标99篇，非目标1篇
- 验证过滤原因：仅1篇无标题格式文档
- 检查质量控制报告是否完整
- 验证各章节类型分布统计

### 最终结果
- 初始获取文档：100篇
- 目标文档：99篇
- 非目标文档：1篇（无Markdown标题格式）
- Section Router成功率：99%（99/100）
- 提取章节总数：293
- 章节类型分布：
  - basic_info：64
  - usage：43
  - change：28
  - problem：32
  - idle：32
  - extra：1
  - other：53

---

## Directory Cleanup

### 问题
- bb目录下存在大量临时文件和重复脚本
- 临时Markdown文件（MinerU_markdown_*.md）占用空间
- 过时的Python脚本和报告文档需要清理
- 影响项目结构清晰度和可维护性

### AI建议
- 保留核心功能脚本和重要文档
- 删除临时文件和过时脚本
- 生成清理报告，记录删除和保留的文件

### 实施方案
- 实现cleanup_bb.py脚本
- 保留：section_router.py、pipeline_run.py、batch_pipeline.py、reclassify_all_docs.py等核心脚本
- 保留：ai_worklog_all.md、demo_script.md、eval_report_final.md等重要文档
- 删除：临时分类脚本、诊断脚本、临时报告等

### 验证方式
- 运行cleanup_bb.py清理目录
- 检查cleanup_report.txt中的删除和保留文件统计
- 验证核心功能脚本是否完整保留

### 最终结果
- 删除文件数：11个
- 保留文件数：16个
- 保留核心功能：Section Router、Pipeline、文档分类、质量检查
- 保留重要文档：工作日志、展示脚本、评估报告、使用说明、设计文档

---

## Batch Pipeline

### 问题
- 缺少批处理管道，无法批量处理大量PDF文件
- 单个文件失败会中断整个处理流程
- 缺少进度显示和日志记录
- 重新运行时会重复处理已完成文件

### AI建议
- 设计生产级批处理管道，包含：
  - PDF解析 → Markdown转换 → Section Router → JSON输出
  - 支持断点续跑（跳过已处理文件）
  - 添加tqdm进度条显示
  - 记录详细运行日志（JSONL格式）
  - 支持失败重试

### 实施方案
- 编写 `pipeline_run.py`，包含：
  - `run_pipeline()` - 主流程控制
  - `parse_pdf()` - PDF解析
  - `route_markdown()` - 章节路由
  - `save_log()` - 日志记录
- 添加argparse支持命令行参数配置
- 实现断点续跑逻辑（检查JSON输出文件是否存在）

### 验证方式
- 运行 `python pipeline_run.py` 处理100个PDF文件
- 检查 `data/routed/` 目录是否生成JSON文件
- 验证 `data/logs/run_log.jsonl` 是否记录完整日志
- 测试断点续跑功能（中断后重新运行）

### 最终结果
- 成功处理100个PDF文件，生成100个Router JSON文件
- 支持断点续跑，跳过已处理文件
- 显示tqdm进度条和处理统计
- 生成详细运行日志，包含成功/失败/跳过状态

---

## Quality Report

### 问题
- 缺少质量评估报告，无法量化Section Router的识别效果
- 无法追踪质量问题分布情况

### AI建议
- 编写质量报告生成器，从Router JSON中提取质量检查数据
- 生成CSV格式的详细质量报告
- 生成JSON格式的统计摘要
- 支持命令行运行，自动创建输出目录

### 实施方案
- 编写 `generate_quality_report.py`
- 遍历 `data/routed/` 目录中的所有JSON文件
- 提取checks字段中的质量检查信息
- 统计各质量问题类型的分布

### 验证方式
- 运行 `python generate_quality_report.py`
- 检查 `data/reports/quality_report.csv` 是否生成
- 检查 `data/reports/quality_summary.json` 是否包含统计信息

### 最终结果
- 成功生成质量报告，包含64条section样本的检查结果
- 统计数据：correct=57, wrong_section=4, incomplete=3
- 准确率：89.06%，有效检索率：93.75%

---

## Manual Validation

### 问题
- 缺少人工验证集，无法进行人工质量评估
- 需要从Router输出中随机抽取样本进行人工检查

### AI建议
- 编写人工验证集抽样脚本
- 固定随机种子确保抽样结果可复现
- 支持指定抽样数量
- 导出样本内容到TXT文件，便于人工检查

### 实施方案
- 编写 `generate_manual_validation_set.py`
- 使用固定随机种子42
- 从Router JSON中随机抽取样本
- 生成 `manual_validation.csv` 和 `sample_contents/` 目录

### 验证方式
- 运行 `python generate_manual_validation_set.py --sample-size 50`
- 检查 `data/eval/manual_validation.csv` 是否生成
- 检查 `data/eval/sample_contents/` 目录是否包含样本TXT文件

### 最终结果
- 成功生成人工验证集，包含50份文档的64条section样本
- 生成CSV格式的验证表格，包含doc_id、section_type、title等字段
- 生成TXT格式的样本内容文件，便于人工检查
- 抽样结果可复现（固定随机种子42）

---

## Section Router - 关键词扩展与解析率提升

### 问题
- 部分文档因标题关键词不匹配无法被正确分类
- 关键词匹配过于严格，如"募集资金的基本情况"与"募集资金基本情况"因"的"字差异无法匹配
- 鉴证报告类型文档被错误过滤
- 项目延期公告等特殊类型文档识别率低

### AI建议
- 扩展关键词配置，添加变体关键词
- 修复文档标题过滤规则，允许鉴证报告通过
- 添加项目延期、使用计划等相关关键词

### 实施方案
- 修改 `section_router.py` 中的 SECTION_CONFIG：
  - basic_info类型添加"募集资金的基本情况"、"前次募集资金使用情况"、"鉴证报告"等关键词
  - change类型添加"延期实施"、"项目延期"、"重新论证"等关键词
- 修改文档标题过滤规则，移除"专项报告"和"鉴证报告"的过滤

### 验证方式
- 运行 `python section_router.py -d data/markdown -o output/sections_v2` 批量处理
- 运行 `python parse_quality_check.py` 生成质量检查报告
- 验证之前失败的文档是否成功解析

### 最终结果
- 解析成功率从88%提升至99%
- 99个文档成功解析，仅1个文档因无Markdown标题格式失败
- 提取章节总数从96增加到293
- 覆盖更多文档类型：鉴证报告、使用计划公告、延期公告等

---

# Human Verification

## 人工检查发现的问题

### wrong_section（分类错误）
| 数量 | 说明 |
|------|------|
| 4 | Router定位到了错误章节 |

### incomplete（内容不完整）
| 数量 | 说明 |
|------|------|
| 3 | Router定位到正确章节，但正文内容不完整 |

## 错误案例

### 案例1：wrong_section
- **doc_id**: 300750_77ab847c58c49e430ec86e6647e55b30
- **Router识别**: "五、募集资金使用及披露中存在的问题"
- **实际类别**: 合规披露章节，不是募集资金实际使用情况
- **原因分析**: 标题包含"募集资金使用"关键词，但实际内容是问题披露，属于合规章节

### 案例2：incomplete
- **doc_id**: 300750_627ff52e2db412b31b8185cc06a0666d
- **Router识别**: "三、本年度募集资金的实际使用情况"
- **正文内容**: "详见附表1"
- **原因分析**: MinerU未完整解析表格内容，仅提取到引用说明

## 修复方案

1. **增加标题权重**：提高标题中关键词的权重，减少正文内容的干扰

2. **增加char_count过滤**：设置最小字符数阈值，过滤内容过短的section

3. **检测"详见附表"类内容**：识别并标记包含"详见附表"、"详见附录"等内容的section

4. **对表格区域进行专门解析**：优化PDF解析，确保表格内容完整提取

---

# Reflection

## AI帮助了什么

1. **技术方案设计**：提供了Section Router评分策略、批处理管道架构设计等核心技术方案

2. **代码实现**：协助实现了Scorer类、标题解析、章节去重、JSON输出等核心功能

3. **调试指导**：帮助定位了分类错误、路径配置、除零错误等问题

4. **文档编写**：协助编写了技术文档、使用说明、评估报告等

5. **最佳实践**：提供了环境变量配置、绝对路径处理、断点续跑等工程实践建议

## 人工验证做了什么

1. **数据验证**：人工检查50份文档的64条section样本

2. **错误发现**：识别出4个wrong_section和3个incomplete错误案例

3. **质量评估**：计算准确率89.06%，有效检索率93.75%

4. **改进建议**：提出增加标题权重、char_count过滤、表格解析优化等改进方案

5. **文档审查**：审查技术文档和评估报告的准确性

## 项目局限

1. **OCR标题识别错误**：MinerU解析时可能误识别标题层级

2. **同义标题覆盖不足**：部分非标准标题可能无法识别，需要持续扩充关键词

3. **规则维护成本**：关键词规则需要不断维护和更新

4. **表格解析质量**：复杂表格可能无法完整解析

5. **依赖外部工具**：依赖MinerU或pdfplumber进行PDF解析，解析质量受限于工具

## 未来优化方向

1. **Embedding Router**：使用文本嵌入进行语义匹配，减少关键词规则依赖

2. **Hybrid Router**：结合规则匹配和机器学习模型，提升识别准确性

3. **LLM Router**：直接使用LLM进行章节分类，提高泛化能力

4. **表格解析优化**：针对金融表格进行专门优化

5. **主动学习**：基于人工验证结果自动更新关键词权重

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