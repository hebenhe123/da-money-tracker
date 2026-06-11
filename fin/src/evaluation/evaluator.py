"""
评估工具模块
用于评估章节路由和信息抽取的质量
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd
from loguru import logger


class SectionEvaluator:
    """章节评估器"""

    def __init__(self, ground_truth_path: Optional[Path] = None):
        """
        初始化评估器

        Args:
            ground_truth_path: 真值文件路径
        """
        self.ground_truth = self._load_ground_truth(ground_truth_path)

    def _load_ground_truth(self, ground_truth_path: Optional[Path]) -> Dict[str, Any]:
        """加载真值数据"""
        if ground_truth_path and ground_truth_path.exists():
            with open(ground_truth_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def evaluate_sections(
        self,
        predicted: List[Dict[str, Any]],
        doc_id: str
    ) -> Dict[str, Any]:
        """
        评估章节分类

        Args:
            predicted: 预测结果
            doc_id: 文档ID

        Returns:
            评估结果
        """
        if doc_id not in self.ground_truth:
            logger.warning(f"文档{doc_id}无真值数据")
            return {
                "accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0
            }

        ground_truth_sections = self.ground_truth[doc_id].get("sections", [])

        # 计算准确率
        correct = 0
        total = len(ground_truth_sections)

        for gt_section in ground_truth_sections:
            gt_title = gt_section.get("title", "")
            gt_type = gt_section.get("section_type", "")

            for pred_section in predicted:
                pred_title = pred_section.get("title", "")
                pred_type = pred_section.get("section_type", "")

                if gt_title == pred_title and gt_type == pred_type:
                    correct += 1
                    break

        accuracy = correct / total if total > 0 else 0.0

        # 计算精确率、召回率、F1
        precision, recall, f1 = self._calculate_metrics(
            ground_truth_sections,
            predicted
        )

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "correct": correct,
            "total": total
        }

    def _calculate_metrics(
        self,
        ground_truth: List[Dict[str, Any]],
        predicted: List[Dict[str, Any]]
    ) -> tuple:
        """
        计算精确率、召回率、F1

        Args:
            ground_truth: 真值
            predicted: 预测

        Returns:
            (precision, recall, f1)
        """
        # 获取所有章节类型
        gt_types = {s.get("section_type") for s in ground_truth}
        pred_types = {s.get("section_type") for s in predicted}

        all_types = gt_types | pred_types

        # 计算每个类型的指标
        tp_total = 0
        fp_total = 0
        fn_total = 0

        for section_type in all_types:
            gt_count = sum(1 for s in ground_truth if s.get("section_type") == section_type)
            pred_count = sum(1 for s in predicted if s.get("section_type") == section_type)

            # 计算TP、FP、FN
            tp = min(gt_count, pred_count)
            fp = max(0, pred_count - gt_count)
            fn = max(0, gt_count - pred_count)

            tp_total += tp
            fp_total += fp
            fn_total += fn

        # 计算指标
        precision = tp_total / (tp_total + fp_total) if (tp_total + fp_total) > 0 else 0.0
        recall = tp_total / (tp_total + fn_total) if (tp_total + fn_total) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return precision, recall, f1

    def generate_report(
        self,
        results: List[Dict[str, Any]],
        output_path: Path
    ) -> None:
        """
        生成评估报告

        Args:
            results: 评估结果列表
            output_path: 输出路径
        """
        # 计算平均指标
        avg_accuracy = sum(r.get("accuracy", 0) for r in results) / len(results)
        avg_precision = sum(r.get("precision", 0) for r in results) / len(results)
        avg_recall = sum(r.get("recall", 0) for r in results) / len(results)
        avg_f1 = sum(r.get("f1", 0) for r in results) / len(results)

        # 生成报告
        report = f"""
# 章节分类评估报告

## 整体指标

| 指标 | 数值 |
|------|------|
| 准确率 | {avg_accuracy:.2%} |
| 精确率 | {avg_precision:.2%} |
| 召回率 | {avg_recall:.2%} |
| F1分数 | {avg_f1:.2%} |

## 详细结果

| 文档ID | 准确率 | 精确率 | 召回率 | F1分数 |
|--------|--------|--------|--------|--------|
"""

        for result in results:
            doc_id = result.get("doc_id", "unknown")
            report += f"| {doc_id} | {result.get('accuracy', 0):.2%} | {result.get('precision', 0):.2%} | {result.get('recall', 0):.2%} | {result.get('f1', 0):.2%} |\n"

        # 保存报告
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"评估报告已保存: {output_path}")


class FieldEvaluator:
    """字段评估器"""

    def __init__(self, ground_truth_path: Optional[Path] = None):
        """
        初始化字段评估器

        Args:
            ground_truth_path: 真值文件路径
        """
        self.ground_truth = self._load_ground_truth(ground_truth_path)

    def _load_ground_truth(self, ground_truth_path: Optional[Path]) -> Dict[str, Any]:
        """加载真值数据"""
        if ground_truth_path and ground_truth_path.exists():
            with open(ground_truth_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def evaluate_fields(
        self,
        predicted: Dict[str, Any],
        doc_id: str
    ) -> Dict[str, Any]:
        """
        评估字段抽取

        Args:
            predicted: 预测结果
            doc_id: 文档ID

        Returns:
            评估结果
        """
        if doc_id not in self.ground_truth:
            logger.warning(f"文档{doc_id}无真值数据")
            return {
                "accuracy": 0.0,
                "field_accuracy": {}
            }

        ground_truth_fields = self.ground_truth[doc_id].get("fields", {})

        # 计算每个字段的准确率
        field_accuracy = {}
        correct_count = 0
        total_count = 0

        for field_name, gt_value in ground_truth_fields.items():
            pred_value = predicted.get(field_name)

            if pred_value is not None:
                total_count += 1
                if str(pred_value).strip() == str(gt_value).strip():
                    correct_count += 1
                    field_accuracy[field_name] = 1.0
                else:
                    field_accuracy[field_name] = 0.0

        accuracy = correct_count / total_count if total_count > 0 else 0.0

        return {
            "accuracy": accuracy,
            "field_accuracy": field_accuracy,
            "correct": correct_count,
            "total": total_count
        }