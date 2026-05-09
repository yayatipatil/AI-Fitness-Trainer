import os
import requests
from dotenv import load_dotenv

load_dotenv()

def calculate_bmi(weight: float, height_cm: float) -> float:
    height_m = height_cm / 100
    if height_m <= 0:
        return 0
    return weight / (height_m * height_m)

def calculate_bmr(weight: float, height_cm: float, age: int, gender: str) -> float:
    # Mifflin-St Jeor Equation
    if gender.lower() == 'male':
        return (10 * weight) + (6.25 * height_cm) - (5 * age) + 5
    else:
        return (10 * weight) + (6.25 * height_cm) - (5 * age) - 161

def fetch_dummyjson_recipes() -> list:
    url = "https://dummyjson.com/recipes?limit=50"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("recipes", [])
    except Exception as e:
        print(f"Error fetching DummyJSON recipes: {e}")
    return []

def get_diet_recommendation(weight: float, height_cm: float, age: int, gender: str, goal: str) -> dict:
    bmr = calculate_bmr(weight, height_cm, age, gender)
    tdee = bmr * 1.55 
    
    calories = tdee
    if goal.lower() == 'weight loss':
        calories = tdee - 500
    elif goal.lower() == 'muscle gain':
        calories = tdee + 300
    
    protein_multiplier = 1.6 if goal.lower() == 'muscle gain' else 1.2
    protein = weight * protein_multiplier
    
    all_recipes = fetch_dummyjson_recipes()
    
    # Fallback if API fails
    if not all_recipes:
        all_recipes = [
            {"name": "Protein Oatmeal", "caloriesPerServing": 350, "mealType": ["Breakfast"], "image": "https://images.unsplash.com/photo-1517673132405-a56a62b18caf?w=400&q=80", "id": 1},
            {"name": "Grilled Chicken Salad", "caloriesPerServing": 450, "mealType": ["Lunch"], "image": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&q=80", "id": 2},
            {"name": "Salmon and Quinoa", "caloriesPerServing": 600, "mealType": ["Dinner"], "image": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400&q=80", "id": 3},
            {"name": "Greek Yogurt & Berries", "caloriesPerServing": 200, "mealType": ["Snack"], "image": "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400&q=80", "id": 4}
        ]
        
    breakfasts = [r for r in all_recipes if "Breakfast" in r.get("mealType", [])]
    lunches = [r for r in all_recipes if "Lunch" in r.get("mealType", [])]
    dinners = [r for r in all_recipes if "Dinner" in r.get("mealType", [])]
    snacks = [r for r in all_recipes if "Snack" in r.get("mealType", [])]
    
    # If API didn't tag properly, just use the whole list
    if not breakfasts: breakfasts = all_recipes
    if not lunches: lunches = all_recipes
    if not dinners: dinners = all_recipes
    if not snacks: snacks = all_recipes
    
    import random
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekly_plan = {}
    
    for day in days:
        b = random.choice(breakfasts)
        l = random.choice(lunches)
        d = random.choice(dinners)
        s = random.choice(snacks)
        
        # We assign calories proportionally to meet the user's daily target
        b_cal = round(calories * 0.25)
        l_cal = round(calories * 0.30)
        d_cal = round(calories * 0.35)
        s_cal = round(calories * 0.10)
        
        weekly_plan[day] = [
            {
                "type": "Breakfast",
                "title": b.get("name", "Healthy Breakfast"),
                "image": b.get("image", ""),
                "calories": b_cal,
                "url": f"https://dummyjson.com/recipes/{b.get('id', 1)}"
            },
            {
                "type": "Lunch",
                "title": l.get("name", "Healthy Lunch"),
                "image": l.get("image", ""),
                "calories": l_cal,
                "url": f"https://dummyjson.com/recipes/{l.get('id', 1)}"
            },
            {
                "type": "Dinner",
                "title": d.get("name", "Healthy Dinner"),
                "image": d.get("image", ""),
                "calories": d_cal,
                "url": f"https://dummyjson.com/recipes/{d.get('id', 1)}"
            },
            {
                "type": "Snack",
                "title": s.get("name", "Healthy Snack"),
                "image": s.get("image", ""),
                "calories": s_cal,
                "url": f"https://dummyjson.com/recipes/{s.get('id', 1)}"
            }
        ]

    return {
        "daily_calories": round(calories),
        "protein_grams": round(protein),
        "suggestion": "Focus on whole foods, lean proteins, and stay hydrated. Your meals below are balanced to meet your daily caloric needs.",
        "weekly_plan": weekly_plan
    }


def get_workout_recommendation(goal: str, experience_level: str, intensity_modifier: float, duration_minutes: int = 30, user_equipment: list = None, db_exercises: dict = None) -> list:
    if user_equipment is None:
        user_equipment = []
    if db_exercises is None:
        db_exercises = {}
        
    # Scale sets and exercise count by duration
    if duration_minutes <= 5:
        base_sets = 2
        ex_count = 1
    elif duration_minutes <= 15:
        base_sets = 2
        ex_count = 3
    elif duration_minutes <= 30:
        base_sets = 3
        ex_count = 5
    elif duration_minutes <= 45:
        base_sets = 4
        ex_count = 6
    else:
        base_sets = 4
        ex_count = 8
        
    base_reps = 10
    if experience_level.lower() == 'beginner':
        base_reps = 12
    elif experience_level.lower() == 'advanced':
        base_reps = 8
        
    # Apply adaptive intensity
    adjusted_sets = max(1, int(base_sets * intensity_modifier))
    adjusted_reps = max(5, int(base_reps * intensity_modifier))
    
    plans = []
    
    # We will generate base plans and then filter/slice them
    if goal.lower() == 'weight loss':
        base_plans = [
            {"type": "High Intensity Interval Training (HIIT) & Cardio", "rest_time": "60 seconds", "exercises": ["Jumping Jacks", "Burpees", "Mountain Climbers", "Bodyweight Squats", "Kettlebell Swings", "Lunges", "High Knees", "Plank"]},
            {"type": "Cardio Core Burner", "rest_time": "45 seconds", "exercises": ["High Knees", "Bicycle Crunches", "Plank Jacks", "Jump Squats", "Russian Twists", "Burpees", "Mountain Climbers", "Leg Press"]},
            {"type": "Active Recovery / Low Impact", "rest_time": "90 seconds", "exercises": ["Glute Bridges", "Bird Dogs", "Modified Push-ups", "Calf Raises", "Lat Pulldown", "Face Pulls", "Squats", "Plank"]}
        ]
    elif goal.lower() == 'muscle gain':
        base_plans = [
            {"type": "Hypertrophy Strength Training (Upper Body)", "rest_time": "90 seconds", "exercises": ["Push-ups", "Pull-ups", "Tricep Dips", "Bench Press", "Overhead Press", "Bicep Curls", "Lat Pulldown", "Cable Crossovers", "Face Pulls"]},
            {"type": "Hypertrophy Strength Training (Lower Body)", "rest_time": "90 seconds", "exercises": ["Squats", "Lunges", "Deadlifts", "Calf Raises", "Glute Bridges", "Leg Press", "Kettlebell Swings"]},
            {"type": "Full Body Power", "rest_time": "120 seconds", "exercises": ["Squats", "Bench Press", "Deadlifts", "Pull-ups", "Overhead Press", "Burpees", "Tricep Dips", "Bicep Curls"]}
        ]
    else: # Maintenance
        base_plans = [
            {"type": "Balanced Functional Training", "rest_time": "60 seconds", "exercises": ["Squats", "Push-ups", "Lunges", "Pull-ups", "Plank", "Deadlifts", "Overhead Press"]},
            {"type": "Core & Mobility", "rest_time": "45 seconds", "exercises": ["Plank", "Russian Twists", "Glute Bridges", "Mountain Climbers", "Bicycle Crunches", "Bird Dogs"]},
            {"type": "Endurance Circuit", "rest_time": "30 seconds", "exercises": ["Jumping Jacks", "High Knees", "Lunges", "Burpees", "Mountain Climbers", "Squats", "Push-ups"]}
        ]
        
    for bp in base_plans:
        filtered_exercises = []
        for ex_name in bp["exercises"]:
            # check equipment
            req_eq = db_exercises.get(ex_name, ["bodyweight"])
            
            can_do = False
            if "bodyweight" in req_eq:
                can_do = True
            else:
                for eq in req_eq:
                    if eq in user_equipment or eq == "bodyweight":
                        can_do = True
                        break
            
            if can_do:
                # Add exercise with reps/sets
                reps_val = adjusted_reps
                if "Plank" in ex_name or "Hold" in ex_name:
                    reps_val = f"{int(30 * intensity_modifier)} sec"
                elif "Jacks" in ex_name or "High Knees" in ex_name:
                    reps_val = f"{int(45 * intensity_modifier)} sec"
                
                filtered_exercises.append({
                    "name": ex_name,
                    "sets": adjusted_sets,
                    "reps": reps_val
                })
            
            if len(filtered_exercises) >= ex_count:
                break
                
        # If we couldn't find enough exercises due to equipment, just return what we have
        plans.append({
            "type": bp["type"],
            "rest_time": bp["rest_time"],
            "exercises": filtered_exercises
        })
        
    return plans

def update_intensity_modifier(current_modifier: float, feedback: str) -> float:
    # If easy, increase intensity by 10%. If hard, decrease by 10%.
    if feedback.lower() == 'easy':
        return min(current_modifier + 0.1, 2.0) # Cap at 2.0x
    elif feedback.lower() == 'hard':
        return max(current_modifier - 0.1, 0.5) # Floor at 0.5x
    return current_modifier # Medium = no change
