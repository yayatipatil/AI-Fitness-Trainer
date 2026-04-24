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

def get_diet_recommendation(weight: float, height_cm: float, age: int, gender: str, goal: str) -> dict:
    bmr = calculate_bmr(weight, height_cm, age, gender)
    
    # Activity multiplier (assuming moderate activity for general fitness app)
    tdee = bmr * 1.55 
    
    calories = tdee
    if goal.lower() == 'weight loss':
        calories = tdee - 500
    elif goal.lower() == 'muscle gain':
        calories = tdee + 300
    
    # Protein intake (g per kg of body weight)
    protein_multiplier = 1.6 if goal.lower() == 'muscle gain' else 1.2
    protein = weight * protein_multiplier
    
    return {
        "daily_calories": round(calories),
        "protein_grams": round(protein),
        "suggestion": "Focus on whole foods, lean proteins, and stay hydrated."
    }

def get_workout_recommendation(goal: str, experience_level: str, intensity_modifier: float) -> dict:
    # Base sets and reps
    base_sets = 3
    base_reps = 10
    
    if experience_level.lower() == 'beginner':
        base_sets = 2
        base_reps = 12
    elif experience_level.lower() == 'advanced':
        base_sets = 4
        base_reps = 8
        
    # Apply adaptive intensity
    adjusted_sets = max(1, int(base_sets * intensity_modifier))
    adjusted_reps = max(5, int(base_reps * intensity_modifier))
    
    plan = {
        "rest_time": "60 seconds",
        "exercises": []
    }
    
    if goal.lower() == 'weight loss':
        plan["type"] = "High Intensity Interval Training (HIIT) & Cardio"
        plan["exercises"] = [
            {"name": "Jumping Jacks", "sets": adjusted_sets, "reps": adjusted_reps + 5},
            {"name": "Burpees", "sets": adjusted_sets, "reps": max(5, adjusted_reps - 2)},
            {"name": "Mountain Climbers", "sets": adjusted_sets, "reps": adjusted_reps + 5},
            {"name": "Bodyweight Squats", "sets": adjusted_sets, "reps": adjusted_reps}
        ]
    elif goal.lower() == 'muscle gain':
        plan["type"] = "Hypertrophy Strength Training"
        plan["exercises"] = [
            {"name": "Push-ups", "sets": adjusted_sets, "reps": adjusted_reps},
            {"name": "Pull-ups / Inverted Rows", "sets": adjusted_sets, "reps": max(5, adjusted_reps - 2)},
            {"name": "Lunges", "sets": adjusted_sets, "reps": adjusted_reps},
            {"name": "Plank", "sets": adjusted_sets, "reps": f"{int(30 * intensity_modifier)} sec"}
        ]
    else: # Maintenance
        plan["type"] = "Balanced Functional Training"
        plan["exercises"] = [
            {"name": "Squats", "sets": adjusted_sets, "reps": adjusted_reps},
            {"name": "Push-ups", "sets": adjusted_sets, "reps": adjusted_reps},
            {"name": "Sit-ups", "sets": adjusted_sets, "reps": adjusted_reps},
            {"name": "Jogging", "sets": 1, "reps": f"{int(15 * intensity_modifier)} mins"}
        ]
        
    return plan

def update_intensity_modifier(current_modifier: float, feedback: str) -> float:
    # If easy, increase intensity by 10%. If hard, decrease by 10%.
    if feedback.lower() == 'easy':
        return min(current_modifier + 0.1, 2.0) # Cap at 2.0x
    elif feedback.lower() == 'hard':
        return max(current_modifier - 0.1, 0.5) # Floor at 0.5x
    return current_modifier # Medium = no change
