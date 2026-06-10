#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中央总控脚本 - 数据采集全流程调度器

负责按顺序调用：
1. crawl_metadata.py - 抓取公告元数据
2. download_pdfs.py - 下载PDF文件
3. check_dataset.py - 检查数据集完整性

支持断点续跑、命令行参数、日志记录
"""

import os
import csv
import yaml
import json
import time
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any

from crawl_metadata import CNInfoCrawler
from download_pdfs import PDFDownloader
from check_dataset import DatasetChecker


class PipelineRunner:
    def __init__(self, config_path: str):
        """
        初始化管道运行器
        :param config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self._init_logging()
        self.state_file = os.path.join('outputs', 'pipeline_state.json')
        self.state = self._load_state()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _init_logging(self):
        """初始化日志系统"""
        log_dir = self.config['output'].get('logs_dir', 'outputs/logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_path = os.path.join(log_dir, 'pipeline.log')
        
        # 创建日志格式
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # 文件处理器
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # 配置根日志器
        self.logger = logging.getLogger('pipeline')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def _load_state(self) -> Dict[str, Any]:
        """加载上次执行状态"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_state(self, step_name: str, status: str, duration: float = 0):
        """保存步骤执行状态"""
        self.state[step_name] = {
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'duration': duration
        }
        
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
    
    def _is_step_completed(self, step_name: str) -> bool:
        """检查步骤是否已完成"""
        step_state = self.state.get(step_name, {})
        return step_state.get('status') == 'success'
    
    def _check_metadata_exists(self) -> bool:
        """检查元数据文件是否存在"""
        metadata_path = self.config['output']['metadata']
        return os.path.exists(metadata_path)
    
    def _check_metadata_completed(self) -> bool:
        """检查元数据是否完整（没有 Request failed 记录）"""
        metadata_path = self.config['output']['metadata']
        if not os.path.exists(metadata_path):
            return False
        
        with open(metadata_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('announcement_title') == 'Request failed':
                    return False
        return True
    
    def _check_download_completed(self) -> bool:
        """检查下载是否完成（所有记录都有success/skipped状态）"""
        metadata_path = self.config['output']['metadata']
        if not os.path.exists(metadata_path):
            return False
        
        with open(metadata_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                status = row.get('download_status', '')
                if status not in ('success', 'skipped'):
                    return False
        return True
    
    def _check_report_exists(self) -> bool:
        """检查报告文件是否存在"""
        report_path = os.path.join('outputs', 'reports', 'dataset_check_report.md')
        return os.path.exists(report_path)
    
    def run_crawl(self) -> bool:
        """执行元数据抓取步骤"""
        try:
            self.logger.info("="*50)
            self.logger.info("开始步骤: 抓取公告元数据")
            self.logger.info("="*50)
            
            # 初始化目录
            os.makedirs('data/metadata', exist_ok=True)
            os.makedirs('data/pdf', exist_ok=True)
            os.makedirs('outputs/logs', exist_ok=True)
            
            # 创建爬虫实例并执行
            crawler = CNInfoCrawler(self.config)
            records = crawler.crawl_all()
            crawler.save_to_csv(records, self.config['output']['metadata'])
            
            self.logger.info(f"元数据抓取完成，共获取 {len(records)} 条记录")
            return True
        except Exception as e:
            self.logger.error(f"元数据抓取失败: {str(e)}", exc_info=True)
            return False
    
    def run_download(self) -> bool:
        """执行PDF下载步骤"""
        try:
            self.logger.info("="*50)
            self.logger.info("开始步骤: 下载PDF文件")
            self.logger.info("="*50)
            
            # 检查元数据文件是否存在
            if not self._check_metadata_exists():
                self.logger.error("错误: 元数据文件不存在，请先执行抓取步骤")
                return False
            
            # 创建下载器实例并执行
            downloader = PDFDownloader(self.config)
            downloader.run()
            
            self.logger.info("PDF下载完成")
            return True
        except Exception as e:
            self.logger.error(f"PDF下载失败: {str(e)}", exc_info=True)
            return False
    
    def run_check(self) -> bool:
        """执行数据集检查步骤"""
        try:
            self.logger.info("="*50)
            self.logger.info("开始步骤: 检查数据集完整性")
            self.logger.info("="*50)
            
            # 创建检查器实例并执行
            checker = DatasetChecker(self.config)
            checker.run()
            
            self.logger.info("数据集检查完成")
            return True
        except Exception as e:
            self.logger.error(f"数据集检查失败: {str(e)}", exc_info=True)
            return False
    
    def run(self, steps_to_run: List[str] = None, force: bool = False):
        """
        执行管道流程
        :param steps_to_run: 指定要执行的步骤列表，None表示执行所有步骤
        :param force: 是否强制重新执行已完成的步骤
        """
        # 定义所有步骤
        all_steps = [
            {'name': 'crawl', 'func': self.run_crawl, 'required': True,
             'check_completed': self._check_metadata_completed,
             'description': '抓取公告元数据'},
            {'name': 'download', 'func': self.run_download, 'required': True,
             'check_completed': self._check_download_completed,
             'description': '下载PDF文件'},
            {'name': 'check', 'func': self.run_check, 'required': False,
             'check_completed': self._check_report_exists,
             'description': '检查数据集完整性'},
        ]
        
        # 确定要执行的步骤
        if steps_to_run:
            steps_to_execute = [step for step in all_steps if step['name'] in steps_to_run]
        else:
            steps_to_execute = all_steps
        
        # 执行步骤
        results = []
        for step in steps_to_execute:
            step_name = step['name']
            step_func = step['func']
            check_completed = step.get('check_completed')
            
            # 检查是否需要跳过（仅通过产物检查判断）
            if not force and check_completed and check_completed():
                self.logger.info(f"步骤 [{step_name}] 产物已存在，跳过执行")
                results.append({'name': step_name, 'status': 'skipped', 'duration': 0})
                continue
            
            # 执行步骤
            start_time = time.time()
            self.logger.info(f"开始执行步骤: {step['description']}")
            
            try:
                success = step_func()
                duration = time.time() - start_time
                
                if success:
                    self._save_state(step_name, 'success', duration)
                    results.append({'name': step_name, 'status': 'success', 'duration': duration})
                    self.logger.info(f"步骤 [{step_name}] 执行成功，耗时: {duration:.2f}秒")
                else:
                    self._save_state(step_name, 'failed', duration)
                    results.append({'name': step_name, 'status': 'failed', 'duration': duration})
                    self.logger.error(f"步骤 [{step_name}] 执行失败，耗时：{duration:.2f}秒")
                    
                    # 如果是必需步骤失败，直接停止执行
                    if step['required']:
                        self.logger.error("必需步骤失败，终止执行")
                        break
            except Exception as e:
                duration = time.time() - start_time
                self._save_state(step_name, 'failed', duration)
                results.append({'name': step_name, 'status': 'failed', 'duration': duration})
                self.logger.error(f"步骤 [{step_name}] 执行异常：{str(e)}，耗时：{duration:.2f}秒")
                
                # 如果是必需步骤异常，直接停止执行
                if step['required']:
                    self.logger.error("必需步骤异常，终止执行")
                    break
        
        # 输出执行结果汇总
        self.logger.info("="*50)
        self.logger.info("管道执行结果汇总")
        self.logger.info("="*50)
        
        for result in results:
            status_color = {
                'success': '✓',
                'failed': '✗',
                'skipped': '~'
            }.get(result['status'], '?')
            
            self.logger.info(f"{status_color} [{result['name']}] {result['status']} - 耗时: {result['duration']:.2f}秒")
        
        # 统计结果
        success_count = sum(1 for r in results if r['status'] == 'success')
        failed_count = sum(1 for r in results if r['status'] == 'failed')
        skipped_count = sum(1 for r in results if r['status'] == 'skipped')
        
        self.logger.info(f"\n执行统计: 成功={success_count} | 失败={failed_count} | 跳过={skipped_count}")
        
        if failed_count > 0:
            self.logger.warning("部分步骤执行失败，请查看日志获取详细信息")
            return False
        return True


def main():
    parser = argparse.ArgumentParser(description='中央总控脚本 - 数据采集全流程调度器')
    parser.add_argument('--all', action='store_true', help='执行全部步骤（默认）')
    parser.add_argument('--step', nargs='+', choices=['crawl', 'download', 'check'],
                        help='执行指定步骤（多个用空格分隔）')
    parser.add_argument('--force', action='store_true', help='强制重新执行已完成的步骤')
    parser.add_argument('--config', default='configs/crawl.yaml', help='指定配置文件路径')
    
    args = parser.parse_args()
    
    # 确定要执行的步骤
    if args.step:
        steps_to_run = args.step
    else:
        steps_to_run = None  # 执行全部步骤
    
    # 创建并运行管道
    runner = PipelineRunner(args.config)
    success = runner.run(steps_to_run, args.force)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
