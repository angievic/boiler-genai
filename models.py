from sqlmodel import SQLModel, Field
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class Person(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    email: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    is_active: bool = Field(default=True)

    class Config:
        arbitrary_types_allowed = True
        
class PersonDataRequest(BaseModel):
    email: str
    first_name: str
    last_name: str


