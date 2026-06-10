import os
import re
import csv
import hashlib
import time
import yaml
import requests
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import quote

class CNInfoCrawler:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': 'http://www.cninfo.com.cn/',
            'X-Requested-With': 'XMLHttpRequest'
        })
        self.base_url = "https://www.cninfo.com.cn/new/fulltextSearch/full"
        
    def generate_doc_id(self, stock_code: str, publish_date: str, title: str) -> str:
        content = f"{stock_code}_{publish_date}_{title}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _parse_timestamp(self, timestamp: Any) -> str:
        """解析时间戳或字符串格式的时间"""
        if not timestamp:
            return ''
        try:
            if isinstance(timestamp, (int, float)):
                return datetime.fromtimestamp(int(timestamp) / 1000).strftime('%Y-%m-%d')
            return str(timestamp)
        except Exception:
            return str(timestamp)
    
    def get_announcements(self, stock_code: str, stock_name: str) -> List[Dict[str, Any]]:
        results = []
        page_num = 1
        total_pages = 1
        
        while page_num <= total_pages:
            try:
                params = {
                    'searchkey': stock_code,
                    'sdate': self.config['date_range']['start'],
                    'edate': self.config['date_range']['end'],
                    'isfulltext': 'false',
                    'sortName': 'pubdate',
                    'sortType': 'desc',
                    'pageNum': page_num,
                    'pageSize': 30,
                    'type': ''
                }
                
                response = self.session.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                total_pages = data.get('totalpages', 1)
                
                announcements = data.get('announcements', [])
                print(f"Page {page_num}/{total_pages}, found {len(announcements)} announcements")
                
                if announcements:
                    for item in announcements:
                        title = item.get('announcementTitle', '')
                        clean_title = re.sub(r'<[^>]+>', '', title)
                        
                        if self._match_keyword(clean_title):
                            publish_time = self._parse_timestamp(item.get('announcementTime', ''))
                            doc_id = self.generate_doc_id(stock_code, publish_time, clean_title)
                            
                            record = {
                                'doc_id': doc_id,
                                'stock_code': stock_code,
                                'stock_name': stock_name,
                                'market': 'sh' if stock_code.startswith('6') else 'sz',
                                'announcement_title': clean_title,
                                'announcement_type': self._classify_type(clean_title),
                                'publish_date': publish_time,
                                'url': item.get('adjunctUrl', ''),
                                'pdf_url': self._get_pdf_url(item),
                                'local_pdf_path': '',
                                'download_status': 'pending',
                                'source': 'cninfo',
                                'crawl_time': datetime.now().isoformat(),
                                'error_message': '',
                                'notes': ''
                            }
                            results.append(record)
                
                time.sleep(self.config['sleep_seconds'])
                page_num += 1
                
            except Exception as e:
                error_record = {
                    'doc_id': self.generate_doc_id(stock_code, str(datetime.now()), 'error'),
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'market': 'sh' if stock_code.startswith('6') else 'sz',
                    'announcement_title': 'Request failed',
                    'announcement_type': '',
                    'publish_date': '',
                    'url': '',
                    'pdf_url': '',
                    'local_pdf_path': '',
                    'download_status': 'failed',
                    'source': 'cninfo',
                    'crawl_time': datetime.now().isoformat(),
                    'error_message': str(e),
                    'notes': f'Page {page_num}'
                }
                results.append(error_record)
                break
        
        return results
    
    def _match_keyword(self, title: str) -> bool:
        keywords = self.config['keywords']
        for keyword in keywords:
            if keyword in title:
                return True
        return False
    
    def _classify_type(self, title: str) -> str:
        if '募集资金年度存放与使用情况专项报告' in title:
            return '募集资金年度存放与使用情况专项报告'
        elif '年度报告' in title:
            return '年度报告'
        else:
            return '其他'
    
    def _get_pdf_url(self, item: Dict[str, Any]) -> str:
        adjunct_url = item.get('adjunctUrl', '')
        if adjunct_url:
            return f"http://static.cninfo.com.cn/{adjunct_url}"
        return ''
    
    def crawl_all(self) -> List[Dict[str, Any]]:
        all_records = []
        max_records = self.config.get('max_records', 100)
        
        for company in self.config.get('companies', []):
            stock_code = company['stock_code']
            stock_name = company['stock_name']
            print(f"Crawling {stock_name} ({stock_code})...")
            
            records = self.get_announcements(stock_code, stock_name)
            
            for record in records:
                if len(all_records) >= max_records:
                    print(f"Reached maximum records limit: {max_records}")
                    return all_records
                all_records.append(record)
            
            print(f"Found {len(records)} records for {stock_name}, total: {len(all_records)}")
            time.sleep(self.config['sleep_seconds'])
        
        return all_records
    
    def save_to_csv(self, records: List[Dict[str, Any]], filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        fieldnames = [
            'doc_id', 'stock_code', 'stock_name', 'market',
            'announcement_title', 'announcement_type',
            'publish_date', 'url', 'pdf_url',
            'local_pdf_path', 'download_status',
            'source', 'crawl_time', 'error_message', 'notes'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        
        print(f"Saved {len(records)} records to {filepath}")

def main():
    config_path = 'configs/crawl.yaml'
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    os.makedirs('data/metadata', exist_ok=True)
    os.makedirs('data/pdf', exist_ok=True)
    os.makedirs('outputs/logs', exist_ok=True)
    
    crawler = CNInfoCrawler(config)
    
    # 测试模式（正式全量时注释掉）
    # config['max_records'] = 5
    
    records = crawler.crawl_all()
    crawler.save_to_csv(records, config['output']['metadata'])
    
    print("Metadata crawling completed successfully!")

if __name__ == "__main__":
    main()
