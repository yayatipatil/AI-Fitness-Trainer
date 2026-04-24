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

    profile = relationship("Profile", back_populates="user", uselist=False)
    workout_logs = relationship("WorkoutLog", back_populates="user")

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    age = Column(Integer)
    height = Column(Float) # in cm
    weight = Column(Float) # in kg
    gender = Column(String)
    goal = Column(String) # Weight Loss, Muscle Gain, Maintenance
    experience_level = Column(String) # Beginner, Intermediate, Advanced

    # Adaptive tracking
    intensity_modifier = Column(Float, default=1.0) # >1 means harder, <1 means easier

    user = relationship("User", back_populates="profile")

class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, default=datetime.utcnow)
    workout_type = Column(String)
    difficulty_feedback = Column(String) # Easy, Medium, Hard
    calories_burned = Column(Float)

    user = relationship("User", back_populates="workout_logs")

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

class ProfileBase(BaseModel):
    age: int
    height: float
    weight: float
    gender: str
    goal: str
    experience_level: str

class ProfileCreate(ProfileBase):
    pass

class ProfileResponse(ProfileBase):
    id: int
    user_id: int
    intensity_modifier: float
    
    class Config:
        from_attributes = True

class WorkoutLogCreate(BaseModel):
    workout_type: str
    difficulty_feedback: str
    calories_burned: float

class WorkoutLogResponse(BaseModel):
    id: int
    date: datetime
    workout_type: str
    difficulty_feedback: str
    calories_burned: float
    
    class Config:
        from_attributes = True
