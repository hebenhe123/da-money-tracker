import json
import os
import pandas as pd
from pathlib import Path
from datetime import datetime

def log_validation_error(doc_id, error_type, reason):
    logs_dir = outputs_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    error_log = {
        "doc_id": doc_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "step": "validate",
        "error_type": error_type,
        "reason": reason
    }
    
    log_file = logs_dir / "validation_errors.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(error_log, ensure_ascii=False) + "\n")

# 1. 路径自动定位
desktop_path = Path(os.path.expanduser("~")) / "Desktop"
outputs_dir = list(desktop_path.rglob("outputs"))

if not outputs_dir:
    print("❌ 未找到 outputs 文件夹")
    exit()

outputs_path = outputs_dir[0]
jsonl_file = outputs_path / "final_results.jsonl"

if not jsonl_file.exists():
    bak_files = list(outputs_path.glob("final_results_bak.jsonl"))
    if bak_files:
        jsonl_file = bak_files[0]
    else:
        print("❌ 未找到任何结果文件（final_results.jsonl）")
        exit()

print(f"正在深度解析自适应数据池: {jsonl_file}")

all_rows = []
total_docs = 0
total_extracted_segments = 0

# 统计计数器
stats = {
    "total_lines": 0,
    "processed_lines": 0,
    "format_error_lines": 0,
    "no_project_lines": 0,
    "empty_evidence_lines": 0,
    "success_rows": 0
}

# 2. 核心清洗逻辑
with open(jsonl_file, "r", encoding="utf-8") as f:
    for line in f:
        stats["total_lines"] += 1
        
        if not line.strip():
            continue
            
        try:
            data = json.loads(line)
        except Exception as e:
            stats["format_error_lines"] += 1
            print(f"  [格式损坏] 第 {stats['total_lines']} 行: JSON解析失败")
            continue
            
        stats["processed_lines"] += 1
        total_docs += 1
        doc_id = data.get("doc_id", "")
        stock_code = doc_id.split("_")[0] if "_" in doc_id else ""
        
        sections = data.get("sections", {})
        projects_list = data.get("projects", [])
        
        doc_type = data.get("document_type", "null")
        is_change = "否" if doc_type == "non_target" else "是"
        
        has_content = False
        
        if isinstance(sections, dict) and sections:
            # 兼容模式 1
            for section_key, section_data in sections.items():
                if not isinstance(section_data, dict):
                    continue
                
                content = section_data.get("content", "")
                content = content if content else ""
                title = section_data.get("title", "")
                
                if content.strip():
                    has_content = True
                    total_extracted_segments += 1
                    stats["success_rows"] += 1
                    change_type = section_key
                    if "idle" in section_key or "cash" in str(doc_type):
                        change_type = "部分闲置资金现金管理"
                    elif "change" in section_key or "delay" in content:
                        change_type = "募投项目延期/变更"
                        
                    policy_impact = "null"
                    if "行业" in content or "环境" in content or "周期" in content:
                        policy_impact = "受宏观环境/行业周期影响"
                        
                    row = {
                        "股票代码": stock_code,
                        "文档ID": doc_id,
                        "是否变更": is_change,
                        "变动具体分类": change_type,
                        "核心变动原因": title if title else "募投项目调整",
                        "政策或环境影响说明": policy_impact,
                        "大模型抓取证据(原文)": str(content).replace("\n", " ")
                    }
                    all_rows.append(row)
                    
        elif isinstance(projects_list, list) and projects_list:
            # 兼容模式 2：加入高精度清洗规则
            has_project = False
            for proj in projects_list:
                if not isinstance(proj, dict):
                    continue
                
                evidence = proj.get("evidence_text", "")
                evidence = str(evidence).strip() if evidence else ""
                
                # 如果没有任何原文证据，直接跳过，不再生成空行
                if not evidence or evidence == "None" or evidence == "null":
                    stats["empty_evidence_lines"] += 1
                    log_validation_error(doc_id, "hallucination", "证据文本为空或为null/None")
                    continue
                    
                has_project = True
                has_content = True
                total_extracted_segments += 1
                stats["success_rows"] += 1
                
                # 根据原文关键词，智能反洗"变动具体分类"
                change_type = proj.get("change_type", "未分类")
                if change_type in ["未分类", "", None]:
                    if "效益" in evidence or "未达到预计效益" in evidence:
                        change_type = "募投项目效益未达预期"
                    elif "存款" in evidence or "理财" in evidence or "现金管理" in evidence:
                        change_type = "部分闲置资金现金管理"
                    elif "延期" in evidence or "调整" in evidence or "停工" in evidence:
                        change_type = "募投项目延期/调整"
                    else:
                        change_type = "募投项目变更说明"
                        
                # 根据原文关键词，智能反洗"核心变动原因"和"政策环境说明"
                change_reason = proj.get("change_reason", "未提及")
                policy_impact = proj.get("policy_impact", "null")
                
                if change_reason in ["未提及", "", None]:
                    if "加息" in evidence or "通货膨胀" in evidence or "周期" in evidence or "供需错配" in evidence:
                        change_reason = "宏观经济波动/行业周期调整"
                        policy_impact = "受宏观环境/行业周期影响"
                    elif "政府许可" in evidence or "审批" in evidence:
                        change_reason = "政府审批或许可进度滞后"
                        policy_impact = "受行政审批进度影响"
                    elif "技术方案调整" in evidence or "设备调试" in evidence:
                        change_reason = "公司技术路线或设备调试优化"
                        policy_impact = "公司内部业务调整"
                    else:
                        change_reason = "市场环境变化及项目推进调整"

                row = {
                    "股票代码": stock_code,
                    "文档ID": doc_id,
                    "是否变更": "是",
                    "变动具体分类": change_type,
                    "核心变动原因": change_reason,
                    "政策或环境影响说明": policy_impact,
                    "大模型抓取证据(原文)": evidence.replace("\n", " ")
                }
                all_rows.append(row)
            
            if not has_project:
                stats["no_project_lines"] += 1
                log_validation_error(doc_id, "section_error", "projects列表为空或无有效证据")
                print(f"  [无项目公告] doc_id={doc_id}: projects列表为空或无有效证据")
                
        else:
            # 阴性样本兜底 - 无项目/无内容
            stats["no_project_lines"] += 1
            log_validation_error(doc_id, "section_error", "sections和projects均为空")
            print(f"  [无项目公告] doc_id={doc_id}: sections和projects均为空")
            
            row = {
                "股票代码": stock_code,
                "文档ID": doc_id,
                "是否变更": "否",
                "变动具体分类": "null",
                "核心变动原因": "无变更事实",
                "政策或环境影响说明": "null",
                "大模型抓取证据(原文)": "null"
            }
            all_rows.append(row)

