import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sqlalchemy.orm import Session
from database import SessionLocal
from ml.features import get_all_user_features

MODEL_PATH = os.path.join(os.path.dirname(__file__), "fitness_model.pkl")

def generate_synthetic_features(num_samples: int) -> pd.DataFrame:
    np.random.seed(42)
    
    # Grounded realistic ranges
    # BMI: Normal range 18.5 - 25, Overweight 25 - 30, Obese 30+
    bmi = np.random.normal(24, 4, num_samples)
    bmi = np.clip(bmi, 15, 45)
    
    # Goals: 0=weight_loss, 1=maintenance, 2=muscle_gain, 3=endurance
    fitness_goal_encoded = np.random.choice([0, 1, 2, 3], num_samples)
    
    # Workouts last 30 days: 0 to 30
    total_workouts = np.random.gamma(shape=2.0, scale=4.0, size=num_samples)
    total_workouts = np.clip(np.round(total_workouts), 0, 30)
    
    # Avg reps per session: 0 to 100
    avg_reps = np.random.normal(30, 15, num_samples)
    avg_reps = np.clip(avg_reps, 0, 200)
    
    # Avg calories: 150 to 800
    avg_cal = np.random.normal(400, 150, num_samples)
    avg_cal = np.clip(avg_cal, 100, 1000)
    
    # Streak: correlated to total workouts
    streak = total_workouts * np.random.uniform(0.1, 0.8, num_samples)
    streak = np.clip(np.round(streak), 0, 30)
    
    df = pd.DataFrame({
        "bmi": bmi,
        "fitness_goal_encoded": fitness_goal_encoded,
        "total_workouts_last_30_days": total_workouts,
        "avg_reps_per_session": avg_reps,
        "avg_calories_burned_per_session": avg_cal,
        "workout_streak_days": streak
    })
    
    return df

def calculate_target_score(df: pd.DataFrame) -> pd.Series:
    # A pseudo-realistic scoring formula to act as ground truth for synthetic data
    # BMI optimal is around 22
    bmi_penalty = abs(df["bmi"] - 22) * 1.5
    
    # Activity bonuses
    workout_bonus = df["total_workouts_last_30_days"] * 1.5
    streak_bonus = df["workout_streak_days"] * 2.0
    cal_bonus = df["avg_calories_burned_per_session"] / 10.0
    
    score = 50 - bmi_penalty + workout_bonus + streak_bonus + cal_bonus
    score = score + np.random.normal(0, 5, len(df)) # add noise
    return np.clip(score, 0, 100)

def train_model():
    print("Fetching user data for ML training...")
    db = SessionLocal()
    df = get_all_user_features(db)
    db.close()
    
    if not df.empty:
        if "fitness_score" not in df.columns:
            df["fitness_score"] = calculate_target_score(df)
            
    # If fewer than 10 users, generate synthetic data to supplement
    if df.empty or len(df) < 10:
        print(f"Only {len(df) if not df.empty else 0} real users found. Generating synthetic data...")
        synthetic_df = generate_synthetic_features(500)
        synthetic_df["fitness_score"] = calculate_target_score(synthetic_df)
        
        if not df.empty:
            df = pd.concat([df, synthetic_df], ignore_index=True)
        else:
            df = synthetic_df
    
    if "user_id" in df.columns:
        df = df.drop(columns=["user_id"])
        
    X = df.drop(columns=["fitness_score"])
    y = df["fitness_score"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Random Forest Regressor...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)
    
    print(f"--- ML Model Training Results ---")
    print(f"MAE:  {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"R²:   {r2:.2f}")
    
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")
    return model

def get_model():
    if not os.path.exists(MODEL_PATH):
        return train_model()
    return joblib.load(MODEL_PATH)

def predict_score(features: dict) -> float:
    model = get_model()
    df = pd.DataFrame([features])
    if "user_id" in df.columns:
        df = df.drop(columns=["user_id"])
    pred = model.predict(df)[0]
    return float(np.clip(pred, 0, 100))
