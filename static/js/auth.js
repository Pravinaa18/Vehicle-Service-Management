// AutoCare Authentication & Form Validation Engine

function fillDemoCredentials(role) {
  const emailInput = document.getElementById('login-email');
  const passwordInput = document.getElementById('login-password');

  if (!emailInput || !passwordInput) return;

  if (role === 'admin') {
    emailInput.value = 'admin@autocare.com';
    passwordInput.value = 'admin123';
    showToast('Admin credentials filled!', 'info');
  } else if (role === 'customer') {
    emailInput.value = 'john@example.com';
    passwordInput.value = 'customer123';
    showToast('Customer credentials filled!', 'info');
  }
}

function checkPasswordStrength(password) {
  const fill = document.getElementById('pwd-meter-fill');
  const label = document.getElementById('pwd-strength-label');
  if (!fill || !label) return;

  if (!password || password.length === 0) {
    fill.className = 'pwd-meter-fill';
    label.textContent = '';
    return;
  }

  let score = 0;
  if (password.length >= 6) score++;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;

  if (score <= 2) {
    fill.className = 'pwd-meter-fill weak';
    label.textContent = 'Weak password';
    label.style.color = 'var(--danger)';
  } else if (score <= 4) {
    fill.className = 'pwd-meter-fill medium';
    label.textContent = 'Medium password';
    label.style.color = 'var(--warning)';
  } else {
    fill.className = 'pwd-meter-fill strong';
    label.textContent = 'Strong password';
    label.style.color = 'var(--success)';
  }
}

function validateSignupForm(e) {
  const fullName = document.getElementById('signup-name');
  const email = document.getElementById('signup-email');
  const phone = document.getElementById('signup-phone');
  const password = document.getElementById('signup-password');
  const confirmPassword = document.getElementById('signup-confirm-password');

  let isValid = true;

  function showError(input, msg) {
    const errorEl = document.getElementById(input.id + '-error');
    if (errorEl) {
      errorEl.textContent = msg;
      errorEl.classList.add('visible');
    }
    input.style.borderColor = 'var(--danger)';
    isValid = false;
  }

  function clearError(input) {
    const errorEl = document.getElementById(input.id + '-error');
    if (errorEl) {
      errorEl.textContent = '';
      errorEl.classList.remove('visible');
    }
    input.style.borderColor = '';
  }

  // Clear previous errors
  [fullName, email, phone, password, confirmPassword].forEach(input => {
    if (input) clearError(input);
  });

  if (!fullName.value.trim()) {
    showError(fullName, 'Please enter your full name');
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email.value.trim())) {
    showError(email, 'Please enter a valid email address');
  }

  if (!phone.value.trim() || phone.value.trim().length < 8) {
    showError(phone, 'Please enter a valid phone number');
  }

  if (!password.value || password.value.length < 6) {
    showError(password, 'Password must be at least 6 characters long');
  }

  if (password.value !== confirmPassword.value) {
    showError(confirmPassword, 'Passwords do not match');
  }

  if (!isValid) {
    e.preventDefault();
  }
}
