#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_test.py

Step 3：基于 SiliconFlow DeepSeek-R1 的募集资金定性抽取测试脚本。

功能：
1. 读取 data/routed 前 5 个 JSON 文件，提取 fund_usage / fund_change 章节文本。
2. 调用 SiliconFlow API（deepseek-ai/DeepSeek-R1）进行结构化抽取。
3. 强制要求模型在思维链结束后，在 ```json ... ``` 代码块中输出符合 Pydantic Schema 的 JSON。
4. 用正则提取 JSON 块，经 FundraisingReportExtract 校验后，以 JSONL 追加保存到 outputs/test_results.jsonl。

运行方式：
    cd c:/Users/Aurora/Desktop/aa
    set SILICONFLOW_API_KEY=your_api_key
    python src/extract_test.py
"""

import os
import re
import json
import sys
from pathlib import Path
from typing import Optional

from openai import OpenAI
from pydantic import ValidationError

# 导入 Step 2 定义的 Schema
from schema import FundraisingReportExtract

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
ROUTED_DIR = Path(__file__).parent.parent / "bb" / "data" / "routed"
OUTPUT_FILE = Path(__file__).parent.parent / "outputs" / "test_results.jsonl"
MAX_FILES = 5

API_BASE_URL = "https://api.siliconflow.cn/v1"
API_MODEL = "deepseek-ai/DeepSeek-R1"
API_KEY = os.environ.get("SILICONFLOW_API_KEY", "")

# ---------------------------------------------------------------------------
# 系统提示词
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """你是一位专业的金融文本信息抽取助手，专门负责从上市公司募集资金相关公告中抽取定性信息。

## 任务说明
请仔细阅读用户提供的公告文本（可能包含 fund_usage 和 fund_change 两个章节），并抽取其中每个募投项目的定性信息。

## 输出要求
1. 你必须先进行详细的思维链（Chain-of-Thought）分析，逐步思考文本中涉及了哪些募投项目、每个项目面临什么风险、政策影响如何。
2. 思维链结束后，在回复的最后，务必输出一个包裹在 ```json ... ``` 代码块中的 JSON 对象。
3. JSON 对象的结构必须严格符合以下 Pydantic Schema（字段不得增减）：
   - doc_id: str  —— 公告唯一ID
   - projects: list[ProjectDetail]  —— 募投项目列表
     - project_name: str  —— 募投项目名称
     - risk_category: str | null  —— 风险类别，仅限 ["市场风险", "行业竞争风险", "经营风险", "财务风险", "政策与合规风险", "其他风险", "无风险"] 之一
     - policy_impact: str | null  —— 政策影响的定性描述
     - evidence_text: str | null  —— 支持判断的原文原句

## 核心原则（必须严格遵守）
- **Null Rule**：若文本中未提及某个字段的信息，或无法确定，该字段必须输出 null，不得根据常识、公司整体情况或外部信息编造。
- **原文证据原则**：evidence_text 必须是输入文本中的原句，不得改写、概括或添加文本中不存在的信息。
- **项目级颗粒度**：一份公告可能包含多个募投项目，必须分别抽取，禁止合并或拆分。
- **禁止臆测**：所有信息必须能从提供的文本中找到依据。

