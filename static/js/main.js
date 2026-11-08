/**
 * Hostel Complaint Management System (HCMS)
 * Vanilla JavaScript Frontend Enhancements (static/js/main.js)
 */

document.addEventListener("DOMContentLoaded", function () {
    // 1. Auto-dismiss flash alerts after 5 seconds
    const flashMessages = document.querySelectorAll(".alert");
    flashMessages.forEach((alert) => {
        setTimeout(() => {
            alert.style.transition = "opacity 0.5s ease, transform 0.5s ease";
            alert.style.opacity = "0";
            alert.style.transform = "translateY(-10px)";
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    // 2. Generic confirmation for critical / destructive actions
    const dangerForms = document.querySelectorAll("form[data-confirm]");
    dangerForms.forEach((form) => {
        form.addEventListener("submit", function (e) {
            const promptMsg = form.getAttribute("data-confirm") || "Are you sure you want to perform this action?";
            if (!confirm(promptMsg)) {
                e.preventDefault();
            }
        });
    });

    // 3. Dynamic Character Counter for complaint descriptions
    const descTextareas = document.querySelectorAll("textarea[data-counter]");
    descTextareas.forEach((ta) => {
        const counterId = ta.getAttribute("data-counter");
        const counterEl = document.getElementById(counterId);
        if (counterEl) {
            const updateCount = () => {
                counterEl.textContent = `${ta.value.length} characters (min ${ta.getAttribute("minlength") || 15})`;
            };
            ta.addEventListener("input", updateCount);
            updateCount();
        }
    });

    // 4. File input size check (5MB max)
    const fileInputs = document.querySelectorAll('input[type="file"][data-max-size]');
    fileInputs.forEach((input) => {
        input.addEventListener("change", function () {
            if (this.files && this.files[0]) {
                const maxBytes = parseInt(this.getAttribute("data-max-size"), 10) || 5 * 1024 * 1024;
                if (this.files[0].size > maxBytes) {
                    alert(`Selected file exceeds the maximum allowed upload limit of ${(maxBytes / (1024 * 1024)).toFixed(0)}MB.`);
                    this.value = "";
                }
            }
        });
    });
});

