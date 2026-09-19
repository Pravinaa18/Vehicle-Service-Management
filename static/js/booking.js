// 7-Step Interactive Service Booking Wizard

let currentStep = 1;
const totalSteps = 7;

let bookingData = {
  vehicleId: '',
  vehicleText: '',
  serviceId: '',
  serviceName: '',
  servicePrice: 0,
  date: '',
  timeSlot: '',
  problemDescription: ''
};

function selectVehicleCard(cardElement, vehicleId, vehicleText) {
  document.querySelectorAll('.vehicle-card-item').forEach(card => card.classList.remove('selected'));
  cardElement.classList.add('selected');
  const radio = cardElement.querySelector('input[type="radio"]');
  if (radio) radio.checked = true;

  bookingData.vehicleId = vehicleId;
  bookingData.vehicleText = vehicleText;
  document.getElementById('hidden-vehicle-id').value = vehicleId;
}

function selectServiceCard(cardElement, serviceId, serviceName, price) {
  document.querySelectorAll('.service-card-item').forEach(card => card.classList.remove('selected'));
  cardElement.classList.add('selected');
  const radio = cardElement.querySelector('input[type="radio"]');
  if (radio) radio.checked = true;

  bookingData.serviceId = serviceId;
  bookingData.serviceName = serviceName;
  bookingData.servicePrice = parseFloat(price);
  document.getElementById('hidden-service-id').value = serviceId;
}

function selectTimeSlot(slotBtn, slotText) {
  if (slotBtn.classList.contains('disabled')) return;
  document.querySelectorAll('.slot-btn').forEach(btn => btn.classList.remove('selected'));
  slotBtn.classList.add('selected');

  bookingData.timeSlot = slotText;
  document.getElementById('hidden-time-slot').value = slotText;
}

function updateStepNavigation(step) {
  document.querySelectorAll('.wizard-step-item').forEach((item, idx) => {
    const stepNum = idx + 1;
    item.classList.remove('active');
    if (stepNum === step) {
      item.classList.add('active');
    } else if (stepNum < step) {
      item.classList.add('completed');
    }
  });

  document.querySelectorAll('.wizard-step-content').forEach((content, idx) => {
    if (idx + 1 === step) {
      content.classList.add('active');
    } else {
      content.classList.remove('active');
    }
  });

  // Toggle prev/next buttons
  const prevBtn = document.getElementById('wizard-prev-btn');
  const nextBtn = document.getElementById('wizard-next-btn');
  const confirmBtn = document.getElementById('wizard-confirm-btn');

  if (prevBtn) prevBtn.style.display = step === 1 ? 'none' : 'inline-flex';
  if (nextBtn) nextBtn.style.display = step === totalSteps ? 'none' : 'inline-flex';
  if (confirmBtn) confirmBtn.style.display = step === totalSteps ? 'inline-flex' : 'none';

  if (step === 6 || step === 7) {
    populateReviewSummary();
  }
}

function validateStep(step) {
  if (step === 1) {
    const selectedVehicle = document.getElementById('hidden-vehicle-id').value;
    if (!selectedVehicle) {
      showToast('Please select a vehicle or add one to your garage', 'warning');
      return false;
    }
  } else if (step === 2) {
    const selectedService = document.getElementById('hidden-service-id').value;
    if (!selectedService) {
      showToast('Please choose a service package', 'warning');
      return false;
    }
  } else if (step === 3) {
    const dateInput = document.getElementById('booking-date-input');
    if (!dateInput || !dateInput.value) {
      showToast('Please choose a valid appointment date', 'warning');
      return false;
    }
    bookingData.date = dateInput.value;
  } else if (step === 4) {
    const timeSlot = document.getElementById('hidden-time-slot').value;
    if (!timeSlot) {
      showToast('Please pick a convenient time slot', 'warning');
      return false;
    }
  } else if (step === 5) {
    const notesInput = document.getElementById('booking-notes-input');
    bookingData.problemDescription = notesInput ? notesInput.value.trim() : '';
  }
  return true;
}

