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


def is_reliever_contact_authorized(db: Session, phone_number: str) -> Optional[Dict[str, Any]]:
    """
    Check if a phone number is registered as a reliever.
    
    Args:
        db: Database session
        phone_number: Phone number to verify (e.g., "+639123456789" or "09123456789")
    
    Returns:
        Dictionary with reliever info if found: {"id", "full_name", "contact", "status"}
        None if not found
    
    This function authenticates incoming SMS by verifying the sender's phone number
    exists in the reliever_request_reliever_line table.
    """
    try:
        reliever = db.query(RelieversContact).filter(
            RelieversContact.contact == phone_number
        ).first()
        
        if reliever:
            logger.info(f"Reliever authorized | Contact: {phone_number} | Name: {reliever.full_name}")
            return {
                "id": reliever.id,
                "full_name": reliever.full_name,
                "contact": reliever.contact,
                "status": reliever.status
            }
        else:
            logger.warning(f"Unauthorized SMS received | Contact: {phone_number}")
            return None
            
    except Exception as e:
        logger.error(f"Error checking reliever authorization: {e}")
        return None


def update_reliever_status_confirmed(db: Session, phone_number: str) -> bool:
    """
    Update reliever's status to "yes" in the database.
    
    Args:
        db: Database session
        phone_number: Phone number of the reliever
    
    Returns:
        True if update was successful, False otherwise
    
    This function is called after the incoming SMS is classified as "Agree"
    to mark the reliever as yes in the system.
    """
    try:
        reliever = db.query(RelieversContact).filter(
            RelieversContact.contact == phone_number
        ).first()
        
        if reliever:
            reliever.status = "yes"
            db.commit()
            logger.info(f"Status updated to 'yes' | Contact: {phone_number} | Name: {reliever.full_name}")
            return True
        else:
            logger.warning(f"Reliever not found for status update | Contact: {phone_number}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating reliever status: {e}")
        db.rollback()
        return False
