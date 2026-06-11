#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
主运行脚本
支持PDF解析、章节路由、信息抽取的完整流程
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

# 添加项目根目录到Python路径
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from src.mineru.parser import PDFParser
from src.workflow.section_router import SectionRouter
from src.llm.client import LLMClient
from src.evaluation.evaluator import SectionEvaluator, FieldEvaluator


class Pipeline:
    """处理流程"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化处理流程

        Args:
            config: 配置字典
        """
        self.config = config
        self.pdf_parser = PDFParser(
            primary=config.get("pdf_parser", {}).get("primary", "mineru"),
            fallback=config.get("pdf_parser", {}).get("fallback", "pdfplumber")
        )
        self.section_router = SectionRouter(
            config_path=ROOT_DIR / "configs" / "section_rules.yaml"
        )
        self.llm_client = LLMClient(
            provider=config.get("llm", {}).get("provider", "openai"),
            base_url=config.get("llm", {}).get("base_url"),
            model=config.get("llm", {}).get("model", "gpt-4o")
        )

    def process_document(
        self,
        pdf_path: Path,
        output_dir: Path
    ) -> Optional[Dict[str, Any]]:
        """
        处理单个文档

        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录

        Returns:
            处理结果
        """
        doc_id = pdf_path.stem
        logger.info(f"开始处理文档: {doc_id}")

        try:
            # 步骤1: PDF解析
            markdown_path = output_dir / "markdown" / f"{doc_id}.md"
            if not self.pdf_parser.parse_to_file(pdf_path, markdown_path):
                logger.error(f"PDF解析失败: {pdf_path}")
                return None

            with open(markdown_path, "r", encoding="utf-8") as f:
                markdown_text = f.read()

            logger.info(f"PDF解析成功: {pdf_path}")

            # 步骤2: 章节路由
            sections = self.section_router.route(markdown_text)
            logger.info(f"章节路由完成: 识别到{len(sections)}个章节")

            # 步骤3: 信息抽取
            results = []
            for section in sections:
                result = self._extract_fields(section, doc_id)
                if result:
                    results.append(result)

            logger.info(f"信息抽取完成: 抽取到{len(results)}个字段")

            # 步骤4: 保存结果
            result = {
                "doc_id": doc_id,
                "sections": sections,
                "results": results,
                "metadata": {
                    "parse_time": datetime.now().isoformat(),
                    "pdf_path": str(pdf_path),
                    "markdown_path": str(markdown_path)
                }
            }

            # 保存JSON结果
            json_path = output_dir / "sections" / f"{doc_id}_sections.json"
            json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            logger.info(f"文档处理完成: {doc_id}")
            return result

        except Exception as e:
            logger.error(f"文档处理失败: {doc_id}, 错误: {e}")
            return None

    def _extract_fields(
        self,
        section: Dict[str, Any],
        doc_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        抽取字段

        Args:
            section: 章节信息
            doc_id: 文档ID

        Returns:
            抽取结果
        """
        section_type = section.get("section_type", "")
        content = section.get("content", "")

        if not content:
            return None

        # 根据章节类型设计不同的抽取提示词
        if section_type == "usage":
            prompt = f"""
请从以下文本中提取募集资金使用情况信息：

{content}

请提取以下字段：
- project_name: 项目名称
- investment_amount: 投资金额
- progress: 投资进度

请以JSON格式输出。
"""
        elif section_type == "change":
            prompt = f"""
请从以下文本中提取募集资金变更信息：

{content}

请提取以下字段：
- project_name: 项目名称
- original_project: 原项目名称
- new_project: 新项目名称
- change_reason: 变更原因

请以JSON格式输出。
"""
        elif section_type == "delay":
            prompt = f"""
请从以下文本中提取募集资金延期信息：

{content}

请提取以下字段：
- project_name: 项目名称
- original_date: 原计划日期
- new_date: 延期后日期
- delay_reason: 延期原因

请以JSON格式输出。
"""
        else:
            return None

        try:
            schema = {
                "type": "object",
                "properties": {}
            }

            result = self.llm_client.extract_structured_data(prompt, schema)
            result["section_type"] = section_type
            result["evidence"] = content[:500]  # 保留前500字符作为证据

            return result

        except Exception as e:
            logger.warning(f"字段抽取失败: {e}")
            return None

    def batch_process(
        self,
        pdf_dir: Path,
        output_dir: Path
    ) -> List[Dict[str, Any]]:
        """
        批量处理文档

        Args:
            pdf_dir: PDF目录
            output_dir: 输出目录

        Returns:
            处理结果列表
        """
        pdf_files = list(pdf_dir.glob("*.pdf"))
        logger.info(f"找到{len(pdf_files)}个PDF文件")

        results = []
        for pdf_path in pdf_files:
            result = self.process_document(pdf_path, output_dir)
            if result:
                results.append(result)

        logger.info(f"批量处理完成: 总共处理{len(results)}个文档")
        return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="募集资金信息抽取流程")
    parser.add_argument("--mode", type=str, default="full",
                       choices=["full", "parse", "route", "extract", "demo"],
                       help="运行模式")
    parser.add_argument("--input", type=str, default="data/pdf",
                       help="输入目录或文件")
    parser.add_argument("--output", type=str, default="outputs/results",
                       help="输出目录")
    parser.add_argument("--config", type=str, default="configs/model_config.yaml",
                       help="配置文件路径")

    args = parser.parse_args()

    # 加载配置
    config_path = ROOT_DIR / args.config
    if config_path.exists():
        import yaml
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    else:
        config = {}

    # 初始化流程
    pipeline = Pipeline(config)

    # 设置输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 根据模式运行
    if args.mode == "demo":
        # 演示模式：处理单个文件
        input_path = Path(args.input)
        if input_path.is_file():
            result = pipeline.process_document(input_path, output_dir)
            if result:
                print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            logger.error(f"文件不存在: {input_path}")
            sys.exit(1)

    elif args.mode == "full":
        # 完整模式：批量处理
        input_dir = Path(args.input)
        if input_dir.is_dir():
            results = pipeline.batch_process(input_dir, output_dir)

            # 生成CSV报告
            if results:
                import csv
                csv_path = output_dir / "final_results.csv"
                with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "doc_id", "company_code", "company_name",
                        "announcement_type", "section_type", "project_name",
                        "investment_amount", "progress", "change_reason",
                        "evidence", "extraction_confidence"
                    ])

                    for result in results:
                        for field_result in result.get("results", []):
                            writer.writerow([
                                result.get("doc_id", ""),
                                result.get("doc_id", "").split("_")[0],
                                "",
                                "",
                                field_result.get("section_type", ""),
                                field_result.get("project_name", ""),
                                field_result.get("investment_amount", ""),
                                field_result.get("progress", ""),
                                field_result.get("change_reason", ""),
                                field_result.get("evidence", ""),
                                ""
                            ])

                logger.info(f"CSV报告已生成: {csv_path}")
        else:
            logger.error(f"目录不存在: {input_dir}")
            sys.exit(1)

    else:
        logger.error(f"不支持的模式: {args.mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()