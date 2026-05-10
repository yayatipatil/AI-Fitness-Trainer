from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
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

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    category = Column(String)
    demo_url = Column(String, nullable=True)
    primary_muscles = Column(String) # Stored as JSON string
    secondary_muscles = Column(String) # Stored as JSON string
    form_tips = Column(String) # Stored as JSON string
    equipment = Column(String) # Stored as JSON string

class UserEquipment(Base):
    __tablename__ = "user_equipment"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True, index=True)
    equipment = Column(String) # Stored as JSON string

    user = relationship("User")

class Challenge(Base):
    __tablename__ = "challenges"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    target_value = Column(Integer) # e.g. 10 workouts, 5000 calories
    metric = Column(String) # "workouts", "calories", "streak"
    badge_url = Column(String, nullable=True)

class UserChallenge(Base):
    __tablename__ = "user_challenges"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    challenge_id = Column(Integer, ForeignKey("challenges.id"))
    progress = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

class Badge(Base):
    __tablename__ = "badges"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    icon_url = Column(String)
    earned_at = Column(DateTime, default=datetime.utcnow)

class SetLog(Base):
    __tablename__ = "set_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    workout_log_id = Column(Integer, ForeignKey("workout_logs.id"), nullable=True)
    exercise_name = Column(String, index=True)
    weight_kg = Column(Float)
    reps = Column(Integer)
    date = Column(DateTime, default=datetime.utcnow)
    
    # 1RM formula: weight * (1 + reps/30)
    def calculate_1rm(self):
        return self.weight_kg * (1 + self.reps / 30.0)

class DietLog(Base):
    __tablename__ = "diet_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, default=datetime.utcnow)
    food_name = Column(String)
    calories = Column(Float, default=0.0)
    protein = Column(Float, default=0.0)
    carbs = Column(Float, default=0.0)
    fat = Column(Float, default=0.0)
    
    user = relationship("User")

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

class AccountUpdate(BaseModel):
    username: str
    email: str

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

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

class ExerciseCreate(BaseModel):
    name: str
    category: str
    demo_url: Optional[str] = None
    primary_muscles: str = "[]"
    secondary_muscles: str = "[]"
    form_tips: str = "[]"
    equipment: str = "[]"

class ExerciseResponse(ExerciseCreate):
    id: int
    
    class Config:
        from_attributes = True

class UserEquipmentUpdate(BaseModel):
    equipment: List[str]

class UserEquipmentResponse(BaseModel):
    user_id: int
    equipment: List[str]

    class Config:
        from_attributes = True

class ChallengeResponse(BaseModel):
    id: int
    title: str
    description: str
    target_value: int
    metric: str
    badge_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserChallengeResponse(BaseModel):
    id: int
    challenge: ChallengeResponse
    progress: int
    completed: bool
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class BadgeResponse(BaseModel):
    id: int
    name: str
    icon_url: str
    earned_at: datetime
    
    class Config:
        from_attributes = True

class SetLogCreate(BaseModel):
    workout_log_id: Optional[int] = None
    exercise_name: str
    weight_kg: float
    reps: int

class SetLogResponse(SetLogCreate):
    id: int
    user_id: int
    date: datetime
    estimated_1rm: float
    
    class Config:
        from_attributes = True

class DietLogCreate(BaseModel):
    food_name: str
    calories: float
    protein: float
    carbs: float
    fat: float

class DietLogResponse(DietLogCreate):
    id: int
    user_id: int
    date: datetime

    class Config:
        from_attributes = True
