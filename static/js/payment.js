// Interactive Local Simulated Payment Engine

let activeInvoiceId = null;
let activeInvoiceAmount = 0;
let activePaymentMethod = 'Card';

function openPaymentModal(invoiceId, amount, invoiceNumber) {
  activeInvoiceId = invoiceId;
  activeInvoiceAmount = amount;
  activePaymentMethod = 'Card';

  const modalTitle = document.getElementById('payment-modal-title');
  const payBtnText = document.getElementById('btn-pay-amount-text');
  const displayNum = document.getElementById('payment-invoice-num');

  if (modalTitle) modalTitle.textContent = `Checkout: ${invoiceNumber}`;
  if (displayNum) displayNum.textContent = invoiceNumber;
  if (payBtnText) payBtnText.textContent = `$${parseFloat(amount).toFixed(2)}`;

  switchPaymentTab('Card');
  openModal('payment-modal');
}

function switchPaymentTab(method) {
  activePaymentMethod = method;
  document.querySelectorAll('.payment-tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.method === method);
  });

  const cardPane = document.getElementById('pay-pane-card');
  const upiPane = document.getElementById('pay-pane-upi');
  const cashPane = document.getElementById('pay-pane-cash');

  if (cardPane) cardPane.style.display = method === 'Card' ? 'block' : 'none';
  if (upiPane) upiPane.style.display = method === 'UPI' ? 'block' : 'none';
  if (cashPane) cashPane.style.display = method === 'Cash' ? 'block' : 'none';
}

async function processSimulatedPayment() {
  const payBtn = document.getElementById('btn-execute-payment');
  if (payBtn) {
    payBtn.disabled = true;
    payBtn.innerHTML = `<span class="spinner">⏳</span> Processing Secure Payment...`;
  }

  let metaInfo = '';
  if (activePaymentMethod === 'Card') {
    const cardNum = document.getElementById('sim-card-number') ? document.getElementById('sim-card-number').value : '4242';
    metaInfo = `Card ending in ${cardNum.slice(-4) || '4242'}`;
  } else if (activePaymentMethod === 'UPI') {
    const vpa = document.getElementById('sim-upi-vpa') ? document.getElementById('sim-upi-vpa').value : 'user@upi';
    metaInfo = `UPI VPA: ${vpa || 'customer@upi'}`;
  } else {
    metaInfo = 'Cash payable at service counter';
  }

  try {
    const response = await fetch(`/api/invoices/${activeInvoiceId}/pay`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        payment_method: activePaymentMethod,
        meta_info: metaInfo
      })
    });

    const result = await response.json();

    if (result.success) {
      showToast('Payment successful! Invoice marked as Paid.', 'success');
      closeModal('payment-modal');
      setTimeout(() => {
        window.location.reload();
      }, 800);
    } else {
      showToast(result.error || 'Payment failed. Please try again.', 'error');
      if (payBtn) {
        payBtn.disabled = false;
        payBtn.innerHTML = `Pay $${activeInvoiceAmount.toFixed(2)}`;
      }
    }
  } catch (err) {
    showToast('Network error during simulated payment.', 'error');
    if (payBtn) {
      payBtn.disabled = false;
      payBtn.innerHTML = `Pay $${activeInvoiceAmount.toFixed(2)}`;
    }
  }
}
