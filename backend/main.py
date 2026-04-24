from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import List

import models, database, auth, recommendation, ml_model

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="AI Fitness Trainer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development, allow all. In prod, restrict to frontend URL.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure ML model is trained on startup
ml_model.get_model()

@app.post("/register", response_model=models.UserCreate)
def register(user: models.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    db_email = db.query(models.User).filter(models.User.email == user.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return user

@app.post("/login", response_model=models.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/profile", response_model=models.ProfileResponse)
def get_profile(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if not current_user.profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return current_user.profile

@app.post("/profile", response_model=models.ProfileResponse)
def create_or_update_profile(profile: models.ProfileCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    db_profile = current_user.profile
    if db_profile:
        for key, value in profile.dict().items():
            setattr(db_profile, key, value)
    else:
        db_profile = models.Profile(**profile.dict(), user_id=current_user.id)
        db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

@app.get("/recommend-workout")
def get_workout(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if not current_user.profile:
        raise HTTPException(status_code=400, detail="Profile required for recommendations")
    
    profile = current_user.profile
    workout_plan = recommendation.get_workout_recommendation(
        goal=profile.goal,
        experience_level=profile.experience_level,
        intensity_modifier=profile.intensity_modifier
    )
    
    diet_plan = recommendation.get_diet_recommendation(
        weight=profile.weight,
        height_cm=profile.height,
        age=profile.age,
        gender=profile.gender,
        goal=profile.goal
    )
    
    return {
        "workout": workout_plan,
        "diet": diet_plan
    }

@app.post("/log-workout", response_model=models.WorkoutLogResponse)
def log_workout(log: models.WorkoutLogCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    new_log = models.WorkoutLog(**log.dict(), user_id=current_user.id)
    db.add(new_log)
    
    # Update adaptive logic
    if current_user.profile:
        new_modifier = recommendation.update_intensity_modifier(
            current_user.profile.intensity_modifier, 
            log.difficulty_feedback
        )
        current_user.profile.intensity_modifier = new_modifier
        
    db.commit()
    db.refresh(new_log)
    return new_log

@app.get("/fitness-score")
def get_fitness_score(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if not current_user.profile:
        return {"fitness_score": 0, "message": "Complete profile to get score"}
        
    profile = current_user.profile
    bmi = recommendation.calculate_bmi(profile.weight, profile.height)
    
    # Calculate stats from logs
    logs = current_user.workout_logs
    
    # Very basic stats for demo:
    workout_frequency = min(len(logs), 7) # Cap at 7 for model input
    avg_calories = sum(log.calories_burned for log in logs) / len(logs) if logs else 200
    
    score = ml_model.predict_fitness_score(bmi, workout_frequency, avg_calories)
    
    return {
        "fitness_score": round(score, 1),
        "bmi": round(bmi, 1)
    }

@app.get("/dashboard-data")
def get_dashboard_data(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    logs = current_user.workout_logs
    
    # Aggregate data for charts
    dates = [log.date.strftime("%Y-%m-%d") for log in logs[-7:]] # Last 7 logs
    calories = [log.calories_burned for log in logs[-7:]]
    
    # Calculate streak (simple version)
    streak = len(logs) if logs else 0
    
    return {
        "dates": dates,
        "calories": calories,
        "streak": streak
    }
