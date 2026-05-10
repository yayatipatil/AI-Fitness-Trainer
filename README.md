# AI Fitness Trainer

A modern, full-stack AI fitness application that combines a multi-layered neural network recommendation engine, real-time pose tracking, Retrieval-Augmented Generation (RAG), and live API integrations to provide truly adaptive, personalised workout and diet plans.

## Features

- **Seq2Seq Neural Network Workouts**: A custom PyTorch Encoder-Decoder (Seq2Seq) model generates personalised workout sequences as the intelligent fallback when the Gemini API is unavailable. Trained on a categorised exercise dataset.
- **RAG-Powered AI Recommendations**: A TF-IDF Retrieval-Augmented Generation (RAG) engine pre-selects the most relevant exercises from a curated database before passing them to Gemini, completely eliminating AI hallucinations.
- **Gemini AI Integration**: Uses the Google Gemini Flash API to generate contextually rich, highly personalised workout and diet plans with full user profile context.
- **Edamam Recipe API**: Diet plans are sourced from the real Edamam Recipe database, providing accurate macros, genuine recipe names, and real food images.
- **Database API Caching**: All Gemini and Edamam API responses are cached in SQLite (keyed by user profile + date). This prevents repeated API calls on page reloads, drastically reducing token usage.
- **Live AI Coach**: Real-time form tracking and rep counting using MediaPipe and your webcam. Includes joint-angle detection and form warnings.
- **Audio Web Speech Coach**: Hear real-time spoken feedback and rep milestones during your workouts so you don't have to stare at the screen.
- **Advanced ML Fitness Score**: A Random Forest model trains on real user workout data to predict an accurate Fitness Score based on BMI, workout frequency, streaks, and calories burned.
- **Weekly Workout Planner**: Plan your week visually. Receive dynamic "progressive overload" suggestions based on your past workout performance.
- **Interactive Video Guides**: Every workout card features a directly embedded YouTube video tutorial to ensure perfect form.
- **Advanced Analytics & Set Logging**: Dedicated charts page to visualise calorie burn history. Log precise reps/weights to automatically track and chart your estimated 1RM (One Rep Max) over time.
- **Equipment-Aware Workouts**: Workouts adapt based on the equipment you own. The RAG engine and Seq2Seq model both filter by available equipment.
- **Challenges, Streaks & Badges**: Gamify your fitness journey. Complete built-in challenges to unlock visual badges and maintain consecutive daily streaks.
- **Robust Security**: Fully secured with bcrypt password hashing and JWT (JSON Web Token) based authentication.
- **Modern Dashboard**: Track progress and streaks with a premium, bento-grid, glassmorphic UI featuring smooth animations.

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend API** | Python, FastAPI, Uvicorn |
| **Database** | SQLite, SQLAlchemy |
| **AI / LLM** | Google Gemini Flash API |
| **Diet Recipes** | Edamam Recipe Search API v2 |
| **Neural Network** | PyTorch (custom Seq2Seq Encoder-Decoder) |
| **RAG Engine** | scikit-learn (TF-IDF + Cosine Similarity) |
| **Fitness Score ML** | scikit-learn (RandomForestRegressor) |
| **Auth** | Passlib (bcrypt), Python-JOSE (JWT) |
| **Frontend** | Vanilla HTML, CSS, JavaScript |
| **UI Libraries** | Chart.js, MediaPipe Pose, Lucide Icons |

## AI Recommendation Pipeline

The system uses a layered, fault-tolerant approach so the app always returns a useful plan:

```
Request → DB Cache?  ──Yes──► Return instantly (no API call)
                │
               No
                │
                ▼
         Edamam API (diet) / RAG + Gemini (workout)
                │
        API fails or rate limited?
                │
               Yes
                ▼
         PyTorch Seq2Seq model (local fallback)
                │
                ▼
         Save result to DB cache → Return to user
```

## Project Structure

