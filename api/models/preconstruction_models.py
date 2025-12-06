"""
Pydantic models for AI Project Analyzer Pre-Construction Phase
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ===================== REQUEST MODELS =====================

class WorkerProfile(BaseModel):
    """Represents an available worker for matching"""
    worker_id: str
    name: str
    trades: List[str] = Field(..., description="List of trades the worker is skilled in")
    certifications: List[str] = Field(default_factory=list)
    reliability_score: float = Field(default=0.8, ge=0.0, le=1.0, description="0-1 scale")
    past_projects: List[str] = Field(default_factory=list, description="Past project types")
    hourly_rate: Optional[float] = None
    availability_start_week: Optional[int] = None
    availability_end_week: Optional[int] = None


class PreConstructionAnalysisRequest(BaseModel):
    """Request body for AI Adaptive Project Analyzer"""
    project_description: str = Field(..., description="Required: Basic project description")
    boq_text: Optional[str] = Field(None, description="Optional: Bill of Quantities text")
    plans_text: Optional[str] = Field(None, description="Optional: Project plans description/text")
    schedule_text: Optional[str] = Field(None, description="Optional: Project schedule/timeline")
    other_docs: Optional[str] = Field(None, description="Optional: Other relevant documents")
    available_workers: Optional[List[WorkerProfile]] = Field(None, description="Optional: Available workers for matching")


# ===================== RESPONSE MODELS =====================

class InputEvaluation(BaseModel):
    """Evaluation of provided input documents"""
    has_boq: bool
    has_plans: bool
    has_schedule: bool
    missing_items: List[str]


class ProjectSummary(BaseModel):
    """High-level project information"""
    project_type: str = Field(..., description="e.g., Residential, Commercial, Infrastructure")
    location: Optional[str] = None
    duration_weeks: Optional[int] = None
    overall_scope_interpretation: str
    assumptions_used: List[str]


class TradeRequirement(BaseModel):
    """Trade requirement for a work package"""
    trade: str
    estimated_headcount: Optional[int] = None
    start_week: Optional[int] = None
    end_week: Optional[int] = None


class WorkPackage(BaseModel):
    """Individual work package in the project"""
    name: str
    phase: str
    start_week: Optional[int] = None
    end_week: Optional[int] = None
    trades_required: List[TradeRequirement]


class WeeklyTrade(BaseModel):
    """Trade allocation for a specific week"""
    trade: str
    headcount: Optional[int] = None


class ManpowerWeek(BaseModel):
    """Weekly manpower breakdown"""
    week: int
    trades: List[WeeklyTrade]
    total_headcount: Optional[int] = None


class LaborCostEstimate(BaseModel):
    """Labor cost estimation"""
    estimated_total_cost: Optional[float] = None
    uncertainty_range_percent: Optional[float] = Field(None, description="Confidence uncertainty range")
    notes: str = ""


class SkillGapAnalysis(BaseModel):
    """Analysis of skill gaps and hiring needs"""
    missing_trades: List[str]
    trades_with_shortages: List[str]
    recommended_hiring_actions: List[str]


class RiskAnalysis(BaseModel):
    """Project risk identification and mitigation"""
    identified_risks: List[str]
    risk_severity: str = Field(..., description="CRITICAL, HIGH, MEDIUM, or LOW")
    recommended_mitigations: List[str]


class WorkerMatchResult(BaseModel):
    """Recommended deployment for a worker"""
    worker_id: str
    worker_name: str
    assigned_trades: List[str]
    assigned_weeks: List[int]
    match_score: float = Field(..., ge=0.0, le=1.0)
    deployment_recommendation: str


class PreConstructionAnalysisResponse(BaseModel):
    """Complete response from AI Adaptive Project Analyzer"""
    input_evaluation: InputEvaluation
    project_summary: ProjectSummary
    work_packages: List[WorkPackage]
    manpower_curve: List[ManpowerWeek]
    labor_cost_estimate: LaborCostEstimate
    skill_gap_analysis: SkillGapAnalysis
    risk_analysis: RiskAnalysis
    clarification_questions: List[str]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    worker_recommendations: Optional[List[WorkerMatchResult]] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict)


# ===================== INTERNAL HELPER MODELS =====================

class GPTPromptBuilder(BaseModel):
    """Helper to build and validate GPT prompts"""
    system_prompt: str
    user_prompt: str


class AnalysisConfig(BaseModel):
    """Configuration for analysis process"""
    use_gpt_extraction: bool = True
    include_worker_matching: bool = True
    confidence_level: str = "medium"  # low, medium, high
    include_cost_estimation: bool = True
