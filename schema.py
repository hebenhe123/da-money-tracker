#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
募集资金使用及变更定性分析 Pydantic Schema

定义项目级数据抽取的数据契约，用于结构化提取公告中募投项目的定性信息。
严格遵循 Null Rule：若文本中未提及或无法确定时必须输出 null，不得编造。
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from typing_extensions import Literal


class ProjectDetail(BaseModel):
    """
    单个募投项目的定性抽取结果
    
    代表一份公告中某个特定募投项目的定性分析信息。
    所有字段均需严格遵循 Null Rule，只能从公告文本中提取，不得编造。
    """
    
    project_name: str = Field(
        description="募投项目名称。必须从公告文本中提取的原文名称，严禁自行推断、合并或编造。"
    )
    
    risk_category: Optional[Literal[
        "市场风险",
        "行业竞争风险",
        "经营风险",
        "财务风险",
        "政策与合规风险",
        "其他风险",
        "无风险"
    ]] = Field(
        default=None,
        description=(
            "该募投项目面临的特定定性风险类别。"
            "必须从公告文本中明确提取或推断，若文本中未提及任何风险相关信息，必须输出 null。"
            "不得根据常识、公司整体情况或外部信息编造风险类别。"
        )
    )
    
    policy_impact: Optional[str] = Field(
        default=None,
        description=(
            "行业政策或宏观政策对该募投项目影响的定性描述。"
            "必须从公告文本中提取，若文本中未提及政策影响相关内容，必须输出 null。"
            "不得根据常识推断政策影响。"
        )
    )
    
    evidence_text: Optional[str] = Field(
        default=None,
        description=(
            "支持上述风险类别和政策影响判断的公告原文片段，必须是输入文本中的原句。"
            "若 risk_category 和 policy_impact 均为 null，则此字段也应为 null。"
            "不得对原文进行改写或概括，必须直接引用原文句子。"
        )
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_name": "高性能锂离子动力电池产业化项目",
                "risk_category": "市场风险",
                "policy_impact": "新能源汽车补贴政策退坡对项目收益产生一定影响",
                "evidence_text": "受新能源汽车补贴政策退坡影响，预计项目投资回收期将延长"
            }
        }
    )


class FundraisingReportExtract(BaseModel):
    """
    募集资金使用及变更定性分析报告的完整结构化结果
    
    承载整份公告中所有募投项目的定性抽取结果。
    每个项目独立抽取，项目之间无关联性。
    """
    
    doc_id: str = Field(
        description="公告唯一ID，对应输入JSON文件中的doc_id字段"
    )
    
    projects: List[ProjectDetail] = Field(
        description=(
            "募投项目列表，承载该公告中所有独立项目的定性抽取结果。"
            "每个项目对应一个 ProjectDetail 对象。"
            "若公告中未提及任何具体募投项目，则此列表为空列表 []。"
            "不得将公司整体情况作为项目信息填充。"
        )
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "doc_id": "300014_0d32b1f7651539af1c4d612792e8c2c4",
                "projects": [
                    {
                        "project_name": "高性能锂离子动力电池产业化项目",
                        "risk_category": "市场风险",
                        "policy_impact": "新能源汽车补贴政策退坡对项目收益产生一定影响",
                        "evidence_text": "受新能源汽车补贴政策退坡影响，预计项目投资回收期将延长"
                    },
                    {
                        "project_name": "荆门圆柱产品线新建产线二期项目",
                        "risk_category": None,
                        "policy_impact": None,
                        "evidence_text": None
                    }
                ]
            }
        }
    )


# 导出模型供外部使用
__all__ = ["ProjectDetail", "FundraisingReportExtract"]