const videoElement = document.getElementById('input_video');
const canvasElement = document.getElementById('output_canvas');
const canvasCtx = canvasElement.getContext('2d');

const repCountEl = document.getElementById('rep-count');
const statusTextEl = document.getElementById('status-text');
const feedbackEl = document.getElementById('feedback');
const exerciseTypeEl = document.getElementById('exercise-type');

let camera = null;
let pose = null;

// State machine for counting reps
let repCount = 0;
let stage = "up"; // "up" or "down"
let isTracking = false;

// Plank specifics
let plankStartTime = null;
let plankTime = 0;

function calculateAngle(a, b, c) {
    // a, b, c are landmarks with x, y properties
    const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
    let angle = Math.abs((radians * 180.0) / Math.PI);
    
    if (angle > 180.0) {
        angle = 360 - angle;
    }
    return angle;
}

function showFeedback(text, colorClass = "var(--primary)") {
    feedbackEl.textContent = text;
    feedbackEl.style.display = "block";
    feedbackEl.style.background = colorClass === "red" ? "rgba(220, 38, 38, 0.9)" : `rgba(59, 130, 246, 0.9)`;
    
    // Audio feedback
    if (window.audioCoach) {
        window.audioCoach.speak(text, colorClass === "red");
    }
    
    setTimeout(() => {
        feedbackEl.style.display = "none";
    }, 1500);
}

// Reset state when changing exercise
exerciseTypeEl.addEventListener('change', () => {
    repCount = 0;
    stage = "up";
    plankStartTime = null;
    plankTime = 0;
    repCountEl.textContent = "0";
    if (exerciseTypeEl.value === 'plank') {
        document.querySelector('.hud-label').textContent = "Hold Time (s)";
    } else {
        document.querySelector('.hud-label').textContent = "Reps Completed";
    }
});

function onResults(results) {
    if (!canvasElement.width || canvasElement.width !== videoElement.videoWidth) {
        canvasElement.width = videoElement.videoWidth;
        canvasElement.height = videoElement.videoHeight;
    }

    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    
    if (results.poseLandmarks) {
        drawConnectors(canvasCtx, results.poseLandmarks, POSE_CONNECTIONS, {color: '#00FF00', lineWidth: 4});
        drawLandmarks(canvasCtx, results.poseLandmarks, {color: '#FF0000', lineWidth: 2});

        const landmarks = results.poseLandmarks;
        const exercise = exerciseTypeEl.value;

        if (exercise === 'squat') {
            const hip = landmarks[23];
            const knee = landmarks[25];
            const ankle = landmarks[27];
            
            const right_knee = landmarks[26];
            const right_ankle = landmarks[28];
            
            if (hip.visibility > 0.5 && knee.visibility > 0.5 && ankle.visibility > 0.5) {
                const angle = calculateAngle(hip, knee, ankle);
                
                // Form Check: Knees caving in
                if (right_knee.visibility > 0.5 && right_ankle.visibility > 0.5) {
                    const knee_dist = Math.abs(knee.x - right_knee.x);
                    const ankle_dist = Math.abs(ankle.x - right_ankle.x);
                    if (knee_dist < ankle_dist * 0.6) {
                        showFeedback("WARNING: Knees caving in!", "red");
                    }
                }
                
                if (angle > 160) {
                    if (stage === "down") {
                        repCount++;
                        repCountEl.textContent = repCount;
                        showFeedback("Good Rep!");
                        if (repCount % 5 === 0) {
                            setTimeout(() => {
                                if (window.audioCoach) window.audioCoach.speak(`You have done ${repCount} reps. Keep it up!`, true);
                            }, 500);
                        }
                    }
                    stage = "up";
                    statusTextEl.textContent = `Status: Standing (${Math.round(angle)}°)`;
                }
                
                if (angle < 100 && stage === "up") {
                    stage = "down";
                    statusTextEl.textContent = `Status: Squatting (${Math.round(angle)}°)`;
                }
            } else {
                statusTextEl.textContent = "Status: Legs not fully visible";
            }
            
        } else if (exercise === 'lunge') {
            const hip = landmarks[23];
            const knee = landmarks[25];
            const ankle = landmarks[27];
            
            if (hip.visibility > 0.5 && knee.visibility > 0.5 && ankle.visibility > 0.5) {
                const angle = calculateAngle(hip, knee, ankle);
                
                if (angle > 160) {
                    if (stage === "down") {
                        repCount++;
                        repCountEl.textContent = repCount;
                        showFeedback("Good Lunge!");
                    }
                    stage = "up";
                    statusTextEl.textContent = `Status: Standing (${Math.round(angle)}°)`;
                }
                
                if (angle < 110 && stage === "up") {
                    stage = "down";
                    statusTextEl.textContent = `Status: Lunging (${Math.round(angle)}°)`;
                }
            } else {
                statusTextEl.textContent = "Status: Legs not fully visible";
            }
            
        } else if (exercise === 'plank') {
            const shoulder = landmarks[11];
            const hip = landmarks[23];
            const ankle = landmarks[27];
            
            if (shoulder.visibility > 0.5 && hip.visibility > 0.5 && ankle.visibility > 0.5) {
                const angle = calculateAngle(shoulder, hip, ankle);
                
                if (angle >= 160 && angle <= 200) {
                    if (!plankStartTime) {
                        plankStartTime = new Date().getTime();
                    }
                    plankTime = Math.floor((new Date().getTime() - plankStartTime) / 1000);
                    repCount = plankTime;
                    repCountEl.textContent = repCount;
                    statusTextEl.textContent = `Status: Good form (${Math.round(angle)}°)`;
                } else {
                    plankStartTime = null; // reset timer if form breaks badly
                    if (angle < 160) {
                        showFeedback("WARNING: Lower your hips!", "red");
                        statusTextEl.textContent = "Status: Hips too high";
                    } else if (angle > 200) {
                        showFeedback("WARNING: Raise your hips!", "red");
                        statusTextEl.textContent = "Status: Hips dropping";
                    }
                }
            } else {
                statusTextEl.textContent = "Status: Body not fully visible";
                plankStartTime = null;
            }
            
        } else if (exercise === 'shoulder_press') {
            const shoulder = landmarks[11];
            const elbow = landmarks[13];
            const wrist = landmarks[15];
            
            if (shoulder.visibility > 0.5 && elbow.visibility > 0.5 && wrist.visibility > 0.5) {
                const angle = calculateAngle(shoulder, elbow, wrist);
                
                if (angle > 160) {
                    if (stage === "down") {
                        repCount++;
                        repCountEl.textContent = repCount;
                        showFeedback("Good Press!");
                    }
                    stage = "up";
                    statusTextEl.textContent = `Status: Arms Extended (${Math.round(angle)}°)`;
                }
                
                if (angle < 100 && stage === "up") {
                    stage = "down";
                    statusTextEl.textContent = `Status: Arms Down (${Math.round(angle)}°)`;
                }
            } else {
                statusTextEl.textContent = "Status: Arms not fully visible";
            }
            
        } else if (exercise === 'pushup') {
            const shoulder = landmarks[11];
            const elbow = landmarks[13];
            const wrist = landmarks[15];
            
            if (shoulder.visibility > 0.5 && elbow.visibility > 0.5 && wrist.visibility > 0.5) {
                const angle = calculateAngle(shoulder, elbow, wrist);
                if (angle > 160) {
                    if (stage === "down") {
                        repCount++;
                        repCountEl.textContent = repCount;
                        showFeedback("Good Rep!");
                        if (repCount % 5 === 0) {
                            setTimeout(() => {
                                if (window.audioCoach) window.audioCoach.speak(`You have done ${repCount} reps. Keep it up!`, true);
                            }, 500);
                        }
                    }
                    stage = "up";
                    statusTextEl.textContent = `Status: Up (${Math.round(angle)}°)`;
                }
                if (angle < 90 && stage === "up") {
                    stage = "down";
                    statusTextEl.textContent = `Status: Down (${Math.round(angle)}°)`;
                }
            }
        }
    }
    
    canvasCtx.restore();
}

