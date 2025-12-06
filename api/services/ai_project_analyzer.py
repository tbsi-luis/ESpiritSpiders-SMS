"""
AI Adaptive Project Analyzer Service
Handles extraction, inference, and manpower forecasting for pre-construction phase
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI

from config import get_settings
from config_crew_templates import (
    TRADE_DEFINITIONS,
    DEFAULT_WORK_PACKAGES,
    CONFIDENCE_MULTIPLIERS,
    WORKER_MATCH_WEIGHTS,
    DEFAULT_ASSUMPTIONS,
    RISK_CATEGORIES
)
from models.preconstruction_models import (
    PreConstructionAnalysisRequest,
    PreConstructionAnalysisResponse,
    InputEvaluation,
    ProjectSummary,
    WorkPackage,
    TradeRequirement,
    ManpowerWeek,
    WeeklyTrade,
    LaborCostEstimate,
    SkillGapAnalysis,
    RiskAnalysis,
    WorkerMatchResult
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are PN-AI: Adaptive Project Analyzer, an expert AI for construction manpower forecasting.
You must generate a full manpower plan even when documents are fully available, partially available, or missing.

Your jobs:
1. Identify which documents are present or missing.
2. When documents are present: extract work packages, required trades, manpower per trade, weekly manpower curve, and labor cost.
3. When documents are missing: infer work packages, manpower needs, schedule phases, confidence level, and questions to ask the client.
4. Identify risks and recommend mitigation.
5. Follow the JSON schema strictly.

IMPORTANT: Return ONLY valid JSON, no markdown formatting, no code blocks."""


