"""
章节路由模块
根据规则识别和分类文档章节
"""

import re
from typing import List, Dict, Optional, Any
from pathlib import Path
import yaml
from loguru import logger


class SectionRouter:
    """章节路由器"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化章节路由器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.section_types = self.config.get("section_types", {})
        self.scoring_config = self.config.get("scoring", {})
        self.dedup_config = self.config.get("deduplication", {})

    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """加载配置文件"""
        if config_path and config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)

        # 默认配置
        return {
            "section_types": {},
            "scoring": {
                "keyword_match_weight": 1.0,
                "title_match_weight": 0.8,
                "content_match_weight": 0.5,
                "min_score": 0.3
            },
            "deduplication": {
                "enabled": True,
                "strategy": "keep_parent",
                "similarity_threshold": 0.9
            }
        }

    def route(self, markdown_text: str) -> List[Dict[str, Any]]:
        """
        路由章节

        Args:
            markdown_text: Markdown文本

        Returns:
            章节列表
        """
        # 提取所有标题
        sections = self._extract_sections(markdown_text)

        # 分类章节
        classified_sections = []
        for section in sections:
            section_type = self._classify_section(section)
            if section_type:
                section["section_type"] = section_type
                classified_sections.append(section)

        # 去重
        if self.dedup_config.get("enabled", True):
            classified_sections = self._deduplicate_sections(classified_sections)

        return classified_sections

    def _extract_sections(self, markdown_text: str) -> List[Dict[str, Any]]:
        """
        提取章节

        Args:
            markdown_text: Markdown文本

        Returns:
            章节列表
        """
        sections = []
        lines = markdown_text.split("\n")

        current_section = None
        current_content = []

        for line in lines:
            # 检测标题
            if line.startswith("#"):
                # 保存上一个章节
                if current_section:
                    current_section["content"] = "\n".join(current_content).strip()
                    sections.append(current_section)

                # 开始新章节
                level = len(line) - len(line.lstrip("#"))
                title = line.lstrip("#").strip()
                current_section = {
                    "level": level,
                    "title": title,
                    "content": ""
                }
                current_content = []
            elif current_section:
                current_content.append(line)

        # 保存最后一个章节
        if current_section:
            current_section["content"] = "\n".join(current_content).strip()
            sections.append(current_section)

        return sections

    def _classify_section(self, section: Dict[str, Any]) -> Optional[str]:
        """
        分类章节

        Args:
            section: 章节信息

        Returns:
            章节类型
        """
        title = section.get("title", "")
        content = section.get("content", "")

        best_type = None
        best_score = self.scoring_config.get("min_score", 0.3)

        for section_type, config in self.section_types.items():
            score = self._calculate_score(title, content, config)
            if score > best_score:
                best_score = score
                best_type = section_type

        return best_type

    def _calculate_score(
        self,
        title: str,
        content: str,
        config: Dict[str, Any]
    ) -> float:
        """
        计算章节得分

        Args:
            title: 章节标题
            content: 章节内容
            config: 配置

        Returns:
            得分
        """
        score = 0.0

        # 关键词匹配
        include_keywords = config.get("include_keywords", [])
        exclude_keywords = config.get("exclude_keywords", [])

        # 标题匹配
        title_score = self._match_keywords(title, include_keywords, exclude_keywords)
        score += title_score * self.scoring_config.get("title_match_weight", 0.8)

        # 内容匹配
        content_score = self._match_keywords(content, include_keywords, exclude_keywords)
        score += content_score * self.scoring_config.get("content_match_weight", 0.5)

        return min(score, 1.0)

    def _match_keywords(
        self,
        text: str,
        include_keywords: List[str],
        exclude_keywords: List[str]
    ) -> float:
        """
        匹配关键词

        Args:
            text: 文本
            include_keywords: 包含关键词
            exclude_keywords: 排除关键词

        Returns:
            匹配得分
        """
        # 排除关键词
        for keyword in exclude_keywords:
            if keyword in text:
                return 0.0

        # 包含关键词
        match_count = 0
        for keyword in include_keywords:
            if keyword in text:
                match_count += 1

        if match_count == 0:
            return 0.0

        return match_count / len(include_keywords)

    def _deduplicate_sections(
        self,
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        去重章节

        Args:
            sections: 章节列表

        Returns:
            去重后的章节列表
        """
        strategy = self.dedup_config.get("strategy", "keep_parent")

        if strategy == "keep_parent":
            return self._keep_parent_sections(sections)
        elif strategy == "keep_child":
            return self._keep_child_sections(sections)
        else:
            return sections

    def _keep_parent_sections(
        self,
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """保留父章节"""
        result = []
        for i, section in enumerate(sections):
            is_duplicate = False
            for j in range(i + 1, len(sections)):
                if sections[j]["section_type"] == section["section_type"]:
                    is_duplicate = True
                    break

            if not is_duplicate:
                result.append(section)

        return result

    def _keep_child_sections(
        self,
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """保留子章节"""
        result = []
        for i, section in enumerate(sections):
            is_duplicate = False
            for j in range(i):
                if sections[j]["section_type"] == section["section_type"]:
                    is_duplicate = True
                    break

            if not is_duplicate:
                result.append(section)

        return result