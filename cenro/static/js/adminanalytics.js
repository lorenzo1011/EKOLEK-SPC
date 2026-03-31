/**
 * Admin Analytics Dashboard JavaScript
 * Handles tabs, year pills, file uploads, and year comparison modal
 */

/* ==================== TAB MANAGEMENT ==================== */

/**
 * Switch between different data view tabs
 * @param {Event} event - Click event
 * @param {string} tabId - ID of tab content to show
 */
function switchTab(event, tabId) {
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
  
  document.getElementById(tabId).classList.add('active');
  event.currentTarget.classList.add('active');
  
  if (window.TabPersistence) {
    window.TabPersistence.saveTabState(tabId);
  }
}

/* ==================== YEAR FILTER (pill-based) ==================== */

/**
 * Set year filter and submit form with loading indicator
 * @param {string} yearType - Year value (current, 2024, 2023, all, compare)
 */
function setYearFilter(yearType) {
  const form = document.getElementById('filterForm');
  const yearFilterInput = document.getElementById('year_filter');
  const startDateInput = document.getElementById('start_date');
  const endDateInput = document.getElementById('end_date');
  
  yearFilterInput.value = yearType;
  
  const currentYear = new Date().getFullYear();
  
  switch (yearType) {
    case 'current':
      startDateInput.value = `${currentYear}-01-01`;
      endDateInput.value = `${currentYear}-12-31`;
      break;
    case 'compare':
    case 'all':
      startDateInput.value = '';
      endDateInput.value = '';
      break;
    default:
      if (/^\d{4}$/.test(yearType)) {
        startDateInput.value = `${yearType}-01-01`;
        endDateInput.value = `${yearType}-12-31`;
      } else {
        startDateInput.value = '';
        endDateInput.value = '';
      }
      break;
  }
  
  // Visual loading feedback on the toolbar card
  const toolbar = document.getElementById('toolbarCard');
  if (toolbar) {
    toolbar.style.opacity = '0.6';
    toolbar.style.pointerEvents = 'none';
  }
  
  form.submit();
}

/**
 * Clear all filters and reload page
 */
function clearYearFilter() {
  const url = new URL(window.location.href);
  url.searchParams.delete('year_filter');
  url.searchParams.delete('compare_year1');
  url.searchParams.delete('compare_year2');
  window.location.href = url.toString();
}

/* ==================== YEAR COMPARISON MODAL ==================== */

/**
 * Open year comparison modal
 */
function openComparisonModal() {
  const modal = document.getElementById('comparisonModal');
  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}

/**
 * Close year comparison modal
 */
function closeComparisonModal() {
  const modal = document.getElementById('comparisonModal');
  modal.classList.remove('active');
  document.body.style.overflow = 'auto';
  
  const y1 = document.getElementById('compareYear1');
  const y2 = document.getElementById('compareYear2');
  if (y1) y1.value = '';
  if (y2) y2.value = '';
}

/* ==================== FILE UPLOAD HANDLING ==================== */

/**
 * Handle Excel file upload for waste data import
 * @param {File} file - Excel file to upload
 */
function handleFileUpload(file) {
  if (!file.name.match(/\.(xlsx|xls)$/)) {
    showMessage('Please select a valid Excel file (.xlsx or .xls)', 'error');
    return;
  }

  const formData = new FormData();
  formData.append('excel_file', file);

  const uploadMessage = document.getElementById('uploadMessage');
  const uploadProgress = document.getElementById('uploadProgress');
  const uploadProgressFill = document.getElementById('uploadProgressFill');

  uploadProgress.style.display = 'block';
  uploadProgressFill.style.width = '0%';
  uploadMessage.innerHTML = '';

  let progress = 0;
  const progressInterval = setInterval(() => {
    progress += 10;
    uploadProgressFill.style.width = progress + '%';
    if (progress >= 90) clearInterval(progressInterval);
  }, 200);

  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

  fetch(window.UPLOAD_URL, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrftoken },
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    clearInterval(progressInterval);
    uploadProgressFill.style.width = '100%';
    
    setTimeout(() => {
      uploadProgress.style.display = 'none';
      uploadProgressFill.style.width = '0%';
    }, 1000);

    if (data.success) {
      let message = `Successfully processed ${data.success_count} transactions`;
      if (data.error_count > 0) {
        message += `. ${data.error_count} errors encountered.`;
        if (data.errors && data.errors.length > 0) {
          message += '<br><br><strong>Errors:</strong><ul>';
          data.errors.forEach(error => { message += `<li>${error}</li>`; });
          message += '</ul>';
        }
        showMessage(message, 'warning');
      } else {
        showMessage(message, 'success');
        setTimeout(() => window.location.reload(), 2000);
      }
    } else {
      showMessage('Error: ' + data.error, 'error');
    }
  })
  .catch(error => {
    clearInterval(progressInterval);
    uploadProgress.style.display = 'none';
    uploadProgressFill.style.width = '0%';
    showMessage('Failed to upload file: ' + error.message, 'error');
  });
}

/**
 * Show upload message with appropriate styling
 * @param {string} message - Message text
 * @param {string} type - success | warning | error
 */
function showMessage(message, type) {
  const alertClass = type === 'success' ? 'alert-success' : (type === 'warning' ? 'alert-warning' : 'alert-error');
  const icon = type === 'success' ? 'bx-check-circle' : (type === 'warning' ? 'bx-error-circle' : 'bx-x-circle');
  
  document.getElementById('uploadMessage').innerHTML = `
    <div class="alert ${alertClass}">
      <i class='bx ${icon}'></i>
      <div>${message}</div>
    </div>
  `;
}

/* ==================== EVENT LISTENERS ==================== */

document.addEventListener('DOMContentLoaded', function() {
  // File upload area events
  const fileUploadArea = document.getElementById('fileUploadArea');
  const fileInput = document.getElementById('excelFileInput');
  
  if (fileUploadArea && fileInput) {
    fileUploadArea.addEventListener('click', () => fileInput.click());
    
    fileUploadArea.addEventListener('dragover', e => {
      e.preventDefault();
      fileUploadArea.classList.add('dragging');
    });
    
    fileUploadArea.addEventListener('dragleave', () => {
      fileUploadArea.classList.remove('dragging');
    });
    
    fileUploadArea.addEventListener('drop', e => {
      e.preventDefault();
      fileUploadArea.classList.remove('dragging');
      if (e.dataTransfer.files.length > 0) handleFileUpload(e.dataTransfer.files[0]);
    });
    
    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) handleFileUpload(fileInput.files[0]);
    });
  }

  // Close comparison modal when clicking backdrop
  document.addEventListener('click', function(event) {
    const modal = document.getElementById('comparisonModal');
    if (modal && event.target === modal) closeComparisonModal();
  });

  // Prevent selecting same year in both comparison dropdowns
  const compareYear1 = document.getElementById('compareYear1');
  const compareYear2 = document.getElementById('compareYear2');
  
  if (compareYear1 && compareYear2) {
    compareYear1.addEventListener('change', function() {
      Array.from(compareYear2.options).forEach(opt => {
        opt.disabled = (opt.value === this.value && this.value !== '');
      });
    });
    compareYear2.addEventListener('change', function() {
      Array.from(compareYear1.options).forEach(opt => {
        opt.disabled = (opt.value === this.value && this.value !== '');
      });
    });
  }
  
  // Tab persistence
  if (window.TabPersistence) {
    window.TabPersistence.init({
      tabButtonsSelector: '.tab-button',
      tabContentsSelector: '.tab-content',
      activeClass: 'active'
    });
  }
});
