"""
Test and demonstration file for AI Adaptive Project Analyzer
Philippines Construction Edition

Run this file to test the analyzer with sample Philippine construction data
All rates and examples are based on Philippines construction standards
"""

import json
import asyncio
from models.preconstruction_models import (
    PreConstructionAnalysisRequest,
    WorkerProfile
)
from services.ai_project_analyzer import AIProjectAnalyzer

# Sample project data for testing

SAMPLE_PROJECT_DESCRIPTION = """
We are planning a 5-story residential condominium complex in Quezon City, Metro Manila.
The project includes:
- Total built-up area: 25,000 square meters
- 120 unit apartments (mix of 1-bed and 2-bed)
- 2 levels of basement parking (250 slots)
- Ground floor retail space (1,500 sqm)
- Community facilities: gymnasium, swimming pool, function room
- Timeline: 20-24 months
- Budget: ₱450 million

Expected phases:
1. Site Mobilization and Excavation (2-3 months)
2. Foundation and Basement Works (3-4 months)
3. Structural Frame (5-6 months)
4. MEP Systems (4-5 months)
5. Interior Finishes and Fit-out (3-4 months)
"""

SAMPLE_BOQ = """
Bill of Quantities Summary (Revised):
- Excavation: 35,000 cubic meters
- Concrete Works: 8,000 cubic meters
- Reinforcement Steel: 950 tons
- Structural Steel: 180 tons
- Concrete Blocks: 1,800,000 pieces
- Plumbing Fixtures: 360 units
- Electrical Outlets and Fixtures: 2,800 units
- HVAC Units: 35 units
- Interior Finishing: Gypsum board, tiles, and paint for 25,000 sqm
- Windows and Doors: 500 units (aluminum and glass)
"""

SAMPLE_SCHEDULE = """
Project Timeline (Revised for Philippine Context):
- Mobilization & Site Preparation: Week 1-2
- Demolition & Excavation: Week 3-10
- Foundation & Basement Concreting: Week 11-16
- Ground Floor Structural: Week 17-22
- Upper Floors Structural: Week 23-35
- Building Envelope: Week 30-36
- MEP Phase 1 (Underground): Week 37-40
- MEP Phase 2 (Above Ground): Week 41-48
- Finishing Phase 1: Week 45-52
- Finishing Phase 2: Week 53-60
- Final Inspections & Handover: Week 61-64
"""

SAMPLE_WORKERS = [
    {
        "worker_id": "W001",
        "name": "Engr. Juan Dela Cruz",
        "trades": ["Excavation & Earthworks", "Site Management & Coordination"],
        "certifications": ["PMP", "DOLE_Safety_Officer", "PCC_Supervisor"],
        "reliability_score": 0.95,
        "past_projects": ["Residential", "Commercial", "Infrastructure"],
        "hourly_rate": 275,  # PHP
        "availability_start_week": 1,
        "availability_end_week": 64
    },
    {
        "worker_id": "W002",
        "name": "Master Craftsman Miguel Santos",
        "trades": ["Rebar & Reinforcement", "Formwork & Carpentry", "Concrete/Mason Works"],
        "certifications": ["DOLE_Certificate", "Safety_Training", "Quality_Cert"],
        "reliability_score": 0.88,
        "past_projects": ["Residential", "Infrastructure"],
        "hourly_rate": 187,  # PHP
        "availability_start_week": 3,
        "availability_end_week": 40
    },
    {
        "worker_id": "W003",
        "name": "Master Electrician Maria Reyes",
        "trades": ["Electrical Installation", "Plumbing & Waterproofing"],
        "certifications": ["PEC_License", "MERALCO_Accredited", "PHREB_Certificate"],
        "reliability_score": 0.92,
        "past_projects": ["Residential", "Commercial"],
        "hourly_rate": 300,  # PHP
        "availability_start_week": 37,
        "availability_end_week": 52
    },
    {
        "worker_id": "W004",
        "name": "Sr. Welder Antonio Gonzales",
        "trades": ["Steel Works & Welding"],
        "certifications": ["AWS_Certification", "Welder_License"],
        "reliability_score": 0.90,
        "past_projects": ["Commercial", "Infrastructure"],
        "hourly_rate": 212,  # PHP
        "availability_start_week": 17,
        "availability_end_week": 36
    },
    {
        "worker_id": "W005",
        "name": "Finish Carpenter Roberto Flores",
        "trades": ["Tile & Flooring", "Painting & Finishing", "Cabinetry & Carpentry"],
        "certifications": ["PCC_License", "Safety_Certificate"],
        "reliability_score": 0.85,
        "past_projects": ["Residential"],
        "hourly_rate": 175,  # PHP
        "availability_start_week": 45,
        "availability_end_week": 62
    },
    {
        "worker_id": "W006",
        "name": "General Laborer Rommel Cruz",
        "trades": ["General Laborers"],
        "certifications": ["Safety_Certificate", "DOLE_Basic_Training"],
        "reliability_score": 0.80,
        "past_projects": ["Residential", "Infrastructure"],
        "hourly_rate": 100,  # PHP
        "availability_start_week": 1,
        "availability_end_week": 64
    }
]


