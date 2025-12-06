"""
Document Generator Service
Converts AI Analysis Response into comprehensive project documentation
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from models.preconstruction_models import (
    PreConstructionAnalysisResponse,
    WorkPackage,
    TradeRequirement,
    ManpowerWeek,
    WorkerMatchResult
)


class DocumentGenerator:
    """Generates comprehensive project documents from analysis responses"""

    def __init__(self):
        """Initialize document generator"""
        self.company_header = "ESPIRIT SPIDERS CONSTRUCTION"
        self.document_version = "1.0"

    def generate_comprehensive_report(
        self,
        analysis: PreConstructionAnalysisResponse,
        project_name: Optional[str] = None,
        include_worker_section: bool = True
    ) -> str:
        """
        Generate comprehensive project analysis document
        
        Args:
            analysis: PreConstructionAnalysisResponse from analyzer
            project_name: Optional project name for document header
            include_worker_section: Whether to include worker recommendations
            
        Returns:
            String containing complete formatted document
        """
        document_parts = []

        # Header section
        document_parts.append(self._generate_header(project_name))

        # Executive Summary
        document_parts.append(self._generate_executive_summary(analysis))

        # Project Overview
        document_parts.append(self._generate_project_overview(analysis))

        # Input Assessment
        document_parts.append(self._generate_input_assessment(analysis))

        # Work Breakdown Structure
        document_parts.append(self._generate_work_breakdown(analysis))

        # Manpower Planning
        document_parts.append(self._generate_manpower_planning(analysis))

        # Labor Cost Analysis
        document_parts.append(self._generate_cost_analysis(analysis))

        # Skill Gap Analysis
        document_parts.append(self._generate_skill_gap_section(analysis))

        # Risk Assessment
        document_parts.append(self._generate_risk_assessment(analysis))

        # Worker Recommendations (if available)
        if include_worker_section and analysis.worker_recommendations:
            document_parts.append(self._generate_worker_recommendations(analysis.worker_recommendations))

        # Clarification Section
        if analysis.clarification_questions:
            document_parts.append(self._generate_clarification_section(analysis))

        # Metadata and Footer
        document_parts.append(self._generate_footer(analysis))

        return "\n".join(document_parts)

    def _generate_header(self, project_name: Optional[str] = None) -> str:
        """Generate document header"""
        lines = [
            "=" * 100,
            f"{self.company_header}".center(100),
            "PRE-CONSTRUCTION PHASE MANPOWER ANALYSIS REPORT".center(100),
            "=" * 100,
            "",
        ]
        
        if project_name:
            lines.extend([
                f"PROJECT: {project_name}",
                f"REPORT GENERATED: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}",
                f"DOCUMENT VERSION: {self.document_version}",
                "",
            ])
        
        return "\n".join(lines)

    def _generate_executive_summary(self, analysis: PreConstructionAnalysisResponse) -> str:
        """Generate executive summary section"""
        summary = analysis.project_summary
        
        lines = [
            "┌" + "─" * 98 + "┐",
            "│ EXECUTIVE SUMMARY".ljust(99) + "│",
            "└" + "─" * 98 + "┘",
            "",
            f"Project Type:              {summary.project_type}",
            f"Location:                  {summary.location or 'Not specified'}",
            f"Duration:                  {summary.duration_weeks or 'TBD'} weeks",
            f"Confidence Level:          {(analysis.confidence_score * 100):.1f}%",
            f"Analysis Generated:        {analysis.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SCOPE INTERPRETATION:",
            f"  {summary.overall_scope_interpretation}",
            "",
        ]
        
        return "\n".join(lines)

    def _generate_project_overview(self, analysis: PreConstructionAnalysisResponse) -> str:
        """Generate detailed project overview"""
        summary = analysis.project_summary
        
        lines = [
            "┌" + "─" * 98 + "┐",
            "│ PROJECT OVERVIEW".ljust(99) + "│",
            "└" + "─" * 98 + "┘",
            "",
        ]
        
        if summary.assumptions_used:
            lines.append("KEY ASSUMPTIONS:")
            for i, assumption in enumerate(summary.assumptions_used, 1):
                lines.append(f"  {i}. {assumption}")
            lines.append("")
        
        return "\n".join(lines)

    def _generate_input_assessment(self, analysis: PreConstructionAnalysisResponse) -> str:
        """Generate input documents assessment"""
        evaluation = analysis.input_evaluation
        
        lines = [
            "┌" + "─" * 98 + "┐",
            "│ INPUT DOCUMENTS ASSESSMENT".ljust(99) + "│",
            "└" + "─" * 98 + "┘",
            "",
            "Available Documents:",
            f"  ✓ Bill of Quantities (BOQ):  {'Yes' if evaluation.has_boq else 'No'}",
            f"  ✓ Project Plans:              {'Yes' if evaluation.has_plans else 'No'}",
            f"  ✓ Schedule/Timeline:          {'Yes' if evaluation.has_schedule else 'No'}",
            "",
        ]
        
        if evaluation.missing_items:
            lines.append("Missing Documents:")
            for item in evaluation.missing_items:
                lines.append(f"  ✗ {item}")
            lines.append("")
        
        return "\n".join(lines)

    def _generate_work_breakdown(self, analysis: PreConstructionAnalysisResponse) -> str:
        """Generate Work Breakdown Structure (WBS)"""
        lines = [
            "┌" + "─" * 98 + "┐",
            "│ WORK BREAKDOWN STRUCTURE (WBS)".ljust(99) + "│",
            "└" + "─" * 98 + "┘",
            "",
        ]
        
        for pkg_num, package in enumerate(analysis.work_packages, 1):
            lines.append(f"WP-{pkg_num}: {package.name}")
            lines.append(f"  Phase:       {package.phase}")
            
            if package.start_week and package.end_week:
                lines.append(f"  Duration:    Weeks {package.start_week} - {package.end_week} ({package.end_week - package.start_week + 1} weeks)")
            
            lines.append(f"  Trades Required ({len(package.trades_required)}):")
            
            for trade_req in package.trades_required:
                headcount_str = f" ({trade_req.estimated_headcount} workers)" if trade_req.estimated_headcount else ""
                timing_str = f" [Weeks {trade_req.start_week}-{trade_req.end_week}]" if trade_req.start_week else ""
                lines.append(f"    • {trade_req.trade}{headcount_str}{timing_str}")
            
            lines.append("")
        
        return "\n".join(lines)

    def _generate_manpower_planning(self, analysis: PreConstructionAnalysisResponse) -> str:
        """Generate manpower planning and curve analysis"""
        lines = [
            "┌" + "─" * 98 + "┐",
            "│ MANPOWER PLANNING & WORKFORCE CURVE".ljust(99) + "│",
            "└" + "─" * 98 + "┘",
            "",
        ]
        
        # Summary statistics
        if analysis.manpower_curve:
            headcounts = [w.total_headcount for w in analysis.manpower_curve if w.total_headcount]
            if headcounts:
                lines.append("WORKFORCE STATISTICS:")
                lines.append(f"  Peak Headcount:            {max(headcounts)} workers")
                lines.append(f"  Minimum Headcount:         {min(headcounts)} workers")
                lines.append(f"  Average Headcount:         {sum(headcounts) / len(headcounts):.1f} workers")
                lines.append("")
        
        # Detailed weekly breakdown
        lines.append("DETAILED WEEKLY BREAKDOWN:")
        lines.append("")
        
        # Group by week ranges for readability
        weeks_per_group = 4
        for start_idx in range(0, len(analysis.manpower_curve), weeks_per_group):
            end_idx = min(start_idx + weeks_per_group, len(analysis.manpower_curve))
            
            # Header
            week_range = analysis.manpower_curve[start_idx:end_idx]
            week_nums = [str(w.week) for w in week_range]
            lines.append(f"  Week:  {' '.join(f'{w:>6}' for w in week_nums)}")
            lines.append("  " + "─" * (7 * weeks_per_group + 5))
            
            # Get all trades
            all_trades = set()
            for week in week_range:
                for trade in week.trades:
                    all_trades.add(trade.trade)
            
            # Print each trade
            for trade in sorted(all_trades):
                headcounts = []
                for week in week_range:
                    hc = next((t.headcount for t in week.trades if t.trade == trade), 0)
                    headcounts.append(hc if hc else 0)
                
                trade_line = f"  {trade[:20]:<20} " + " ".join(f"{hc:>6}" for hc in headcounts)
                lines.append(trade_line)
            
            # Total line
            totals = [w.total_headcount or 0 for w in week_range]
            total_line = f"  {'TOTAL':<20} " + " ".join(f"{t:>6}" for t in totals)
            lines.append(total_line)
            lines.append("")
        
        return "\n".join(lines)

    def _generate_cost_analysis(self, analysis: PreConstructionAnalysisResponse) -> str:
        """Generate labor cost analysis"""
        cost = analysis.labor_cost_estimate
        
        lines = [
            "┌" + "─" * 98 + "┐",
            "│ LABOR COST ESTIMATION & ANALYSIS".ljust(99) + "│",
            "└" + "─" * 98 + "┘",
            "",
        ]
        
        if cost.estimated_total_cost:
            lines.append(f"ESTIMATED TOTAL LABOR COST:  ₱{cost.estimated_total_cost:,.2f}")
            
            if cost.uncertainty_range_percent:
                uncertainty_amount = cost.estimated_total_cost * (cost.uncertainty_range_percent / 100)
                lower_bound = cost.estimated_total_cost - uncertainty_amount
                upper_bound = cost.estimated_total_cost + uncertainty_amount
                lines.append(f"Uncertainty Range:           ±{cost.uncertainty_range_percent:.1f}%")
                lines.append(f"  Lower Bound:               ₱{lower_bound:,.2f}")
                lines.append(f"  Upper Bound:               ₱{upper_bound:,.2f}")
            
            lines.append("")
        
        if cost.notes:
            lines.append("COST NOTES & ASSUMPTIONS:")
            for note in cost.notes.split(";"):
                if note.strip():
                    lines.append(f"  • {note.strip()}")
            lines.append("")
        
        return "\n".join(lines)

    def _generate_skill_gap_section(self, analysis: PreConstructionAnalysisResponse) -> str:
        """Generate skill gap analysis"""
        gaps = analysis.skill_gap_analysis
        
        lines = [
            "┌" + "─" * 98 + "┐",
            "│ SKILL GAP ANALYSIS".ljust(99) + "│",
            "└" + "─" * 98 + "┘",
            "",
        ]
        
        if gaps.missing_trades:
            lines.append("MISSING TRADE SKILLS:")
            for trade in gaps.missing_trades:
                lines.append(f"  ✗ {trade}")
            lines.append("")
        
        if gaps.trades_with_shortages:
            lines.append("TRADES WITH SHORTAGES:")
            for trade in gaps.trades_with_shortages:
                lines.append(f"  ⚠ {trade}")
            lines.append("")
        
        if gaps.recommended_hiring_actions:
            lines.append("RECOMMENDED HIRING ACTIONS:")
            for i, action in enumerate(gaps.recommended_hiring_actions, 1):
                lines.append(f"  {i}. {action}")
            lines.append("")
        
        return "\n".join(lines)

    def _generate_risk_assessment(self, analysis: PreConstructionAnalysisResponse) -> str:
        """Generate risk assessment section"""
        risks = analysis.risk_analysis
        
        lines = [
            "┌" + "─" * 98 + "┐",
            "│ RISK ASSESSMENT & MITIGATION".ljust(99) + "│",
            "└" + "─" * 98 + "┘",
            "",
            f"Overall Risk Severity:  {risks.risk_severity}",
            "",
        ]
        
        if risks.identified_risks:
            lines.append("IDENTIFIED RISKS:")
            for i, risk in enumerate(risks.identified_risks, 1):
                lines.append(f"  {i}. {risk}")
            lines.append("")
        
        if risks.recommended_mitigations:
            lines.append("RECOMMENDED MITIGATIONS:")
            for i, mitigation in enumerate(risks.recommended_mitigations, 1):
                lines.append(f"  {i}. {mitigation}")
            lines.append("")
        
        return "\n".join(lines)

    def _generate_worker_recommendations(self, worker_matches: List[WorkerMatchResult]) -> str:
        """Generate worker recommendations section"""
        lines = [
            "┌" + "─" * 98 + "┐",
            "│ WORKER DEPLOYMENT RECOMMENDATIONS".ljust(99) + "│",
            "└" + "─" * 98 + "┘",
            "",
        ]
        
        # Group by match score
        excellent = [w for w in worker_matches if w.match_score >= 0.8]
        good = [w for w in worker_matches if 0.6 <= w.match_score < 0.8]
        fair = [w for w in worker_matches if 0.4 <= w.match_score < 0.6]
        poor = [w for w in worker_matches if w.match_score < 0.4]
        
        for category_name, category_workers, symbol in [
            ("HIGHLY RECOMMENDED (Score ≥ 0.80)", excellent, "★★★"),
            ("RECOMMENDED (Score 0.60-0.79)", good, "★★"),
            ("CONSIDER WITH CAUTION (Score 0.40-0.59)", fair, "★"),
            ("LIMITED MATCH (Score < 0.40)", poor, "•"),
        ]:
            if category_workers:
                lines.append(f"{symbol} {category_name}")
                lines.append("")
                
                for worker in category_workers:
                    lines.append(f"  {worker.worker_name} (ID: {worker.worker_id})")
                    lines.append(f"    Match Score:       {worker.match_score:.1%}")
                    lines.append(f"    Assigned Trades:   {', '.join(worker.assigned_trades)}")
                    lines.append(f"    Available Weeks:   {min(worker.assigned_weeks)}-{max(worker.assigned_weeks)}")
                    lines.append(f"    Recommendation:    {worker.deployment_recommendation}")
                    lines.append("")
        
        return "\n".join(lines)

    def _generate_clarification_section(self, analysis: PreConstructionAnalysisResponse) -> str:
        """Generate clarification questions section"""
        lines = [
            "┌" + "─" * 98 + "┐",
            "│ CLARIFICATION QUESTIONS FOR CLIENT".ljust(99) + "│",
            "└" + "─" * 98 + "┘",
            "",
            "The following information would improve analysis accuracy:",
            "",
        ]
        
        for i, question in enumerate(analysis.clarification_questions, 1):
            lines.append(f"  {i}. {question}")
        
        lines.append("")
        
        return "\n".join(lines)

    def _generate_footer(self, analysis: PreConstructionAnalysisResponse) -> str:
        """Generate document footer with metadata"""
        lines = [
            "┌" + "─" * 98 + "┐",
            "│ DOCUMENT METADATA".ljust(99) + "│",
            "└" + "─" * 98 + "┘",
            "",
            f"Generated:              {analysis.generated_at.strftime('%B %d, %Y at %H:%M:%S')}",
            f"Confidence Score:       {(analysis.confidence_score * 100):.1f}%",
            f"Report Type:            Pre-Construction Phase Manpower Analysis",
            f"System:                 PN-AI: Adaptive Project Analyzer v1.0",
            "",
            "DISCLAIMER:",
            "  This analysis is AI-generated and based on the information provided. It should be reviewed",
            "  by qualified construction professionals before use in actual project planning. Labor costs and",
            "  schedules may vary based on market conditions, project-specific factors, and regulatory changes.",
            "",
            "=" * 100,
            f"{"Proprietary - ESpirit Spiders Construction".center(100)}",
            "=" * 100,
        ]
        
        return "\n".join(lines)

    def generate_summary_report(self, analysis: PreConstructionAnalysisResponse) -> str:
        """
        Generate a concise summary report (for quick review)
        
        Args:
            analysis: PreConstructionAnalysisResponse from analyzer
            
        Returns:
            String containing formatted summary
        """
        lines = [
            self._generate_header(),
            self._generate_executive_summary(analysis),
            self._generate_project_overview(analysis),
            self._generate_work_breakdown(analysis),
            self._generate_cost_analysis(analysis),
            self._generate_risk_assessment(analysis),
            self._generate_footer(analysis),
        ]
        
        return "\n".join(lines)
