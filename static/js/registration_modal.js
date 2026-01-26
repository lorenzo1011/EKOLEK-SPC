/**
 * Registration Success Modal Handler
 * Shows a modal popup when user successfully registers
 * Prevents registration messages from mixing with login page messages
 */

function closeRegistrationModal() {
    const modal = document.getElementById('registrationSuccessModal');
    if (modal) {
        modal.classList.remove('show');
        modal.style.display = 'none';
    }
}

function showRegistrationModal(registrationType) {
    const modal = document.getElementById('registrationSuccessModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    
    if (!modal || !modalTitle || !modalMessage) {
        console.error('Registration modal elements not found');
        return;
    }
    
    // Set content based on registration type
    if (registrationType === 'family') {
        modalTitle.textContent = 'Family Registration Successful!';
        modalMessage.textContent = 'Your family account has been created successfully. Please wait for admin approval before you and your family members can log in.';
    } else if (registrationType === 'member') {
        modalTitle.textContent = 'Member Registration Successful!';
        modalMessage.textContent = 'You have successfully joined your family! Please wait for admin approval before logging in.';
    } else {
        modalTitle.textContent = 'Registration Successful!';
        modalMessage.textContent = 'Your account has been created successfully. Please wait for admin approval before logging in.';
    }
    
    // Show the modal
    modal.classList.add('show');
    modal.style.display = 'flex';
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check if registration was successful (injected from Django)
    if (typeof window.REGISTRATION_SUCCESS !== 'undefined' && window.REGISTRATION_SUCCESS) {
        const registrationType = window.REGISTRATION_TYPE || '';
        showRegistrationModal(registrationType);
    }
});
