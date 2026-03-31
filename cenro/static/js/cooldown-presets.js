/**
 * Game Cooldown Configuration — Days + Hours Support
 * Pill-style preset selection with dual custom inputs
 */

// Format duration for display
function formatDuration(totalHours) {
    if (totalHours === 0) return 'No cooldown (unlimited plays)';

    const days  = Math.floor(totalHours / 24);
    const hours = totalHours % 24;
    const parts = [];

    if (days > 0) {
        if (days === 1)       parts.push('1 day');
        else if (days === 7)  parts.push('1 week');
        else if (days === 14) parts.push('2 weeks');
        else if (days === 30) parts.push('1 month');
        else                  parts.push(`${days} day${days !== 1 ? 's' : ''}`);
    }
    if (hours > 0) {
        parts.push(`${hours} hour${hours !== 1 ? 's' : ''}`);
    }

    const label = parts.join(' ');
    return `${label} (${totalHours}h total)`;
}

// Form-id lookup for a given gameType key
function formIdFor(gameType) {
    if (gameType === 'default') return 'default-cooldown-form';
    return gameType + '-cooldown-form';
}

// Set cooldown using preset buttons (days + hours)
function setCooldown(gameType, days, hours) {
    const totalHours = (days * 24) + hours;

    // Update hidden fields
    document.getElementById(`${gameType}-cooldown_hours`).value  = totalHours;
    document.getElementById(`${gameType}-cooldown_minutes`).value = 0;

    // Update visible custom inputs
    const daysEl  = document.getElementById(`${gameType}-days`);
    const hoursEl = document.getElementById(`${gameType}-hours`);
    if (daysEl)  daysEl.value  = days;
    if (hoursEl) hoursEl.value = hours;

    // Duration text
    updateDurationDisplay(gameType, totalHours);

    // Highlight the selected pill
    const form = document.getElementById(formIdFor(gameType));
    if (form) {
        form.querySelectorAll('.preset-btn').forEach(btn => btn.classList.remove('selected'));
    }
    if (event && event.target && event.target.classList.contains('preset-btn')) {
        event.target.classList.add('selected');
    }

    // Update status badge text
    updateStatusText(gameType, totalHours);
}

// Update cooldown from manual days + hours inputs
function updateCooldownFromInputs(gameType) {
    const daysInput  = document.getElementById(`${gameType}-days`);
    const hoursInput = document.getElementById(`${gameType}-hours`);

    let days  = parseInt(daysInput.value)  || 0;
    let hours = parseInt(hoursInput.value) || 0;

    // Clamp values
    days  = Math.max(0, Math.min(30, days));
    hours = Math.max(0, Math.min(23, hours));
    daysInput.value  = days;
    hoursInput.value = hours;

    const totalHours = (days * 24) + hours;

    // Update hidden fields
    document.getElementById(`${gameType}-cooldown_hours`).value  = totalHours;
    document.getElementById(`${gameType}-cooldown_minutes`).value = 0;

    updateDurationDisplay(gameType, totalHours);

    // Clear all pill selections, then highlight if matching
    const form = document.getElementById(formIdFor(gameType));
    if (form) {
        form.querySelectorAll('.preset-btn').forEach(btn => btn.classList.remove('selected'));
        const match = form.querySelector(`.preset-btn[data-total-hours="${totalHours}"]`);
        if (match) match.classList.add('selected');
    }

    updateStatusText(gameType, totalHours);
}

// Update the duration display text
function updateDurationDisplay(gameType, totalHours) {
    const el = document.getElementById(`${gameType}-duration-display`);
    if (el) el.textContent = formatDuration(totalHours);
}

// Update status badge text next to the toggle
function updateStatusText(gameType, totalHours) {
    const toggleId = gameType === 'default' ? 'default-is_active'
                   : gameType + '-is_active';
    const toggle   = document.getElementById(toggleId);
    const statusId = gameType === 'default' ? 'default-status' : gameType + '-status';
    const statusEl = document.getElementById(statusId);

    if (!statusEl) return;
    if (toggle && toggle.checked) {
        statusEl.textContent = 'Active — ' + formatDuration(totalHours);
    } else {
        statusEl.textContent = 'Disabled — Unlimited plays';
    }
}

// Load existing cooldown values and populate inputs
function loadExistingCooldowns() {
    const gameTypes = ['quiz', 'dragdrop', 'default'];

    gameTypes.forEach(gt => {
        const storedHours = parseInt(document.getElementById(`${gt}-cooldown_hours`)?.value) || 0;
        const days  = Math.floor(storedHours / 24);
        const hours = storedHours % 24;

        const daysInput  = document.getElementById(`${gt}-days`);
        const hoursInput = document.getElementById(`${gt}-hours`);
        if (daysInput)  daysInput.value  = days;
        if (hoursInput) hoursInput.value = hours;

        updateDurationDisplay(gt, storedHours);

        // Auto-highlight matching preset pill
        const form = document.getElementById(formIdFor(gt));
        if (form) {
            const match = form.querySelector(`.preset-btn[data-total-hours="${storedHours}"]`);
            if (match) match.classList.add('selected');
        }
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadExistingCooldowns();
});
