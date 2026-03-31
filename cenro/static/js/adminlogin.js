/**
 * E-KOLEK Admin Login v2.1
 * Alert cleanup, form handling, password toggle, micro-interactions
 */

document.addEventListener('DOMContentLoaded', () => {
  cleanupAlerts();
  initForm();
  initPasswordToggle();
  initInputFocus();
});

/* ──── Alert cleanup & auto-dismiss ──── */
function cleanupAlerts() {
  const seen = new Set();
  const adminKeywords = [
    'Admin account "', 'created successfully', 'Password reset email sent',
    'has been unlocked', 'has been reactivated', 'Updated barangay',
    'barangay assignments for', 'now has access to all barangays',
    'Barangay assignments updated', 'Family verified', 'User approved',
    'User rejected', 'Schedule notification', 'Reward has been',
    'Content has been', 'Quiz has been', 'Notification sent to'
  ];

  document.querySelectorAll('.alert').forEach((el, i) => {
    const text = (el.textContent || '').trim();

    if (seen.has(text)) { el.remove(); return; }
    seen.add(text);

    if (adminKeywords.some(kw => text.includes(kw))) { el.remove(); return; }

    // Stagger entrance animation
    el.style.animationDelay = `${i * 0.08}s`;

    // Auto-dismiss after 6s (staggered)
    setTimeout(() => {
      el.style.transition = 'opacity 0.4s ease, transform 0.4s ease, max-height 0.3s ease 0.2s';
      el.style.opacity = '0';
      el.style.transform = 'translateY(-8px) scale(0.98)';
      el.style.maxHeight = '0';
      el.style.overflow = 'hidden';
      el.style.marginBottom = '0';
      el.style.padding = '0';
      setTimeout(() => el.remove(), 500);
    }, 6000 + i * 300);
  });
}

/* ──── Form submission with loading state ──── */
function initForm() {
  const form = document.getElementById('loginForm');
  if (!form) return;

  form.addEventListener('submit', () => {
    const btn = document.getElementById('loginBtn');
    if (btn) {
      btn.classList.add('is-loading');
      btn.disabled = true;
    }
  });
}

/* ──── Password visibility toggle ──── */
function initPasswordToggle() {
  const toggle = document.getElementById('passwordToggle');
  const input  = document.getElementById('password');
  const icon   = document.getElementById('toggleIcon');

  if (!toggle || !input || !icon) return;

  toggle.addEventListener('click', () => {
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    icon.classList.replace(
      show ? 'bx-show' : 'bx-hide',
      show ? 'bx-hide' : 'bx-show'
    );
    toggle.setAttribute('aria-label',
      show ? 'Hide password' : 'Show password'
    );

    // Subtle bounce on toggle
    toggle.style.transform = 'scale(0.85)';
    requestAnimationFrame(() => {
      toggle.style.transition = 'transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)';
      toggle.style.transform = 'scale(1)';
    });
  });
}

/* ──── Input focus ripple & filled state ──── */
function initInputFocus() {
  document.querySelectorAll('.form-input').forEach(input => {
    // Add filled class for styling when input has value
    const check = () => input.classList.toggle('is-filled', input.value.length > 0);
    input.addEventListener('input', check);
    input.addEventListener('change', check);
    check(); // initial state
  });
}
