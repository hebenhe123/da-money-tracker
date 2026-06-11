"""
PDF解析模块
使用MinerU或pdfplumber解析PDF文件
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import pdfplumber
from loguru import logger


class PDFParser:
    """PDF解析器"""

    def __init__(self, primary: str = "mineru", fallback: str = "pdfplumber"):
        """
        初始化PDF解析器

        Args:
            primary: 主解析器（mineru/pdfplumber）
            fallback: 备用解析器
        """
        self.primary = primary
        self.fallback = fallback
        self.mineru_cmd = os.getenv("MINERU_CMD", "mineru")

    def parse(self, pdf_path: Path) -> Optional[str]:
        """
        解析PDF为Markdown

        Args:
            pdf_path: PDF文件路径

        Returns:
            Markdown文本
        """
        if self.primary == "mineru":
            result = self._parse_with_mineru(pdf_path)
            if result:
                return result

        if self.fallback == "pdfplumber":
            return self._parse_with_pdfplumber(pdf_path)

        return None

    def _parse_with_mineru(self, pdf_path: Path) -> Optional[str]:
        """
        使用MinerU解析PDF

        Args:
            pdf_path: PDF文件路径

        Returns:
            Markdown文本
        """
        try:
            import subprocess

            cmd = [
                self.mineru_cmd,
                str(pdf_path),
                "--output", "-",
                "--format", "markdown"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                logger.info(f"MinerU解析成功: {pdf_path}")
                return result.stdout
            else:
                logger.warning(f"MinerU解析失败: {result.stderr}")
                return None

        except FileNotFoundError:
            logger.warning("MinerU未安装，尝试使用备用解析器")
            return None
        except Exception as e:
            logger.error(f"MinerU解析异常: {e}")
            return None

    def _parse_with_pdfplumber(self, pdf_path: Path) -> Optional[str]:
        """
        使用pdfplumber解析PDF

        Args:
            pdf_path: PDF文件路径

        Returns:
            Markdown文本
        """
        try:
            markdown_lines = []

            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        # 添加页码标记
                        markdown_lines.append(f"\n\n--- 第{page_num}页 ---\n\n")
                        markdown_lines.append(text)

            markdown_text = "\n".join(markdown_lines)
            logger.info(f"pdfplumber解析成功: {pdf_path}")
            return markdown_text

        except Exception as e:
            logger.error(f"pdfplumber解析失败: {e}")
            return None

    def parse_to_file(
        self,
        pdf_path: Path,
        output_path: Path
    ) -> bool:
        """
        解析PDF并保存到文件

        Args:
            pdf_path: PDF文件路径
            output_path: 输出文件路径

        Returns:
            是否成功
        """
        markdown_text = self.parse(pdf_path)

        if markdown_text:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_text)
            return True

        return False