## 示例输出格式
```json
{
  "doc_id": "示例ID",
  "projects": [
    {
      "project_name": "某募投项目",
      "risk_category": "市场风险",
      "policy_impact": "受新能源补贴政策影响",
      "evidence_text": "原文原句片段"
    }
  ]
}
```
"""

# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def find_routed_json_files(directory: Path, max_files: int = MAX_FILES):
    """查找路由输出目录下的 JSON 文件（排除汇总类），按文件名排序。"""
    if not directory.exists():
        print(f"[错误] 目录不存在: {directory}")
        sys.exit(1)

    files = sorted(
        f for f in directory.iterdir()
        if f.is_file()
        and f.suffix.lower() == ".json"
        and "failed" not in f.name.lower()
        and "summary" not in f.name.lower()
    )
    return files[:max_files]


def build_input_text(record: dict) -> Optional[str]:
    """
    从单条路由记录中提取 fund_usage 和 fund_change 章节的文本并拼接。
    若 sections 为空或目标章节均不存在，返回 None。
    """
    sections = record.get("sections", [])
    if not sections:
        return None

    target_types = {"fund_usage", "fund_change"}
    texts = []
    for sec in sections:
        sec_type = sec.get("section_type", "")
        if sec_type in target_types:
            title = sec.get("section_title", "")
            body = sec.get("section_text", "")
            texts.append(f"【{sec_type}】{title}\n{body}")

    if not texts:
        return None

    return "\n\n".join(texts)


def extract_json_block(raw_text: str) -> Optional[str]:
    """从模型返回的文本中提取 ```json ... ``` 代码块内容。"""
    # 优先匹配 ```json ... ```
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, raw_text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 备选：匹配 ``` ... ```（无 json 标记）
    pattern_plain = r"```\s*(.*?)\s*```"
    match_plain = re.search(pattern_plain, raw_text, re.DOTALL)
    if match_plain:
        return match_plain.group(1).strip()

    return None


def save_jsonl(record: dict, path: Path):
    """以 JSONL 格式追加保存单条记录。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main():
    if not API_KEY:
        print("[错误] 未设置环境变量 SILICONFLOW_API_KEY，请先设置后再运行。")
        print("  Windows CMD : set SILICONFLOW_API_KEY=your_key")
        print("  Windows PS  : $env:SILICONFLOW_API_KEY='your_key'")
        sys.exit(1)

    client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

    files = find_routed_json_files(ROUTED_DIR, MAX_FILES)
    print(f"扫描到 {len(files)} 个文件，准备处理前 {MAX_FILES} 个...\n")

    success_count = 0
    skip_count = 0
    fail_count = 0

    for idx, file_path in enumerate(files, start=1):
        print("-" * 60)
        print(f"[{idx}/{len(files)}] 处理: {file_path.name}")

        # 1. 读取并解析 JSON
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                record = json.load(f)
        except Exception as e:
            print(f"  [跳过] 读取失败: {e}")
            skip_count += 1
            continue

        doc_id = record.get("doc_id", file_path.stem)

        # 2. 构建输入文本
        input_text = build_input_text(record)
        if input_text is None:
            print(f"  [跳过] doc_id={doc_id}，未找到 fund_usage / fund_change 章节或 sections 为空。")
            skip_count += 1
            continue

        print(f"  doc_id={doc_id}，输入文本长度={len(input_text)} 字符")

        # 3. 调用 API
        try:
            response = client.chat.completions.create(
                model=API_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": input_text},
                ],
                temperature=0.2,
                max_tokens=4096,
            )
            raw_content = response.choices[0].message.content or ""
        except Exception as e:
            print(f"  [失败] API 调用异常: {e}")
            fail_count += 1
            continue

        # 4. 提取 JSON 块
        json_str = extract_json_block(raw_content)
        if json_str is None:
            print(f"  [失败] 未能在模型回复中找到 ```json ... ``` 代码块。")
            # 可选：将原始回复写入日志以便排查
            debug_path = Path(__file__).parent.parent / "outputs" / "debug_raw"
            debug_path.mkdir(parents=True, exist_ok=True)
            with open(debug_path / f"{doc_id}_raw.txt", "w", encoding="utf-8") as f:
                f.write(raw_content)
            fail_count += 1
            continue

        # 5. Pydantic 校验
        try:
            # 先校验 JSON 格式本身
            parsed = json.loads(json_str)
            # 注入 doc_id（若模型未返回或返回不一致，强制修正）
            parsed["doc_id"] = doc_id
            validated = FundraisingReportExtract.model_validate(parsed)
        except json.JSONDecodeError as e:
            print(f"  [失败] JSON 解析错误: {e}")
            fail_count += 1
            continue
        except ValidationError as e:
            print(f"  [失败] Pydantic 校验错误: {e}")
            fail_count += 1
            continue

        # 6. 保存结果
        result_dict = validated.model_dump()
        save_jsonl(result_dict, OUTPUT_FILE)
        print(f"  [成功] 已保存到 {OUTPUT_FILE}")
        success_count += 1

    print("-" * 60)
    print("处理完成：")
    print(f"  成功: {success_count} | 跳过: {skip_count} | 失败: {fail_count}")
    print(f"  结果文件: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
