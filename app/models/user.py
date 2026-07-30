from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

class Role(str, Enum):
    HR_ADMIN = "HR_ADMIN"
    HR_MANAGER = "HR_MANAGER"
    EMPLOYEE = "EMPLOYEE"

class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class Profile(BaseModel):
    id: str
    auth_user_id: str
    name: str
    email: str
    role: Role
    department: Optional[str] = None
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