# 3. 落地生成最终的干净表格
if not all_rows:
    print("⚠️ 警告：未提取到任何有效数据，请检查原始文件内容！")
    exit()

df = pd.DataFrame(all_rows)
column_order = ["股票代码", "文档ID", "是否变更", "变动具体分类", "核心变动原因", "政策或环境影响说明", "大模型抓取证据(原文)"]
df = df[column_order]

output_csv = outputs_path / "Listed_Companies_Fundraising_Analysis.csv"
df.to_csv(output_csv, index=False, encoding="utf-8-sig")

# 4. 生成验证摘要报告
print("\n" + "="*50)
print(f"高浓度结构化清洗完成！")
print(f"[-] 累计解析原始文档: {total_docs} 篇")
print(f"[-] 成功对齐并解包的核心高价值文本段落: {total_extracted_segments} 行")
print(f"[-] 最终完美版 CSV 落地路径: {output_csv}")
print("="*50)

# 输出统计摘要
print("\n数据验证统计摘要:")
print(f"  总行数: {stats['total_lines']}")
print(f"  成功处理行数: {stats['processed_lines']}")
print(f"  格式损坏拦截: {stats['format_error_lines']}")
print(f"  无项目公告拦截: {stats['no_project_lines']}")
print(f"  空证据拦截: {stats['empty_evidence_lines']}")
print(f"  最终输出行数: {stats['success_rows']}")

# 生成 validation_summary.txt
summary_content = f"""# 数据验证摘要报告
生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## 处理统计
- 总行数: {stats['total_lines']}
- 成功处理行数: {stats['processed_lines']}
- 格式损坏拦截: {stats['format_error_lines']}
- 无项目公告拦截: {stats['no_project_lines']}
- 空证据拦截: {stats['empty_evidence_lines']}
- 最终输出行数: {stats['success_rows']}

## 原始文档统计
- 累计解析原始文档: {total_docs} 篇
- 成功提取核心段落: {total_extracted_segments} 行

## 输出文件
- CSV路径: {output_csv}
"""

summary_file = outputs_path / "validation_summary.txt"
with open(summary_file, "w", encoding="utf-8") as f:
    f.write(summary_content)

print(f"\n验证摘要已生成: {summary_file}")