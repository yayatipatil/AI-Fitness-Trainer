// exercise-demo.js

const MUSCLE_COLORS = {
    primary: '#F59E0B',
    secondary: '#14B8A6',
    default: 'rgba(255, 255, 255, 0.1)'
};

// Simplified SVG representation of muscles for demo purposes
// In a real app, this would be a complex set of SVG paths mapped to exact anatomical shapes.
function getMuscleSVG(primaryMuscles, secondaryMuscles) {
    const isPrimary = (m) => primaryMuscles.includes(m);
    const isSecondary = (m) => secondaryMuscles.includes(m);
    
    const getColor = (m) => {
        if (isPrimary(m)) return MUSCLE_COLORS.primary;
        if (isSecondary(m)) return MUSCLE_COLORS.secondary;
        return MUSCLE_COLORS.default;
    };

    return `
    <svg viewBox="0 0 200 300" width="100%" height="100%" style="max-height: 200px;">
        <!-- FRONT -->
        <g transform="translate(40, 20)">
            <text x="30" y="-5" fill="var(--text-muted)" font-size="10" text-anchor="middle">FRONT</text>
            <!-- Head & Torso outline -->
            <circle cx="30" cy="10" r="10" fill="rgba(255,255,255,0.05)" />
            <rect x="15" y="25" width="30" height="60" rx="10" fill="rgba(255,255,255,0.05)" />
            
            <!-- Shoulders -->
            <circle cx="10" cy="30" r="8" fill="${getColor('shoulders')}" />
            <circle cx="50" cy="30" r="8" fill="${getColor('shoulders')}" />
            
            <!-- Chest -->
            <rect x="18" y="28" width="11" height="15" rx="3" fill="${getColor('chest')}" />
            <rect x="31" y="28" width="11" height="15" rx="3" fill="${getColor('chest')}" />
            
            <!-- Abs -->
            <rect x="22" y="45" width="16" height="30" rx="4" fill="${getColor('abs')}" />
            
            <!-- Obliques -->
            <rect x="16" y="45" width="5" height="25" rx="2" fill="${getColor('obliques')}" />
            <rect x="39" y="45" width="5" height="25" rx="2" fill="${getColor('obliques')}" />
            
            <!-- Biceps -->
            <rect x="5" y="40" width="8" height="20" rx="4" fill="${getColor('biceps')}" />
            <rect x="47" y="40" width="8" height="20" rx="4" fill="${getColor('biceps')}" />
            
            <!-- Forearms -->
            <rect x="2" y="62" width="7" height="18" rx="3" fill="${getColor('forearms')}" />
            <rect x="51" y="62" width="7" height="18" rx="3" fill="${getColor('forearms')}" />
            
            <!-- Quads -->
            <rect x="16" y="90" width="12" height="35" rx="5" fill="${getColor('quads')}" />
            <rect x="32" y="90" width="12" height="35" rx="5" fill="${getColor('quads')}" />
            
            <!-- Calves (front) -->
            <rect x="18" y="130" width="8" height="25" rx="3" fill="${getColor('calves')}" />
            <rect x="34" y="130" width="8" height="25" rx="3" fill="${getColor('calves')}" />
        </g>
        
        <!-- BACK -->
        <g transform="translate(130, 20)">
            <text x="30" y="-5" fill="var(--text-muted)" font-size="10" text-anchor="middle">BACK</text>
            <!-- Head & Torso outline -->
            <circle cx="30" cy="10" r="10" fill="rgba(255,255,255,0.05)" />
            <rect x="15" y="25" width="30" height="60" rx="10" fill="rgba(255,255,255,0.05)" />
            
            <!-- Back (Lats/Traps) -->
            <path d="M 18 28 L 42 28 L 38 60 L 22 60 Z" fill="${getColor('back')}" />
            
            <!-- Triceps -->
            <rect x="5" y="40" width="8" height="20" rx="4" fill="${getColor('triceps')}" />
            <rect x="47" y="40" width="8" height="20" rx="4" fill="${getColor('triceps')}" />
            
            <!-- Glutes -->
            <rect x="16" y="80" width="13" height="15" rx="5" fill="${getColor('glutes')}" />
            <rect x="31" y="80" width="13" height="15" rx="5" fill="${getColor('glutes')}" />
            
            <!-- Hamstrings -->
            <rect x="17" y="98" width="11" height="30" rx="4" fill="${getColor('hamstrings')}" />
            <rect x="32" y="98" width="11" height="30" rx="4" fill="${getColor('hamstrings')}" />
            
            <!-- Calves (back) -->
            <rect x="18" y="130" width="9" height="25" rx="4" fill="${getColor('calves')}" />
            <rect x="33" y="130" width="9" height="25" rx="4" fill="${getColor('calves')}" />
        </g>
    </svg>
    `;
}

