// Visual Service Tracking Timeline & Dynamic Live Polling Engine

const STATUS_STAGES = [
  'Confirmed',
  'Vehicle Received',
  'Inspection',
  'In Service',
  'Quality Check',
  'Ready for Pickup',
  'Completed'
];

let liveTrackingTimer = null;
let currentTrackingStatus = '';

function initTrackingTimeline(currentStatus) {
  currentTrackingStatus = currentStatus;
  updateTimelineUI(currentStatus);
}

function updateTimelineUI(currentStatus) {
  const progressBar = document.getElementById('tracking-progress-bar');
  const nodes = document.querySelectorAll('.timeline-node');

  let activeIndex = STATUS_STAGES.findIndex(s => s.toLowerCase() === currentStatus.toLowerCase());
  if (activeIndex === -1) {
    if (currentStatus === 'Assigned') activeIndex = 0;
    else if (currentStatus === 'Pending') activeIndex = 0;
    else if (currentStatus === 'Cancelled') activeIndex = -1;
    else activeIndex = 0;
  }

  // Calculate percentage
  const totalStages = STATUS_STAGES.length;
  const percentage = activeIndex >= 0 ? (activeIndex / (totalStages - 1)) * 100 : 0;

  if (progressBar) {
    progressBar.style.width = `${Math.min(percentage, 100)}%`;
  }

  nodes.forEach((node, idx) => {
    node.classList.remove('active', 'completed');
    if (idx < activeIndex) {
      node.classList.add('completed');
    } else if (idx === activeIndex) {
      node.classList.add('active');
    }
  });
}

function startLiveTracking(appointmentId) {
  if (liveTrackingTimer) clearInterval(liveTrackingTimer);

  liveTrackingTimer = setInterval(async () => {
    try {
      const res = await fetch(`/api/appointments/${appointmentId}/status`);
      if (res.ok) {
        const data = await res.json();
        if (data.status && data.status !== currentTrackingStatus) {
          currentTrackingStatus = data.status;
          updateTimelineUI(data.status);
          
          // Update status label on screen
          const titleEl = document.getElementById('live-status-title');
          if (titleEl) {
            titleEl.textContent = `Status: ${data.status}`;
          }

          const notesEl = document.getElementById('live-tech-notes');
          if (notesEl && data.technician_notes) {
            notesEl.textContent = data.technician_notes;
          }

          showToast(`Service status updated to ${data.status}!`, 'info');
        }
      }
    } catch (err) {
      // Silently continue polling
    }
  }, 6000);
}
