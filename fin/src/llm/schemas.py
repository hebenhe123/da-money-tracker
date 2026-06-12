#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pydantic Schema定义 - 募集资金信息抽取字段规范
"""

from pydantic import BaseModel, Field
from typing import Optional


class FundUsage(BaseModel):
    """
    募集资金使用情况字段Schema
    """
    doc_id: str = Field(..., description="文档ID")
    project_name: str = Field(..., description="项目名称")
    investment_amount: Optional[str] = Field(None, description="投资金额")
    progress: Optional[str] = Field(None, description="投资进度")
    section_type: str = Field(..., description="章节类型")
    evidence: Optional[str] = Field(None, description="证据文本")
    extraction_confidence: Optional[float] = Field(None, description="抽取置信度")


class FundChange(BaseModel):
    """
    募集资金变更情况字段Schema
    """
    doc_id: str = Field(..., description="文档ID")
    project_name: str = Field(..., description="项目名称")
    original_project: Optional[str] = Field(None, description="原项目名称")
    new_project: Optional[str] = Field(None, description="新项目名称")
    change_reason: Optional[str] = Field(None, description="变更原因")
    section_type: str = Field(..., description="章节类型")
    evidence: Optional[str] = Field(None, description="证据文本")
    extraction_confidence: Optional[float] = Field(None, description="抽取置信度")


class FundDelay(BaseModel):
    """
    募集资金延期情况字段Schema
    """
    doc_id: str = Field(..., description="文档ID")
    project_name: str = Field(..., description="项目名称")
    original_date: Optional[str] = Field(None, description="原计划日期")
    new_date: Optional[str] = Field(None, description="延期后日期")
    delay_reason: Optional[str] = Field(None, description="延期原因")
    section_type: str = Field(..., description="章节类型")
    evidence: Optional[str] = Field(None, description="证据文本")
    extraction_confidence: Optional[float] = Field(None, description="抽取置信度")


class FundTermination(BaseModel):
    """
    募集资金终止情况字段Schema
    """
    doc_id: str = Field(..., description="文档ID")
    project_name: str = Field(..., description="项目名称")
    termination_reason: Optional[str] = Field(None, description="终止原因")
    termination_date: Optional[str] = Field(None, description="终止日期")
    section_type: str = Field(..., description="章节类型")
    evidence: Optional[str] = Field(None, description="证据文本")
    extraction_confidence: Optional[float] = Field(None, description="抽取置信度")


class FundBasicInfo(BaseModel):
    """
    募集资金基本情况字段Schema
    """
    doc_id: str = Field(..., description="文档ID")
    total_amount: Optional[str] = Field(None, description="募集资金总额")
    net_amount: Optional[str] = Field(None, description="实际募集资金净额")
    issue_date: Optional[str] = Field(None, description="发行日期")
    section_type: str = Field(..., description="章节类型")
    evidence: Optional[str] = Field(None, description="证据文本")
    extraction_confidence: Optional[float] = Field(None, description="抽取置信度")