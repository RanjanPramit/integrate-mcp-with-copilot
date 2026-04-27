"""
Database models for the activities management system
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Table, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

# Association table for many-to-many relationship between students and activities
activity_signups = Table(
    'activity_signups',
    Base.metadata,
    Column('student_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('activity_id', Integer, ForeignKey('activity.id'), primary_key=True),
    Column('signed_up_at', DateTime, default=datetime.utcnow)
)

# Association table for attendance
activity_attendance = Table(
    'activity_attendance',
    Base.metadata,
    Column('student_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('activity_id', Integer, ForeignKey('activity.id'), primary_key=True),
    Column('attended_at', DateTime, default=datetime.utcnow),
    Column('performance_score', Integer, default=None)  # 0-10 score
)


class UserRole(str, enum.Enum):
    """User roles in the system"""
    ADMIN = "admin"
    STUDENT = "student"


class User(Base):
    """User model for both admins and students"""
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    grade_level = Column(Integer, nullable=True)  # For students (9-12)
    role = Column(SQLEnum(UserRole), default=UserRole.STUDENT)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    activities = relationship("Activity", secondary=activity_signups, back_populates="students")
    attended_activities = relationship("Activity", secondary=activity_attendance, back_populates="attendees")
    created_activities = relationship("Activity", back_populates="created_by_user")


class Activity(Base):
    """Activity/Club model"""
    __tablename__ = "activity"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    category = Column(String)  # "technical", "sports", "cultural", "academic", etc.
    schedule = Column(String)
    location = Column(String, nullable=True)
    max_participants = Column(Integer)
    created_by = Column(Integer, ForeignKey('user.id'))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    students = relationship("User", secondary=activity_signups, back_populates="activities")
    attendees = relationship("User", secondary=activity_attendance, back_populates="attended_activities")
    created_by_user = relationship("User", back_populates="created_activities", foreign_keys=[created_by])
    
    @property
    def participant_count(self):
        """Get current number of participants"""
        return len(self.students)
    
    @property
    def available_spots(self):
        """Get number of available spots"""
        return max(0, self.max_participants - self.participant_count)
    
    @property
    def is_full(self):
        """Check if activity is at max capacity"""
        return self.participant_count >= self.max_participants