function renderMuscleMap(primaryMuscles, secondaryMuscles) {
    return getMuscleSVG(primaryMuscles, secondaryMuscles);
}

function toggleTips(btn) {
    const content = btn.nextElementSibling;
    if (content.style.maxHeight) {
        content.style.maxHeight = null;
        content.style.padding = "0 10px";
        btn.querySelector('i').style.transform = 'rotate(0deg)';
    } else {
        content.style.maxHeight = content.scrollHeight + "px";
        content.style.padding = "10px";
        btn.querySelector('i').style.transform = 'rotate(180deg)';
    }
}

function renderExerciseCard(exercise, enableSwap = false) {
    const primary = JSON.parse(exercise.primary_muscles || '[]');
    const secondary = JSON.parse(exercise.secondary_muscles || '[]');
    const tips = JSON.parse(exercise.form_tips || '[]');
    
    // Placeholder image based on category
    const categoryImages = {
        'Legs': 'https://images.unsplash.com/photo-1434682881908-b43d0467b798?w=400&q=80',
        'Chest': 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&q=80',
        'Back': 'https://images.unsplash.com/photo-1603287681836-b174ce5074c2?w=400&q=80',
        'Arms': 'https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=400&q=80',
        'Shoulders': 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400&q=80',
        'Core': 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400&q=80',
        'Full Body': 'https://images.unsplash.com/photo-1599058917212-d750089bc07e?w=400&q=80'
    };
    
    const youtubeVideos = {
        'Squats': 'https://www.youtube.com/embed/gcNh17Ckjgg',
        'Push-ups': 'https://www.youtube.com/embed/IODxDxX7oi4',
        'Pull-ups': 'https://www.youtube.com/embed/eGo4IYPNUKk',
        'Deadlifts': 'https://www.youtube.com/embed/op9kVnSso6Q',
        'Bench Press': 'https://www.youtube.com/embed/gRVjAtPip0Y',
        'Lunges': 'https://www.youtube.com/embed/QOVaHwm-Q6U',
        'Overhead Press': 'https://www.youtube.com/embed/QAQ64hK4Xxs',
        'Bicep Curls': 'https://www.youtube.com/embed/ykJmrZ5v0Oo',
        'Tricep Dips': 'https://www.youtube.com/embed/0326dy_-CzM',
        'Plank': 'https://www.youtube.com/embed/pSHjTRCQxIw',
        'Russian Twists': 'https://www.youtube.com/embed/wkD8rjkodUI',
        'Calf Raises': 'https://www.youtube.com/embed/-M4-G8p8fmc',
        'Leg Press': 'https://www.youtube.com/embed/IZxyjW7OSvc',
        'Lat Pulldown': 'https://www.youtube.com/embed/CAwf7n6Luuc',
        'Cable Crossovers': 'https://www.youtube.com/embed/taI4XduLpTk',
        'Face Pulls': 'https://www.youtube.com/embed/rep-qVOkqgk',
        'Kettlebell Swings': 'https://www.youtube.com/embed/YSxHifyI6s8',
        'Burpees': 'https://www.youtube.com/embed/TU8QYVW0gDU',
        'Mountain Climbers': 'https://www.youtube.com/embed/nmwgirgXLYM',
        'Glute Bridges': 'https://www.youtube.com/embed/OUgsJ8-Vi0E'
    };
    
    const embedUrl = exercise.demo_url || youtubeVideos[exercise.name];
    let mediaHtml = '';
    
    if (embedUrl && embedUrl.includes('youtube.com/embed')) {
        mediaHtml = `<iframe width="100%" height="100%" src="${embedUrl}" title="${exercise.name} Tutorial" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="position: absolute; top: 0; left: 0; border: none; border-radius: 14px 14px 0 0;"></iframe>`;
    } else {
        const imgUrl = embedUrl || categoryImages[exercise.category] || categoryImages['Full Body'];
        mediaHtml = `<img src="${imgUrl}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 14px 14px 0 0;" alt="${exercise.name}">`;
    }
    
    let swapBtnHtml = enableSwap ? `
        <button class="btn btn-outline" style="padding: 5px 10px; font-size: 0.8rem;" onclick="swapExercise('${exercise.name}', this)">
            <i data-lucide="refresh-cw" style="width: 14px; height: 14px;"></i> Swap
        </button>
    ` : '';

    return `
    <div class="exercise-card glass-panel" style="padding: 0; overflow: hidden; display: flex; flex-direction: column;" id="card-${exercise.name.replace(/\s+/g, '-')}">
        <div style="position: relative; height: 200px; z-index: 1;">
            ${mediaHtml}
            <div style="position: absolute; top: 10px; right: 10px; display: flex; gap: 5px; z-index: 10; pointer-events: none;">
                <span class="badge" style="background: rgba(0,0,0,0.6); color: white;">${exercise.category}</span>
            </div>
        </div>
        <div style="padding: 15px; flex-grow: 1;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h3 style="margin: 0; font-size: 1.2rem; color: var(--text-main);">${exercise.name}</h3>
                ${swapBtnHtml}
            </div>
            
            <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                <div style="flex: 1; min-width: 120px;">
                    ${renderMuscleMap(primary, secondary)}
                </div>
                <div style="flex: 1; display: flex; flex-direction: column; justify-content: center;">
                    <div style="display: flex; align-items: center; gap: 5px; margin-bottom: 5px;">
                        <div style="width: 10px; height: 10px; background: ${MUSCLE_COLORS.primary}; border-radius: 2px;"></div>
                        <span style="font-size: 0.8rem; color: var(--text-muted);">Primary</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 5px;">
                        <div style="width: 10px; height: 10px; background: ${MUSCLE_COLORS.secondary}; border-radius: 2px;"></div>
                        <span style="font-size: 0.8rem; color: var(--text-muted);">Secondary</span>
                    </div>
                </div>
            </div>
            
            <div class="form-tips-section" style="margin-top: 10px;">
                <button onclick="toggleTips(this)" style="width: 100%; text-align: left; background: rgba(255,255,255,0.05); border: 1px solid var(--border-light); color: var(--text-main); padding: 8px 10px; border-radius: 8px; cursor: pointer; display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.9rem; font-weight: 600;">Form Tips</span>
                    <i data-lucide="chevron-down" style="width: 16px; height: 16px; transition: transform 0.3s;"></i>
                </button>
                <div class="tips-content" style="max-height: 0; overflow: hidden; transition: max-height 0.3s ease-out, padding 0.3s; padding: 0 10px; background: rgba(0,0,0,0.2); border-radius: 0 0 8px 8px;">
                    <ul style="margin: 0; padding-left: 20px; font-size: 0.85rem; color: var(--text-muted); padding-top: 5px; padding-bottom: 5px;">
                        ${tips.map(t => `<li>${t}</li>`).join('')}
                    </ul>
                </div>
            </div>
            
            <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1);">
                <div style="font-size: 0.85rem; margin-bottom: 8px; color: var(--text-muted); font-weight: 600;">Log Set</div>
                <div style="display: flex; gap: 5px;">
                    <input type="number" id="weight-${exercise.name.replace(/\s+/g, '-')}" placeholder="kg" style="width: 60px; padding: 5px; background: rgba(0,0,0,0.3); border: 1px solid var(--border-light); color: white; border-radius: 5px; font-size: 0.9rem;">
                    <input type="number" id="reps-${exercise.name.replace(/\s+/g, '-')}" placeholder="reps" style="width: 60px; padding: 5px; background: rgba(0,0,0,0.3); border: 1px solid var(--border-light); color: white; border-radius: 5px; font-size: 0.9rem;">
                    <button class="btn btn-primary" style="padding: 5px 10px; flex-grow: 1;" onclick="logSet('${exercise.name}', 'weight-${exercise.name.replace(/\s+/g, '-')}', 'reps-${exercise.name.replace(/\s+/g, '-')}', this)">
                        <i data-lucide="plus" style="width: 16px; height: 16px;"></i> Log
                    </button>
                </div>
            </div>
        </div>
    </div>
    `;
}

