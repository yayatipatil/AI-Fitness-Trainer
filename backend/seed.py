import os
import random
import json
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
        
        # Add Demo User Equipment
        demo_equipment = models.UserEquipment(
            user_id=demo_user.id,
            equipment=json.dumps(["dumbbells", "bodyweight", "resistance bands"])
        )
        db.add(demo_equipment)

        db.commit()

        print("Seeding exercises...")
        exercises_data = [
            {"name": "Squats", "category": "Legs", "primary_muscles": '["quads", "glutes"]', "secondary_muscles": '["hamstrings", "calves"]', "form_tips": '["Keep chest up", "Push through heels"]', "equipment": '["bodyweight", "barbell", "dumbbells"]'},
            {"name": "Push-ups", "category": "Chest", "primary_muscles": '["chest", "triceps"]', "secondary_muscles": '["shoulders", "abs"]', "form_tips": '["Keep core tight", "Elbows at 45 degrees"]', "equipment": '["bodyweight"]'},
            {"name": "Pull-ups", "category": "Back", "primary_muscles": '["back", "biceps"]', "secondary_muscles": '["forearms", "shoulders"]', "form_tips": '["Pull with your lats", "Full range of motion"]', "equipment": '["pull-up bar"]'},
            {"name": "Deadlifts", "category": "Back", "primary_muscles": '["hamstrings", "glutes", "back"]', "secondary_muscles": '["quads", "forearms", "abs"]', "form_tips": '["Keep back straight", "Hinge at hips"]', "equipment": '["barbell", "dumbbells"]'},
            {"name": "Bench Press", "category": "Chest", "primary_muscles": '["chest", "triceps"]', "secondary_muscles": '["shoulders"]', "form_tips": '["Keep feet flat", "Squeeze shoulder blades"]', "equipment": '["barbell", "bench", "dumbbells"]'},
            {"name": "Lunges", "category": "Legs", "primary_muscles": '["quads", "glutes"]', "secondary_muscles": '["hamstrings", "calves"]', "form_tips": '["Keep torso upright", "Don\'t let knee pass toe"]', "equipment": '["bodyweight", "dumbbells"]'},
            {"name": "Overhead Press", "category": "Shoulders", "primary_muscles": '["shoulders", "triceps"]', "secondary_muscles": '["abs"]', "form_tips": '["Press in a straight line", "Don\'t lean back excessively"]', "equipment": '["barbell", "dumbbells"]'},
            {"name": "Bicep Curls", "category": "Arms", "primary_muscles": '["biceps"]', "secondary_muscles": '["forearms"]', "form_tips": '["Keep elbows stationary", "Squeeze at top"]', "equipment": '["dumbbells", "barbell", "resistance bands"]'},
            {"name": "Tricep Dips", "category": "Arms", "primary_muscles": '["triceps", "chest"]', "secondary_muscles": '["shoulders"]', "form_tips": '["Keep elbows tucked", "Lower slowly"]', "equipment": '["bodyweight", "bench"]'},
            {"name": "Plank", "category": "Core", "primary_muscles": '["abs", "obliques"]', "secondary_muscles": '["shoulders", "back"]', "form_tips": '["Keep body in straight line", "Don\'t let hips sag"]', "equipment": '["bodyweight"]'},
            {"name": "Russian Twists", "category": "Core", "primary_muscles": '["obliques", "abs"]', "secondary_muscles": '[]', "form_tips": '["Rotate from torso", "Keep legs still"]', "equipment": '["bodyweight", "dumbbells", "kettlebell"]'},
            {"name": "Calf Raises", "category": "Legs", "primary_muscles": '["calves"]', "secondary_muscles": '[]', "form_tips": '["Full extension at top", "Slow descent"]', "equipment": '["bodyweight", "dumbbells", "barbell"]'},
            {"name": "Leg Press", "category": "Legs", "primary_muscles": '["quads", "glutes"]', "secondary_muscles": '["hamstrings"]', "form_tips": '["Don\'t lock knees at top", "Feet shoulder-width"]', "equipment": '["full gym"]'},
            {"name": "Lat Pulldown", "category": "Back", "primary_muscles": '["back", "biceps"]', "secondary_muscles": '["shoulders"]', "form_tips": '["Pull to upper chest", "Squeeze lats"]', "equipment": '["cable machine", "full gym"]'},
            {"name": "Cable Crossovers", "category": "Chest", "primary_muscles": '["chest"]', "secondary_muscles": '["shoulders"]', "form_tips": '["Slight bend in elbows", "Squeeze chest at center"]', "equipment": '["cable machine", "full gym"]'},
            {"name": "Face Pulls", "category": "Shoulders", "primary_muscles": '["shoulders", "back"]', "secondary_muscles": '["biceps"]', "form_tips": '["Pull towards face", "Keep elbows high"]', "equipment": '["cable machine", "resistance bands"]'},
            {"name": "Kettlebell Swings", "category": "Full Body", "primary_muscles": '["glutes", "hamstrings"]', "secondary_muscles": '["back", "shoulders", "abs"]', "form_tips": '["Hinge at hips", "Thrust with glutes, don\'t pull with arms"]', "equipment": '["kettlebell"]'},
            {"name": "Burpees", "category": "Full Body", "primary_muscles": '["chest", "quads", "abs"]', "secondary_muscles": '["shoulders", "triceps", "calves"]', "form_tips": '["Maintain plank form", "Explode on jump"]', "equipment": '["bodyweight"]'},
            {"name": "Mountain Climbers", "category": "Core", "primary_muscles": '["abs", "shoulders"]', "secondary_muscles": '["quads", "chest"]', "form_tips": '["Keep hips down", "Drive knees to chest"]', "equipment": '["bodyweight"]'},
            {"name": "Glute Bridges", "category": "Legs", "primary_muscles": '["glutes", "hamstrings"]', "secondary_muscles": '["abs"]', "form_tips": '["Squeeze glutes at top", "Don\'t overextend back"]', "equipment": '["bodyweight"]'}
        ]
        
        for ex_data in exercises_data:
            exercise = models.Exercise(**ex_data)
            db.add(exercise)
        db.commit()

        print("Seeding challenges...")
        challenges_data = [
            {
                "title": "First Step",
                "description": "Complete your first workout.",
                "target_value": 1,
                "metric": "workouts",
                "badge_url": "https://cdn-icons-png.flaticon.com/512/3112/3112946.png"
            },
            {
                "title": "Consistency is Key",
                "description": "Complete 10 workouts.",
                "target_value": 10,
                "metric": "workouts",
                "badge_url": "https://cdn-icons-png.flaticon.com/512/3113/3113038.png"
            },
            {
                "title": "Calorie Crusher",
                "description": "Burn 5000 calories.",
                "target_value": 5000,
                "metric": "calories",
                "badge_url": "https://cdn-icons-png.flaticon.com/512/3112/3112993.png"
            }
        ]
        
        for c_data in challenges_data:
            challenge = models.Challenge(**c_data)
            db.add(challenge)
        db.commit()

        print("Seeding 8 weeks of 1RM data...")
        # 8 weeks of Squats, Bench Press, Deadlifts
        base_weights = {"Squats": 60, "Bench Press": 50, "Deadlifts": 80}
        
        for week in range(8):
            date = datetime.utcnow() - timedelta(weeks=8-week)
            for ex, bw in base_weights.items():
                # Simulate linear progression + some noise
                weight = bw + (week * 2.5) + random.uniform(-2, 2)
                reps = random.randint(8, 12)
                
                s_log = models.SetLog(
                    user_id=demo_user.id,
                    exercise_name=ex,
                    weight_kg=round(weight, 1),
                    reps=reps,
                    date=date
                )
                db.add(s_log)
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
