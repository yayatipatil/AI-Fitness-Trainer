from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session
import models

def encode_goal(goal: str) -> int:
    mapping = {
        "weight_loss": 0,
        "maintenance": 1,
        "muscle_gain": 2,
        "endurance": 3
    }
    if not goal:
        return 1
    return mapping.get(goal.lower(), 1)

def extract_user_features(user: models.User, logs: list) -> dict:
    # 1. BMI
    bmi = 22.5
    if user.height_cm and user.weight_kg and user.height_cm > 0:
        height_m = user.height_cm / 100
        bmi = user.weight_kg / (height_m * height_m)
        
    # 2. Fitness goal encoded
    goal_encoded = encode_goal(user.fitness_goal)
    
    # 3. Last 30 days workouts
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    recent_logs = [log for log in logs if log.date >= thirty_days_ago]
    total_workouts_last_30_days = len(recent_logs)
    
    # 4. Avg reps and calories
    avg_reps = 0.0
    avg_cal = 0.0
    if recent_logs:
        avg_reps = sum(log.reps or 0 for log in recent_logs) / len(recent_logs)
        avg_cal = sum(log.calories_burned or 0 for log in recent_logs) / len(recent_logs)
        
    # 5. Workout streak days
    streak = 0
    if logs:
        sorted_logs = sorted(logs, key=lambda x: x.date, reverse=True)
        current_date = now.date()
        for log in sorted_logs:
            log_date = log.date.date()
            if log_date == current_date or log_date == current_date - timedelta(days=1):
                streak += 1
                current_date = log_date
            elif log_date < current_date - timedelta(days=1):
                break
                
    return {
        "user_id": user.id,
        "bmi": bmi,
        "fitness_goal_encoded": goal_encoded,
        "total_workouts_last_30_days": total_workouts_last_30_days,
        "avg_reps_per_session": avg_reps,
        "avg_calories_burned_per_session": avg_cal,
        "workout_streak_days": streak
    }

def get_all_user_features(db: Session) -> pd.DataFrame:
    users = db.query(models.User).all()
    data = []
    for user in users:
        logs = db.query(models.WorkoutLog).filter(models.WorkoutLog.user_id == user.id).all()
        features = extract_user_features(user, logs)
        data.append(features)
    
    if not data:
        return pd.DataFrame()
        
    return pd.DataFrame(data)
