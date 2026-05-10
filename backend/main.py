from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import List
import json
import os

import models, database, auth, recommendation
from ml import model as ml_model, features as ml_features
from utils import security, jwt as jwt_utils
from dotenv import load_dotenv

load_dotenv(override=True)

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
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    return current_user

@app.put("/auth/account", response_model=models.UserResponse)
def update_account(account_update: models.AccountUpdate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    # Check if username exists and is not the current user
    if account_update.username != current_user.username:
        db_user = db.query(models.User).filter(models.User.username == account_update.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Username already taken")
    
    # Check if email exists and is not the current user
    if account_update.email != current_user.email:
        db_email = db.query(models.User).filter(models.User.email == account_update.email).first()
        if db_email:
            raise HTTPException(status_code=400, detail="Email already taken")
            
    current_user.username = account_update.username
    current_user.email = account_update.email
    db.commit()
    db.refresh(current_user)
    return current_user

@app.put("/auth/password")
def update_password(password_update: models.PasswordUpdate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if not security.verify_password(password_update.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
        
    current_user.hashed_password = security.hash_password(password_update.new_password)
    db.commit()
    return {"detail": "Password updated successfully"}

@app.delete("/auth/account")
def delete_account(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    user_id = current_user.id
    
    # Hard Delete: Wipe all associated records manually to ensure no foreign key constraint failures
    db.query(models.WorkoutLog).filter(models.WorkoutLog.user_id == user_id).delete()
    db.query(models.WorkoutPlan).filter(models.WorkoutPlan.user_id == user_id).delete()
    db.query(models.UserEquipment).filter(models.UserEquipment.user_id == user_id).delete()
    db.query(models.SetLog).filter(models.SetLog.user_id == user_id).delete()
    db.query(models.UserChallenge).filter(models.UserChallenge.user_id == user_id).delete()
    db.query(models.Badge).filter(models.Badge.user_id == user_id).delete()
    
    # Finally, delete the user
    db.delete(current_user)
    db.commit()
    
    return {"detail": "Account deleted successfully"}

@app.get("/recommend-workout")
def get_workout(duration_minutes: int = 30, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if not current_user.fitness_goal or not current_user.experience_level:
        raise HTTPException(status_code=400, detail="Profile required for recommendations")
    
    eq_record = db.query(models.UserEquipment).filter(models.UserEquipment.user_id == current_user.id).first()
    user_eq = json.loads(eq_record.equipment) if eq_record else []

    all_ex = db.query(models.Exercise).all()
    db_exercises = {ex.name: json.loads(ex.equipment) for ex in all_ex}

    workout_plan = recommendation.get_workout_recommendation(
        goal=current_user.fitness_goal if current_user.fitness_goal else "Maintenance",
        experience_level=current_user.experience_level if current_user.experience_level else "Beginner",
        intensity_modifier=current_user.intensity_modifier,
        duration_minutes=duration_minutes,
        user_equipment=user_eq,
        db_exercises=db_exercises,
        db=db
    )
    
    diet_plan = recommendation.get_diet_recommendation(
        weight=current_user.weight_kg if current_user.weight_kg else 70,
        height_cm=current_user.height_cm if current_user.height_cm else 170,
        age=current_user.age if current_user.age else 25,
        gender=current_user.gender if current_user.gender else "Male",
        goal=current_user.fitness_goal if current_user.fitness_goal else "Maintenance",
        db=db
    )
    
    return {
        "workout": workout_plan,
        "diet": diet_plan
    }

def check_and_update_challenges(user: models.User, log: models.WorkoutLogCreate, db: Session):
    # Get user challenges
    user_challenges = db.query(models.UserChallenge).filter(
        models.UserChallenge.user_id == user.id,
        models.UserChallenge.completed == False
    ).all()
    
    from datetime import datetime
    
    for uc in user_challenges:
        challenge = db.query(models.Challenge).filter(models.Challenge.id == uc.challenge_id).first()
        if not challenge: continue
        
        if challenge.metric == "workouts":
            uc.progress += 1
        elif challenge.metric == "calories":
            uc.progress += log.calories_burned
        # Note: Streak is harder to track incrementally here, but let's assume we do it on load or simplified.
        # For this demo, we'll just track workouts and calories
        
        if uc.progress >= challenge.target_value:
            uc.completed = True
            uc.completed_at = datetime.utcnow()
            uc.progress = challenge.target_value
            
            # Award badge
            if challenge.badge_url:
                badge = models.Badge(
                    user_id=user.id,
                    name=challenge.title,
                    icon_url=challenge.badge_url
                )
                db.add(badge)

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
    
    check_and_update_challenges(current_user, log, db)
        
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
    
    check_and_update_challenges(current_user, log, db)
        
    db.commit()
    db.refresh(new_log)
    return new_log

@app.get("/challenges", response_model=List[models.UserChallengeResponse])
def get_challenges(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    all_challenges = db.query(models.Challenge).all()
    user_challenges = db.query(models.UserChallenge).filter(models.UserChallenge.user_id == current_user.id).all()
    
    # create dict for fast lookup
    uc_dict = {uc.challenge_id: uc for uc in user_challenges}
    
    result = []
    for c in all_challenges:
        uc = uc_dict.get(c.id)
        if uc:
            result.append({
                "id": uc.id,
                "challenge": c,
                "progress": uc.progress,
                "completed": uc.completed,
                "completed_at": uc.completed_at
            })
        else:
            # Create the tracking record if it doesn't exist
            new_uc = models.UserChallenge(user_id=current_user.id, challenge_id=c.id)
            db.add(new_uc)
            db.commit()
            db.refresh(new_uc)
            result.append({
                "id": new_uc.id,
                "challenge": c,
                "progress": new_uc.progress,
                "completed": new_uc.completed,
                "completed_at": new_uc.completed_at
            })
            
    return result

@app.get("/badges", response_model=List[models.BadgeResponse])
def get_badges(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    badges = db.query(models.Badge).filter(models.Badge.user_id == current_user.id).all()
    return badges


@app.post("/set-logs", response_model=models.SetLogResponse)
def log_set(set_log: models.SetLogCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    db_set = models.SetLog(**set_log.dict(), user_id=current_user.id)
    db.add(db_set)
    db.commit()
    db.refresh(db_set)
    
    # Return with calculated 1RM
    resp = db_set.__dict__.copy()
    resp["estimated_1rm"] = db_set.calculate_1rm()
    return resp

@app.get("/set-logs/1rm/{exercise_name}")
def get_1rm_history(exercise_name: str, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    logs = db.query(models.SetLog).filter(
        models.SetLog.user_id == current_user.id,
        models.SetLog.exercise_name == exercise_name
    ).order_by(models.SetLog.date.asc()).all()
    
    # We want to group by date or just return points
    # Let's return raw points for the chart
    history = []
    for log in logs:
        history.append({
            "date": log.date.strftime("%Y-%m-%d"),
            "estimated_1rm": log.calculate_1rm(),
            "weight": log.weight_kg,
            "reps": log.reps
        })
        
    return {"exercise": exercise_name, "history": history}

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

@app.get("/exercises", response_model=List[models.ExerciseResponse])
def get_exercises(db: Session = Depends(database.get_db)):
    return db.query(models.Exercise).all()

@app.get("/exercises/{name}", response_model=models.ExerciseResponse)
def get_exercise_by_name(name: str, db: Session = Depends(database.get_db)):
    exercise = db.query(models.Exercise).filter(models.Exercise.name == name).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return exercise

@app.get("/user/equipment", response_model=models.UserEquipmentResponse)
def get_user_equipment(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    equipment = db.query(models.UserEquipment).filter(models.UserEquipment.user_id == current_user.id).first()
    if not equipment:
        return {"user_id": current_user.id, "equipment": []}
    return {"user_id": equipment.user_id, "equipment": json.loads(equipment.equipment)}

@app.put("/user/equipment", response_model=models.UserEquipmentResponse)
def update_user_equipment(update_data: models.UserEquipmentUpdate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    equipment = db.query(models.UserEquipment).filter(models.UserEquipment.user_id == current_user.id).first()
    if not equipment:
        equipment = models.UserEquipment(user_id=current_user.id, equipment=json.dumps(update_data.equipment))
        db.add(equipment)
    else:
        equipment.equipment = json.dumps(update_data.equipment)
    db.commit()
    db.refresh(equipment)
    return {"user_id": equipment.user_id, "equipment": json.loads(equipment.equipment)}

@app.get("/exercises/swap")
def get_exercise_swap(name: str, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    target_ex = db.query(models.Exercise).filter(models.Exercise.name == name).first()
    if not target_ex:
        raise HTTPException(status_code=404, detail="Exercise not found")
        
    user_eq_record = db.query(models.UserEquipment).filter(models.UserEquipment.user_id == current_user.id).first()
    user_eq = json.loads(user_eq_record.equipment) if user_eq_record else []
    
    # Simple logic: Same category, not same exercise
    candidates = db.query(models.Exercise).filter(
        models.Exercise.category == target_ex.category,
        models.Exercise.name != target_ex.name
    ).all()
    
    # Score candidates: prioritize if their equipment matches user's equipment or is bodyweight
    scored = []
    for c in candidates:
        c_eq = json.loads(c.equipment)
        score = 0
        if "bodyweight" in c_eq:
            score += 1
        for eq in c_eq:
            if eq in user_eq:
                score += 2
        scored.append((score, c))
    
    if not scored:
        raise HTTPException(status_code=404, detail="No swap found")
        
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


@app.get("/dashboard-data")
def get_dashboard_data(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    logs = db.query(models.WorkoutLog).filter(models.WorkoutLog.user_id == current_user.id).order_by(models.WorkoutLog.date.desc()).all()
    
    # Aggregate data for charts
    dates = [log.date.strftime("%Y-%m-%d") for log in reversed(logs[:7])] # Last 7 logs
    calories = [log.calories_burned for log in reversed(logs[:7])]
    
    # Calculate streak (consecutive days)
    streak = 0
    if logs:
        from datetime import datetime
        
        current_date = datetime.utcnow().date()
        last_log_date = logs[0].date.date()
        
        if (current_date - last_log_date).days <= 1:
            streak = 1
            for i in range(1, len(logs)):
                diff = (logs[i-1].date.date() - logs[i].date.date()).days
                if diff == 1:
                    streak += 1
                elif diff == 0:
                    continue # same day
                else:
                    break
    
    return {
        "dates": dates,
        "calories": calories,
        "streak": streak
    }

@app.post("/log-diet-nlp", response_model=models.DietLogResponse)
def log_diet_nlp(text_input: dict, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    text = text_input.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Text input is required")
        
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured")
        
    import google.generativeai as genai
    try:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        
        prompt = f"""
        Extract the food items and their estimated nutritional macros from the following text: "{text}"
        Return ONLY a JSON object with the following keys:
        - "food_name": A short summary string of the food (e.g. "Oatmeal and 3 eggs")
        - "calories": total estimated calories (number)
        - "protein": total estimated protein in grams (number)
        - "carbs": total estimated carbohydrates in grams (number)
        - "fat": total estimated fat in grams (number)
        
        Do not wrap the response in markdown backticks or include any other text.
        """
        
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        import json
        data = json.loads(raw_text.strip())
        
        new_log = models.DietLog(
            user_id=current_user.id,
            food_name=data.get("food_name", "Unknown Food"),
            calories=float(data.get("calories", 0)),
            protein=float(data.get("protein", 0)),
            carbs=float(data.get("carbs", 0)),
            fat=float(data.get("fat", 0))
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return new_log
    except Exception as e:
        print(f"Error calling Gemini for NLP diet logging: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse diet log using AI")

@app.get("/diet-logs", response_model=List[models.DietLogResponse])
def get_diet_logs(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    from datetime import datetime
    today = datetime.utcnow().date()
    # Simple filter by day (assuming UTC)
    logs = db.query(models.DietLog).filter(models.DietLog.user_id == current_user.id).all()
    # We filter in Python to avoid complex SQLAlchemy date cast which differs by dialect
    today_logs = [log for log in logs if log.date.date() == today]
    return today_logs
