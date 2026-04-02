/**
 * @file sidebar.js
 * @description Handles sidebar toggle functionality for the backoffice dashboard.
 */

document.addEventListener('DOMContentLoaded', () => {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mainSidebar = document.getElementById('mainSidebar');

    if (sidebarToggle && mainSidebar) {
        sidebarToggle.addEventListener('click', (e) => {
            e.preventDefault();
            // Toggle for desktop/tablet
            if (window.innerWidth >= 768) {
                mainSidebar.classList.toggle('collapsed');
            } else {
                // Toggle for mobile
                mainSidebar.classList.toggle('show');
            }
        });
    }

    // Close sidebar on mobile when clicking outside
    document.addEventListener('click', (e) => {
        if (window.innerWidth < 768 && mainSidebar && sidebarToggle) {
            if (!mainSidebar.contains(e.target) && !sidebarToggle.contains(e.target) && mainSidebar.classList.contains('show')) {
                mainSidebar.classList.remove('show');
            }
        }
    });
});
