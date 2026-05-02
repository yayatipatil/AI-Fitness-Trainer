from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- SQLAlchemy Models ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    # Profile fields merged into User
    age = Column(Integer, nullable=True)
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    gender = Column(String, nullable=True)
    fitness_goal = Column(String, nullable=True) # weight_loss, muscle_gain, endurance, maintenance
    experience_level = Column(String, nullable=True)
    intensity_modifier = Column(Float, default=1.0)

    workout_logs = relationship("WorkoutLog", back_populates="user")
    workout_plans = relationship("WorkoutPlan", back_populates="user")

class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, default=datetime.utcnow)
    workout_type = Column(String)
    difficulty_feedback = Column(String) # Easy, Medium, Hard
    calories_burned = Column(Float)
    reps = Column(Integer, default=0)

    user = relationship("User", back_populates="workout_logs")

class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    day_of_week = Column(Integer) # 0=Mon to 6=Sun
    exercise_name = Column(String)
    target_sets = Column(Integer)
    target_reps = Column(Integer)
    target_duration_mins = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="workout_plans")


# --- Pydantic Schemas ---

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserUpdate(BaseModel):
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    gender: Optional[str] = None
    fitness_goal: Optional[str] = None
    experience_level: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    gender: Optional[str] = None
    fitness_goal: Optional[str] = None
    experience_level: Optional[str] = None
    intensity_modifier: float
    
    class Config:
        from_attributes = True

class WorkoutLogCreate(BaseModel):
    workout_type: str
    difficulty_feedback: str
    calories_burned: float
    reps: Optional[int] = 0

class WorkoutLogResponse(BaseModel):
    id: int
    date: datetime
    workout_type: str
    difficulty_feedback: str
    calories_burned: float
    reps: Optional[int] = 0
    
    class Config:
        from_attributes = True

class WorkoutPlanCreate(BaseModel):
    day_of_week: int
    exercise_name: str
    target_sets: int
    target_reps: int
    target_duration_mins: Optional[int] = None

class WorkoutPlanResponse(WorkoutPlanCreate):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
