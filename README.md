# AI-Powered Adaptive Fitness Trainer

A modern, full-stack AI fitness application that uses rule-based logic and machine learning to provide adaptive workout and diet recommendations.

## Features
- **Live AI Coach**: Real-time form tracking and rep counting using MediaPipe and your webcam.
- **Adaptive Workouts**: Adjusts intensity based on user feedback.
- **Smart Diet Recommendations**: Calculates BMR and suggests macros based on user goals, visualized with beautiful circular progress rings.
- **ML Fitness Score**: A Scikit-learn Random Forest model predicts your overall fitness score.
- **Advanced Analytics**: Dedicated charts page to visualize calorie burn history and fitness score breakdowns.
- **Modern Dashboard**: Track progress and streaks with a premium, bento-grid, glassmorphic UI featuring smooth animations.

## Tech Stack
- **Backend**: Python, FastAPI, SQLite, Scikit-Learn
- **Frontend**: Vanilla HTML, CSS, JavaScript (Fetch API, Chart.js, MediaPipe Pose Tracking, Lucide Icons)

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
uvicorn main:app --reload
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
When you run `python seed.py`, it will generate a demo user:
- **Username**: `demo_student`
- **Password**: `password123`

You can use these credentials to log in and immediately see a populated dashboard with historical workout data and charts!
