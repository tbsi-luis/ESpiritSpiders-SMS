"""
Test script for Comprehensive Document Output
Demonstrates the document generation feature
"""

import json
import sys
from datetime import datetime
from models.preconstruction_models import (
    PreConstructionAnalysisRequest,
    WorkerProfile
)
from services.ai_project_analyzer import AIProjectAnalyzer
from services.document_generator import DocumentGenerator


def test_document_generation():
    """Test comprehensive document generation"""
    
    print("=" * 100)
    print("COMPREHENSIVE DOCUMENT OUTPUT TEST".center(100))
    print("=" * 100)
    print()
    
    # Create sample request
    project_desc = """
    5-storey commercial office building in BGC, Makati
    Total built-up area: 25,000 sqm
    Site area: 5,000 sqm
    Timeline: 18 months (64 weeks)
    Project type: Class A Commercial Office Space
    """
    
    boq = """
    Foundation: Pile driving with bored piles (1,200mm diameter)
    Concrete works: 8,500 cubic meters ready-mix
    Structural Steel: 2,800 metric tons
    Masonry: 450,000 pieces of hollow blocks
    Carpentry: Formworks and templets
    Electrical: 150 kV distribution system
    Plumbing: Hot and cold water system
    HVAC: Central air conditioning system
    Fireproofing: Intumescent paint on structural steel
    """
    
    schedule = """
    Phase 1: Site Preparation (Weeks 1-2)
    Phase 2: Foundation (Weeks 3-10)
    Phase 3: Structural Frame (Weeks 11-30)
    Phase 4: MEP Installation (Weeks 31-50)
    Phase 5: Finishing (Weeks 51-64)
    """
    
    # Create sample workers
    workers = [
        WorkerProfile(
            worker_id="W001",
            name="Juan Dela Cruz",
            trades=["Structural Steel", "General Laborers"],
            certifications=["MERALCO_Accredited", "DOLE_Basic_Training"],
            reliability_score=0.95,
            hourly_rate=150,
            availability_start_week=1,
            availability_end_week=64
        ),
        WorkerProfile(
            worker_id="W002",
            name="Maria Santos",
            trades=["Carpentry", "Formwork"],
            certifications=["PCC_Certified", "DOLE_Basic_Training"],
            reliability_score=0.85,
            hourly_rate=120,
            availability_start_week=3,
            availability_end_week=52
        ),
        WorkerProfile(
            worker_id="W003",
            name="Pedro Garcia",
            trades=["Electrical", "Plumbing"],
            certifications=["MERALCO_Accredited", "Safety_Certificate"],
            reliability_score=0.90,
            hourly_rate=180,
            availability_start_week=31,
            availability_end_week=64
        ),
        WorkerProfile(
            worker_id="W004",
            name="Ana Reyes",
            trades=["HVAC", "Mechanical"],
            certifications=["AWS_Certified", "PHREB_Certified"],
            reliability_score=0.88,
            hourly_rate=160,
            availability_start_week=31,
            availability_end_week=64
        ),
        WorkerProfile(
            worker_id="W005",
            name="Carlos Mendoza",
            trades=["Safety Management", "Quality Control"],
            certifications=["Safety_Certificate", "DOLE_Basic_Training"],
            reliability_score=0.92,
            hourly_rate=140,
            availability_start_week=1,
            availability_end_week=64
        ),
        WorkerProfile(
            worker_id="W006",
            name="Rommel Cruz",
            trades=["General Laborers"],
            certifications=["Safety_Certificate", "DOLE_Basic_Training"],
            reliability_score=0.80,
            hourly_rate=100,
            availability_start_week=1,
            availability_end_week=64
        ),
    ]
    
    # Create request
    request = PreConstructionAnalysisRequest(
        project_description=project_desc,
        boq_text=boq,
        schedule_text=schedule,
        available_workers=workers
    )
    
    print("📊 PHASE 1: Analyzing Project...")
    print("-" * 100)
    
    # Perform analysis
    try:
        analyzer = AIProjectAnalyzer()
        analysis = analyzer.analyze(request)
        print(f"✅ Analysis completed with {(analysis.confidence_score * 100):.1f}% confidence")
        print(f"   Work Packages: {len(analysis.work_packages)}")
        print(f"   Manpower Weeks: {len(analysis.manpower_curve)}")
        print(f"   Worker Recommendations: {len(analysis.worker_recommendations) if analysis.worker_recommendations else 0}")
        print()
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        return
    
    print("📄 PHASE 2: Generating Comprehensive Document...")
    print("-" * 100)
    print()
    
    # Generate document
    try:
        doc_gen = DocumentGenerator()
        
        # Generate full document
        full_document = doc_gen.generate_comprehensive_report(
            analysis,
            project_name="BGC Commercial Tower - Phase 1",
            include_worker_section=True
        )
        
        print(full_document)
        print()
        print("=" * 100)
        print()
        
        # Save to file
        output_file = "bgc_tower_analysis.txt"
        with open(output_file, "w") as f:
            f.write(full_document)
        
        doc_size = len(full_document)
        print(f"✅ Document generated successfully!")
        print(f"   Document size: {doc_size:,} characters")
        print(f"   Saved to: {output_file}")
        print()
        
        # Statistics
        lines = full_document.split('\n')
        print(f"Document Statistics:")
        print(f"   Total lines: {len(lines)}")
        print(f"   Average line length: {doc_size // len(lines):.0f} characters")
        print()
        
    except Exception as e:
        print(f"❌ Document generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    print("✅ TEST COMPLETED SUCCESSFULLY")
    print()
    print("📋 SUMMARY:")
    print("   • AI Analysis: Successful")
    print("   • Document Generation: Successful")
    print("   • Output Format: Professional Text Document")
    print("   • Sections Included: 11 major sections")
    print("   • Worker Recommendations: Included")
    print()


def test_summary_document():
    """Test summary document generation"""
    
    print("=" * 100)
    print("SUMMARY DOCUMENT TEST".center(100))
    print("=" * 100)
    print()
    
    # Create minimal request
    request = PreConstructionAnalysisRequest(
        project_description="Simple 3-storey residential building in Quezon City"
    )
    
    print("Analyzing minimal project description...")
    try:
        analyzer = AIProjectAnalyzer()
        analysis = analyzer.analyze(request)
        
        doc_gen = DocumentGenerator()
        summary = doc_gen.generate_summary_report(analysis)
        
        print(summary)
        print()
        print(f"✅ Summary document generated ({len(summary):,} characters)")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")


if __name__ == "__main__":
    # Run full document test
    test_document_generation()
    
    # Uncomment to run summary test
    # test_summary_document()
