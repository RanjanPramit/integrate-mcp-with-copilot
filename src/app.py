"""
Mergington High School Activities Management System

A FastAPI application for managing extracurricular activities with:
- User authentication (admin and student roles)
- Persistent database storage
- Activity management and signup
- Attendance tracking
- Merit/performance scoring
"""

from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
import os
from pathlib import Path

# Import models, auth, schemas, and database
from models import User, Activity, UserRole
from auth import (
    verify_password, get_password_hash, create_access_token, 
    decode_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
)
from schemas import (
    UserRegister, UserLogin, UserResponse, UserUpdate,
    ActivityCreate, ActivityUpdate, ActivityResponse, ActivityDetailResponse,
    SignupResponse, AttendanceRecord, StudentStats, MeritList
)
from database import get_db, init_db, create_default_activities

# Initialize FastAPI app
app = FastAPI(
    title="Mergington High School Activities API",
    description="API for managing and signing up for extracurricular activities"
)

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent, "static")), name="static")


# ============================================
# Initialization
# ============================================

@app.on_event("startup")
def startup_event():
    """Initialize database on startup"""
    init_db()
    db = next(get_db())
    create_default_activities(db)
    db.close()


# ============================================
# Utility Functions
# ============================================

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    token_data = decode_access_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Verify current user is admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ============================================
# Authentication Routes
# ============================================

@app.post("/auth/register", response_model=UserResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user (student)"""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        grade_level=user_data.grade_level,
        role=UserRole.STUDENT
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@app.post("/auth/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token"""
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "role": user.role.value
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value
        }
    }


# ============================================
# User Routes
# ============================================

@app.get("/users/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@app.put("/users/me", response_model=UserResponse)
def update_user_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    if update_data.full_name:
        current_user.full_name = update_data.full_name
    if update_data.grade_level:
        current_user.grade_level = update_data.grade_level
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


# ============================================
# Activity Routes - Public
# ============================================

@app.get("/")
def root():
    """Redirect to frontend"""
    return RedirectResponse(url="/static/index.html")


@app.get("/activities", response_model=list[ActivityResponse])
def get_activities(
    category: str = None,
    db: Session = Depends(get_db)
):
    """Get all active activities, optionally filtered by category"""
    query = db.query(Activity).filter(Activity.is_active == True)
    
    if category:
        query = query.filter(Activity.category == category)
    
    activities = query.all()
    return activities


@app.get("/activities/{activity_id}", response_model=ActivityDetailResponse)
def get_activity_detail(
    activity_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about an activity"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    
    return activity


# ============================================
# Signup/Enrollment Routes
# ============================================

@app.post("/activities/{activity_id}/signup", response_model=SignupResponse)
def signup_for_activity(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sign up for an activity"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    
    if not activity.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activity is not active"
        )
    
    # Check if already signed up
    if current_user in activity.students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already signed up for this activity"
        )
    
    # Check if activity is full
    if activity.is_full:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activity is at maximum capacity"
        )
    
    # Add signup
    activity.students.append(current_user)
    db.commit()
    db.refresh(activity)
    
    return {
        "message": f"Successfully signed up for {activity.name}",
        "activity": activity,
        "student": current_user
    }


@app.delete("/activities/{activity_id}/unregister")
def unregister_from_activity(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unregister from an activity"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    
    # Check if signed up
    if current_user not in activity.students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not signed up for this activity"
        )
    
    # Remove signup
    activity.students.remove(current_user)
    db.commit()
    
    return {"message": f"Unregistered from {activity.name}"}


@app.get("/my-activities", response_model=list[ActivityResponse])
def get_my_activities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all activities the current user is signed up for"""
    return current_user.activities


# ============================================
# Admin Routes - Activity Management
# ============================================

@app.post("/admin/activities", response_model=ActivityResponse)
def create_activity(
    activity_data: ActivityCreate,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new activity (admin only)"""
    # Check if activity name already exists
    existing = db.query(Activity).filter(Activity.name == activity_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activity with this name already exists"
        )
    
    new_activity = Activity(
        **activity_data.dict(),
        created_by=admin.id
    )
    
    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)
    
    return new_activity


@app.put("/admin/activities/{activity_id}", response_model=ActivityResponse)
def update_activity(
    activity_id: int,
    activity_data: ActivityUpdate,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update an activity (admin only)"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    
    # Update fields
    update_dict = activity_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(activity, key, value)
    
    db.commit()
    db.refresh(activity)
    
    return activity


@app.delete("/admin/activities/{activity_id}")
def delete_activity(
    activity_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete an activity (admin only)"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    
    db.delete(activity)
    db.commit()
    
    return {"message": f"Activity {activity.name} deleted"}


# ============================================
# Admin Routes - Attendance & Performance
# ============================================

@app.post("/admin/attendance")
def record_attendance(
    attendance_data: AttendanceRecord,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Record attendance and performance for a student in an activity"""
    student = db.query(User).filter(User.id == attendance_data.student_id).first()
    activity = db.query(Activity).filter(Activity.id == attendance_data.activity_id).first()
    
    if not student or not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student or activity not found"
        )
    
    # Check if student is signed up
    if student not in activity.students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is not signed up for this activity"
        )
    
    # Add to attendance (will update if exists)
    if student not in activity.attendees:
        activity.attendees.append(student)
    
    db.commit()
    
    return {
        "message": f"Attendance recorded for {student.full_name} in {activity.name}",
        "student": student,
        "activity": activity
    }


# ============================================
# Statistics Routes
# ============================================

@app.get("/stats/my-activities", response_model=StudentStats)
def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get statistics for current student"""
    total_activities = len(current_user.activities)
    attended_activities = len(current_user.attended_activities)
    
    return {
        "total_activities": total_activities,
        "attended_activities": attended_activities,
        "average_performance": None,
        "active_activities": current_user.activities
    }


@app.get("/admin/merit-list", response_model=list[MeritList])
def get_merit_list(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get merit list of students by participation"""
    students = db.query(User).filter(User.role == UserRole.STUDENT).all()
    
    merit_list = []
    for student in students:
        total = len(student.activities)
        attended = len(student.attended_activities)
        if total > 0:
            merit_list.append({
                "student": student,
                "total_activities": total,
                "attended_activities": attended,
                "average_performance": None
            })
    
    # Sort by total activities
    merit_list.sort(key=lambda x: x["total_activities"], reverse=True)
    
    return merit_list
