#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评估基础信息字段抽取准确率
"""

import os
import json
import argparse
from datetime import datetime


def load_jsonl(file_path):
    """加载 JSONL 文件"""
    data = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                doc_id = record.get('doc_id')
                if doc_id:
                    data[doc_id] = record
            except json.JSONDecodeError as e:
                print(f"Warning: Error parsing line {line_num}: {e}")
    return data


def compare_fields(truth, pred):
    """
    比对字段，返回比对结果
    返回：(字段名, 是否正确, 真值, 预测值) 的列表
    """
    results = []
    
    # stock_code: 字符串完全一致
    truth_code = truth.get('stock_code', '')
    pred_code = pred.get('stock_code', '')
    results.append(('stock_code', truth_code == pred_code, truth_code, pred_code))
    
    # announcement_date: 字符串完全一致
    truth_date = truth.get('announcement_date', '')
    pred_date = pred.get('announcement_date', '')
    results.append(('announcement_date', truth_date == pred_date, truth_date, pred_date))
    
    # announcement_title: 去除首尾空格和所有空格后完全一致
    truth_title = truth.get('announcement_title', '').strip().replace(' ', '')
    pred_title = pred.get('announcement_title', '').strip().replace(' ', '')
    results.append(('announcement_title', truth_title == pred_title, 
                    truth.get('announcement_title', ''), pred.get('announcement_title', '')))
    
    # company_name: 字符串完全一致
    truth_name = truth.get('company_name', '')
    pred_name = pred.get('company_name', '')
    results.append(('company_name', truth_name == pred_name, truth_name, pred_name))
    
    # report_year: 整数完全一致
    truth_year = truth.get('report_year')
    pred_year = pred.get('report_year')
    try:
        truth_year_int = int(truth_year) if truth_year is not None else None
        pred_year_int = int(pred_year) if pred_year is not None else None
        results.append(('report_year', truth_year_int == pred_year_int, truth_year, pred_year))
    except (ValueError, TypeError):
        results.append(('report_year', False, truth_year, pred_year))
    
    return results


def main():
    parser = argparse.ArgumentParser(description='评估基础信息字段抽取准确率')
    parser.add_argument('--truth', default='data/evaluation/ground_truth.jsonl',
                        help='真值文件路径')
    parser.add_argument('--pred', required=True, help='模型输出文件路径')
    parser.add_argument('--output', default='outputs/reports/basic_fields_evaluation.md',
                        help='报告输出路径')
    args = parser.parse_args()
    
    # 加载数据
    print(f"Loading truth file: {args.truth}")
    truth_data = load_jsonl(args.truth)
    print(f"Loading prediction file: {args.pred}")
    pred_data = load_jsonl(args.pred)
    
    print(f"\nTruth records: {len(truth_data)}")
    print(f"Prediction records: {len(pred_data)}")
    
    # 找出匹配的 doc_id
    truth_ids = set(truth_data.keys())
    pred_ids = set(pred_data.keys())
    
    matched_ids = truth_ids & pred_ids
    only_in_truth = truth_ids - pred_ids
    only_in_pred = pred_ids - truth_ids
    
    print(f"\nMatched doc_ids: {len(matched_ids)}")
    if only_in_truth:
        print(f"Only in truth (skipped): {len(only_in_truth)}")
    if only_in_pred:
        print(f"Only in prediction (skipped): {len(only_in_pred)}")
    
    # 逐字段统计
    field_stats = {
        'stock_code': {'correct': 0, 'total': 0},
        'announcement_date': {'correct': 0, 'total': 0},
        'announcement_title': {'correct': 0, 'total': 0},
        'company_name': {'correct': 0, 'total': 0},
        'report_year': {'correct': 0, 'total': 0}
    }
    
    total_correct_samples = 0
    error_cases = []
    
    # 比对每个匹配的记录
    for doc_id in matched_ids:
        truth = truth_data[doc_id]
        pred = pred_data[doc_id]
        
        field_results = compare_fields(truth, pred)
        sample_correct = True
        
        for field_name, is_correct, truth_val, pred_val in field_results:
            field_stats[field_name]['total'] += 1
            if is_correct:
                field_stats[field_name]['correct'] += 1
            else:
                sample_correct = False
                error_cases.append({
                    'doc_id': doc_id,
                    'field': field_name,
                    'truth': truth_val,
                    'pred': pred_val
                })
        
        if sample_correct:
            total_correct_samples += 1
    
    # 计算准确率
    field_accuracies = {}
    for field, stats in field_stats.items():
        if stats['total'] > 0:
            field_accuracies[field] = stats['correct'] / stats['total']
        else:
            field_accuracies[field] = 0.0
    
    overall_accuracy = total_correct_samples / len(matched_ids) if matched_ids else 0.0
    
    # 生成报告
    report_lines = []
    report_lines.append('# 基础信息字段抽取准确率评估报告')
    report_lines.append('')
    report_lines.append(f'**评估日期**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    report_lines.append(f'**真值样本数**: {len(truth_data)}')
    report_lines.append(f'**预测样本数**: {len(pred_data)}')
    report_lines.append(f'**成功配对数**: {len(matched_ids)}')
    report_lines.append('')
    
    # 字段准确率表格
    report_lines.append('## 各字段准确率')
    report_lines.append('')
    report_lines.append('| 字段 | 正确数 | 配对总数 | 准确率 |')
    report_lines.append('|------|--------|----------|--------|')
    
    field_names_cn = {
        'stock_code': '股票代码',
        'announcement_date': '公告日期',
        'announcement_title': '公告标题',
        'company_name': '公司名称',
        'report_year': '报告年度'
    }
    
    for field, stats in field_stats.items():
        acc = field_accuracies[field]
        report_lines.append(f"| {field_names_cn[field]} | {stats['correct']} | {stats['total']} | {acc:.2%} |")
    
    report_lines.append('')
    
    # 整体准确率
    report_lines.append('## 整体准确率')
    report_lines.append('')
    report_lines.append(f"**所有字段全部正确的样本比例**: {overall_accuracy:.2%} ({total_correct_samples}/{len(matched_ids)})")
    report_lines.append('')
    
    # 错误案例
    if error_cases:
        report_lines.append('## 错误案例（前10条）')
        report_lines.append('')
        report_lines.append('| doc_id | 字段 | 真值 | 模型输出 |')
        report_lines.append('|--------|------|------|----------|')
        
        for case in error_cases[:10]:
            truth_val = str(case['truth']) if case['truth'] is not None else 'null'
            pred_val = str(case['pred']) if case['pred'] is not None else 'null'
            if len(truth_val) > 50:
                truth_val = truth_val[:50] + '...'
            if len(pred_val) > 50:
                pred_val = pred_val[:50] + '...'
            report_lines.append(f"| {case['doc_id'][:12]}... | {field_names_cn[case['field']]} | {truth_val} | {pred_val} |")
    
    # 保存报告
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    # 打印汇总
    print('\n=== 评估结果汇总 ===')
    for field, stats in field_stats.items():
        acc = field_accuracies[field]
        print(f"{field_names_cn[field]}: {stats['correct']}/{stats['total']} ({acc:.2%})")
    print(f"\n整体准确率: {total_correct_samples}/{len(matched_ids)} ({overall_accuracy:.2%})")
    print(f"\n报告已保存到: {args.output}")


if __name__ == "__main__":
    main()
