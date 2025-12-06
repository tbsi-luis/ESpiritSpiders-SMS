"""
API routes for AI Adaptive Project Analyzer
POST /api/ai/preconstruction/analyze endpoint
"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from typing import Optional

from models.preconstruction_models import PreConstructionAnalysisRequest
from services.ai_project_analyzer import AIProjectAnalyzer
from services.document_generator import DocumentGenerator

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/ai",
    tags=["ai_analyzer"]
)

# Initialize analyzer and document generator (could be dependency-injected if needed)
analyzer = None
doc_generator = None


def get_analyzer() -> AIProjectAnalyzer:
    """Get or create analyzer instance"""
    global analyzer
    if analyzer is None:
        analyzer = AIProjectAnalyzer()
    return analyzer


def get_document_generator() -> DocumentGenerator:
    """Get or create document generator instance"""
    global doc_generator
    if doc_generator is None:
        doc_generator = DocumentGenerator()
    return doc_generator


@router.post(
    "/preconstruction/analyze/document",
    response_class=PlainTextResponse,
    summary="AI Adaptive Project Analyzer - Document Output",
    description="Analyzes construction project and returns comprehensive formatted report"
)
async def analyze_project_document(
    request: PreConstructionAnalysisRequest,
    project_name: Optional[str] = None,
    include_workers: bool = True
) -> str:
    """
    Analyze construction project and generate comprehensive formatted document
    
    This endpoint performs the same analysis as /analyze but returns a
    professionally formatted text document instead of JSON.
    
    Query Parameters:
        project_name (optional): Name of project for document header
        include_workers (optional): Whether to include worker recommendations (default: true)
    
    Args:
        request: PreConstructionAnalysisRequest with project details
        project_name: Optional project name for document
        include_workers: Whether to include worker section
        
    Returns:
        Formatted text document with complete analysis
        
    Raises:
        HTTPException: If analysis fails
    """
    try:
        logger.info(f"Received document analysis request for project: {request.project_description[:50]}...")

        # Validate minimum requirements
        if not request.project_description or not request.project_description.strip():
            raise HTTPException(
                status_code=400,
                detail="project_description is required"
            )

        # Get analyzer and perform analysis
        analyzer_instance = get_analyzer()
        analysis_response = analyzer_instance.analyze(request)

        # Generate document
        doc_gen = get_document_generator()
        document = doc_gen.generate_comprehensive_report(
            analysis_response,
            project_name=project_name,
            include_worker_section=include_workers
        )

        logger.info(f"Document generated successfully. Confidence: {analysis_response.confidence_score}")
        return document

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get(
    "/preconstruction/health",
    summary="Health Check",
    description="Check if AI analyzer service is available"
)
async def health_check():
    """Health check endpoint for AI analyzer"""
    try:
        analyzer_instance = get_analyzer()
        return {
            "status": "healthy",
            "service": "AI Adaptive Project Analyzer",
            "model": analyzer_instance.model,
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Analyzer service unavailable"
        )
