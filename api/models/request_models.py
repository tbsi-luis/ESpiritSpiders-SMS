from pydantic import BaseModel, Field
from typing import List

class Reliever(BaseModel):
    name: str
    contact: str

class RelieverRequest(BaseModel):
    message: str = Field(..., description="Message to send to selected relievers")
    relievers: List[Reliever] = Field(..., description="List of relievers to notify")