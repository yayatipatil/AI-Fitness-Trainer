import os
import requests
import json
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import models
from datetime import datetime

load_dotenv(override=True)

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

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

def fetch_edamam_weekly_plan(calories_target: float) -> dict:
    app_id = os.getenv("EDAMAM_APP_ID")
    app_key = os.getenv("EDAMAM_APP_KEY")
    if not app_id or not app_key:
        return None
        
    meals = {"Breakfast": 0.25, "Lunch": 0.35, "Dinner": 0.30, "Snack": 0.10}
    import random
    
    weekly_plan = {day: [] for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
    
    try:
        pool = {}
        headers = {"Edamam-Account-User": app_id}
        for meal_type, weight in meals.items():
            meal_cals = int(calories_target * weight)
            url = f"https://api.edamam.com/api/recipes/v2?type=public&app_id={app_id}&app_key={app_key}&mealType={meal_type}&calories={max(50, meal_cals-150)}-{meal_cals+150}&random=true"
            resp = requests.get(url, headers=headers, timeout=10)
            print(f"Edamam [{meal_type}] status: {resp.status_code}")
            if resp.status_code == 200:
                hits = resp.json().get("hits", [])
                pool[meal_type] = [h["recipe"] for h in hits] if hits else []
            else:
                pool[meal_type] = []
                
        if all(not p for p in pool.values()):
            return None
            
        for day in weekly_plan.keys():
            for meal_type, weight in meals.items():
                if pool.get(meal_type):
                    recipe = random.choice(pool[meal_type])
                    cals_per_serving = int(recipe.get("calories", calories_target * weight) / max(1, recipe.get("yield", 1)))
                    weekly_plan[day].append({
                        "type": meal_type,
                        "title": recipe.get("label", f"Healthy {meal_type}"),
                        "calories": cals_per_serving,
                        "image": recipe.get("image", ""),
                        "url": recipe.get("url", "")
                    })
                else:
                    weekly_plan[day].append({
                        "type": meal_type,
                        "title": f"Healthy {meal_type}",
                        "calories": int(calories_target * weight),
                        "image": "",
                        "url": ""
                    })
        return weekly_plan
    except Exception as e:
        print(f"Error calling Edamam: {e}")
    return None


def get_diet_recommendation(weight: float, height_cm: float, age: int, gender: str, goal: str, db: Session = None) -> dict:
    if db:
        cache_key = f"diet_{weight}_{height_cm}_{age}_{gender}_{goal}_{datetime.utcnow().date()}"
        cached = db.query(models.APICache).filter(models.APICache.cache_key == cache_key).first()
        if cached:
            return json.loads(cached.response_data)
            
    bmr = calculate_bmr(weight, height_cm, age, gender)
    tdee = bmr * 1.55 
    
    calories = tdee
    if goal.lower() == 'weight loss':
        calories = tdee - 500
    elif goal.lower() == 'muscle gain':
        calories = tdee + 300
    
    protein_multiplier = 1.6 if goal.lower() == 'muscle gain' else 1.2
    protein = weight * protein_multiplier
    
    # Try Edamam API First (Free & Accurate)
    edamam_plan = fetch_edamam_weekly_plan(calories)
    if edamam_plan:
        result = {
            "daily_calories": round(calories),
            "protein_grams": round(protein),
            "suggestion": "Focus on whole foods, lean proteins, and stay hydrated. Enjoy these verified Edamam recipes!",
            "weekly_plan": edamam_plan
        }
        if db:
            new_cache = models.APICache(cache_key=cache_key, response_data=json.dumps(result))
            db.add(new_cache)
            db.commit()
        return result
        
    # Fallback to Dynamic AI Diet Generation using Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if HAS_GENAI and gemini_key:
        try:
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-flash-latest')
            
            prompt = f"""
            You are an expert AI Nutritionist. 
            Create a 7-day weekly diet plan for a {gender}, age {age}, weight {weight}kg, height {height_cm}cm.
            Their goal is {goal}. Their daily caloric target is {round(calories)} kcal and protein target is {round(protein)}g.
            
            Return ONLY a JSON object.
            The object must contain two keys:
            - "suggestion": A short 2 sentence encouraging nutritional advice.
            - "weekly_plan": A dictionary with keys "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday".
              Each day must be an array of exactly 4 meals: Breakfast, Lunch, Dinner, Snack.
              Each meal must be an object with:
               - "type": "Breakfast" | "Lunch" | "Dinner" | "Snack"
               - "title": Name of the dish
               - "calories": Integer representing calories for this meal
               - "image": ""
               - "url": ""
               
            Make sure the total calories for the 4 meals each day add up to approximately {round(calories)}.
            Do not wrap the JSON in Markdown backticks or provide any other text.
            """
            
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            
            ai_data = json.loads(raw_text.strip())
            
            # Decorate with fallback images
            default_images = {
                "Breakfast": "https://images.unsplash.com/photo-1517673132405-a56a62b18caf?w=400&q=80",
                "Lunch": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&q=80",
                "Dinner": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400&q=80",
                "Snack": "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400&q=80"
            }
            
            for day, meals in ai_data.get("weekly_plan", {}).items():
                for meal in meals:
                    if not meal.get("image"):
                        meal["image"] = default_images.get(meal.get("type", "Snack"), default_images["Snack"])
            
            result = {
                "daily_calories": round(calories),
                "protein_grams": round(protein),
                "suggestion": ai_data.get("suggestion", "Focus on whole foods, lean proteins, and stay hydrated."),
                "weekly_plan": ai_data.get("weekly_plan", {})
            }
            if db:
                new_cache = models.APICache(cache_key=cache_key, response_data=json.dumps(result))
                db.add(new_cache)
                db.commit()
            return result
        except Exception as e:
            print(f"Error calling Gemini for diet generation: {e}")
            # Fall back to rule-based generation below
            
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

    result = {
        "daily_calories": round(calories),
        "protein_grams": round(protein),
        "suggestion": "Focus on whole foods, lean proteins, and stay hydrated. Your meals below are balanced to meet your daily caloric needs.",
        "weekly_plan": weekly_plan
    }
    if db:
        new_cache = models.APICache(cache_key=cache_key, response_data=json.dumps(result))
        db.add(new_cache)
        db.commit()
    return result


def get_workout_recommendation(goal: str, experience_level: str, intensity_modifier: float, duration_minutes: int = 30, user_equipment: list = None, db_exercises: dict = None, db: Session = None) -> list:
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
    
    if db:
        eq_hash = hash(frozenset(user_equipment))
        cache_key = f"workout_{goal}_{experience_level}_{intensity_modifier}_{duration_minutes}_{eq_hash}_{datetime.utcnow().date()}"
        cached = db.query(models.APICache).filter(models.APICache.cache_key == cache_key).first()
        if cached:
            return json.loads(cached.response_data)
            
    # Dynamic AI Workout Generation using Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if HAS_GENAI and gemini_key:
        try:
            from ml.rag import retrieve_exercises
            rag_context = retrieve_exercises(goal, experience_level, user_equipment if user_equipment else ["bodyweight"])
            rag_text = "\n".join([f"- {ex['name']} (Equipment: {', '.join(ex['equipment'])}): {ex['description']}" for ex in rag_context])
            
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-flash-latest')
            
            prompt = f"""
            You are an expert AI Fitness Trainer.
            Generate a personalized workout plan for a user with the following profile:
            - Goal: {goal}
            - Experience Level: {experience_level}
            - Intensity Modifier: {intensity_modifier} (1.0 is normal, higher is harder)
            - Duration: {duration_minutes} minutes
            - Available Equipment: {user_equipment if user_equipment else 'Bodyweight only'}
            
            Using ONLY the following verified exercises, create a workout plan. Do not invent any exercises not on this list.
            VERIFIED EXERCISES:
            {rag_text}
            
            Return ONLY a JSON array containing 3 workout routines. 
            Each routine must be an object with:
            - "type": A descriptive name for the routine (e.g. "Full Body Power")
            - "rest_time": The rest time as a string (e.g. "60 seconds")
            - "exercises": An array of objects, each with "name" (must exactly match a VERIFIED EXERCISE), "sets" (integer, usually around {adjusted_sets}), and "reps" (string or integer, e.g. "{adjusted_reps}" or "30 sec"). Limit to {ex_count} exercises per routine.
            
            Do not wrap the JSON in Markdown backticks or provide any other text.
            """
            
            response = model.generate_content(prompt)
            # Try to parse the response as JSON. Strip backticks if present.
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            
            plans = json.loads(raw_text.strip())
            if db:
                new_cache = models.APICache(cache_key=cache_key, response_data=json.dumps(plans))
                db.add(new_cache)
                db.commit()
            return plans
        except Exception as e:
            print(f"Error calling Gemini for workout generation: {e}")
            # Fall back to rule-based generation below
    
    plans = []
    
    try:
        from ml.seq2seq_model import predict_workout_sequence
        import random
        
        predicted_exercises = predict_workout_sequence(goal, experience_level, intensity_modifier, duration_minutes)
        
        routine_names = ["Primary Workout", "Secondary Workout", "Core & Cardio focus"]
        rest_times = ["60 seconds", "45 seconds", "30 seconds"]
        
        for i in range(3):
            filtered_exercises = []
            for ex_name in predicted_exercises:
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
                
            # Shuffle slightly for variety between the 3 routines
            random.shuffle(filtered_exercises)
            
            plans.append({
                "type": routine_names[i],
                "rest_time": rest_times[i],
                "exercises": filtered_exercises[:ex_count]
            })
            
    except Exception as e:
        print(f"Error calling Seq2Seq for workout generation: {e}")
        plans = [{
            "type": "Basic Bodyweight",
            "rest_time": "60 seconds",
            "exercises": [{"name": "Jumping Jacks", "sets": adjusted_sets, "reps": adjusted_reps}]
        }]
        
    if db:
        new_cache = models.APICache(cache_key=cache_key, response_data=json.dumps(plans))
        db.add(new_cache)
        db.commit()
        
    return plans

def update_intensity_modifier(current_modifier: float, feedback: str) -> float:
    # If easy, increase intensity by 10%. If hard, decrease by 10%.
    if feedback.lower() == 'easy':
        return min(current_modifier + 0.1, 2.0) # Cap at 2.0x
    elif feedback.lower() == 'hard':
        return max(current_modifier - 0.1, 0.5) # Floor at 0.5x
    return current_modifier # Medium = no change
