"""
配置管理模块
从环境变量读取配置，提供统一的配置接口
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent.parent

# 数据目录配置
DATA_DIR = ROOT_DIR / os.getenv("DATA_DIR", "data")
PDF_DIR = DATA_DIR / os.getenv("PDF_DIR", "pdf")
MARKDOWN_DIR = DATA_DIR / os.getenv("MARKDOWN_DIR", "markdown")
METADATA_DIR = DATA_DIR / os.getenv("METADATA_DIR", "metadata")
PARSED_DIR = DATA_DIR / os.getenv("PARSED_DIR", "parsed")

# 输出目录配置
OUTPUT_DIR = ROOT_DIR / os.getenv("OUTPUT_DIR", "outputs")
LOG_DIR = OUTPUT_DIR / os.getenv("LOG_DIR", "logs")
RESULT_DIR = OUTPUT_DIR / os.getenv("RESULT_DIR", "results")
REPORT_DIR = OUTPUT_DIR / os.getenv("REPORT_DIR", "reports")

# LLM配置
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))

# 并发配置
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))

# MinerU配置
MINERU_CMD = os.getenv("MINERU_CMD", "mineru")


def init_directories() -> None:
    """初始化所有必要的目录"""
    directories = [
        DATA_DIR,
        PDF_DIR,
        MARKDOWN_DIR,
        METADATA_DIR,
        PARSED_DIR,
        OUTPUT_DIR,
        LOG_DIR,
        RESULT_DIR,
        REPORT_DIR
    ]
    
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
