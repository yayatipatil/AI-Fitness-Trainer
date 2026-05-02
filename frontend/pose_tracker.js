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
    feedbackEl.style.background = `rgba(${colorClass}, 0.8)`; // pseudo color handling
    
    setTimeout(() => {
        feedbackEl.style.display = "none";
    }, 1500);
}

function onResults(results) {
    if (!canvasElement.width || canvasElement.width !== videoElement.videoWidth) {
        canvasElement.width = videoElement.videoWidth;
        canvasElement.height = videoElement.videoHeight;
    }

    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    
    // Do not draw original video, let the <video> element show through
    // canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);

    if (results.poseLandmarks) {
        // Draw pose
        drawConnectors(canvasCtx, results.poseLandmarks, POSE_CONNECTIONS,
                       {color: '#00FF00', lineWidth: 4});
        drawLandmarks(canvasCtx, results.poseLandmarks,
                      {color: '#FF0000', lineWidth: 2});

        const landmarks = results.poseLandmarks;
        const exercise = exerciseTypeEl.value;

        if (exercise === 'squat') {
            // Squat tracking (Hip - Knee - Ankle)
            // Left leg
            const hip = landmarks[23];
            const knee = landmarks[25];
            const ankle = landmarks[27];
            
            // Check visibility
            if (hip.visibility > 0.5 && knee.visibility > 0.5 && ankle.visibility > 0.5) {
                const angle = calculateAngle(hip, knee, ankle);
                
                // State machine for squat
                if (angle > 160) {
                    if (stage === "down") {
                        repCount++;
                        repCountEl.textContent = repCount;
                        showFeedback("Good Rep!");
                    }
                    stage = "up";
                    statusTextEl.textContent = `Status: Standing (${Math.round(angle)}°)`;
                }
                
                if (angle < 90 && stage === "up") {
                    stage = "down";
                    statusTextEl.textContent = `Status: Squatting (${Math.round(angle)}°)`;
                }
            } else {
                statusTextEl.textContent = "Status: Body not fully visible";
            }
        } 
        else if (exercise === 'pushup') {
            // Pushup tracking (Shoulder - Elbow - Wrist)
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
                    }
                    stage = "up";
                    statusTextEl.textContent = `Status: Up (${Math.round(angle)}°)`;
                }
                
                if (angle < 90 && stage === "up") {
                    stage = "down";
                    statusTextEl.textContent = `Status: Down (${Math.round(angle)}°)`;
                }
            } else {
                statusTextEl.textContent = "Status: Arms not fully visible";
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
        alert("You haven't done any reps yet!");
        return;
    }
    
    if (camera) {
        camera.stop();
    }
    
    const exercise = exerciseTypeEl.value;
    const calories = repCount * (exercise === 'squat' ? 0.5 : 0.4); // Rough estimate
    
    try {
        await apiCall('/log-live-workout', 'POST', {
            workout_type: `Live AI ${exercise.charAt(0).toUpperCase() + exercise.slice(1)} Session`,
            difficulty_feedback: 'Medium',
            calories_burned: calories,
            reps: repCount
        });
        
        // Save locally for dashboard widget
        localStorage.setItem('lastLiveSession', JSON.stringify({
            type: exercise.charAt(0).toUpperCase() + exercise.slice(1),
            reps: repCount
        }));

        alert(`Workout Logged! ${repCount} reps successfully tracked and saved to your profile.`);
        window.location.href = 'dashboard.html';
        
    } catch (err) {
        alert('Error logging workout: ' + err.message);
    }
}
