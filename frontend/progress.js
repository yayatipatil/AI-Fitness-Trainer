// progress.js
// Assumes Chart.js is loaded in the HTML file

let currentChart = null;

async function render1RMChart(exerciseName, canvasId) {
    try {
        const data = await apiCall(`/set-logs/1rm/${encodeURIComponent(exerciseName)}`);
        const history = data.history;
        
        if (!history || history.length === 0) {
            console.log("No data for 1RM chart.");
            return;
        }

        const labels = history.map(h => {
            const d = new Date(h.date);
            return `${d.getMonth()+1}/${d.getDate()}`;
        });
        
        const points = history.map(h => parseFloat(h.estimated_1rm).toFixed(1));

        const ctx = document.getElementById(canvasId).getContext('2d');
        
        if (currentChart) {
            currentChart.destroy();
        }
        
        currentChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Estimated 1RM (kg)',
                    data: points,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    pointBackgroundColor: '#10b981',
                    pointRadius: 4,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: 'rgba(255, 255, 255, 0.5)' }
                    },
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: 'rgba(255, 255, 255, 0.5)' }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: 'rgba(255, 255, 255, 0.8)' }
                    }
                }
            }
        });

    } catch (e) {
        console.error("Error rendering chart:", e);
    }
}

window.render1RMChart = render1RMChart;

// Inline set logging
window.logSet = async function(exerciseName, weightInputId, repsInputId, btnElement) {
    const weight = parseFloat(document.getElementById(weightInputId).value);
    const reps = parseInt(document.getElementById(repsInputId).value);
    
    if (!weight || !reps) {
        alert("Please enter both weight and reps.");
        return;
    }
    
    try {
        const originalText = btnElement.innerHTML;
        btnElement.innerHTML = `<i data-lucide="loader" class="spin" style="width: 14px; height: 14px;"></i>`;
        lucide.createIcons({root: btnElement});
        
        await apiCall('/set-logs', 'POST', {
            exercise_name: exerciseName,
            weight_kg: weight,
            reps: reps
        });
        
        btnElement.innerHTML = `<i data-lucide="check" style="width: 14px; height: 14px; color: #10b981;"></i>`;
        lucide.createIcons({root: btnElement});
        
        setTimeout(() => {
            btnElement.innerHTML = originalText;
            document.getElementById(weightInputId).value = '';
            document.getElementById(repsInputId).value = '';
            // If the chart is on screen, update it
            if (document.getElementById('1rm-chart')) {
                render1RMChart(exerciseName, '1rm-chart');
            }
        }, 1500);
        
    } catch (e) {
        alert("Error logging set: " + e.message);
        btnElement.innerHTML = `<i data-lucide="x" style="width: 14px; height: 14px; color: #ef4444;"></i>`;
        lucide.createIcons({root: btnElement});
    }
}
