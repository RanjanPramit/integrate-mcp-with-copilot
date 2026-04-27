"""
Database configuration and initialization
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path
import os
from models import Base

# Create database file in the src directory
DATABASE_URL = "sqlite:///./activities.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database with tables"""
    Base.metadata.create_all(bind=engine)


def create_default_activities(db: Session):
    """Create default activities in the database"""
    from models import Activity, User, UserRole
    from auth import get_password_hash
    
    # Check if activities already exist
    existing_count = db.query(Activity).count()
    if existing_count > 0:
        return
    
    # Create admin user if doesn't exist
    admin = db.query(User).filter(User.email == "admin@mergington.edu").first()
    if not admin:
        admin = User(
            email="admin@mergington.edu",
            full_name="Admin User",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    
    # Default activities
    default_activities = [
        Activity(
            name="Chess Club",
            description="Learn strategies and compete in chess tournaments",
            category="academic",
            schedule="Fridays, 3:30 PM - 5:00 PM",
            location="Room 101",
            max_participants=12,
            created_by=admin.id
        ),
        Activity(
            name="Programming Class",
            description="Learn programming fundamentals and build software projects",
            category="technical",
            schedule="Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            location="Computer Lab",
            max_participants=20,
            created_by=admin.id
        ),
        Activity(
            name="Gym Class",
            description="Physical education and sports activities",
            category="sports",
            schedule="Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            location="Gymnasium",
            max_participants=30,
            created_by=admin.id
        ),
        Activity(
            name="Soccer Team",
            description="Join the school soccer team and compete in matches",
            category="sports",
            schedule="Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            location="Soccer Field",
            max_participants=22,
            created_by=admin.id
        ),
        Activity(
            name="Basketball Team",
            description="Practice and play basketball with the school team",
            category="sports",
            schedule="Wednesdays and Fridays, 3:30 PM - 5:00 PM",
            location="Gymnasium",
            max_participants=15,
            created_by=admin.id
        ),
        Activity(
            name="Art Club",
            description="Explore your creativity through painting and drawing",
            category="cultural",
            schedule="Thursdays, 3:30 PM - 5:00 PM",
            location="Art Room",
            max_participants=15,
            created_by=admin.id
        ),
        Activity(
            name="Drama Club",
            description="Act, direct, and produce plays and performances",
            category="cultural",
            schedule="Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            location="Auditorium",
            max_participants=20,
            created_by=admin.id
        ),
        Activity(
            name="Math Club",
            description="Solve challenging problems and participate in math competitions",
            category="academic",
            schedule="Tuesdays, 3:30 PM - 4:30 PM",
            location="Room 205",
            max_participants=10,
            created_by=admin.id
        ),
        Activity(
            name="Debate Team",
            description="Develop public speaking and argumentation skills",
            category="academic",
            schedule="Fridays, 4:00 PM - 5:30 PM",
            location="Room 301",
            max_participants=12,
            created_by=admin.id
        )
    ]
    
    # Add activities to database
    db.add_all(default_activities)
    db.commit()
