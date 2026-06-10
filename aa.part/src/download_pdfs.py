import os
import csv
import time
import yaml
import requests
from datetime import datetime
from typing import List, Dict

class PDFDownloader:
    def __init__(self, config: Dict):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf, application/octet-stream',
            'Referer': 'http://www.cninfo.com.cn/'
        })
        self.max_retries = 3
        self.sleep_seconds = config.get('sleep_seconds', 1.5)
        self.failed_records = []
        
    def download_pdf(self, pdf_url: str, local_path: str) -> bool:
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(pdf_url, stream=True, timeout=30)
                response.raise_for_status()
                
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                if os.path.getsize(local_path) < 100:
                    os.remove(local_path)
                    if attempt < self.max_retries - 1:
                        time.sleep(self.sleep_seconds * 2)
                        continue
                    return False
                
                return True
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.sleep_seconds * (attempt + 1))
                    continue
                return False
        
        return False
    
    def load_metadata(self, metadata_path: str) -> List[Dict]:
        records = []
        with open(metadata_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
        return records
    
    def save_metadata(self, records: List[Dict], metadata_path: str):
        fieldnames = records[0].keys() if records else []
        with open(metadata_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
    
    def save_failed_log(self):
        log_dir = self.config['output']['logs_dir']
        os.makedirs(log_dir, exist_ok=True)
        
        log_path = self.config['output']['failed_downloads']
        with open(log_path, 'a', encoding='utf-8') as f:
            for record in self.failed_records:
                f.write(f"{datetime.now().isoformat()} | {record['stock_code']} | {record['stock_name']} | {record['pdf_url']} | {record['error_message']}\n")
    
    def run(self):
        metadata_path = self.config['output']['metadata']
        pdf_dir = self.config['output']['pdf_dir']
        
        os.makedirs(pdf_dir, exist_ok=True)
        
        records = self.load_metadata(metadata_path)
        total = len(records)
        success_count = 0
        skip_count = 0
        failed_count = 0
        
        print(f"Starting PDF download...")
        print(f"Total records to process: {total}")
        
        for i, record in enumerate(records, 1):
            pdf_url = record.get('pdf_url', '')
            stock_code = record.get('stock_code', '')
            
            if not pdf_url:
                record['download_status'] = 'skipped'
                record['error_message'] = 'No PDF URL'
                skip_count += 1
                continue
            
            filename = f"{stock_code}_{record['doc_id']}.pdf"
            local_path = os.path.join(pdf_dir, filename)
            record['local_pdf_path'] = local_path
            
            if os.path.exists(local_path):
                record['download_status'] = 'skipped'
                record['notes'] = 'File already exists'
                skip_count += 1
                print(f"[{i}/{total}] SKIPPED: {filename} (already exists)")
                time.sleep(self.sleep_seconds)
                continue
            
            print(f"[{i}/{total}] DOWNLOADING: {filename}")
            
            if self.download_pdf(pdf_url, local_path):
                record['download_status'] = 'success'
                success_count += 1
                print(f"[{i}/{total}] SUCCESS: {filename}")
            else:
                record['download_status'] = 'failed'
                error_msg = f"Failed after {self.max_retries} attempts"
                record['error_message'] = error_msg
                failed_count += 1
                
                self.failed_records.append({
                    'stock_code': stock_code,
                    'stock_name': record.get('stock_name', ''),
                    'pdf_url': pdf_url,
                    'error_message': error_msg
                })
                print(f"[{i}/{total}] FAILED: {filename} - {error_msg}")
            
            time.sleep(self.sleep_seconds)
        
        self.save_metadata(records, metadata_path)
        
        if self.failed_records:
            self.save_failed_log()
        
        print(f"\nDownload completed!")
        print(f"Success: {success_count}")
        print(f"Skipped: {skip_count}")
        print(f"Failed: {failed_count}")
        
        if failed_count > 0:
            print(f"Failed downloads logged to: {self.config['output']['failed_downloads']}")

def main():
    config_path = 'configs/crawl.yaml'
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    downloader = PDFDownloader(config)
    downloader.run()

if __name__ == "__main__":
    main()