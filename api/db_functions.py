from sqlalchemy.orm import Session
from models.relievers_contact import RelieversContact
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def get_relievers_minimal(db: Session) -> List[Dict[str, Any]]:
    """Get only id, contact_number, and name from all relievers"""
    try:
        results = db.query(
            RelieversContact.id,
            RelieversContact.contact,
            RelieversContact.full_name
        ).all()
        
        return [
            {
                "id": result.id,
                "contact": result.contact,
                "full_name": result.full_name
            }
            for result in results
        ]
    except Exception as e:
        logger.error(f"Error fetching minimal reliever data: {e}")
        return []
