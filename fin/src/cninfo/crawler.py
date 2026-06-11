"""
巨潮资讯网爬虫模块
用于从巨潮资讯网下载募集资金相关公告PDF
"""

import requests
from typing import List, Dict, Optional
from pathlib import Path
import time
import logging

logger = logging.getLogger(__name__)


class CnInfoCrawler:
    """巨潮资讯网爬虫"""

    def __init__(self, base_url: str = "http://www.cninfo.com.cn"):
        self.base_url = base_url
        self.search_url = f"{base_url}/new/hisAnnouncement/query"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def search_announcements(
        self,
        stock_code: str = "",
        category: str = "010401",
        page_num: int = 1,
        page_size: int = 100
    ) -> List[Dict]:
        """
        搜索公告

        Args:
            stock_code: 股票代码，空表示全部
            category: 公告分类
            page_num: 页码
            page_size: 每页数量

        Returns:
            公告列表
        """
        params = {
            "stock": stock_code,
            "category": category,
            "pageNum": page_num,
            "pageSize": page_size
        }

        try:
            response = requests.post(
                self.search_url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if data.get("announcements"):
                return data["announcements"]
            return []

        except Exception as e:
            logger.error(f"搜索公告失败: {e}")
            return []

    def download_pdf(
        self,
        pdf_url: str,
        save_path: Path,
        retry: int = 3,
        delay: float = 1.0
    ) -> bool:
        """
        下载PDF文件

        Args:
            pdf_url: PDF下载链接
            save_path: 保存路径
            retry: 重试次数
            delay: 请求间隔（秒）

        Returns:
            是否下载成功
        """
        for attempt in range(retry):
            try:
                response = requests.get(pdf_url, headers=self.headers, timeout=30)
                response.raise_for_status()

                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(response.content)

                logger.info(f"PDF下载成功: {save_path}")
                return True

            except Exception as e:
                logger.warning(f"PDF下载失败（第{attempt + 1}次）: {e}")
                if attempt < retry - 1:
                    time.sleep(delay)

        logger.error(f"PDF下载失败: {pdf_url}")
        return False

    def batch_download(
        self,
        announcements: List[Dict],
        output_dir: Path,
        delay: float = 1.0
    ) -> Dict[str, bool]:
        """
        批量下载PDF

        Args:
            announcements: 公告列表
            output_dir: 输出目录
            delay: 请求间隔（秒）

        Returns:
            下载结果字典 {doc_id: success}
        """
        results = {}

        for idx, announcement in enumerate(announcements):
            doc_id = announcement.get("announcementId", "")
            pdf_url = announcement.get("adjunctUrl", "")

            if not doc_id or not pdf_url:
                logger.warning(f"跳过无效公告: {announcement}")
                continue

            save_path = output_dir / f"{doc_id}.pdf"
            success = self.download_pdf(pdf_url, save_path, delay=delay)
            results[doc_id] = success

            # 请求间隔
            if idx < len(announcements) - 1:
                time.sleep(delay)

        return results