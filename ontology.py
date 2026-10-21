from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


RelationType = Literal[
    "REQUESTS",
    "CONTAINS",
    "REQUIRES",
    "DEPENDS_ON",
    "DELIVERS",
    "PRODUCES",
    "ASSIGNED_TO",
    "HAS_COST",
]


class University(BaseModel):
    name: str
    region: Optional[str] = None
    type: Optional[str] = None


class PIProject(BaseModel):
    id: str
    name: str
    university: str
    objective: str
    scope: List[str] = Field(default_factory=list)
    duration_months: int
    complexity: str = "medium"


class BusinessProcess(BaseModel):
    id: str
    name: str
    department: Optional[str] = None
    pain_point: Optional[str] = None


class ProjectModule(BaseModel):
    id: str
    name: str
    base_workload_pm: int
    dependencies: List[str] = Field(default_factory=list)
    required_roles: List[str] = Field(default_factory=list)
    deliverables: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class Task(BaseModel):
    id: str
    name: str
    module_id: str
    effort_pm: int
    depends_on: List[str] = Field(default_factory=list)


class Role(BaseModel):
    name: str
    monthly_cost_krw: int
    focus: Optional[str] = None


class Deliverable(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None


class Outcome(BaseModel):
    id: str
    name: str
    type: Optional[str] = None
    description: Optional[str] = None


class CostItem(BaseModel):
    id: str
    category: str
    amount_krw: int
    basis: str


class KnowledgeRelation(BaseModel):
    source: str
    target: str
    relation: RelationType
