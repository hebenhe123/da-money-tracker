#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_step1_input.py

Step 1 输入验证脚本：读取并验证同学 B 章节路由（Section Router）的输出数据。

功能：
1. 自动扫描同学 B 目录（bb/data/routed/）下的 JSON 路由输出文件。
2. 读取前 3 条记录（每个文件对应一篇公告的路由结果）。
3. 打印 doc_id 与每个 section 的 section_text 字符长度，验证数据可正常加载。
4. 自动探测并显示实际使用的键名，便于下游模块对齐。

运行方式：
    cd c:/Users/Aurora/Desktop/aa
    python src/check_step1_input.py
"""

import json
import sys
from pathlib import Path

# 配置：同学 B 的章节路由输出目录
ROUTED_DIR = Path(__file__).parent.parent / "bb" / "data" / "routed"


def find_routed_json_files(directory: Path):
    """查找目录下所有 .json 文件（排除汇总类文件），按文件名排序。"""
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
    return files


def inspect_keys(record: dict, prefix=""):
    """递归打印字典键名，帮助确认数据结构。"""
    for key, value in record.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            inspect_keys(value, full_key)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            print(f"  键: {full_key} -> list[dict]，子键示例: {list(value[0].keys())}")
        else:
            type_name = type(value).__name__
            preview = str(value)[:60].replace("\n", "\\n")
            print(f"  键: {full_key} -> {type_name} | 示例: {preview}")


def main():
    print("=" * 60)
    print("Step 1 输入验证：章节路由（Section Router）输出检查")
    print("=" * 60)

    files = find_routed_json_files(ROUTED_DIR)
    print(f"\n发现路由输出文件数量: {len(files)}")
    print(f"扫描目录: {ROUTED_DIR}\n")

    if not files:
        print("[警告] 未找到任何 JSON 路由文件，请确认同学 B 已运行章节路由模块。")
        sys.exit(0)

    # 只取前 3 个文件进行展示
    sample_files = files[:3]

    for idx, file_path in enumerate(sample_files, start=1):
        print("-" * 60)
        print(f"[{idx}/{len(sample_files)}] 文件: {file_path.name}")
        print("-" * 60)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                record = json.load(f)
        except json.JSONDecodeError as e:
            print(f"  [错误] JSON 解析失败: {e}")
            continue
        except Exception as e:
            print(f"  [错误] 读取失败: {e}")
            continue

        # 1. 打印顶级键名
        print("  顶级键名:", list(record.keys()))

        # 2. 提取 doc_id
        doc_id = record.get("doc_id", "<未找到 doc_id>")
        print(f"  公告 ID (doc_id): {doc_id}")

        # 3. 提取 sections
        sections = record.get("sections", [])
        if not sections:
            print("  [警告] 该记录中未找到 'sections' 键或为空列表。")
            print("  可用键结构探测:")
            inspect_keys(record)
            continue

        print(f"  章节数量: {len(sections)}")

        # 4. 遍历前 3 个 section，打印文本长度
        for s_idx, section in enumerate(sections[:3], start=1):
            title = section.get("section_title", "<无标题>")
            text = section.get("section_text", "")
            section_type = section.get("section_type", "<无类型>")

            print(f"    [{s_idx}] 章节类型: {section_type}")
            print(f"        章节标题: {title[:60]}{'...' if len(title) > 60 else ''}")
            print(f"        section_text 字符长度: {len(text)}")

        # 5. 若还有剩余章节，简要提示
        if len(sections) > 3:
            print(f"    ... 还有 {len(sections) - 3} 个章节未展示")

        print()

    print("=" * 60)
    print("验证完成。若以上 doc_id 与 section_text 长度正常输出，")
    print("说明 Step 1 输入数据可正常加载，键名对齐无误。")
    print("=" * 60)


if __name__ == "__main__":
    main()