function validateCurrentStep() {
  return validateStep(currentStep);
}

function goToStep(targetStep) {
  if (targetStep < currentStep) {
    currentStep = targetStep;
    updateStepNavigation(currentStep);
    return;
  }
  for (let s = currentStep; s < targetStep; s++) {
    if (!validateStep(s)) {
      currentStep = s;
      updateStepNavigation(s);
      return;
    }
  }
  currentStep = targetStep;
  updateStepNavigation(currentStep);
}

function nextWizardStep() {
  if (!validateCurrentStep()) return;
  if (currentStep < totalSteps) {
    currentStep++;
    updateStepNavigation(currentStep);
    window.scrollTo({ top: 120, behavior: 'smooth' });
  }
}

function prevWizardStep() {
  if (currentStep > 1) {
    currentStep--;
    updateStepNavigation(currentStep);
    window.scrollTo({ top: 120, behavior: 'smooth' });
  }
}

function populateReviewSummary() {
  const reviewVehicle = document.getElementById('review-vehicle-text');
  const reviewService = document.getElementById('review-service-text');
  const reviewDate = document.getElementById('review-date-text');
  const reviewTime = document.getElementById('review-time-text');
  const reviewNotes = document.getElementById('review-notes-text');
  const reviewPrice = document.getElementById('review-price-text');
  const reviewTax = document.getElementById('review-tax-text');
  const reviewTotal = document.getElementById('review-total-text');

  if (reviewVehicle) reviewVehicle.textContent = bookingData.vehicleText || 'Selected Vehicle';
  if (reviewService) reviewService.textContent = bookingData.serviceName || 'Selected Service';
  if (reviewDate) reviewDate.textContent = bookingData.date || 'Not Selected';
  if (reviewTime) reviewTime.textContent = bookingData.timeSlot || 'Not Selected';
  if (reviewNotes) reviewNotes.textContent = bookingData.problemDescription || 'None specified';

  const price = bookingData.servicePrice || 0;
  const tax = price * 0.10;
  const total = price + tax;

  if (reviewPrice) reviewPrice.textContent = `$${price.toFixed(2)}`;
  if (reviewTax) reviewTax.textContent = `$${tax.toFixed(2)}`;
  if (reviewTotal) reviewTotal.textContent = `$${total.toFixed(2)}`;

  // Also update Step 7 final confirm card
  const finalSummaryEl = document.getElementById('step7-summary');
  if (finalSummaryEl) {
    finalSummaryEl.innerHTML = `
      <div style="background: var(--bg-muted); border-radius: var(--radius-md); padding: 1.25rem; margin-top: 1rem; text-align: left;">
        <div style="margin-bottom: 0.5rem;"><strong>Vehicle:</strong> ${escapeHtml(bookingData.vehicleText || 'Selected Vehicle')}</div>
        <div style="margin-bottom: 0.5rem;"><strong>Service:</strong> ${escapeHtml(bookingData.serviceName || 'Selected Service')}</div>
        <div style="margin-bottom: 0.5rem;"><strong>Date & Time:</strong> ${escapeHtml(bookingData.date || 'Scheduled Date')} at ${escapeHtml(bookingData.timeSlot || 'Selected Window')}</div>
        <div style="margin-bottom: 0.5rem;"><strong>Estimated Total:</strong> $${total.toFixed(2)}</div>
        ${bookingData.problemDescription ? `<div style="font-size: 0.85rem; color: var(--text-muted); font-style: italic;">Notes: ${escapeHtml(bookingData.problemDescription)}</div>` : ''}
      </div>
    `;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // Set minimum date for booking date picker to today
  const datePicker = document.getElementById('booking-date-input');
  if (datePicker) {
    const today = new Date().toISOString().split('T')[0];
    datePicker.min = today;
  }
});
