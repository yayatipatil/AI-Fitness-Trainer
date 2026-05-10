import os
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DB_PATH = os.path.join(os.path.dirname(__file__), "exercises_db.json")

def load_exercises():
    with open(DB_PATH, 'r') as f:
        return json.load(f)

def build_exercise_documents(exercises):
    docs = []
    for ex in exercises:
        # Create a rich text representation of the exercise for TF-IDF
        muscles = " ".join(ex.get("muscle_group", []))
        equip = " ".join(ex.get("equipment", []))
        level = ex.get("level", "")
        ex_type = ex.get("type", "")
        desc = ex.get("description", "")
        
        doc = f"{ex['name']} {muscles} {equip} {level} {ex_type} {desc}"
        docs.append(doc)
    return docs

def retrieve_exercises(goal: str, experience_level: str, user_equipment: list, top_k: int = 15) -> list:
    exercises = load_exercises()
    
    # 1. Hard filter by equipment
    filtered_exercises = []
    for ex in exercises:
        req_eq = ex.get("equipment", ["bodyweight"])
        can_do = False
        if "bodyweight" in req_eq:
            can_do = True
        else:
            for eq in req_eq:
                if eq in user_equipment or eq == "bodyweight":
                    can_do = True
                    break
        if can_do:
            filtered_exercises.append(ex)
            
    if not filtered_exercises:
        return []
        
    # 2. Build TF-IDF
    docs = build_exercise_documents(filtered_exercises)
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(docs)
    
    # 3. Create query based on user profile
    # Map goal to keywords
    goal_keywords = ""
    if goal.lower() == "weight loss":
        goal_keywords = "cardio high intensity full body"
    elif goal.lower() == "muscle gain":
        goal_keywords = "strength hypertrophy compound isolation chest back legs"
    else:
        goal_keywords = "strength cardio core stability"
        
    query = f"{goal_keywords} {experience_level}"
    query_vec = vectorizer.transform([query])
    
    # 4. Calculate similarities
    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
    
    # 5. Get top K indices
    top_indices = similarities.argsort()[-top_k:][::-1]
    
    results = []
    for idx in top_indices:
        ex = filtered_exercises[idx]
        results.append({
            "name": ex["name"],
            "description": ex["description"],
            "equipment": ex["equipment"]
        })
        
    return results

if __name__ == "__main__":
    # Test RAG
    print(retrieve_exercises("muscle gain", "intermediate", ["dumbbells", "bench"]))