window.swapExercise = async function(exerciseName, btnElement) {
    try {
        btnElement.innerHTML = `<i data-lucide="loader" class="spin" style="width: 14px; height: 14px;"></i> Swapping...`;
        lucide.createIcons({root: btnElement});
        
        // Fetch swap
        const newEx = await apiCall(`/exercises/swap?name=${encodeURIComponent(exerciseName)}`);
        
        // Find the card container
        const cardContainer = btnElement.closest('.exercise-card');
        
        // Keep the target text if it exists above the card in planner/workouts (we replace just the card)
        // Re-render
        const newHtml = renderExerciseCard(newEx, true);
        
        // Create a temp div to parse HTML
        const temp = document.createElement('div');
        temp.innerHTML = newHtml;
        const newCard = temp.firstElementChild;
        
        // Replace old card with new
        cardContainer.replaceWith(newCard);
        lucide.createIcons();
        
        // If this is in planner, we'd ideally update the backend plan too, 
        // but for demo purposes, UI swap is fine or we can let user save.
        
    } catch(e) {
        console.error(e);
        btnElement.innerHTML = `<i data-lucide="refresh-cw" style="width: 14px; height: 14px;"></i> Failed`;
        lucide.createIcons({root: btnElement});
        setTimeout(() => {
            btnElement.innerHTML = `<i data-lucide="refresh-cw" style="width: 14px; height: 14px;"></i> Swap`;
            lucide.createIcons({root: btnElement});
        }, 2000);
    }
}

window.renderMuscleMap = renderMuscleMap;
window.renderExerciseCard = renderExerciseCard;
