// FADE-IN BODY
window.addEventListener("load", () => {
    document.body.style.opacity = 1;

    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
        document.documentElement.setAttribute("data-theme", "dark");
    }
});

// DARK MODE TOGGLE
function toggleTheme() {
    if (document.documentElement.getAttribute("data-theme") === "dark") {
        document.documentElement.removeAttribute("data-theme");
        localStorage.setItem("theme", "light");
    } else {
        document.documentElement.setAttribute("data-theme", "dark");
        localStorage.setItem("theme", "dark");
    }
}

// PROFILE MODAL (if not already in base.html)
const profileModal = document.getElementById("profileModal");
const openProfileBtn = document.getElementById("openProfileModal");
const closeProfileBtn = document.getElementById("closeProfileModal");

if (openProfileBtn && closeProfileBtn && profileModal) {
    openProfileBtn.onclick = () => profileModal.style.display = "flex";
    closeProfileBtn.onclick = () => profileModal.style.display = "none";
    window.onclick = (event) => {
        if (event.target == profileModal) profileModal.style.display = "none";
    };
}

// CHARTS
function initCharts(gradeLabels, gradeCounts, subjects, subjectAverages) {
    if (document.getElementById('gradesChart')) {
        new Chart(document.getElementById('gradesChart'), {
            type: 'bar',
            data: {
                labels: gradeLabels,
                datasets: [{ data: gradeCounts, backgroundColor: '#4e73df', borderRadius: 5 }]
            },
            options: { plugins: { legend: { display: false } }, responsive: true, scales: { y: { beginAtZero: true } } }
        });
    }

    if (document.getElementById('topStudentsChart')) {
        new Chart(document.getElementById('topStudentsChart'), {
            type: 'doughnut',
            data: {
                labels: subjects,
                datasets: [{ data: subjectAverages, backgroundColor: ['#0072ff','#00c6ff','#43e97b','#fa709a'] }]
            },
            options: { responsive: true }
        });
    }

    // FADE IN BODY
window.addEventListener("load", () => {
    document.body.style.opacity = 1;
});

// PROFILE MODAL
const profileModal = document.getElementById("profileModal");
const openProfileBtn = document.getElementById("openProfileModal");
const closeProfileBtn = document.getElementById("closeProfileModal");

if (profileModal && openProfileBtn && closeProfileBtn) {
    openProfileBtn.onclick = () => profileModal.style.display = "flex";
    closeProfileBtn.onclick = () => profileModal.style.display = "none";
    window.onclick = (event) => {
        if (event.target === profileModal) profileModal.style.display = "none";
    };
}

// DARK MODE
const savedTheme = localStorage.getItem("theme");
if (savedTheme === "dark" || (!savedTheme && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
    document.documentElement.setAttribute("data-theme", "dark");
}

function toggleTheme() {
    if (document.documentElement.getAttribute("data-theme") === "dark") {
        document.documentElement.removeAttribute("data-theme");
        localStorage.setItem("theme", "light");
    } else {
        document.documentElement.setAttribute("data-theme", "dark");
        localStorage.setItem("theme", "dark");
    }
}

// CHART INITIALIZATION
function initCharts(gradeLabels, gradeCounts, subjects, subjectAverages) {
    const gradesChartEl = document.getElementById('gradesChart');
    if (gradesChartEl) {
        new Chart(gradesChartEl, {
            type: 'bar',
            data: { labels: gradeLabels, datasets: [{ data: gradeCounts, backgroundColor: '#4e73df' }] },
            options: { plugins: { legend: { display: false } }, responsive: true }
        });
    }

    const topStudentsChartEl = document.getElementById('topStudentsChart');
    if (topStudentsChartEl) {
        new Chart(topStudentsChartEl, {
            type: 'doughnut',
            data: { labels: subjects, datasets: [{ data: subjectAverages, backgroundColor: ['#0072ff','#00c6ff','#43e97b','#fa709a'] }] },
            options: { responsive: true }
        });
    }
}


 






   
}
