"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ============================================
# User Schemas
# ============================================

class UserRegister(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str
    full_name: str
    grade_level: Optional[int] = None  # For students


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    email: str
    full_name: str
    grade_level: Optional[int]
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    full_name: Optional[str] = None
    grade_level: Optional[int] = None


# ============================================
# Activity Schemas
# ============================================

class ActivityCreate(BaseModel):
    """Schema for creating an activity"""
    name: str
    description: str
    category: str  # "technical", "sports", "cultural", "academic"
    schedule: str
    location: Optional[str] = None
    max_participants: int


class ActivityUpdate(BaseModel):
    """Schema for updating an activity"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    schedule: Optional[str] = None
    location: Optional[str] = None
    max_participants: Optional[int] = None
    is_active: Optional[bool] = None


class ActivityResponse(BaseModel):
    """Schema for activity response"""
    id: int
    name: str
    description: str
    category: str
    schedule: str
    location: Optional[str]
    max_participants: int
    participant_count: int
    available_spots: int
    is_full: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ActivityDetailResponse(ActivityResponse):
    """Detailed activity response with student list"""
    students: List[UserResponse] = []


# ============================================
# Signup/Enrollment Schemas
# ============================================

class SignupResponse(BaseModel):
    """Response for signup operation"""
    message: str
    activity: ActivityResponse
    student: UserResponse


class AttendanceRecord(BaseModel):
    """Schema for attendance record"""
    student_id: int
    activity_id: int
    performance_score: Optional[int] = None  # 0-10


class AttendanceResponse(BaseModel):
    """Response for attendance record"""
    student: UserResponse
    activity: ActivityResponse
    attended_at: datetime
    performance_score: Optional[int]


# ============================================
# Statistics Schemas
# ============================================

class StudentStats(BaseModel):
    """Student statistics"""
    total_activities: int
    attended_activities: int
    average_performance: Optional[float]
    active_activities: List[ActivityResponse] = []


class ActivityStats(BaseModel):
    """Activity statistics"""
    name: str
    total_signups: int
    total_attendance: int
    average_performance: Optional[float]
    attendance_rate: float


class MeritList(BaseModel):
    """Merit list entry"""
    student: UserResponse
    total_activities: int
    attended_activities: int
    average_performance: Optional[float]
