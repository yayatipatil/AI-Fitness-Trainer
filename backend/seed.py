import os
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models
import auth

def seed_database():
    print("Creating tables...")
    Base.metadata.drop_all(bind=engine) # Reset for demo
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Creating demo user...")
        demo_username = "demo_student"
        demo_password = "password123"
        demo_email = "student@demo.com"
        
        hashed_pw = auth.get_password_hash(demo_password)
        user = models.User(username=demo_username, email=demo_email, hashed_password=hashed_pw)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print("Creating demo profile...")
        profile = models.Profile(
            user_id=user.id,
            age=22,
            height=175.0,
            weight=70.0,
            gender="Male",
            goal="Muscle Gain",
            experience_level="Intermediate",
            intensity_modifier=1.1
        )
        db.add(profile)
        db.commit()
        
        print("Generating historical workout logs...")
        # Create 14 days of workout history
        base_date = datetime.utcnow() - timedelta(days=14)
        
        workout_types = ["Hypertrophy Strength Training", "High Intensity Interval Training (HIIT) & Cardio", "Balanced Functional Training"]
        difficulties = ["Easy", "Medium", "Hard"]
        
        for i in range(14):
            # Workout 4 times a week on average
            if random.random() < 0.6: 
                log_date = base_date + timedelta(days=i)
                log = models.WorkoutLog(
                    user_id=user.id,
                    date=log_date,
                    workout_type=random.choice(workout_types),
                    difficulty_feedback=random.choices(difficulties, weights=[0.2, 0.6, 0.2])[0],
                    calories_burned=random.uniform(250, 600)
                )
                db.add(log)
        
        db.commit()
        
        print("========================================")
        print("Demo data seeded successfully!")
        print(f"Username: {demo_username}")
        print(f"Password: {demo_password}")
        print("========================================")
        
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
