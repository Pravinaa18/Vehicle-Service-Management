// AutoCare Admin Dashboard, Charting & Workflow Control

// 1. Chart.js Dashboard Visualizations
function initAdminCharts(chartData) {
  if (typeof Chart === 'undefined') return;

  // Monthly Revenue Chart
  const revCtx = document.getElementById('adminRevenueChart');
  if (revCtx && chartData.monthlyRevenue) {
    new Chart(revCtx, {
      type: 'line',
      data: {
        labels: chartData.monthlyRevenue.labels,
        datasets: [{
          label: 'Revenue ($)',
          data: chartData.monthlyRevenue.values,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.12)',
          borderWidth: 3,
          fill: true,
          tension: 0.35,
          pointBackgroundColor: '#2563eb',
          pointRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: 'rgba(150, 150, 150, 0.1)' } },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // Appointment Status Breakdown (Doughnut)
  const statusCtx = document.getElementById('adminStatusChart');
  if (statusCtx && chartData.statusBreakdown) {
    new Chart(statusCtx, {
      type: 'doughnut',
      data: {
        labels: chartData.statusBreakdown.labels,
        datasets: [{
          data: chartData.statusBreakdown.values,
          backgroundColor: [
            '#10b981', // Completed
            '#3b82f6', // In Service
            '#f59e0b', // Pending
            '#06b6d4', // Confirmed / Ready
            '#ef4444'  // Cancelled
          ]
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom' }
        }
      }
    });
  }

  // Popular Services (Bar)
  const serviceCtx = document.getElementById('adminServicesChart');
  if (serviceCtx && chartData.topServices) {
    new Chart(serviceCtx, {
      type: 'bar',
      data: {
        labels: chartData.topServices.labels,
        datasets: [{
          label: 'Bookings',
          data: chartData.topServices.values,
          backgroundColor: '#3b82f6',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, ticks: { stepSize: 1 } },
          x: { grid: { display: false } }
        }
      }
    });
  }
}

// 2. Admin Appointment Workflow Modals
let activeAdminAppointmentId = null;

function openAssignMechanicModal(appointmentId, currentMechanicId) {
  activeAdminAppointmentId = appointmentId;
  const select = document.getElementById('assign-mechanic-select');
  if (select && currentMechanicId) {
    select.value = currentMechanicId;
  }
  openModal('assign-mechanic-modal');
}

async function submitAssignMechanic() {
  const select = document.getElementById('assign-mechanic-select');
  const mechanicId = select ? select.value : null;

  if (!mechanicId) {
    showToast('Please select a mechanic', 'warning');
    return;
  }

  try {
    const res = await fetch(`/admin/appointments/${activeAdminAppointmentId}/assign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mechanic_id: mechanicId })
    });
    const data = await res.json();
    if (data.success) {
      showToast('Mechanic assigned successfully!', 'success');
      closeModal('assign-mechanic-modal');
      setTimeout(() => window.location.reload(), 600);
    } else {
      showToast(data.error || 'Failed to assign mechanic', 'error');
    }
  } catch (err) {
    showToast('Server error while assigning mechanic', 'error');
  }
}

function openUpdateStatusModal(appointmentId, currentStatus) {
  activeAdminAppointmentId = appointmentId;
  const select = document.getElementById('update-status-select');
  if (select) {
    select.value = currentStatus;
  }
  openModal('update-status-modal');
}

async function submitUpdateStatus() {
  const select = document.getElementById('update-status-select');
  const notes = document.getElementById('update-status-notes');
  const status = select ? select.value : '';

  if (!status) {
    showToast('Please select a status', 'warning');
    return;
  }

  try {
    const res = await fetch(`/admin/appointments/${activeAdminAppointmentId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        status: status,
        notes: notes ? notes.value : ''
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Appointment status updated to ${status}!`, 'success');
      closeModal('update-status-modal');
      setTimeout(() => window.location.reload(), 600);
    } else {
      showToast(data.error || 'Failed to update status', 'error');
    }
  } catch (err) {
    showToast('Server error while updating status', 'error');
  }
}

// 3. Client-Side Real-time Table Filter
function filterTable(inputId, tableId) {
  const input = document.getElementById(inputId);
  const filter = input.value.toLowerCase();
  const table = document.getElementById(tableId);
  if (!table) return;

  const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
  for (let i = 0; i < rows.length; i++) {
    const text = rows[i].textContent.toLowerCase();
    rows[i].style.display = text.includes(filter) ? '' : 'none';
  }
}
