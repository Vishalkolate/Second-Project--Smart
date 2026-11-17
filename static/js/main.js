// Smart LMS Interactive Script
document.addEventListener('DOMContentLoaded', function () {
    // Sidebar toggle for mobile
    const toggleBtn = document.getElementById('menu-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function (e) {
            e.preventDefault();
            document.getElementById('sidebar-wrapper').classList.toggle('toggled');
            document.getElementById('page-content-wrapper').classList.toggle('toggled');
        });
    }

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function () {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Exam Timer Countdown helper
function startExamTimer(durationSeconds, displayElementId, formElementId) {
    let timer = durationSeconds;
    const display = document.getElementById(displayElementId);
    const form = document.getElementById(formElementId);

    const interval = setInterval(function () {
        const hours = parseInt(timer / 3600, 10);
        const minutes = parseInt((timer % 3600) / 60, 10);
        const seconds = parseInt(timer % 60, 10);

        const hStr = hours < 10 ? "0" + hours : hours;
        const mStr = minutes < 10 ? "0" + minutes : minutes;
        const sStr = seconds < 10 ? "0" + seconds : seconds;

        if (display) {
            display.textContent = (hours > 0 ? hStr + ":" : "") + mStr + ":" + sStr;
        }

        if (timer <= 300 && display) {
            display.classList.remove('text-primary');
            display.classList.add('text-danger', 'fw-bold');
        }

        if (--timer < 0) {
            clearInterval(interval);
            alert("Time has expired! Submitting your exam automatically.");
            if (form) {
                form.submit();
            }
        }
    }, 1000);
}
