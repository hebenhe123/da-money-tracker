import os
import csv
import yaml
from collections import Counter
from typing import List, Dict, Tuple

class DatasetChecker:
    def __init__(self, config: Dict):
        self.config = config
        self.keywords = config.get('keywords', [])
    
    def load_metadata(self, metadata_path: str) -> List[Dict]:
        records = []
        with open(metadata_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
        return records
    
    def check_duplicates(self, records: List[Dict]) -> Tuple[List[str], int]:
        doc_ids = [record['doc_id'] for record in records]
        counter = Counter(doc_ids)
        duplicates = [doc_id for doc_id, count in counter.items() if count > 1]
        return duplicates, len(duplicates)
    
    def check_download_status(self, records: List[Dict]) -> Tuple[int, int, int]:
        success = 0
        failed = 0
        skipped = 0
        
        for record in records:
            status = record.get('download_status', '')
            if status == 'success':
                success += 1
            elif status == 'failed':
                failed += 1
            elif status == 'skipped':
                skipped += 1
        
        return success, failed, skipped
    
    def check_missing_pdfs(self, records: List[Dict]) -> List[Dict]:
        missing = []
        pdf_dir = self.config['output']['pdf_dir']
        
        for record in records:
            local_path = record.get('local_pdf_path', '')
            if local_path and not os.path.exists(local_path):
                missing.append(record)
        
        return missing
    
    def check_relevance(self, records: List[Dict], top_n: int = 5) -> List[Dict]:
        irrelevant = []
        
        for record in records:
            title = record.get('announcement_title', '')
            matched = False
            
            for keyword in self.keywords:
                if keyword in title:
                    matched = True
                    break
            
            if not matched:
                irrelevant.append(record)
                if len(irrelevant) >= top_n:
                    break
        
        return irrelevant
    
    def generate_report(self, records: List[Dict]) -> str:
        total_records = len(records)
        duplicates, duplicate_count = self.check_duplicates(records)
        success_count, failed_count, skipped_count = self.check_download_status(records)
        missing_pdfs = self.check_missing_pdfs(records)
        irrelevant_samples = self.check_relevance(records)
        
        report = f"""# 数据集检查报告

生成时间: {__import__('datetime').datetime.now().isoformat()}

---

## 1. 总记录数

- **总数**: {total_records}

## 2. PDF 下载状态统计

| 状态 | 数量 | 占比 |
|------|------|------|
| 成功 | {success_count} | {(success_count/total_records*100):.1f}% |
| 失败 | {failed_count} | {(failed_count/total_records*100):.1f}% |
| 跳过 | {skipped_count} | {(skipped_count/total_records*100):.1f}% |

## 3. 缺失 PDF 文件数

- **缺失数量**: {len(missing_pdfs)}

## 4. 重复记录检查

- **重复 doc_id 数量**: {duplicate_count}

{"### 重复 doc_id 列表:\n" + "\n".join([f"- {doc_id}" for doc_id in duplicates]) if duplicates else ""}

## 5. 可能不相关公告样例

- **发现不相关样例数**: {len(irrelevant_samples)}

{"### 样例列表:\n" + "\n".join([f"- [{record['stock_name']} ({record['stock_code']})] {record['announcement_title']}" for record in irrelevant_samples]) if irrelevant_samples else "未发现不相关公告样例"}

## 6. 检查总结

| 检查项 | 结果 | 状态 |
|--------|------|------|
| 总记录数 | {total_records} | {'通过' if total_records > 0 else '警告'} |
| PDF 下载成功率 | {(success_count/total_records*100):.1f}% | {'通过' if success_count/total_records >= 0.8 else '警告'} |
| 重复记录 | {duplicate_count} | {'通过' if duplicate_count == 0 else '警告'} |
| 缺失 PDF | {len(missing_pdfs)} | {'通过' if len(missing_pdfs) == 0 else '警告'} |

---

**数据来源**: {self.config['output']['metadata']}
**PDF 目录**: {self.config['output']['pdf_dir']}

"""
        
        return report
    
    def run(self):
        metadata_path = self.config['output']['metadata']
        
        if not os.path.exists(metadata_path):
            print(f"错误: 元数据文件不存在 - {metadata_path}")
            return
        
        records = self.load_metadata(metadata_path)
        report = self.generate_report(records)
        
        report_dir = 'outputs/reports'
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, 'dataset_check_report.md')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"数据集检查报告已生成: {report_path}")

def main():
    config_path = 'configs/crawl.yaml'
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    checker = DatasetChecker(config)
    checker.run()

if __name__ == "__main__":
    main()