class AIProjectAnalyzer:
    """Main analyzer service"""

    def __init__(self):
        """Initialize OpenAI client and settings"""
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.model = self.settings.OPENAI_MODEL or "gpt-4"
        self.temperature = self.settings.OPENAI_TEMPERATURE

    def analyze(self, request: PreConstructionAnalysisRequest) -> PreConstructionAnalysisResponse:
        """
        Main entry point for project analysis
        
        Args:
            request: PreConstructionAnalysisRequest with project details
            
        Returns:
            PreConstructionAnalysisResponse with complete manpower plan
        """
        try:
            logger.info("Starting AI Adaptive Project Analysis")

            # Step 1: Evaluate input documents
            input_eval = self._evaluate_input(request)

            # Step 2: Build GPT prompt
            gpt_input = self._build_gpt_prompt(request, input_eval)

            # Step 3: Call OpenAI for analysis
            gpt_response = self._call_openai(gpt_input)

            # Step 4: Parse and validate response
            parsed_response = self._parse_gpt_response(gpt_response, input_eval)

            # Step 5: Enrich with crew templates and calculations
            enriched_response = self._enrich_with_crew_templates(parsed_response, request)

            # Step 6: Match workers if available
            if request.available_workers:
                worker_matches = self._match_workers(enriched_response, request.available_workers)
                enriched_response.worker_recommendations = worker_matches

            logger.info("Analysis completed successfully")
            return enriched_response

        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}", exc_info=True)
            raise

    def _evaluate_input(self, request: PreConstructionAnalysisRequest) -> InputEvaluation:
        """Evaluate which documents are provided"""
        has_boq = bool(request.boq_text and request.boq_text.strip())
        has_plans = bool(request.plans_text and request.plans_text.strip())
        has_schedule = bool(request.schedule_text and request.schedule_text.strip())

        missing_items = []
        if not has_boq:
            missing_items.append("Bill of Quantities (BOQ)")
        if not has_plans:
            missing_items.append("Project Plans")
        if not has_schedule:
            missing_items.append("Schedule/Timeline")

        return InputEvaluation(
            has_boq=has_boq,
            has_plans=has_plans,
            has_schedule=has_schedule,
            missing_items=missing_items
        )

    def _build_gpt_prompt(self, request: PreConstructionAnalysisRequest, input_eval: InputEvaluation) -> str:
        """Build comprehensive prompt for GPT"""
        prompt_parts = [
            "Analyze the following construction project and generate a complete manpower plan.\n"
        ]

        # Add input evaluation context
        prompt_parts.append("INPUT DOCUMENTS AVAILABLE:")
        prompt_parts.append(f"- BOQ: {'YES' if input_eval.has_boq else 'NO'}")
        prompt_parts.append(f"- Plans: {'YES' if input_eval.has_plans else 'NO'}")
        prompt_parts.append(f"- Schedule: {'YES' if input_eval.has_schedule else 'NO'}")
        prompt_parts.append("")

        # Add project description
        prompt_parts.append("PROJECT DESCRIPTION:")
        prompt_parts.append(request.project_description)
        prompt_parts.append("")

        # Add optional documents if provided
        if request.boq_text:
            prompt_parts.append("BILL OF QUANTITIES:")
            prompt_parts.append(request.boq_text[:2000])  # Limit to 2000 chars
            prompt_parts.append("")

        if request.plans_text:
            prompt_parts.append("PLANS INFORMATION:")
            prompt_parts.append(request.plans_text[:2000])  # Limit to 2000 chars
            prompt_parts.append("")

        if request.schedule_text:
            prompt_parts.append("SCHEDULE/TIMELINE:")
            prompt_parts.append(request.schedule_text[:2000])  # Limit to 2000 chars
            prompt_parts.append("")

        if request.other_docs:
            prompt_parts.append("OTHER DOCUMENTS:")
            prompt_parts.append(request.other_docs[:1000])  # Limit to 1000 chars
            prompt_parts.append("")

        # Add output schema requirements
        prompt_parts.append(self._get_schema_description())

        return "\n".join(prompt_parts)

    def _get_schema_description(self) -> str:
        """Get JSON schema requirements for GPT"""
        return """
REQUIRED JSON OUTPUT SCHEMA (respond with ONLY this JSON, no markdown):
{
  "input_evaluation": {
    "has_boq": boolean,
    "has_plans": boolean,
    "has_schedule": boolean,
    "missing_items": [string]
  },
  "project_summary": {
    "project_type": string (Residential/Commercial/Infrastructure/Other),
    "location": string or null,
    "duration_weeks": number or null,
    "overall_scope_interpretation": string,
    "assumptions_used": [string]
  },
  "work_packages": [
    {
      "name": string,
      "phase": string,
      "start_week": number or null,
      "end_week": number or null,
      "trades_required": [
        {"trade": string, "estimated_headcount": number or null}
      ]
    }
  ],
  "manpower_curve": [
    {
      "week": number,
      "trades": [
        {"trade": string, "headcount": number or null}
      ],
      "total_headcount": number or null
    }
  ],
  "labor_cost_estimate": {
    "estimated_total_cost": number or null,
    "uncertainty_range_percent": number or null,
    "notes": string
  },
  "skill_gap_analysis": {
    "missing_trades": [string],
    "trades_with_shortages": [string],
    "recommended_hiring_actions": [string]
  },
  "risk_analysis": {
    "identified_risks": [string],
    "risk_severity": string (CRITICAL/HIGH/MEDIUM/LOW),
    "recommended_mitigations": [string]
  },
  "clarification_questions": [string],
  "confidence_score": number between 0 and 1
}
"""

    def _call_openai(self, user_prompt: str) -> str:
        """Call OpenAI API with system and user prompts"""
        try:
            logger.info(f"Calling OpenAI API with model: {self.model}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=4000,
                response_format={"type": "json_object"}  # Force JSON response
            )

            result = response.choices[0].message.content
            logger.info("OpenAI API call successful")
            return result

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise

    def _parse_gpt_response(self, gpt_response: str, input_eval: InputEvaluation) -> PreConstructionAnalysisResponse:
        """Parse and validate GPT response"""
        try:
            logger.info("Parsing GPT response")

            # Clean response if needed
            response_text = gpt_response.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            response_text = response_text.strip()

            # Parse JSON
            parsed = json.loads(response_text)

            # Build response object with validation
            response = PreConstructionAnalysisResponse(
                input_evaluation=InputEvaluation(**parsed.get("input_evaluation", {})),
                project_summary=ProjectSummary(**parsed.get("project_summary", {})),
                work_packages=[WorkPackage(**wp) for wp in parsed.get("work_packages", [])],
                manpower_curve=[ManpowerWeek(**mc) for mc in parsed.get("manpower_curve", [])],
                labor_cost_estimate=LaborCostEstimate(**parsed.get("labor_cost_estimate", {})),
                skill_gap_analysis=SkillGapAnalysis(**parsed.get("skill_gap_analysis", {})),
                risk_analysis=RiskAnalysis(**parsed.get("risk_analysis", {})),
                clarification_questions=parsed.get("clarification_questions", []),
                confidence_score=parsed.get("confidence_score", 0.5)
            )

            logger.info("GPT response parsed successfully")
            return response

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            raise ValueError(f"Failed to parse GPT response as JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            raise

    def _enrich_with_crew_templates(
        self,
        response: PreConstructionAnalysisResponse,
        request: PreConstructionAnalysisRequest
    ) -> PreConstructionAnalysisResponse:
        """
        Enrich response with crew templates and calculations
        """
        try:
            logger.info("Enriching response with crew templates")

            # Calculate labor costs based on crew templates
            total_cost = self._calculate_total_cost(response)
            response.labor_cost_estimate.estimated_total_cost = total_cost

            # Add metadata
            response.analysis_metadata = {
                "crew_templates_applied": True,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "available_trades": list(TRADE_DEFINITIONS.keys()),
                "total_work_packages": len(response.work_packages),
                "peak_headcount": self._get_peak_headcount(response),
                "total_person_weeks": self._calculate_total_person_weeks(response)
            }

            return response

        except Exception as e:
            logger.error(f"Error enriching response: {str(e)}")
            raise

    def _calculate_total_cost(self, response: PreConstructionAnalysisResponse) -> Optional[float]:
        """Calculate total labor cost from manpower curve"""
        try:
            total_cost = 0.0

            for week_data in response.manpower_curve:
                for trade_data in week_data.trades:
                    trade_name = trade_data.trade
                    headcount = trade_data.headcount or 0

                    if trade_name in TRADE_DEFINITIONS:
                        daily_rate = TRADE_DEFINITIONS[trade_name].get("daily_rate_usd", 0)
                        weekly_cost = headcount * daily_rate * 5  # 5 working days per week
                        total_cost += weekly_cost

            return total_cost if total_cost > 0 else None

        except Exception as e:
            logger.warning(f"Error calculating total cost: {str(e)}")
            return None

    def _get_peak_headcount(self, response: PreConstructionAnalysisResponse) -> int:
        """Get peak headcount from manpower curve"""
        peak = 0
        for week_data in response.manpower_curve:
            if week_data.total_headcount and week_data.total_headcount > peak:
                peak = week_data.total_headcount
        return peak

    def _calculate_total_person_weeks(self, response: PreConstructionAnalysisResponse) -> int:
        """Calculate total person-weeks of work"""
        total = 0
        for week_data in response.manpower_curve:
            if week_data.total_headcount:
                total += week_data.total_headcount
        return total

    def _match_workers(
        self,
        response: PreConstructionAnalysisResponse,
        available_workers: List
    ) -> List[WorkerMatchResult]:
        """
        Match available workers to project needs
        """
        try:
            logger.info(f"Matching {len(available_workers)} workers to project")

            matches = []

            for worker in available_workers:
                match_score = self._calculate_worker_match_score(worker, response)

                if match_score > 0.3:  # Only include if reasonable match
                    assigned_weeks = self._assign_worker_weeks(worker, response)
                    assigned_trades = self._assign_worker_trades(worker, response)

                    match = WorkerMatchResult(
                        worker_id=worker.get("worker_id", ""),
                        worker_name=worker.get("name", ""),
                        assigned_trades=assigned_trades,
                        assigned_weeks=assigned_weeks,
                        match_score=match_score,
                        deployment_recommendation=self._generate_deployment_recommendation(
                            match_score, assigned_trades
                        )
                    )
                    matches.append(match)

            logger.info(f"Matched {len(matches)} workers")
            return sorted(matches, key=lambda x: x.match_score, reverse=True)

        except Exception as e:
            logger.warning(f"Error matching workers: {str(e)}")
            return []

    def _calculate_worker_match_score(self, worker: Dict[str, Any], response: PreConstructionAnalysisResponse) -> float:
        """Calculate match score between worker and project"""
        score = 0.0

        worker_trades = set(worker.get("trades", []))
        worker_certs = set(worker.get("certifications", []))
        reliability = worker.get("reliability_score", 0.5)

        # Collect required trades and certs from project
        required_trades = set()
        for wp in response.work_packages:
            for tr in wp.trades_required:
                required_trades.add(tr.trade)

        # Skill match weight
        if worker_trades and required_trades:
            skill_overlap = len(worker_trades.intersection(required_trades)) / len(required_trades)
            score += skill_overlap * WORKER_MATCH_WEIGHTS["skill_match"]

        # Reliability weight
        score += reliability * WORKER_MATCH_WEIGHTS["reliability"]

        # Certification bonus
        if worker_certs:
            score += 0.1 * WORKER_MATCH_WEIGHTS["certification_match"]

        return min(score, 1.0)

    def _assign_worker_weeks(self, worker: Dict[str, Any], response: PreConstructionAnalysisResponse) -> List[int]:
        """Assign worker to specific weeks based on availability"""
        assigned_weeks = []

        if not response.manpower_curve:
            return assigned_weeks

        worker_start = worker.get("availability_start_week", 1)
        worker_end = worker.get("availability_end_week", len(response.manpower_curve))

        for i, week_data in enumerate(response.manpower_curve):
            week_num = week_data.week
            if worker_start <= week_num <= worker_end:
                assigned_weeks.append(week_num)

        return assigned_weeks[:8]  # Limit to 8 weeks for reasonable assignments

    def _assign_worker_trades(self, worker: Dict[str, Any], response: PreConstructionAnalysisResponse) -> List[str]:
        """Assign trades the worker can handle"""
        worker_trades = set(worker.get("trades", []))
        assigned = []

        for wp in response.work_packages:
            for tr in wp.trades_required:
                if tr.trade in worker_trades and tr.trade not in assigned:
                    assigned.append(tr.trade)

        return assigned[:3]  # Limit to 3 trades

    def _generate_deployment_recommendation(self, match_score: float, trades: List[str]) -> str:
        """Generate human-readable deployment recommendation"""
        if match_score >= 0.8:
            return f"Highly recommended. Deploy for: {', '.join(trades)}"
        elif match_score >= 0.6:
            return f"Recommended with supervision. Can work on: {', '.join(trades)}"
        elif match_score >= 0.4:
            return f"Consider for support roles. Possible assignments: {', '.join(trades)}"
        else:
            return "Limited match. Consider only for specific tasks."
