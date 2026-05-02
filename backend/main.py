from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import List

import models, database, auth, recommendation
from ml import model as ml_model, features as ml_features
from utils import security, jwt as jwt_utils

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

@app.post("/register", response_model=models.UserResponse)
def register(user: models.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    db_email = db.query(models.User).filter(models.User.email == user.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = security.hash_password(user.password)
    new_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/auth/login", response_model=models.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Using jwt_utils
    access_token_expires = timedelta(minutes=60 * 24 * 7) # 1 week
    access_token = jwt_utils.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=models.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.post("/auth/me", response_model=models.UserResponse)
def update_me(user_update: models.UserUpdate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    update_data = user_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    return current_user

@app.get("/recommend-workout")
def get_workout(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if not current_user.fitness_goal or not current_user.experience_level:
        raise HTTPException(status_code=400, detail="Profile required for recommendations")
    
    workout_plan = recommendation.get_workout_recommendation(
        goal=current_user.fitness_goal if current_user.fitness_goal else "Maintenance",
        experience_level=current_user.experience_level if current_user.experience_level else "Beginner",
        intensity_modifier=current_user.intensity_modifier
    )
    
    diet_plan = recommendation.get_diet_recommendation(
        weight=current_user.weight_kg if current_user.weight_kg else 70,
        height_cm=current_user.height_cm if current_user.height_cm else 170,
        age=current_user.age if current_user.age else 25,
        gender=current_user.gender if current_user.gender else "Male",
        goal=current_user.fitness_goal if current_user.fitness_goal else "Maintenance"
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
    new_modifier = recommendation.update_intensity_modifier(
        current_user.intensity_modifier, 
        log.difficulty_feedback
    )
    current_user.intensity_modifier = new_modifier
        
    db.commit()
    db.refresh(new_log)
    return new_log

@app.post("/log-live-workout", response_model=models.WorkoutLogResponse)
def log_live_workout(log: models.WorkoutLogCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    new_log = models.WorkoutLog(**log.dict(), user_id=current_user.id)
    db.add(new_log)
    
    # If the user completed a high number of verified reps, we can increase intensity faster
    if log.reps and log.reps > 15:
        new_modifier = min(current_user.intensity_modifier + 0.15, 2.5)
    else:
        new_modifier = recommendation.update_intensity_modifier(
            current_user.intensity_modifier, 
            log.difficulty_feedback
        )
    current_user.intensity_modifier = new_modifier
        
    db.commit()
    db.refresh(new_log)
    return new_log

@app.get("/fitness-score")
def get_fitness_score(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    logs = current_user.workout_logs
    features = ml_features.extract_user_features(current_user, logs)
    
    score = ml_model.predict_score(features)
    
    return {
        "fitness_score": round(score, 1),
        "bmi": round(features["bmi"], 1)
    }

@app.post("/ml/train")
def train_model():
    ml_model.train_model()
    return {"status": "Model training completed successfully"}

@app.get("/planner/week", response_model=List[models.WorkoutPlanResponse])
def get_planner_week(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    return db.query(models.WorkoutPlan).filter(models.WorkoutPlan.user_id == current_user.id).all()

@app.post("/planner/day", response_model=models.WorkoutPlanResponse)
def add_planner_day(plan: models.WorkoutPlanCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    new_plan = models.WorkoutPlan(**plan.dict(), user_id=current_user.id)
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return new_plan

@app.delete("/planner/day/{plan_id}")
def delete_planner_day(plan_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    plan = db.query(models.WorkoutPlan).filter(models.WorkoutPlan.id == plan_id, models.WorkoutPlan.user_id == current_user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(plan)
    db.commit()
    return {"detail": "Deleted successfully"}

@app.get("/planner/suggestions")
def get_planner_suggestions(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    from datetime import datetime, timedelta
    two_weeks_ago = datetime.utcnow() - timedelta(days=14)
    logs = db.query(models.WorkoutLog).filter(
        models.WorkoutLog.user_id == current_user.id,
        models.WorkoutLog.date >= two_weeks_ago
    ).all()
    
    # We want to check: if avg reps >= target_reps for an exercise in last 3 sessions, suggest progressive overload
    # Let's map exercise names from planner to logs
    plans = db.query(models.WorkoutPlan).filter(models.WorkoutPlan.user_id == current_user.id).all()
    suggestions = []
    
    for plan in plans:
        # Simple match logic: if plan exercise name is in log workout_type
        relevant_logs = [l for l in logs if plan.exercise_name.lower() in l.workout_type.lower()]
        # Sort by date descending, take last 3
        relevant_logs.sort(key=lambda x: x.date, reverse=True)
        last_3 = relevant_logs[:3]
        
        if len(last_3) >= 3:
            avg_reps = sum(l.reps for l in last_3) / 3.0
            if avg_reps >= plan.target_reps:
                suggestions.append({
                    "exercise": plan.exercise_name,
                    "current_target": plan.target_reps,
                    "suggested_target": plan.target_reps + 2,
                    "reason": f"You averaged {round(avg_reps)} reps over your last 3 sessions. Time to level up!"
                })
                
    # Return unique suggestions (since planner might have same exercise on multiple days)
    unique_suggs = {s["exercise"]: s for s in suggestions}.values()
    return list(unique_suggs)

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