def test_with_full_documents():
    """Test analyzer with complete documents - Philippines residential project"""
    print("\n" + "="*80)
    print("TEST 1: Analysis with Full Documents (BOQ, Plans, Schedule)")
    print("PROJECT: 5-Story Residential Condo - Quezon City, Metro Manila")
    print("="*80)

    request = PreConstructionAnalysisRequest(
        project_description=SAMPLE_PROJECT_DESCRIPTION,
        boq_text=SAMPLE_BOQ,
        schedule_text=SAMPLE_SCHEDULE,
        available_workers=SAMPLE_WORKERS
    )

    analyzer = AIProjectAnalyzer()
    response = analyzer.analyze(request)

    print(f"\n✓ Analysis completed successfully")
    print(f"✓ Project Type: {response.project_summary.project_type}")
    print(f"✓ Duration: {response.project_summary.duration_weeks} weeks")
    print(f"✓ Work Packages: {len(response.work_packages)}")
    print(f"✓ Confidence Score: {response.confidence_score:.2%}")
    print(f"✓ Peak Headcount: {max([m.total_headcount or 0 for m in response.manpower_curve])}")
    print(f"✓ Estimated Cost: ${response.labor_cost_estimate.estimated_total_cost:,.2f}" if response.labor_cost_estimate.estimated_total_cost else "")
    
    if response.worker_recommendations:
        print(f"\n✓ Worker Matches: {len(response.worker_recommendations)}")
        for match in response.worker_recommendations[:3]:
            print(f"  - {match.worker_name}: {match.match_score:.2%} match ({', '.join(match.assigned_trades)})")

    return response


def test_with_description_only():
    """Test analyzer with only project description - Philippines commercial project"""
    print("\n" + "="*80)
    print("TEST 2: Analysis with Description Only (No Documents)")
    print("PROJECT: Shopping Complex - Makati, Metro Manila (Inferred Analysis)")
    print("="*80)

    request = PreConstructionAnalysisRequest(
        project_description=SAMPLE_PROJECT_DESCRIPTION,
        available_workers=SAMPLE_WORKERS
    )

    analyzer = AIProjectAnalyzer()
    response = analyzer.analyze(request)

    print(f"\n✓ Analysis completed successfully")
    print(f"✓ Project Type: {response.project_summary.project_type}")
    print(f"✓ Confidence Score: {response.confidence_score:.2%}")
    print(f"✓ Inferred Duration: {response.project_summary.duration_weeks} weeks")
    print(f"✓ Missing Documents: {len(response.input_evaluation.missing_items)}")
    
    print(f"\n✓ Clarification Questions ({len(response.clarification_questions)}):")
    for i, q in enumerate(response.clarification_questions[:3], 1):
        print(f"  {i}. {q}")

    print(f"\n✓ Risk Severity: {response.risk_analysis.risk_severity}")
    print(f"✓ Identified Risks: {len(response.risk_analysis.identified_risks)}")

    return response


def test_without_workers():
    """Test analyzer without worker matching - Philippines infrastructure project"""
    print("\n" + "="*80)
    print("TEST 3: Analysis without Worker Matching")
    print("PROJECT: Barangay Road Improvement - Provincial Area")
    print("="*80)

    request = PreConstructionAnalysisRequest(
        project_description=SAMPLE_PROJECT_DESCRIPTION,
        boq_text=SAMPLE_BOQ,
        schedule_text=SAMPLE_SCHEDULE
    )

    analyzer = AIProjectAnalyzer()
    response = analyzer.analyze(request)

    print(f"\n✓ Analysis completed successfully")
    print(f"✓ Manpower Curve Weeks: {len(response.manpower_curve)}")
    
    if response.manpower_curve:
        print(f"✓ Weekly Breakdown Sample (First 5 weeks):")
        for week_data in response.manpower_curve[:5]:
            print(f"  Week {week_data.week}: {week_data.total_headcount} workers", end="")
            if week_data.trades:
                print(f" ({', '.join([t.trade for t in week_data.trades[:2]])}...)")
            else:
                print()

    print(f"\n✓ Skill Gap Analysis:")
    print(f"  - Missing Trades: {len(response.skill_gap_analysis.missing_trades)}")
    print(f"  - Shortage Areas: {len(response.skill_gap_analysis.trades_with_shortages)}")

    return response


def display_full_response(response):
    """Pretty print full response"""
    print("\n" + "="*80)
    print("FULL ANALYSIS RESPONSE")
    print("="*80)
    print(json.dumps(response.model_dump(), indent=2, default=str)[:2000] + "...")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("AI ADAPTIVE PROJECT ANALYZER - TEST SUITE")
    print("="*80)
    
    try:
        # Test 1: Full documents with workers
        response1 = test_with_full_documents()
        
        # Test 2: Description only
        response2 = test_with_description_only()
        
        # Test 3: Without worker matching
        response3 = test_without_workers()
        
        print("\n" + "="*80)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        print("\nThe AI Adaptive Project Analyzer is ready for deployment!")
        print("\nAPI Endpoint: POST /api/ai/preconstruction/analyze")
        print("Health Check: GET /api/ai/preconstruction/health")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # For async testing
    asyncio.run(main())
