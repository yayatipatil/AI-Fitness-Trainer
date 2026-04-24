import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import pickle
import os

MODEL_PATH = "fitness_model.pkl"

def generate_synthetic_data(num_samples=1000):
    np.random.seed(42)
    
    # Features
    # BMI: Normal range is 18.5 to 24.9. Let's say 15 to 40.
    bmi = np.random.uniform(15, 40, num_samples)
    
    # Workout frequency (days per week)
    workout_freq = np.random.randint(0, 7, num_samples)
    
    # Calories burned (weekly average per session)
    calories_burned = np.random.uniform(100, 800, num_samples)
    
    # Target: Fitness Score (0-100)
    # Higher workout freq, higher calories burned, and BMI closer to 22.5 is better.
    
    bmi_score = 100 - (abs(bmi - 22.5) * 3)
    bmi_score = np.clip(bmi_score, 0, 100)
    
    freq_score = (workout_freq / 7) * 100
    
    cal_score = (calories_burned / 800) * 100
    
    # Weighted average
    fitness_score = (bmi_score * 0.4) + (freq_score * 0.4) + (cal_score * 0.2)
    
    # Add some noise
    noise = np.random.normal(0, 5, num_samples)
    fitness_score = np.clip(fitness_score + noise, 0, 100)
    
    df = pd.DataFrame({
        "bmi": bmi,
        "workout_frequency": workout_freq,
        "calories_burned": calories_burned,
        "fitness_score": fitness_score
    })
    
    return df

def train_model():
    print("Generating synthetic data and training ML model...")
    df = generate_synthetic_data()
    
    X = df[["bmi", "workout_frequency", "calories_burned"]]
    y = df["fitness_score"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Save the model
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    
    print(f"Model trained. R^2 score on test set: {model.score(X_test, y_test):.2f}")
    return model

def get_model():
    if not os.path.exists(MODEL_PATH):
        return train_model()
    
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)

def predict_fitness_score(bmi: float, workout_frequency: int, calories_burned: float) -> float:
    model = get_model()
    # Create DataFrame to match feature names
    X = pd.DataFrame({
        "bmi": [bmi],
        "workout_frequency": [workout_frequency],
        "calories_burned": [calories_burned]
    })
    prediction = model.predict(X)[0]
    return float(np.clip(prediction, 0, 100))
