/**
 * Career System — 100% Offline Local Studio Client Logic
 * Handles HTML5 Drag & Drop Priority Reordering, Offline URL Ingestion,
 * Live Table Filtering, and Application Actions.
 */

// Initialize Drag & Drop Table Listeners
document.addEventListener('DOMContentLoaded', () => {
  initTableDragAndDrop();
});

let draggedRow = null;

function initTableDragAndDrop() {
  const tableBody = document.getElementById('jobs-table-body');
  if (!tableBody) return;

  const rows = tableBody.querySelectorAll('tr[draggable="true"]');

  rows.forEach((row) => {
    row.addEventListener('dragstart', (e) => {
      draggedRow = row;
      row.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/html', row.innerHTML);
    });

    row.addEventListener('dragend', () => {
      if (draggedRow) {
        draggedRow.classList.remove('dragging');
      }
      rows.forEach((r) => r.classList.remove('drag-over'));
      draggedRow = null;
      updatePriorityNumbersAndPersist();
    });

    row.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      const targetRow = e.currentTarget;
      if (targetRow && targetRow !== draggedRow) {
        targetRow.classList.add('drag-over');
      }
    });

    row.addEventListener('dragleave', (e) => {
      e.currentTarget.classList.remove('drag-over');
    });

    row.addEventListener('drop', (e) => {
      e.preventDefault();
      const targetRow = e.currentTarget;
      targetRow.classList.remove('drag-over');

      if (draggedRow && targetRow && draggedRow !== targetRow) {
        const allRows = Array.from(tableBody.querySelectorAll('tr[draggable="true"]'));
        const draggedIndex = allRows.indexOf(draggedRow);
        const targetIndex = allRows.indexOf(targetRow);

        if (draggedIndex < targetIndex) {
          targetRow.parentNode.insertBefore(draggedRow, targetRow.nextSibling);
        } else {
          targetRow.parentNode.insertBefore(draggedRow, targetRow);
        }
      }
    });
  });
}

// Update table priority index numbers and persist new order to backend
async function updatePriorityNumbersAndPersist() {
  const tableBody = document.getElementById('jobs-table-body');
  if (!tableBody) return;

  const rows = Array.from(tableBody.querySelectorAll('tr[draggable="true"]'));
  const jobIds = [];

  rows.forEach((row, index) => {
    const numCell = row.querySelector('.row-priority-num');
    if (numCell) {
      numCell.textContent = index + 1;
    }
    const jobId = row.getAttribute('data-job-id');
    if (jobId) {
      jobIds.push(parseInt(jobId, 10));
    }
  });

  if (jobIds.length > 0) {
    try {
      await fetch('/api/jobs/reorder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_ids: jobIds })
      });
    } catch (err) {
      console.error('Failed to save priority order:', err);
    }
  }
}

// Handle URL Scrape & Offline Parsing
async function handleUrlScrape(e) {
  e.preventDefault();
  const urlInput = document.getElementById('scrape-url-input');
  const submitBtn = document.getElementById('scrape-submit-btn');
  const statusEl = document.getElementById('scrape-status');

  const url = urlInput.value.trim();
  if (!url) return;

  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...';
  statusEl.classList.remove('hidden');
  statusEl.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin text-blue-400"></i> Fetching snapshot, extracting details & generating tailored documents...';

  try {
    const res = await fetch('/api/jobs/scrape', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: url, candidate_id: 'default' })
    });

    const data = await res.json();
    if (res.ok && data.status === 'success') {
      statusEl.innerHTML = '<i class="fa-solid fa-check-circle text-emerald-400"></i> Job ingested successfully! Redirecting to workspace...';
      setTimeout(() => {
        window.location.href = `/job/${data.job_id}`;
      }, 600);
    } else {
      statusEl.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-rose-400"></i> Error: ${data.detail || 'Failed to ingest URL'}`;
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Ingest & Auto-Tailor';
    }
  } catch (err) {
    console.error('Scrape error:', err);
    statusEl.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-rose-400"></i> Ingestion error: ${err.message}`;
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Ingest & Auto-Tailor';
  }
}

// Handle Manual Job Creation
async function handleManualJobSubmit(e) {
  e.preventDefault();
  const company = document.getElementById('manual-company').value.trim();
  const role_title = document.getElementById('manual-role').value.trim();
  const location = document.getElementById('manual-location').value.trim();
  const job_id_ref = document.getElementById('manual-job-id-ref').value.trim();
  const raw_text = document.getElementById('manual-raw-text').value.trim();

  try {
    const res = await fetch('/api/jobs/manual', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        company: company,
        role_title: role_title,
        location: location,
        job_id_ref: job_id_ref,
        raw_text: raw_text,
        candidate_id: 'default'
      })
    });

    const data = await res.json();
    if (res.ok && data.status === 'success') {
      window.location.href = `/job/${data.job_id}`;
    } else {
      alert('Failed to add job: ' + (data.detail || 'Unknown error'));
    }
  } catch (err) {
    console.error('Manual job create error:', err);
    alert('An error occurred while creating job.');
  }
}

// Delete Job Entry
async function deleteJobEntry(jobId, btn) {
  if (!confirm('Are you sure you want to delete this job application workspace?')) {
    return;
  }

  try {
    const res = await fetch(`/api/jobs/${jobId}`, {
      method: 'DELETE'
    });

    if (res.ok) {
      const row = btn.closest('tr');
      if (row) {
        row.remove();
        updatePriorityNumbersAndPersist();
      }
      const countEl = document.getElementById('job-count-badge');
      if (countEl) {
        const remaining = document.querySelectorAll('#jobs-table-body tr[draggable="true"]').length;
        countEl.textContent = `${remaining} Jobs`;
      }
    } else {
      alert('Failed to delete job entry.');
    }
  } catch (err) {
    console.error('Delete error:', err);
    alert('An error occurred during deletion.');
  }
}

// Filter jobs table live
function filterJobsTable() {
  const query = document.getElementById('table-search').value.toLowerCase().trim();
  const rows = document.querySelectorAll('#jobs-table-body tr[draggable="true"]');

  rows.forEach((row) => {
    const text = row.innerText.toLowerCase();
    if (!query || text.includes(query)) {
      row.style.display = '';
    } else {
      row.style.display = 'none';
    }
  });
}

// Modal Helpers
function openManualJobModal() {
  const modal = document.getElementById('manual-modal');
  if (modal) modal.classList.remove('hidden');
}

function closeManualJobModal() {
  const modal = document.getElementById('manual-modal');
  if (modal) modal.classList.add('hidden');
}
