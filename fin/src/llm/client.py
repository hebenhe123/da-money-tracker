"""
LLM客户端模块
提供统一的LLM调用接口
"""

import os
from typing import Dict, List, Optional, Any
from openai import OpenAI
from loguru import logger

# 导入统一配置
from ..config import (
    LLM_PROVIDER,
    LLM_BASE_URL,
    LLM_API_KEY,
    LLM_MODEL,
    LLM_TIMEOUT
)


class LLMClient:
    """LLM客户端"""

    def __init__(
        self,
        provider: str = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        timeout: int = None
    ):
        """
        初始化LLM客户端

        Args:
            provider: LLM提供商
            base_url: API基础URL
            api_key: API密钥
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            timeout: 超时时间（秒）
        """
        self.provider = provider or LLM_PROVIDER
        self.model = model or LLM_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout or LLM_TIMEOUT

        # 从环境变量获取配置
        base_url = base_url or LLM_BASE_URL
        api_key = api_key or LLM_API_KEY

        if not api_key:
            raise ValueError("LLM_API_KEY环境变量未设置")

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=self.timeout
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        聊天接口

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            响应文本
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                **kwargs
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise

    def extract_structured_data(
        self,
        prompt: str,
        schema: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        结构化数据抽取

        Args:
            prompt: 提示词
            schema: 数据结构定义
            **kwargs: 其他参数

        Returns:
            抽取的结构化数据
        """
        messages = [
            {
                "role": "system",
                "content": f"你是一个专业的信息抽取助手。请严格按照以下JSON Schema格式输出数据：\n{schema}"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        response_text = self.chat(messages, **kwargs)

        # 解析JSON响应
        import json
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"原始响应: {response_text}")
            raise

    def classify_text(
        self,
        text: str,
        categories: List[str],
        **kwargs
    ) -> Dict[str, float]:
        """
        文本分类

        Args:
            text: 待分类文本
            categories: 类别列表
            **kwargs: 其他参数

        Returns:
            分类结果 {category: score}
        """
        categories_str = "、".join(categories)

        prompt = f"""
请将以下文本分类到以下类别之一：{categories_str}

文本：
{text}

请输出JSON格式，包含每个类别的置信度分数（0-1之间）。
"""

        messages = [
            {
                "role": "system",
                "content": "你是一个专业的文本分类助手。请严格按照JSON格式输出分类结果。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        response_text = self.chat(messages, **kwargs)

        import json
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            raise