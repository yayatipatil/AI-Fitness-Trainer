# AI Fitness Trainer

A modern, full-stack AI fitness application that uses rule-based logic, real-time pose tracking, and machine learning to provide adaptive workout recommendations and accurate form tracking.

## Features

- **Live AI Coach**: Real-time form tracking and rep counting using MediaPipe and your webcam. Includes joint-angle detection and form warnings!
- **Audio Web Speech Coach**: Hear real-time spoken feedback and rep milestones during your workouts so you don't have to stare at the screen.
- **Advanced Machine Learning Pipeline**: A Random Forest model trains on real user workout data from the database to predict an accurate Fitness Score based on BMI, workout frequency, streaks, and calories burned.
- **Weekly Workout Planner**: Plan your week visually. Receive dynamic "progressive overload" suggestions based on your past workout performance.
- **Smart Diet Recommendations**: Calculates BMR and suggests macros based on user goals, visualized with beautiful circular progress rings.
- **Interactive Video Guides**: Every workout card features a directly embedded YouTube video tutorial to ensure perfect form.
- **Advanced Analytics & Set Logging**: Dedicated charts page to visualize calorie burn history. Log precise reps/weights to automatically track and chart your estimated 1RM (One Rep Max) over time.
- **Equipment-Aware Workouts & Swapping**: Workouts adapt based on the equipment you own. Easily swap exercises dynamically on the fly based on gear and duration targets.
- **Challenges, Streaks & Badges**: Gamify your fitness journey. Complete built-in challenges to unlock visual badges, and maintain your consecutive daily streaks.
- **Robust Security**: Fully secured with bcrypt password hashing and JWT (JSON Web Token) based authentication.
- **Modern Dashboard**: Track progress and streaks with a premium, bento-grid, glassmorphic UI featuring smooth animations.

## Tech Stack

- **Backend**: Python, FastAPI, SQLite, Scikit-Learn, Joblib, Passlib (bcrypt), Python-JOSE (JWT)
- **Frontend**: Vanilla HTML, CSS, JavaScript (Fetch API, Chart.js, MediaPipe Pose Tracking, Lucide Icons)

## Project Structure

```text
AI Fitness Trainer/
├── backend/
│   ├── ml/
│   │   ├── features.py      # ML Feature extraction from DB
│   │   ├── model.py         # RandomForest training and prediction
│   │   └── fitness_model.pkl# Saved ML model (generated on run)
│   ├── utils/
│   │   ├── jwt.py           # JWT token generation and validation
│   │   └── security.py      # Bcrypt password hashing
│   ├── auth.py              # FastAPI auth dependencies
│   ├── database.py          # SQLite connection
│   ├── main.py              # FastAPI app and endpoints
│   ├── models.py            # SQLAlchemy models
│   ├── recommendation.py    # Rule-based logic (Diet & Workouts)
│   ├── seed.py              # Database seeder (generates 50 synthetic users)
│   └── requirements.txt     # Python dependencies
└── frontend/
    ├── index.html           # Landing page
    ├── dashboard.html       # User dashboard
    ├── planner.html         # Weekly workout planner
    ├── live_coach.html      # MediaPipe camera interface
    ├── ... (other HTML pages)
    ├── styles.css           # Premium dark-mode UI styles
    ├── script.js            # Global logic and API calls
    └── pose_tracker.js      # MediaPipe angle detection logic
```

## ML Model

The fitness score is generated using a **RandomForestRegressor**.
- **Features Used**: BMI, fitness goal (encoded), total workouts in the last 30 days, average reps per session, average calories burned per session, and current workout streak (days).
- **Prediction**: It predicts an overall Fitness Score from 0 to 100 based on consistency and effort.
- **Retraining**: You can trigger a model retrain at any time by making a `POST` request to `/ml/train`. The model automatically trains itself on startup if it detects no saved `.pkl` file.

## Exercises Supported

The Live AI Coach supports the following exercises using real-time joint angle tracking:

1. **Squats**: Tracks the angle between your hip, knee, and ankle. A rep is counted when the knee bends below 100° and extends past 160°. *Form Warning:* It checks the horizontal distance between your knees vs ankles to warn you if your "knees are caving in".
2. **Lunges**: Tracks the front knee angle. A rep is counted when the knee drops below 110° and returns past 160°.
3. **Plank**: Does not count reps. Instead, it tracks the angle of your shoulder, hip, and ankle to measure a straight line (between 160° and 200°). It provides a live hold timer in seconds, and throws form warnings if your "hips are too high" or "hips are dropping".
4. **Shoulder Press**: Tracks the angle between your shoulder, elbow, and wrist. A rep is counted when your elbows drop below 100° and extend past 160°.
5. **Push-ups**: Tracks your shoulder, elbow, and wrist angle to verify full extension and depth.

## Setup Instructions

### 1. Backend Setup

Open a terminal in the `backend` directory:

```bash
cd backend
```

Create a virtual environment (optional but recommended):
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Generate the synthetic ML dataset and seed the database with demo data:
```bash
python seed.py
```
*(This will output the demo student credentials)*

Run the FastAPI server:
```bash
python -m uvicorn main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

### 2. Frontend Setup

Since the frontend uses Vanilla HTML/CSS/JS with the `fetch` API, you can simply open the files in your browser, or use a local development server like Live Server (VS Code).

To use Python's built-in server, open a new terminal in the `frontend` directory:
```bash
cd frontend
python -m http.server 3000
```
Then navigate to `http://localhost:3000/index.html` in your browser.

## Using the Demo Data

When you run `python seed.py`, it will generate 50 synthetic users for ML training, plus a demo user:
- **Username**: `demo_student`
- **Password**: `password123`

You can use these credentials to log in and immediately see a populated dashboard with historical workout data, charts, and a pre-populated weekly planner!
