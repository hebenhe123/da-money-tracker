#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import re
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Set, Tuple
from datetime import datetime

try:
    from openai import OpenAI, APIError, APIConnectionError, RateLimitError
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    from tqdm import tqdm
    from schema import FundraisingReportExtract
except ImportError as e:
    print(f"Import Error: {e}")     
    print("Please install dependencies: pip install openai tenacity tqdm pydantic")
    exit(1)

# ==================== CONFIGURATION ====================

API_KEY = os.getenv("SILICONFLOW_API_KEY")   
BASE_URL = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
MODEL_NAME = os.getenv("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-R1")

# Fixed path configuration
ROUTED_DIR = Path(__file__).parent.parent / "data" / "routed"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
OUTPUT_FILE = OUTPUT_DIR / "final_results.jsonl"
LOG_FILE = OUTPUT_DIR / "extract_all.log"    

MAX_RETRIES = 3
INITIAL_WAIT = 1  

# ==================== LOGGING CONFIGURATION ====================

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== SYSTEM PROMPT ====================

SYSTEM_PROMPT = """你是一个顶尖的金融文本结构化抽取专家，正在使用 deepseek-ai/DeepSeek-R1 模型进行工作。
【核心任务】请仔细分析局部的募集资金章节文本，提取出其中所有的"募投项目"及其定性风险和政策影响。
【Null Rule 原则】如果文本中完全没有提及某个项目的特定风险或政策影响，对应字段必须返回 null，严禁基于常识或公司整体情况进行任何编造、猜测或合并。
【原文证据原则】evidence_text 字段必须严格复用输入文本中的原句片段，严禁进行任何改写、润色或概括。
【项目识别原则】- 项目名称必须从文本中明确提取或合理推断 - 同一个公告可能包含多个不同的募投项目，每个项目需要独立抽取 - 不得将公司整体情况作为项目信息
【思考流程】请先进行思维链思考：
1. 文本中提到了哪些募投项目？
2. 每个项目有什么风险相关描述？       
3. 有哪些政策影响相关描述？      
4. 哪些信息是明确提及的，哪些是缺失的？

【输出要求】在思考结束后，请在回复的最后务必输出一个包裹在 ```json ... ``` 代码块中的JSON对象，其结构必须完全符合以下要求：
{       
  "doc_id": "公告唯一ID",
  "projects": [
    {
      "project_name": "募投项目名称",   
      "risk_category": "市场风险" 或 "行业竞争风险" 或 "经营风险" 或 "财务风险" 或 "政策与合规风险" 或 "其他风险" 或 "无风险" 或 null,
      "policy_impact": "政策影响描述" 或 null,
      "evidence_text": "原文片段" 或 null 
    }
  ]
}
注意：只在最后输出一个 JSON 代码块，不要输出多个代码块。"""       

# ==================== UTILITY FUNCTIONS ====================

def load_processed_doc_ids(output_file: Path) -> Set[str]:
    processed_ids = set()
    if output_file.exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()      
                    if line:
                        try:
                            data = json.loads(line)
                            doc_id = data.get('doc_id')
                            if doc_id:       
                                processed_ids.add(doc_id)
                        except json.JSONDecodeError:
                            continue
            logger.info(f"Loaded {len(processed_ids)} processed doc_ids.")
        except Exception as e:
            logger.error(f"Failed to load processed records: {e}")
    return processed_ids

def get_all_routed_files(routed_dir: Path) -> list[Path]:
    if not routed_dir.exists():
        raise FileNotFoundError(f"Directory does not exist: {routed_dir}")
    json_files = sorted(routed_dir.glob("*.json"))
    logger.info(f"Found {len(json_files)} JSON files.")
    return json_files

