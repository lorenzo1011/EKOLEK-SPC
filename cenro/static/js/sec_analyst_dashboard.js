/**
 * Security Analyst Dashboard JavaScript
 * Handles tab switching and section navigation for the security dashboard
 */

/**
 * Tab switching function
 * @param {string} sectionName - Name of the section to display
 * @param {Event} event - Click event (optional)
 */
function showSection(sectionName, event) {
    if (event) {
        event.preventDefault();
    }
    
    // Hide all sections
    var sections = document.querySelectorAll('.dashboard-section');
    sections.forEach(function(section) {
        section.classList.remove('active');
    });
    
    // Show selected section
    var targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    // Update the URL hash so sidebar sub-active tracks it
    if (sectionName && sectionName !== 'overview') {
        history.replaceState(null, '', '#' + sectionName);
    } else {
        history.replaceState(null, '', window.location.pathname);
    }

    // Update sidebar submenu highlight (provided by sidebar.html)
    if (typeof updateSubActive === 'function') {
        updateSubActive();
    }
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Initialize dashboard on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    // Check if there's a hash in the URL
    var hash = window.location.hash.substring(1); // Remove the '#'
    
    if (hash) {
        showSection(hash);
    } else {
        showSection('overview');
    }

    // Intercept sidebar submenu clicks: switch section without full reload
    document.querySelectorAll('#sidebar .submenu a').forEach(function(link) {
        link.addEventListener('click', function(e) {
            var href = this.getAttribute('href') || '';
            var hashIdx = href.indexOf('#');
            // Only intercept links pointing to this same page (security-dashboard) with a hash
            if (hashIdx !== -1) {
                var linkPath = href.substring(0, hashIdx);
                // If the link path matches the current page or is empty
                if (!linkPath || linkPath === window.location.pathname) {
                    e.preventDefault();
                    var section = href.substring(hashIdx + 1);
                    showSection(section);
                }
            }
            // Links without hash (Security Overview, Security Settings) navigate normally
        });
    });
});

/**
 * Handle hash changes for back/forward navigation
 */
window.addEventListener('hashchange', function() {
    var hash = window.location.hash.substring(1);
    if (hash) {
        showSection(hash);
    }
});
