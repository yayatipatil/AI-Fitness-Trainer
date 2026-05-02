import os
import random
from datetime import datetime, timedelta
from database import SessionLocal, engine, Base
import models
from utils import security

def seed_database():
    print("Creating tables...")
    Base.metadata.drop_all(bind=engine) # Reset for demo
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Generating 50 synthetic users for ML training...")
        goals = ["weight_loss", "muscle_gain", "endurance", "maintenance"]
        workout_types = ["Hypertrophy Strength Training", "High Intensity Interval Training (HIIT) & Cardio", "Balanced Functional Training"]
        difficulties = ["Easy", "Medium", "Hard"]
        
        base_date = datetime.utcnow() - timedelta(days=30)
        
        for i in range(50):
            pw = security.hash_password("password123")
            user = models.User(
                username=f"user_{i}",
                email=f"user_{i}@example.com",
                hashed_password=pw,
                age=random.randint(18, 65),
                height_cm=random.uniform(150, 200),
                weight_kg=random.uniform(50, 120),
                gender=random.choice(["Male", "Female"]),
                fitness_goal=random.choice(goals),
                experience_level=random.choice(["Beginner", "Intermediate", "Advanced"]),
                intensity_modifier=random.uniform(0.8, 1.5)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Generate workout logs for the past 30 days
            # Randomize their activity level
            activity_level = random.uniform(0.1, 1.0)
            for d in range(30):
                if random.random() < activity_level:
                    log_date = base_date + timedelta(days=d)
                    log = models.WorkoutLog(
                        user_id=user.id,
                        date=log_date,
                        workout_type=random.choice(workout_types),
                        difficulty_feedback=random.choices(difficulties, weights=[0.2, 0.6, 0.2])[0],
                        calories_burned=random.uniform(150, 800),
                        reps=random.randint(10, 100)
                    )
                    db.add(log)
            db.commit()

        print("Creating demo user...")
        demo_username = "demo_student"
        demo_password = "password123"
        demo_email = "student@demo.com"
        
        hashed_pw = security.hash_password(demo_password)
        
        demo_user = models.User(
            username=demo_username, 
            email=demo_email, 
            hashed_password=hashed_pw,
            age=25,
            height_cm=178.0,
            weight_kg=75.0,
            gender="Male",
            fitness_goal="muscle_gain",
            experience_level="Intermediate",
            intensity_modifier=1.1
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        
        # 14 days history for demo user
        demo_base_date = datetime.utcnow() - timedelta(days=14)
        for i in range(14):
            if random.random() < 0.6: 
                log_date = demo_base_date + timedelta(days=i)
                log = models.WorkoutLog(
                    user_id=demo_user.id,
                    date=log_date,
                    workout_type=random.choice(workout_types),
                    difficulty_feedback=random.choices(difficulties, weights=[0.2, 0.6, 0.2])[0],
                    calories_burned=random.uniform(250, 600),
                    reps=random.randint(20, 80)
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