def read_routed_data(file_path: Path) -> Optional[dict]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        try:
            data = json.loads(content)
            return data
        except json.JSONDecodeError:
            pass
        
        objects = []
        brace_count = 0
        current_obj = []
        in_string = False
        escape = False
        
        for char in content:
            if escape:
                current_obj.append(char)
                escape = False
                continue
            
            if char == '\\' and in_string:
                current_obj.append(char)
                escape = True
                continue
            
            if char == '"':
                in_string = not in_string
                current_obj.append(char)
                continue
            
            if not in_string:
                if char == '{':
                    brace_count += 1
                    current_obj.append(char)
                elif char == '}':
                    brace_count -= 1
                    current_obj.append(char)
                    if brace_count == 0:
                        try:
                            obj_str = ''.join(current_obj)
                            obj = json.loads(obj_str)
                            objects.append(obj)
                        except json.JSONDecodeError:
                            pass
                        current_obj = []
                elif brace_count > 0:
                    current_obj.append(char)
        
        if len(objects) >= 2:
            logger.debug(f"File {file_path.name} has {len(objects)} JSON objects, using the second one")
            return objects[1]
        elif len(objects) == 1:
            return objects[0]
        else:
            logger.error(f"Failed to parse any valid JSON object from {file_path.name}")
            return None
            
    except json.JSONDecodeError as e:        
        logger.error(f"Failed to parse {file_path.name}: JSON format error - {e}")   
        return None
    except Exception as e:
        logger.error(f"Failed to read {file_path.name}: {e}")
        return None

def prepare_input_text(data: dict) -> Optional[Tuple[str, str]]:
    doc_id = data.get('doc_id', '')
    sections = data.get('sections', [])      
    
    if isinstance(sections, dict):
        logger.debug(f"File {doc_id} sections is dict, converting to list")
        sections_list = []
        for key, value in sections.items():
            if isinstance(value, dict):
                section_item = {
                    'section_type': key,
                    'section_title': value.get('title', ''),
                    'section_text': value.get('content', '')
                }
                sections_list.append(section_item)
            sections = sections_list
    
    if not isinstance(sections, list) or len(sections) == 0:
        logger.warning(f"File {doc_id} sections is empty or not a list.")
        return None

    combined_text = ""
    for idx, section in enumerate(sections, 1):
        section_type = section.get('section_type', 'unknown')
        title = section.get('section_title', '')
        text = section.get('section_text', '')
        if text:
            combined_text += f"【章节{idx} - {section_type}】{title}\n{text}\n\n"

    if not combined_text.strip():
        logger.warning(f"File {doc_id} has no text content in sections.")
        return None

    return doc_id, combined_text

def extract_json_from_response(response_text: str) -> Optional[str]:
    pattern = r'```json\s*([\s\S]*?)\s*```'   
    matches = re.findall(pattern, response_text)
    if matches:
        return matches[-1].strip()

    pattern = r'```\s*([\s\S]*?)\s*```'
    matches = re.findall(pattern, response_text)
    if matches:
        return matches[-1].strip()
    return None

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=INITIAL_WAIT, max=10),
    retry=retry_if_exception_type((APIConnectionError, RateLimitError)),
    before_sleep=lambda retry_state: logger.warning(
        f"Retry attempt {retry_state.attempt_number}, waiting {retry_state.next_action.sleep} seconds."
    )
)
def call_llm(client: OpenAI, system_prompt: str, user_prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0,
        max_tokens=4096,
    )
    return response.choices[0].message.content

def extract_with_llm(client: OpenAI, doc_id: str, input_text: str) -> Optional[FundraisingReportExtract]:
    try:
        user_prompt = f"请分析以下募集资金文本，doc_id = \"{doc_id}\"\n\n{input_text}"
        response_text = call_llm(client, SYSTEM_PROMPT, user_prompt)

        if not response_text:
            logger.error(f"Model returned empty response - doc_id: {doc_id}")
            return None

        json_str = extract_json_from_response(response_text)
        if not json_str:
            logger.error(f"Failed to extract JSON block from response - doc_id: {doc_id}")  
            return None

        try:
            result = FundraisingReportExtract.model_validate_json(json_str)
            if result.doc_id != doc_id:      
                logger.warning(f"doc_id mismatch in response, corrected - {result.doc_id} -> {doc_id}")
                result.doc_id = doc_id       
            return result
        except Exception as e:
            logger.error(f"JSON validation failed - doc_id: {doc_id}, error: {e}")
            return None

    except Exception as e:
        logger.error(f"LLM extraction failed - doc_id: {doc_id}, error: {e}")
        return None