function startCamera() {
    if (isTracking) return;
    
    document.getElementById('btn-start').style.display = "none";
    document.getElementById('btn-finish').style.display = "block";
    
    pose = new Pose({locateFile: (file) => {
        return `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`;
    }});
    
    pose.setOptions({
        modelComplexity: 1,
        smoothLandmarks: true,
        enableSegmentation: false,
        smoothSegmentation: false,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
    });
    
    pose.onResults(onResults);
    
    camera = new Camera(videoElement, {
        onFrame: async () => {
            await pose.send({image: videoElement});
        },
        width: 1280,
        height: 720
    });
    
    camera.start().then(() => {
        isTracking = true;
        statusTextEl.textContent = "Status: Tracking Active";
    }).catch(err => {
        alert("Could not start camera: " + err);
        document.getElementById('btn-start').style.display = "block";
        document.getElementById('btn-finish').style.display = "none";
    });
}

async function finishWorkout() {
    if (repCount === 0) {
        alert("You haven't completed any tracked movement yet!");
        return;
    }
    
    if (camera) {
        camera.stop();
    }
    
    const exercise = exerciseTypeEl.value;
    const calories = repCount * 0.5;
    
    try {
        await apiCall('/log-live-workout', 'POST', {
            workout_type: `Live AI ${exercise.charAt(0).toUpperCase() + exercise.slice(1)} Session`,
            difficulty_feedback: 'Medium',
            calories_burned: calories,
            reps: repCount
        });
        
        localStorage.setItem('lastLiveSession', JSON.stringify({
            type: exercise.charAt(0).toUpperCase() + exercise.slice(1),
            reps: repCount
        }));

        alert(`Workout Logged! ${repCount} ${exercise === 'plank' ? 'seconds' : 'reps'} successfully tracked and saved to your profile.`);
        window.location.href = 'dashboard.html';
        
    } catch (err) {
        alert('Error logging workout: ' + err.message);
    }
}