```text
AI Fitness Trainer/
├── backend/
│   ├── ml/
│   │   ├── exercises_db.json    # Curated exercise dataset (RAG knowledge base)
│   │   ├── rag.py               # TF-IDF retrieval engine
│   │   ├── seq2seq_model.py     # PyTorch Seq2Seq neural network
│   │   ├── seq2seq_model.pt     # Saved model weights (auto-generated)
│   │   ├── seq2seq_vocab.json   # Exercise vocabulary (auto-generated)
│   │   ├── features.py          # ML Feature extraction from DB
│   │   ├── model.py             # RandomForest training and prediction
│   │   └── fitness_model.pkl    # Saved RF model (auto-generated)
│   ├── utils/
│   │   ├── jwt.py               # JWT token generation and validation
│   │   └── security.py          # Bcrypt password hashing
│   ├── auth.py                  # FastAPI auth dependencies
│   ├── database.py              # SQLite connection
│   ├── main.py                  # FastAPI app and all endpoints
│   ├── models.py                # SQLAlchemy models (includes APICache)
│   ├── recommendation.py        # Multi-layered recommendation engine
│   ├── seed.py                  # Database seeder (generates 50 synthetic users)
│   └── requirements.txt         # Python dependencies
└── frontend/
    ├── index.html               # Landing page
    ├── dashboard.html           # User dashboard
    ├── planner.html             # Weekly workout planner
    ├── live_coach.html          # MediaPipe camera interface
    ├── workouts.html            # Workout recommendations
    ├── diet.html                # Diet plan & food logging
    ├── profile.html             # User profile management
    ├── analytics.html           # Charts and 1RM tracking
    ├── styles.css               # Premium dark-mode UI styles
    ├── script.js                # Global logic and API calls
    └── pose_tracker.js          # MediaPipe angle detection logic
```

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

Create a `.env` file in the `backend/` folder with your API keys:
```env
GEMINI_API_KEY=your_google_gemini_api_key
EDAMAM_APP_ID=your_edamam_app_id
EDAMAM_APP_KEY=your_edamam_app_key
```

> **Note:** The app works without Edamam keys (falls back to Gemini for diet), and works without Gemini (falls back to the local PyTorch model for workouts). Only `GEMINI_API_KEY` is required for full AI features.

Seed the database with demo data:
```bash
python seed.py
```

Run the FastAPI server:
```bash
python -m uvicorn main:app --reload
```
The API will be available at `http://127.0.0.1:8000`. Swagger docs at `http://127.0.0.1:8000/docs`.

### 2. Frontend Setup

Open a new terminal in the `frontend` directory and serve it:
```bash
cd frontend
python -m http.server 3000
```
Then navigate to `http://localhost:3000/index.html` in your browser.

## Getting API Keys

### Google Gemini (Free)
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click **"Get API key"** → **"Create API key"**
4. Copy and paste into your `.env` as `GEMINI_API_KEY`

### Edamam Recipe API (Free Developer Tier)
1. Go to [Edamam Developer Portal](https://developer.edamam.com/edamam-recipe-api)
2. Sign up for a free account
3. Create an application under the **Recipe Search API** (free tier)
4. Copy the **Application ID** and **Application Key** into your `.env`

## Using the Demo Data

When you run `python seed.py`, it generates 50 synthetic users for ML training, plus a demo user:
- **Username**: `demo_student`
- **Password**: `password123`

Log in with these credentials to immediately see a populated dashboard with historical workout data, charts, and a pre-populated weekly planner!

## Exercises Supported (Live AI Coach)

The Live AI Coach supports the following exercises using real-time joint angle tracking via MediaPipe:

1. **Squats** — Tracks knee angle; warns if knees cave in.
2. **Lunges** — Tracks front knee angle for depth and form.
3. **Plank** — Timed hold with live alignment tracking; warns for hip drop or hip pike.
4. **Shoulder Press** — Tracks elbow angle for full extension.
5. **Push-ups** — Tracks shoulder-elbow-wrist angle for depth and lockout.
