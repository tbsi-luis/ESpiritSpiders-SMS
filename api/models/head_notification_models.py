from pydantic import BaseModel, Field
from typing import List, Optional
from typing import Optional, List, Dict

class Employees(BaseModel):
    id: str
    name: str
    position: str

class EmployeeList(BaseModel):
    employees: List[Employees]

class Heads(BaseModel):
    head_name: str
    contact_number: str

class HeadList(BaseModel):
    heads: List[Heads]

class HeadNotificationRequest(BaseModel):
    head_list: List[Heads]
    message: str
    employees_under: List[EmployeeList]

class NotificationResponse(BaseModel):
    name: str
    contact: str
    response: dict
    
class HeadNotificationResult(BaseModel):
    success: bool
    sent_to: List[NotificationResponse]
    failed: List[Dict[str, str]]
    message: str