def save_result(result: FundraisingReportExtract, output_file: Path):
    try:
        result_dict = result.model_dump(mode='json')
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result_dict, ensure_ascii=False) + '\n')
    except Exception as e:
        logger.error(f"Failed to save result - doc_id: {result.doc_id}, error: {e}")      

def print_statistics(start_time: datetime, total_files: int, success_count: int,
                     skip_count: int, fail_count: int, output_file: Path):
    end_time = datetime.now()
    duration = end_time - start_time

    print("\n" + "="*70)
    print(" Batch Extraction Task Report")
    print("="*70)
    print(f" Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Duration: {duration.total_seconds():.2f} seconds")
    print("-"*70)
    print(f" Total Files: {total_files}")
    print(f" Success: {success_count} ({success_count/total_files*100:.1f}%)")
    print(f" Skipped: {skip_count} ({skip_count/total_files*100:.1f}%)")
    print(f" Failed: {fail_count} ({fail_count/total_files*100:.1f}%)")
    print("-"*70)
    print(f" Output File: {output_file}")
    print(f" Log File: {LOG_FILE}")  
    print("="*70)

    logger.info(f"Task finished - Total: {total_files}, Success: {success_count}, Skipped: {skip_count}, Failed: {fail_count}")

# ==================== MAIN FUNCTION ====================

def main():
    start_time = datetime.now()

    logger.info("="*70)
    logger.info(f"Starting batch extraction task. Model: {MODEL_NAME}")
    logger.info("="*70)

    if not API_KEY:
        logger.error("Error: SILICONFLOW_API_KEY environment variable not set.")
        return

    try:       
        client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        logger.info("SiliconFlow client initialized successfully.")
    except Exception as e:
        logger.error(f"SiliconFlow client initialization failed: {e}")
        return

    processed_ids = load_processed_doc_ids(OUTPUT_FILE)

    try:       
        all_files = get_all_routed_files(ROUTED_DIR)
    except Exception as e:
        logger.error(f"Failed to scan directory: {e}")
        return

    if not all_files:
        logger.error("No JSON files found in the target directory.")
        return

    success_count = 0
    skip_count = 0
    fail_count = 0

    with tqdm(total=len(all_files), desc="Processing progress", unit="file") as pbar:      
        for file_path in all_files:
            try:
                data = read_routed_data(file_path)
                if not data:
                    fail_count += 1
                    pbar.update(1)
                    continue

                doc_id = data.get('doc_id', '')
                if doc_id in processed_ids:  
                    logger.info(f"Skipping already processed file: {doc_id}")
                    skip_count += 1
                    pbar.update(1)
                    continue

                input_data = prepare_input_text(data)
                if not input_data:
                    skip_count += 1
                    pbar.update(1)
                    continue

                _, input_text = input_data   

                result = extract_with_llm(client, doc_id, input_text)

                if result:
                    save_result(result, OUTPUT_FILE)
                    success_count += 1       
                    logger.info(f"Successfully processed: {doc_id}")
                else:
                    fail_count += 1
                    logger.warning(f"Failed to process: {doc_id}")

            except Exception as e:
                fail_count += 1
                logger.error(f"Exception raised while processing {file_path.name}: {e}")

            pbar.update(1)

    print_statistics(
        start_time=start_time,
        total_files=len(all_files),
        success_count=success_count,
        skip_count=skip_count,
        fail_count=fail_count,
        output_file=OUTPUT_FILE
    )

if __name__ == "__main__":
    main()