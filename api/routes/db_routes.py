from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from db_functions import get_relievers_minimal
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/relievers",
    tags=["relievers"]
)


@router.get("/minimal")
async def list_minimal_relievers(db: Session = Depends(get_db)):
    """Get relievers with only id, contact_number, and name"""
    relievers = get_relievers_minimal(db)
    if not relievers:
        raise HTTPException(status_code=404, detail="No relievers found")
    return relievers
